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
echo "   python -m src"
echo "   → Hold SPACE to record, release to transcribe"
echo ""

echo "2. SPECIFY LANGUAGE"
echo "   python -m src --language en"
echo "   python -m src --language es"
echo "   python -m src --language fr"
echo ""

echo "3. CHOOSE MODEL SIZE"
echo "   python -m src --model tiny    # Fastest, least accurate"
echo "   python -m src --model base    # Good speed"
echo "   python -m src --model small   # Default balance"
echo "   python -m src --model medium  # More accurate, slower"
echo ""

echo "4. SELECT MICROPHONE"
echo "   python -m src --list-devices  # Show available mics"
echo "   python -m src --device 1      # Use mic at index 1"
echo ""

echo "5. PIPE TO AI AGENTS"
echo "   python -m src | opencode"
echo "   python -m src | claude"
echo "   python -m src --language en | gemini"
echo ""

echo "6. SAVE TRANSCRIPTIONS"
echo "   python -m src > transcript.txt           # Save to file"
echo "   python -m src | tee transcript.txt       # Save AND display"
echo "   python -m src | tee -a history.txt       # Append to file"
echo ""

echo "7. PROCESS TRANSCRIPTIONS"
echo "   python -m src | wc -w                    # Count words"
echo "   python -m src | grep -i 'importante'     # Search keywords"
echo "   python -m src | tr '[:lower:]' '[:upper:]' # Uppercase"
echo ""

echo "8. COMBINED WORKFLOWS"
echo "   # Transcribe, save, and send to agent"
echo "   python -m src | tee -a daily.log | opencode"
echo ""
echo "   # Transcribe in English, filter, and save"
echo "   python -m src --language en | grep -v 'silence' | tee output.txt"
echo ""
echo "   # Transcribe and count words in real-time"
echo "   python -m src | tee transcript.txt | wc -w"
echo ""

echo "9. AUTOMATION SCRIPT EXAMPLE"
echo "   #!/bin/bash"
echo "   # transcribe-meeting.sh"
echo "   DATE=\$(date +%Y%m%d_%H%M)"
echo "   echo 'Starting meeting transcription...'"
echo "   python -m src --language es | tee \"meeting_\${DATE}.txt\" | opencode"
echo ""

echo "10. PERFORMANCE TIPS"
echo "    # Use smaller model for faster response"
echo "    python -m src --model base"
echo ""
echo "    # Force language for faster transcription"
echo "    python -m src --language es"
echo ""
echo "    # Combine both for best CPU performance"
echo "    python -m src --model base --language es"
echo ""

echo "========================================="
echo "  For detailed docs, see docs/ folder"
echo "========================================="
