# Live AI Assistant

Real-time audio transcription using AWS Transcribe.

## Setup

1. Make sure you have Python 3.7 or later installed
2. Copy `config/config.example.json` to `config/config.json`
3. Edit `config/config.json` with your AWS credentials
4. Run `setup.bat`
5. Run `start_transcription.bat` to start the application

## Manual Setup

If you prefer to set up manually:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

## Running the App

After setup, you can start the app by:
- Double-clicking `start_transcription.bat`
  or
- Running these commands:
  ```bash
  .\venv\Scripts\activate
  python -m src.main
  ```