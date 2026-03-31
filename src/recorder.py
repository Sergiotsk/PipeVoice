"""Microphone audio recording using sounddevice.

Captures audio from the system microphone at 16kHz mono float32,
which is the native format expected by OpenAI's Whisper model.
Uses PortAudio backend via sounddevice for cross-platform compatibility.
"""

import sys

import numpy as np
import sounddevice as sd


class AudioRecorder:
    """Records audio from microphone into a numpy array.

    Records at 16kHz sample rate, mono channel, float32 dtype.
    Uses a dynamic buffer that grows as needed, so there's no
    fixed maximum recording duration.

    Attributes:
        sample_rate: Audio sample rate in Hz (default: 16000).
        channels: Number of audio channels (default: 1 for mono).
        dtype: NumPy dtype for audio samples (default: float32).
        device: Specific device index or None for default.
        _buffer: List to accumulate audio chunks during recording.
        _stream: Active sounddevice InputStream when recording.
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = "float32"

    def __init__(self, device=None):
        """Initialize the audio recorder.

        Args:
            device: Device index to use for recording.
                    If None, uses the system default input device.
                    Use list_devices() to see available devices.
        """
        self.sample_rate = self.SAMPLE_RATE
        self.channels = self.CHANNELS
        self.dtype = self.DTYPE
        self.device = device
        self._buffer = None
        self._stream = None

    @staticmethod
    def list_devices():
        """List all available audio input devices.

        Returns:
            List of dicts with device info (name, max_input_channels, etc.)
        """
        devices = sd.query_devices()
        input_devices = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                input_devices.append(
                    {
                        "index": i,
                        "name": dev["name"],
                        "channels": dev["max_input_channels"],
                        "sample_rate": dev["default_samplerate"],
                    }
                )
        return input_devices

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback called by sounddevice for each audio chunk.

        Appends incoming audio data to the internal buffer.
        Runs in a real-time audio thread, so it must be fast
        and avoid allocations or blocking operations.

        Args:
            indata: NumPy array of shape (frames, channels) with audio data.
            frames: Number of frames in this chunk.
            time_info: Dict with input/output/adapted time info.
            status: Status flags (overflow, underflow, etc.).
        """
        if status:
            print(f"[recorder] Status: {status}", file=sys.stderr)
        if self._buffer is not None:
            self._buffer.append(indata.copy())

    def record(self):
        """Record audio until stop() is called.

        Opens a non-blocking input stream and accumulates audio
        chunks into an internal buffer. Call get_audio() after
        stop() to retrieve the recorded audio as a numpy array.

        Raises:
            sd.PortAudioError: If no input device is available.
            RuntimeError: If already recording.
        """
        if self._stream is not None and self._stream.active:
            raise RuntimeError("Already recording. Call stop() first.")

        self._buffer = []
        self._stream = sd.InputStream(
            device=self.device,
            channels=self.channels,
            samplerate=self.sample_rate,
            dtype=self.dtype,
            callback=self._audio_callback,
        )
        self._stream.start()

    def stop(self):
        """Stop the active recording and close the stream.

        After calling stop(), use get_audio() to retrieve
        the recorded audio data.
        """
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def get_audio(self):
        """Get the recorded audio as a single numpy array.

        Concatenates all buffered chunks into one continuous array
        of shape (total_samples,). Returns the audio flattened to
        1D since we record mono.

        Returns:
            NumPy array of float32 samples, or empty array if nothing recorded.
        """
        if not self._buffer:
            return np.array([], dtype=np.float32)

        audio = np.concatenate(self._buffer, axis=0)
        # Flatten to 1D for mono audio
        if audio.ndim > 1:
            audio = audio.flatten()
        return audio

    def get_duration(self):
        """Get the duration of the current recording in seconds.

        Returns:
            Duration in seconds, or 0.0 if nothing recorded.
        """
        if not self._buffer:
            return 0.0
        total_samples = sum(chunk.shape[0] for chunk in self._buffer)
        return total_samples / self.sample_rate
