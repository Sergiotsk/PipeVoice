"""Speech-to-text transcription using local OpenAI Whisper.

Runs Whisper models entirely locally with no API calls or costs.
Supports all model sizes (tiny, base, small, medium, large) with
lazy loading and caching. Optimized for CPU inference with the
'small' model as default balance of speed and accuracy.

All models are free and open-source (MIT license). No OpenAI API
key or internet connection required after initial model download.
"""

import sys

import numpy as np
import torch
import whisper


class Transcriber:
    """Transcribes audio using local Whisper models.

    Loads the Whisper model on first use (lazy loading) and caches
    it for subsequent transcriptions. This avoids the ~2-5 second
    model load time on every transcription.

    Model sizes and approximate CPU performance:
        tiny  (39M params):  ~3x real-time, lowest accuracy
        base  (74M params):  ~5x real-time, decent for clear speech
        small (244M params): ~10x real-time, good accuracy (default)
        medium(769M params): ~30x real-time, high accuracy, slower
        large(1550M params): ~60x real-time, best accuracy, very slow

    Attributes:
        model_name: Name of the Whisper model to use.
        device: Device to run inference on ('cpu' or 'cuda').
        _model: Loaded Whisper model (None until first use).
    """

    AVAILABLE_MODELS = ("tiny", "base", "small", "medium", "large")

    def __init__(self, model_name="small", device=None):
        """Initialize the transcriber.

        Args:
            model_name: Whisper model size. One of: tiny, base, small,
                       medium, large. Default is 'small' for best
                       CPU speed/accuracy balance.
            device: Compute device. 'cpu' or 'cuda'. If None, CUDA is
                   used automatically when an NVIDIA GPU is available,
                   otherwise falls back to CPU.

        Raises:
            ValueError: If model_name is not a valid Whisper model.
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model '{model_name}'. "
                f"Choose from: {', '.join(self.AVAILABLE_MODELS)}"
            )
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None

    def _load_model(self):
        """Load the Whisper model into memory.

        Downloads the model weights on first use if not cached locally.
        Models are cached in ~/.cache/whisper by default.

        Logs progress to stderr to avoid polluting stdout pipe output.
        """
        print(
            f"[transcriber] Loading Whisper model '{self.model_name}'...",
            file=sys.stderr,
        )
        self._model = whisper.load_model(self.model_name, device=self.device)
        print(
            f"[transcriber] Model loaded successfully.",
            file=sys.stderr,
        )

    @property
    def model(self):
        """Get the loaded Whisper model, loading it if necessary.

        Returns:
            The loaded Whisper model instance.
        """
        if self._model is None:
            self._load_model()
        return self._model

    def transcribe(self, audio: np.ndarray, language=None):
        """Transcribe audio data to text.

        Args:
            audio: NumPy array of float32 audio samples at 16kHz.
            language: Optional language code (e.g., 'es', 'en', 'fr').
                     If None, Whisper auto-detects the language.

        Returns:
            The transcribed text string.

        Raises:
            RuntimeError: If transcription fails.
        """
        if len(audio) == 0:
            return ""

        options = {}
        if language:
            options["language"] = language

        try:
            result = self.model.transcribe(audio, **options)
            return result["text"].strip()
        except Exception as e:
            print(f"[transcriber] Error: {e}", file=sys.stderr)
            raise RuntimeError(f"Transcription failed: {e}") from e

    def get_model_info(self):
        """Get information about the configured model.

        Returns:
            Dict with model name, device, and parameter count.
        """
        info = {
            "model": self.model_name,
            "device": self.device,
        }
        if self._model is not None:
            params = sum(p.numel() for p in self._model.parameters())
            info["parameters"] = f"{params:,}"
            info["loaded"] = "yes"
        else:
            info["loaded"] = "no"
        return info
