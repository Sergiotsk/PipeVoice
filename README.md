# PipeVoice

> Push-to-talk voice transcription CLI tool. Hold F9 to record, release to transcribe. Pipe the output to any AI agent or auto-type into any window.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)

## Features

- **Push-to-talk**: Hold F9 to record, release to transcribe
- **100% free**: Uses local Whisper models — no API keys, no costs, no limits
- **Privacy-first**: Audio never leaves your machine
- **Pipe-friendly**: Output to stdout, pipe to any CLI tool or AI agent
- **Cross-platform**: Works on Windows, Linux, and macOS
- **Configurable**: Choose model size, language, microphone, and trigger mode

## Quick Start

### Installation

Requires [uv](https://docs.astral.sh/uv/).

```bash
# Install globally as a CLI command — no clone needed
uv tool install git+https://github.com/Sergiotsk/PipeVoice.git

# pipevoice is now on your PATH
pipevoice --help
```

For local development:

```bash
git clone https://github.com/Sergiotsk/PipeVoice.git
cd PipeVoice
uv sync --extra dev   # installs pytest too

uv run pipevoice      # run from source
uv run pytest         # run the test suite
```

### Basic Usage

```bash
# Start PipeVoice (default: F9, auto-detect language, small model)
pipevoice

# Hold F9 to speak, release to transcribe
# Transcribed text goes to stdout

# Auto-type mode — types text into the active window
pipevoice --type
```

### Piping to AI Agents

```bash
# Pipe to opencode
pipevoice | opencode

# Pipe to Claude CLI
pipevoice --language en | claude

# Pipe to any tool that reads stdin
pipevoice | your-tool-here
```

## Usage

### Command Line Options

```
pipevoice [OPTIONS]

Options:
  --model {tiny,base,small,medium,large}  Whisper model size (default: small)
  --language LANG                         Language code (es, en, fr, etc.) or auto-detect
  --device N                              Microphone device index
  --list-devices                          Show available microphones and exit
  --type                                  Simulate keyboard and auto-type transcribed text
  --no-vad                                Disable voice activity detection (transcribes everything)
  --vad-threshold THRESHOLD               RMS silence threshold (default: 0.01)
                                          Lower = more sensitive, Higher = louder speech required
  -h, --help                              Show help message
```

### Examples

```bash
# List available microphones (marks the real system default)
pipevoice --list-devices

# Use specific microphone (index 1)
pipevoice --device 1

# English transcription with faster model
pipevoice --model base --language en

# Spanish transcription with higher accuracy model
pipevoice --model medium --language es

# Noisy environment — raise VAD threshold to ignore background noise
pipevoice --vad-threshold 0.03

# Quiet voice or distant microphone — lower VAD threshold
pipevoice --vad-threshold 0.005

# Disable VAD — transcribe everything regardless of silence
pipevoice --no-vad

# Auto-type mode — types text into whatever window is active
pipevoice --type

# Save transcriptions to file
pipevoice | tee transcriptions.txt

# Save AND send to agent
pipevoice | tee -a history.txt | opencode
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
│    (F9)     │     │  (recorder)  │     │ (transcriber)│     │ (text)  │
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
├── pipevoice/                 # Package
│   ├── __init__.py            # Package init
│   ├── main.py                # CLI entry point
│   ├── recorder.py            # Microphone recording (sounddevice)
│   ├── transcriber.py         # Speech-to-text (Whisper)
│   ├── audio_processor.py     # Audio preprocessing
│   └── push_to_talk.py        # Keyboard listener (pynput)
├── examples/
│   └── usage-examples.sh      # Practical pipe examples
├── pyproject.toml
├── .gitignore
└── README.md
```

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
pipevoice

# Show RMS value when audio is discarded — useful for calibrating
pipevoice --vad-threshold 0.01
# stderr: [pipevoice] Silence detected (RMS 0.0032 < 0.01), ignoring.

# Noisy room / fan noise / air conditioning
pipevoice --vad-threshold 0.03

# Soft voice, headset, or far microphone
pipevoice --vad-threshold 0.005

# Disable VAD entirely
pipevoice --no-vad
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

## Changelog

### Unreleased

#### Changed
- **Trigger key**: Changed from `spacebar` to `F9` to avoid conflicts with normal typing
- **Default language**: Changed from Spanish (`es`) to auto-detect — Whisper now detects language automatically
- **Signal handler**: Fixed double-shutdown issue on Ctrl+C — handler now guards against repeated calls

#### Added
- **`--type` flag**: Virtual keyboard mode that auto-types transcribed text into the active window. Useful for dictating into any application without piping.
- **Animated status indicators**: UI with fluid spinners (`🎤 GRABANDO ●○○○` and `📝 PROCESANDO ◓...`) shown on stderr. In `--type` mode, these indicators are dynamically typed and erased in the active window.
- **Anti-Hallucination Filter**: Whisper occasionally hallucinates text during silence or noise (e.g., repeating characters like "වවවවව" or outputting "Subtitles by Amara"). PipeVoice now automatically detects and ignores these hallucinations.
- **`torch>=2.0.0` dependency**: Explicit PyTorch requirement for GPU acceleration support

#### Improved
- Transcription now runs in a background daemon thread, keeping the keyboard listener fully responsive.
- Better thread synchronization between recording, transcription, and UI animation threads.
- Refactored project structure to a proper python package (`pipevoice`).

## License

MIT License — see LICENSE file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

