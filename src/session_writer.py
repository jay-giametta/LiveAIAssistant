import time
import aiofiles
from datetime import datetime
from pathlib import Path

class SessionWriter:
    def __init__(self, config: dict):
        self.master_config = config
        self.transcript_file = self.setup_transcript_file()
        self.write_buffer = []
        self.last_write_time = time.time()

    async def flush_buffer(self):
        if not self.write_buffer:
            return
            
        async with aiofiles.open(self.transcript_file, mode='a', encoding='utf-8') as f:
            await f.write('\n'.join(self.write_buffer) + '\n')
        self.write_buffer = []
        self.last_write_time = time.time()
        
    def format_line(self, timestamp, speaker, transcript):
        if speaker is not None:
            return f"[{timestamp}] Speaker {speaker}: {transcript}"
        return f"[{timestamp}] Transcript: {transcript}"

    def setup_transcript_file(self):
        Path('output/transcripts').mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        file_path = f"output/transcripts/transcript_{timestamp}.txt"
        self.write_header(file_path)
        return file_path
    
    async def write_to_console(self, output_line):
        print(output_line)

    async def write_to_file(self, output_line):
        async with aiofiles.open(self.transcript_file, mode='a', encoding='utf-8') as f:
            await f.write(f"{output_line}\n")
    
    def write_header(self, file_path):
        header = f"Transcript started at {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n\n"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header)

    async def write_transcript(self, speaker, transcript):
        timestamp = datetime.now().strftime('%m-%d-%Y %I:%M %p')
        output_line = self.format_line(timestamp, speaker, transcript)
        
        await self.write_to_console(output_line)
        self.write_buffer.append(output_line)
        
        if time.time() - self.last_write_time > 2 or len(self.write_buffer) >= 5:
            await self.flush_buffer()