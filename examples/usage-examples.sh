#!/bin/bash
# PipeVoice - Usage Examples
# These examples demonstrate how to use PipeVoice with various tools.
#
# Usage:
#   chmod +x examples/usage-examples.sh
#   ./examples/usage-examples.sh

echo "========================================="
echo "  PipeVoice - Usage Examples"
echo "========================================="
echo ""

echo "1. BASIC USAGE"
echo "   python -m pipevoice"
echo "   → Hold SPACE to record, release to transcribe"
echo ""

echo "2. SPECIFY LANGUAGE"
echo "   python -m pipevoice --language en"
echo "   python -m pipevoice --language es"
echo "   python -m pipevoice --language fr"
echo ""

echo "3. CHOOSE MODEL SIZE"
echo "   python -m pipevoice --model tiny    # Fastest, least accurate"
echo "   python -m pipevoice --model base    # Good speed"
echo "   python -m pipevoice --model small   # Default balance"
echo "   python -m pipevoice --model medium  # More accurate, slower"
echo ""

echo "4. SELECT MICROPHONE"
echo "   python -m pipevoice --list-devices  # Show available mics"
echo "   python -m pipevoice --device 1      # Use mic at index 1"
echo ""

echo "5. PIPE TO AI AGENTS"
echo "   python -m pipevoice | opencode"
echo "   python -m pipevoice | claude"
echo "   python -m pipevoice --language en | gemini"
echo ""

echo "6. SAVE TRANSCRIPTIONS"
echo "   python -m pipevoice > transcript.txt           # Save to file"
echo "   python -m pipevoice | tee transcript.txt       # Save AND display"
echo "   python -m pipevoice | tee -a history.txt       # Append to file"
echo ""

echo "7. PROCESS TRANSCRIPTIONS"
echo "   python -m pipevoice | wc -w                    # Count words"
echo "   python -m pipevoice | grep -i 'importante'     # Search keywords"
echo "   python -m pipevoice | tr '[:lower:]' '[:upper:]' # Uppercase"
echo ""

echo "8. COMBINED WORKFLOWS"
echo "   # Transcribe, save, and send to agent"
echo "   python -m pipevoice | tee -a daily.log | opencode"
echo ""
echo "   # Transcribe in English, filter, and save"
echo "   python -m pipevoice --language en | grep -v 'silence' | tee output.txt"
echo ""
echo "   # Transcribe and count words in real-time"
echo "   python -m pipevoice | tee transcript.txt | wc -w"
echo ""

echo "9. AUTOMATION SCRIPT EXAMPLE"
echo "   #!/bin/bash"
echo "   # transcribe-meeting.sh"
echo "   DATE=\$(date +%Y%m%d_%H%M)"
echo "   echo 'Starting meeting transcription...'"
echo "   python -m pipevoice --language es | tee \"meeting_\${DATE}.txt\" | opencode"
echo ""

echo "10. PERFORMANCE TIPS"
echo "    # Use smaller model for faster response"
echo "    python -m pipevoice --model base"
echo ""
echo "    # Force language for faster transcription"
echo "    python -m pipevoice --language es"
echo ""
echo "    # Combine both for best CPU performance"
echo "    python -m pipevoice --model base --language es"
echo ""

echo "========================================="
echo "  For detailed docs, see docs/ folder"
echo "========================================="
