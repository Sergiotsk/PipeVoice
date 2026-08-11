"""Audio preprocessing utilities for Whisper transcription.

Provides functions to normalize audio volume and trim silence from
the beginning and end of recordings to optimize transcription speed
and accuracy.
"""

import numpy as np


def normalize_peak(
    audio: np.ndarray, target_db: float = -3.0, reference_percentile: float = 99.0
) -> np.ndarray:
    """Normalize audio to a target peak level in decibels.

    Scales the audio so that a robust "peak" reference corresponds to
    the target dB level. This ensures consistent volume levels
    regardless of microphone input gain.

    Uses a percentile (default: 99th) instead of the absolute maximum
    as the reference sample. A single transient spike — a driver pop,
    a click when the stream starts/stops, electrical noise — can be
    10-100x louder than real speech on a quiet microphone. If that one
    sample were used as the peak, it would dominate the gain
    calculation and leave the actual voice under-amplified, which in
    turn made push-to-talk's silence detection (VAD) discard real
    speech as silence. Bug found in production 2026-08-11 — see
    docs/06-operaciones/BACKLOG.md (local) for the real-world repro.

    Args:
        audio: Input audio as float32 numpy array with values in [-1, 1].
        target_db: Target peak level in decibels. Default is -3.0 dB
                  (leaves some headroom). Must be <= 0.
        reference_percentile: Percentile of |audio| used as the "peak"
                  reference instead of the true max. Default 99.0 —
                  ignores the loudest 1% of samples, which absorbs
                  isolated spikes without needing to detect them
                  explicitly. Use 100.0 to restore the old
                  absolute-max behavior.

    Returns:
        Normalized audio array with same dtype and shape. Note: unlike
        the absolute-max version, a genuine transient spike can end up
        louder than the target after scaling — it gets hard-clipped to
        [-1, 1], which is an acceptable trade-off for one noise sample
        versus losing the entire recording's real content.

    Example:
        >>> audio = np.array([0.01, 0.05, 0.03, 0.08, 0.02])  # quiet
        >>> normalized = normalize_peak(audio, target_db=-3.0)
        >>> print(f"Peak: {np.max(np.abs(normalized)):.3f}")  # ~0.707

        Only amplifies — audio already louder than the target is left
        untouched (gain_db would be negative, never applied):
        >>> loud = np.array([0.1, 0.5, 0.3, 0.8, 0.2])  # peak 0.8 > target
        >>> normalize_peak(loud, target_db=-3.0)[3]  # unchanged
        0.8
    """
    if len(audio) == 0:
        return audio

    reference_peak = np.percentile(np.abs(audio), reference_percentile)
    if reference_peak == 0:
        return audio

    current_db = 20 * np.log10(reference_peak)
    gain_db = target_db - current_db

    if gain_db > 0:
        gain_linear = 10 ** (gain_db / 20)
        audio = audio * gain_linear

    audio = np.clip(audio, -1.0, 1.0)

    return audio


def trim_silence(
    audio: np.ndarray,
    threshold: float = 0.005,
    min_samples: int = 100
) -> np.ndarray:
    """Trim silence from the beginning and end of audio.

    Uses a simple energy-based approach to find the first and last
    samples above the threshold and trims everything else.

    Args:
        audio: Input audio as float32 numpy array with values in [-1, 1].
        threshold: Energy threshold for silence detection. Default 0.005
                  (very quiet). Higher = more aggressive trimming.
        min_samples: Minimum number of samples to keep. Default 100 (6.25ms
                   at 16kHz). Prevents trimming to empty if all audio is
                   below threshold.

    Returns:
        Trimmed audio array. Returns original audio if no valid audio
        found or if trimmed result would be empty.

    Example:
        >>> audio = np.array([0.0, 0.0, 0.0, 0.1, 0.5, 0.3, 0.0, 0.0])
        >>> trimmed = trim_silence(audio, threshold=0.01)
        >>> print(len(trimmed))  # 5 (samples 0.1, 0.5, 0.3, and surrounding)
    """
    if len(audio) == 0 or len(audio) < min_samples:
        return audio

    energy = audio ** 2

    start_idx = 0
    for i in range(len(energy)):
        if energy[i] > threshold:
            start_idx = i
            break

    end_idx = len(energy)
    for i in range(len(energy) - 1, -1, -1):
        if energy[i] > threshold:
            end_idx = i + 1
            break

    trimmed_len = end_idx - start_idx
    if trimmed_len < min_samples:
        return audio

    return audio[start_idx:end_idx]


def apply_soft_limit(audio: np.ndarray, threshold: float = 0.95) -> np.ndarray:
    """Apply soft limiting to prevent clipping.

    Uses a tanh-based soft clipper that smoothly compresses loud
    signals instead of hard clipping. This prevents harsh digital
    distortion while preserving most of the dynamic range.

    Args:
        audio: Input audio as float32 numpy array with values in [-1, 1].
        threshold: Threshold for soft limiting. Default 0.95 leaves
                  5% headroom. Must be in (0, 1].

    Returns:
        Audio with soft limiting applied, values in [-1, 1].

    Example:
        >>> audio = np.array([0.5, 1.0, 0.8, -0.9, -0.5])
        >>> limited = apply_soft_limit(audio, threshold=0.95)
        >>> print(f"Max: {np.max(np.abs(limited)):.3f}")  # < 0.95
    """
    if len(audio) == 0:
        return audio

    if threshold <= 0 or threshold > 1:
        threshold = 0.95

    audio = np.tanh(audio / threshold) * threshold

    return audio


def preprocess_audio(
    audio: np.ndarray,
    normalize: bool = True,
    trim: bool = True,
    soft_limit: bool = True,
    trim_threshold: float = 0.005,
) -> np.ndarray:
    """Apply full preprocessing pipeline to audio for Whisper.

    Combines normalization, soft limiting, and silence trimming in
    the optimal order for best transcription results.

    Args:
        audio: Input audio as float32 numpy array at 16kHz.
        normalize: Whether to normalize peak volume. Default True.
        trim: Whether to trim silence from edges. Default True.
        soft_limit: Whether to apply soft limiting. Default True.
        trim_threshold: Threshold for silence detection. Default 0.005.

    Returns:
        Preprocessed audio ready for Whisper transcription.

    Note:
        Order of operations:
        1. Soft limit (prevents clipping during normalization)
        2. Normalize peak (ensures consistent volume)
        3. Trim silence (removes non-speech at edges)
    """
    if len(audio) == 0:
        return audio

    if soft_limit:
        audio = apply_soft_limit(audio)

    if normalize:
        audio = normalize_peak(audio)

    if trim:
        audio = trim_silence(audio, threshold=trim_threshold)

    return audio