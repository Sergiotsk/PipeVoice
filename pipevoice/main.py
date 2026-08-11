"""PipeVoice CLI entry point.

Orchestrates the push-to-talk workflow:
1. Listen for spacebar press
2. Record audio from microphone
3. Transcribe with local Whisper model
4. Output text to stdout (for piping to other tools)

All status messages go to stderr so they don't interfere
with the stdout pipe that carries the transcribed text.
"""

import argparse
import signal
import sys
import threading
import time

import numpy as np

from pipevoice.push_to_talk import PushToTalk
from pipevoice.recorder import AudioRecorder
from pipevoice.transcriber import Transcriber
from pipevoice.audio_processor import preprocess_audio


def parse_args():
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="pipevoice",
        description=(
            "Push-to-talk voice transcription tool. "
            "Hold F9 to record, release to transcribe. "
            "Output goes to stdout, or simulates keyboard if --type is used."
        ),
        epilog=(
            "Examples:\n"
            "  python -m pipevoice                          # Default (F9, auto-detect)\n"
            "  python -m pipevoice --type                   # Auto-type transcribed text\n"
            "  python -m pipevoice --language en            # English transcription\n"
            "  python -m pipevoice --model base             # Faster, less accurate model\n"
            "  python -m pipevoice --list-devices           # Show available microphones\n"
            "  python -m pipevoice --device 1               # Use specific microphone\n"
            "\n"
            "Pipe examples:\n"
            "  python -m pipevoice | opencode               # Send to opencode agent\n"
            "  python -m pipevoice | claude                 # Send to Claude CLI\n"
            "  python -m pipevoice | tee transcript.txt     # Save and display\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--model",
        choices=Transcriber.AVAILABLE_MODELS,
        default="small",
        help="Whisper model size (default: small). "
        "tiny/base = faster, medium/large = more accurate but slower.",
    )

    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Language code for transcription (e.g., es, en, fr). "
        "If not specified, Whisper auto-detects the language.",
    )

    parser.add_argument(
        "--device",
        type=int,
        default=None,
        help="Microphone device index. Use --list-devices to see options.",
    )

    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio input devices and exit.",
    )

    parser.add_argument(
        "--type",
        action="store_true",
        help="Simulate a virtual keyboard and type the transcribed text into the active window.",
    )

    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="Disable voice activity detection. "
        "Records everything while key is held, including silence.",
    )

    parser.add_argument(
        "--vad-threshold",
        type=float,
        default=0.01,
        metavar="THRESHOLD",
        help="RMS energy threshold for silence detection (default: 0.01). "
        "Lower = more sensitive to quiet speech. "
        "Higher = only transcribes loud audio. "
        "Ignored if --no-vad is set.",
    )

    return parser.parse_args()


def list_audio_devices():
    """Print available audio input devices to stdout."""
    devices = AudioRecorder.list_devices()
    if not devices:
        print("No audio input devices found.", file=sys.stderr)
        sys.exit(1)

    import sounddevice as sd
    default_input = sd.default.device[0]

    print("Available audio input devices:")
    print("-" * 60)
    for dev in devices:
        default_marker = " (default)" if dev["index"] == default_input else ""
        print(
            f"  [{dev['index']}] {dev['name']}{default_marker}\n"
            f"       Channels: {dev['channels']}, "
            f"Sample rate: {dev['sample_rate']} Hz"
        )
    print("-" * 60)


