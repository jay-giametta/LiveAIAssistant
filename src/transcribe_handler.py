import time
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from session_writer import SessionWriter

class TranscribeHandler(TranscriptResultStreamHandler):    
    def __init__(self, output_stream, master_config):
        super().__init__(output_stream)
        self.session_writer = SessionWriter(master_config)
        self.speaker = None
        self.output_stream = output_stream
        self.sentence_endings = {'.', '?', '!'}
        self.buffer = []
        self.last_flush_time = time.time()
        self.max_buffer_size = 10 

    async def flush_buffer(self, force=False):
        current_time = time.time()
        if (force or 
            len(self.buffer) >= self.max_buffer_size or 
            current_time - self.last_flush_time > 1):  # Reduced from 2 seconds
            
            for speaker, transcript in self.buffer:
                await self.handle_segment(speaker, transcript)
            self.buffer = []
            self.last_flush_time = current_time

    def extract_speaker(self, alternative_items):
        for alternative_item in alternative_items:
            if hasattr(alternative_item, 'speaker'):
                return alternative_item.speaker
        return None
    
    async def handle_events(self):
        async for transcript_event in self.output_stream:
            await self.handle_transcript(transcript_event)

    async def handle_segment(self, speaker, transcript):
        await self.session_writer.write_transcript(speaker, transcript)
        self.speaker = speaker

    async def handle_transcript(self, transcript_event):
        transcript_results = transcript_event.transcript.results
        
        for transcript_result in transcript_results:
            if transcript_result.is_partial:
                continue
            
            for alternative in transcript_result.alternatives:
                if not hasattr(alternative, 'items'):
                    continue
                
                speaker = self.extract_speaker(alternative.items)
                alternative_transcript = alternative.transcript.strip()
                
                if alternative_transcript and self.should_output(speaker, alternative_transcript):
                    self.buffer.append((speaker, alternative_transcript))
                    
                    if time.time() - self.last_flush_time > 2 or len(self.buffer) >= 5:
                        await self.flush_buffer()

    def should_output(self, current_speaker, alternative_transcript):
        if current_speaker != self.speaker:
            return True
        return alternative_transcript[-1] in self.sentence_endings