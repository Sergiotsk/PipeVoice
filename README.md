# PipeVoice

> Push-to-talk voice transcription CLI tool. Hold spacebar to record, release to transcribe. Pipe the output to any AI agent.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## Features

- **Push-to-talk**: Hold spacebar to record, release to transcribe
- **100% free**: Uses local Whisper models — no API keys, no costs, no limits
- **Privacy-first**: Audio never leaves your machine
- **Pipe-friendly**: Output to stdout, pipe to any CLI tool or AI agent
- **Cross-platform**: Works on Windows, Linux, and macOS
- **Configurable**: Choose model size, language, and microphone

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/pipevoice.git
cd pipevoice

# Create a virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Start PipeVoice (default: spacebar, auto-detect language, small model)
python -m src

# Hold SPACE to speak, release to transcribe
# Transcribed text goes to stdout
```

### Piping to AI Agents

```bash
# Pipe to opencode
python -m src | opencode

# Pipe to Claude CLI
python -m src --language en | claude

# Pipe to any tool that reads stdin
python -m src | your-tool-here
```

## Usage

### Command Line Options

```
python -m src [OPTIONS]

Options:
  --model {tiny,base,small,medium,large}  Whisper model size (default: small)
  --language LANG                         Language code (es, en, fr, etc.) or auto-detect
  --device N                              Microphone device index
  --list-devices                          Show available microphones and exit
  --no-vad                                Disable voice activity detection (transcribes everything)
  --vad-threshold THRESHOLD               RMS silence threshold (default: 0.01)
                                          Lower = more sensitive, Higher = louder speech required
  -h, --help                              Show help message
```

### Examples

```bash
# List available microphones (marks the real system default)
python -m src --list-devices

# Use specific microphone (index 1)
python -m src --device 1

# English transcription with faster model
python -m src --model base --language en

# Spanish transcription with higher accuracy model
python -m src --model medium --language es

# Noisy environment — raise VAD threshold to ignore background noise
python -m src --vad-threshold 0.03

# Quiet voice or distant microphone — lower VAD threshold
python -m src --vad-threshold 0.005

# Disable VAD — transcribe everything regardless of silence
python -m src --no-vad

# Save transcriptions to file
python -m src | tee transcriptions.txt

# Save AND send to agent
python -m src | tee -a history.txt | opencode
```

### Model Selection Guide

| Model | Parameters | Size | Speed (CPU) | Accuracy | Best For |
|-------|-----------|------|-------------|----------|----------|
| tiny | 39M | ~75 MB | ~3x real-time | Low | Quick tests, very slow CPUs |
| base | 74M | ~142 MB | ~5x real-time | Decent | Clear speech, good speed |
| **small** | 244M | ~466 MB | ~10x real-time | **Good** | **Default - best balance** |
| medium | 769M | ~1.5 GB | ~30x real-time | High | High accuracy, powerful CPU |
| large | 1550M | ~3 GB | ~60x real-time | Best | Maximum accuracy, GPU recommended |

> **Note**: The model downloads automatically on first use (~466 MB for `small`). Subsequent runs load from cache.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│  pynput     │────▶│ sounddevice  │────▶│   Whisper    │────▶│ stdout  │
│ (spacebar)  │     │  (recorder)  │     │ (transcriber)│     │ (text)  │
└─────────────┘     └──────────────┘     └──────────────┘     └────┬────┘
                                                                   │
                                                            ┌──────▼──────┐
                                                            │ AI Agent    │
                                                            │ (opencode,  │
                                                            │  claude...) │
                                                            └─────────────┘
```

### Project Structure

```
PipeVoice/
├── src/
│   ├── __init__.py           # Package init
│   ├── main.py               # CLI entry point
│   ├── recorder.py           # Microphone recording (sounddevice)
│   ├── transcriber.py        # Speech-to-text (Whisper)
│   └── push_to_talk.py       # Keyboard listener (pynput)
├── docs/
│   ├── 01-audio-capture.md   # Audio digital concepts & sounddevice
│   ├── 02-keyboard-hooks.md  # Keyboard hooks & pynput
│   ├── 03-whisper-local.md   # Whisper models & local inference
│   ├── 04-numpy-audio.md     # NumPy for audio processing
│   └── 05-cli-pipe-pattern.md # Unix pipes & CLI best practices
├── examples/
│   └── usage-examples.sh     # Practical pipe examples
├── requirements.txt
├── .gitignore
└── README.md
```

## Documentation

Each document in `docs/` is written in a teaching style — like a programming professor explaining concepts to a student, with specific details, specifications, examples, and professional tips.

- [01 - Audio Capture](docs/01-audio-capture.md) — Digital audio, sample rate, sounddevice, PortAudio
- [02 - Keyboard Hooks](docs/02-keyboard-hooks.md) — pynput, event listeners, cross-platform input
- [03 - Whisper Local](docs/03-whisper-local.md) — openai-whisper, models, CPU optimization
- [04 - NumPy Audio](docs/04-numpy-audio.md) — NumPy arrays for audio processing
- [05 - CLI Pipe Pattern](docs/05-cli-pipe-pattern.md) — Unix pipes, stdin/stdout, CLI best practices

## Platform Notes

### Windows

Works out-of-the-box. PortAudio is included in the sounddevice wheel.

### Linux

May require PortAudio development headers:

```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev

# Fedora
sudo dnf install portaudio-devel

# Arch
sudo pacman -S portaudio
```

### macOS

May require microphone permissions in System Preferences → Security & Privacy → Microphone.

## GPU Acceleration

PipeVoice automatically uses NVIDIA GPU when available — no configuration needed.

At startup you will see the detected device:

```
[pipevoice] Model: small | Device: cuda    ← GPU detected
[pipevoice] Model: small | Device: cpu     ← CPU fallback
```

GPU inference is 5-10x faster than CPU, especially noticeable with `medium` and `large` models.

## Voice Activity Detection (VAD)

VAD filters out recordings where no real speech was detected, preventing Whisper from running on silence.

```bash
# Default threshold (works well in quiet environments)
python -m src

# Show RMS value when audio is discarded — useful for calibrating
python -m src --vad-threshold 0.01
# stderr: [pipevoice] Silence detected (RMS 0.0032 < 0.01), ignoring.

# Noisy room / fan noise / air conditioning
python -m src --vad-threshold 0.03

# Soft voice, headset, or far microphone
python -m src --vad-threshold 0.005

# Disable VAD entirely
python -m src --no-vad
```

VAD state is shown at startup:
```
[pipevoice] VAD: on (threshold=0.01)
[pipevoice] VAD: off
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "PortAudio not found" | Install portaudio19-dev (Linux) |
| No audio recorded | Check microphone permissions, use `--list-devices` |
| Transcription too slow | Use `--model base` or `--model tiny` |
| Wrong language detected | Force language with `--language es` |
| Valid speech gets ignored | Lower `--vad-threshold` or use `--no-vad` |
| Silence triggers transcription | Raise `--vad-threshold` |
| GPU not detected | Ensure CUDA-compatible PyTorch is installed |

## License

MIT License — see LICENSE file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
# PipeVoice
