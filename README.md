# Live AI Assistant

A Python application that provides real-time transcription and AI-powered summarization of meetings using AWS services.

## Features

- Real-time audio transcription using AWS Transcribe
- Automatic meeting summarization using AWS Bedrock (Claude v2)
- Multi-window interface for separate transcript and summary views
- Speaker identification and timestamping
- Automatic saving of transcripts and meeting notes
- Robust logging system for debugging and monitoring

## Important Note

⚠️ **Platform Compatibility**: This application was developed and tested on Windows systems and uses Windows-specific commands in some of its internal operations. While the core functionality may work on other operating systems, some features might require modification for:
- macOS
- Linux
- Other Unix-based systems

If you're using a non-Windows system, you will need to:
- Modify console launching mechanisms
- Adjust path handling
- Replace Windows-specific system commands
- Use alternative terminal commands

## Prerequisites

- Python 3.8+
- AWS Account with access to:
  - AWS Transcribe
  - AWS Bedrock (Claude v2)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:  
```bash 
git clone https://github.com/jay-giametta/LiveAIAssistant.git cd LiveAIAssistant`
```
2. Install required packages:  
```bash 
pip install -r requirements.txt`
```
3. Create a configuration file at `config/config.json`:  
```json
{
    "aws_access_key_id": "your_access_key",
    "aws_secret_access_key": "your_secret_key",
    "region": "your_aws_region"
}
```

## Usage

1. Start the application:  
```bash 
python src/main.py`
```

2. The application will open three windows:
   - Main control window
   - Real-time transcript window
   - Live meeting summary window

3. Speak into your microphone to begin transcription

4. Meeting transcripts and summaries are automatically saved to:
   - `output/transcripts/`
   - `output/meeting_notes/`

## Project Structure
```
LiveAiAssistant/
├── src/
│   ├── main.py
│   ├── meeting_service.py
│   ├── console_manager.py
│   ├── transcribe_handler.py
│   ├── summary_handler.py
│   └── session_writer.py
├── config/
│   ├── config.json
│   └── prompt_template.txt
├── output/
│   ├── transcripts/
│   └── meeting_notes/
└── logs/
```
## Configuration

### Logging
- Logs are stored in `logs/current_session.log`
- Configurable log levels and formats
- Separate logging for each process

### Summary Generation
- Customizable summary templates in `config/prompt_template.txt`
- Adjustable update intervals
- Markdown-formatted output