"""Tests for audio_processor.normalize_peak() robustness to transient spikes.

Bug real de producción, 2026-08-11: un pico transitorio (click del
driver, pop al arrancar/parar el stream, ruido eléctrico) mucho más
fuerte que la voz real dominaba la normalización basada en np.max(),
dejando la voz real sub-amplificada — el VAD de main.py la descartaba
como silencio. Ver docs/06-operaciones/BACKLOG.md (local, no
versionado) para el repro real reportado por el usuario.
"""

import numpy as np
import pytest

from pipevoice.audio_processor import normalize_peak, preprocess_audio


def _quiet_voice_like_signal(n=5 * 16000, peak=0.003):
    """Señal sintética con envolvente variable, como voz real floja
    (mismo orden de magnitud que se midió con examples/diagnose_mic.py
    en el hardware real donde apareció el bug)."""
    t = np.linspace(0, n / 16000, n, dtype=np.float32)
    envelope = 0.3 + 0.7 * np.abs(np.sin(2 * np.pi * 2 * t))
    return (peak * np.sin(2 * np.pi * 180 * t) * envelope).astype(np.float32)


def _vad_rms(audio):
    """Replica el cálculo de RMS que hace main.py después de preprocess_audio."""
    processed = preprocess_audio(audio, trim=True, normalize=True, soft_limit=True)
    if len(processed) == 0:
        return 0.0
    k = max(1, len(processed) // 10)
    top_energy = np.partition(processed**2, -k)[-k:]
    return float(np.sqrt(np.mean(top_energy)))


class TestNormalizePeakRobustToSpikes:
    def test_single_loud_spike_does_not_suppress_real_voice(self):
        """El bug real: un sample ~80x más fuerte que la voz no debe
        dejar la voz sub-amplificada."""
        voice = _quiet_voice_like_signal()
        with_spike = voice.copy()
        with_spike[100] = 0.25  # ~80x el peak de la voz real

        rms_with_spike = _vad_rms(with_spike)
        rms_without_spike = _vad_rms(voice)

        # Con y sin spike, el resultado debe ser prácticamente el mismo —
        # el spike no puede arruinar la normalización de toda la grabación.
        assert rms_with_spike == pytest.approx(rms_without_spike, rel=0.05)

    def test_spike_case_stays_above_default_vad_threshold(self):
        """Regresión directa del bug real: antes del fix esto daba 0.0113
        (peligrosamente cerca del umbral 0.01); debe quedar cómodamente
        por encima."""
        voice = _quiet_voice_like_signal()
        voice[100] = 0.25

        rms = _vad_rms(voice)

        assert rms > 0.5  # antes del fix: ~0.011

    def test_clean_quiet_voice_still_normalizes_correctly(self):
        """Sin spike, el comportamiento de siempre (amplificar voz floja
        a un nivel usable) no debe cambiar."""
        voice = _quiet_voice_like_signal()

        rms = _vad_rms(voice)

        assert rms > 0.5

    def test_true_digital_silence_stays_silent(self):
        """Silencio real (dispositivo equivocado / sin señal, todo en
        cero) sigue sin amplificarse — normalize_peak no inventa señal
        de la nada."""
        silence = np.zeros(5 * 16000, dtype=np.float32)

        result = normalize_peak(silence)

        assert np.max(np.abs(result)) == 0.0

    def test_reference_percentile_100_restores_old_max_based_behavior(self):
        """El parámetro reference_percentile=100.0 preserva el
        comportamiento viejo (np.max) para quien lo necesite explícitamente.
        Usa audio flojo (peak < target) para que la amplificación
        realmente se dispare — con audio ya fuerte, normalize_peak no
        atenúa (ver docstring de la función)."""
        quiet_audio = np.array([0.01, 0.05, 0.03, 0.08, 0.02], dtype=np.float32)

        result = normalize_peak(quiet_audio, reference_percentile=100.0)

        assert np.max(np.abs(result)) == pytest.approx(0.7079, rel=0.01)

    def test_normalize_peak_does_not_attenuate_already_loud_audio(self):
        """normalize_peak solo amplifica audio flojo — si ya supera el
        target, gain_db es negativo y no se aplica (nunca atenúa)."""
        loud_audio = np.array([0.1, 0.5, 0.3, 0.8, 0.2], dtype=np.float32)

        result = normalize_peak(loud_audio)

        np.testing.assert_array_almost_equal(result, loud_audio)
