"""PipeVoice - Push-to-talk voice transcription CLI tool.

Records audio from microphone when spacebar is held,
transcribes with local Whisper model, outputs text to stdout.

Usage:
    python -m src | opencode
    python -m src --language en | claude
    python -m src --list-devices
"""

from pipevoice.push_to_talk import PushToTalk
from pipevoice.recorder import AudioRecorder
from pipevoice.transcriber import Transcriber

__version__ = "1.0.0"