def main():
    """Main entry point for PipeVoice CLI."""
    args = parse_args()

    if args.list_devices:
        list_audio_devices()
        return

    # Setup signal handler for clean exit
    running = True

    def signal_handler(sig, frame):
        nonlocal running
        if running:
            running = False
            print("\n[pipevoice] Shutting down...", file=sys.stderr)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize components
    recorder = AudioRecorder(device=args.device)
    transcriber = Transcriber(model_name=args.model)
    ptt = PushToTalk()

    print("[pipevoice] Starting PipeVoice...", file=sys.stderr)
    print(f"[pipevoice] Model: {args.model} | Device: {transcriber.device}", file=sys.stderr)
    print(f"[pipevoice] Language: {args.language or 'auto-detect'}", file=sys.stderr)
    print(f"[pipevoice] VAD: {'off' if args.no_vad else f'on (threshold={args.vad_threshold})'}", file=sys.stderr)
    print("[pipevoice] Press and hold F9 to record, release to transcribe.", file=sys.stderr)
    print("[pipevoice] Press Ctrl+C to exit.", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    recording_indicator_active = False
    transcribing_indicator_active = False
    is_actively_recording = False
    is_transcribing = False
    ui_cleanup_in_progress = False
    anim_thread = None

    def recording_animation():
        chars = ['●○○○', '○●○○', '○○●○', '○○○●', '○○●○', '○●○○']
        console_msg = "🎤 GRABANDO"
        i = 0
        
        if args.type:
            try:
                import keyboard
                keyboard.write(f"{chars[i]}")
            except Exception:
                pass

        while recording_indicator_active:
            print(f"\r[pipevoice] {console_msg} {chars[i % len(chars)]} (soltá F9)  ", end="", file=sys.stderr, flush=True)
            time.sleep(0.15)
            i += 1
            if args.type and recording_indicator_active:
                try:
                    import keyboard
                    for _ in range(len(chars[0])):
                        keyboard.send('backspace')
                    keyboard.write(f"{chars[i % len(chars)]}")
                except Exception:
                    pass

        print("\r" + " " * 80 + "\r", end="", file=sys.stderr, flush=True)
        
        if args.type:
            try:
                import keyboard
                for _ in range(len(chars[0])):
                    keyboard.send('backspace')
            except Exception:
                pass

    def transcribing_animation():
        # Smooth clockwise rotation
        chars = ['◓', '◑', '◒', '◐']
        console_msg = "📝 PROCESANDO"
        i = 0

        if args.type:
            try:
                import keyboard
                keyboard.write(f"{chars[i]}")
            except Exception:
                pass

        while transcribing_indicator_active:
            print(f"\r[pipevoice] {console_msg} {chars[i % len(chars)]}...", end="", file=sys.stderr, flush=True)
            time.sleep(0.15)
            i += 1
            if args.type and transcribing_indicator_active:
                try:
                    import keyboard
                    for _ in range(len(chars[0])):
                        keyboard.send('backspace')
                    keyboard.write(f"{chars[i % len(chars)]}")
                except Exception:
                    pass

        print("\r" + " " * 80 + "\r", end="", file=sys.stderr, flush=True)

        if args.type:
            try:
                import keyboard
                for _ in range(len(chars[0])):
                    keyboard.send('backspace')
            except Exception:
                pass

    def on_key_press(key):
        """Start recording when trigger key is pressed."""
        nonlocal recording_indicator_active, is_actively_recording, anim_thread
        
        if transcribing_indicator_active or is_transcribing or is_actively_recording or ui_cleanup_in_progress:
            return  # Ignore rapid spamming while busy

        is_actively_recording = True
        recording_indicator_active = True
        anim_thread = threading.Thread(target=recording_animation, daemon=True)
        anim_thread.start()
        recorder.record()

    def on_key_release(key):
        """Stop recording and transcribe when trigger key is released."""
        nonlocal recording_indicator_active, is_actively_recording, anim_thread
        
        if not is_actively_recording:
            return
            
        is_actively_recording = False
        recording_indicator_active = False
        if anim_thread:
            anim_thread.join()
            anim_thread = None
            
        # Stop stream first so no more chunks are added, then read the buffer.
        recorder.stop()
        audio = recorder.get_audio()
        audio = preprocess_audio(audio, trim=True, normalize=True, soft_limit=True)
        duration = recorder.get_duration()

        print(f"[pipevoice] Recorded {duration:.1f}s of audio. ({len(audio)/16000:.1f}s after processing)", file=sys.stderr)

        if duration < 0.3:
            print("[pipevoice] Too short, ignoring.", file=sys.stderr)
            return

        if not args.no_vad:
            # Use top 10% loudest samples to prevent long pauses from diluting the mean energy
            k = max(1, len(audio) // 10)
            top_energy = np.partition(audio ** 2, -k)[-k:]
            rms = float(np.sqrt(np.mean(top_energy)))
            
            if rms < args.vad_threshold:
                print(
                    f"[pipevoice] Silence detected (RMS {rms:.4f} < {args.vad_threshold}), ignoring.",
                    file=sys.stderr,
                )
                return

        # Run transcription in a daemon thread so the keyboard listener
        # is never blocked and the spacebar stays responsive.
        def _transcribe():
            nonlocal transcribing_indicator_active, is_transcribing, anim_thread
            is_transcribing = True
            transcribing_indicator_active = True
            anim_thread = threading.Thread(target=transcribing_animation, daemon=True)
            anim_thread.start()
            
            text = transcriber.transcribe(audio, language=args.language)
            
            transcribing_indicator_active = False
            if anim_thread:
                anim_thread.join()
                anim_thread = None
            
            if text:
                # Output ONLY to stdout - this is what gets piped
                print(text)
                # Flush immediately so piped tools receive it right away
                sys.stdout.flush()
                
                # If virtual keyboard mode is on, type the text into the active window
                if args.type:
                    try:
                        import keyboard
                        keyboard.write(text + " ")
                    except Exception as e:
                        print(f"[pipevoice] Keyboard type failed: {e}", file=sys.stderr)
            else:
                print("[pipevoice] No speech detected.", file=sys.stderr)
                
            is_transcribing = False

        threading.Thread(target=_transcribe, daemon=True).start()

    ptt._on_press = on_key_press
    ptt._on_release = on_key_release

    # Pre-load the model before starting the listener
    # This avoids a delay on the first transcription
    transcriber.model

    # Start listening
    ptt.start()

    # Keep main thread alive
    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        recording_indicator_active = False
        transcribing_indicator_active = False
        time.sleep(0.2)  # Give animation threads time to clear the UI
        ptt.stop()
        print("[pipevoice] Goodbye!", file=sys.stderr)


if __name__ == "__main__":
    main()
