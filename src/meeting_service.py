import asyncio
import uuid
import boto3
from amazon_transcribe.client import TranscribeStreamingClient
from microphone_handler import MicrophoneHandler
from summary_handler import SummaryHandler
from transcribe_handler import TranscribeHandler

class MeetingService:
    def __init__(self, config: dict, console_type=None):
        self.master_config = config
        self.console_type = console_type
        self.mic_handler = MicrophoneHandler()
        self.summary_handler = SummaryHandler(config, console_type)
        self.audio_queue = asyncio.Queue(maxsize=10) 
        self.setup_aws_session()

    def cleanup_resources(self, mic_stream, mic_client):
        mic_stream.stop_stream()
        mic_stream.close()
        mic_client.terminate()

    async def handle_audio_stream(self, mic_stream):
        print("Listening... Speak into your microphone")
        while True:
            try:
                audio_input = mic_stream.read(self.mic_handler.chunk_size, exception_on_overflow=False)
                if len(audio_input) > 0:
                    try:
                        await asyncio.wait_for(
                            self.audio_queue.put(audio_input),
                            timeout=0.1
                        )
                    except asyncio.TimeoutError:
                        continue
            except Exception as e:
                print(f"Error reading audio: {e}")
                await asyncio.sleep(0.1)

    async def handle_streams(self, mic_stream, transcribe_stream, transcribe_handler):
        await asyncio.gather(
            self.handle_audio_stream(mic_stream),
            self.process_audio_queue(transcribe_stream),
            transcribe_handler.handle_events()
        )

    async def process_audio_queue(self, transcribe_stream):
        while True:
            try:
                audio_chunk = await self.audio_queue.get()
                await transcribe_stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
                self.audio_queue.task_done()
            except Exception as e:
                print(f"Error processing audio chunk: {e}")
                await asyncio.sleep(0.1)

    def setup_aws_session(self):
        boto3.setup_default_session(
            aws_access_key_id=self.master_config['aws_access_key_id'],
            aws_secret_access_key=self.master_config['aws_secret_access_key'],
            region_name=self.master_config['region']
        )

    async def setup_transcribe_stream(self, transcribe_client):
        return await transcribe_client.start_stream_transcription(
            language_code="en-US",
            media_sample_rate_hz=16000,
            media_encoding="pcm",
            show_speaker_label=True,
            enable_partial_results_stabilization=True,
            partial_results_stability="medium",
            session_id=str(uuid.uuid4())
        )

    def setup_transcript_handler(self, transcribe_stream):
        transcribe_handler = TranscribeHandler(
            transcribe_stream.output_stream,
            self.master_config
        )
        self.summary_handler.transcript_file = transcribe_handler.session_writer.transcript_file
        return transcribe_handler
        
    async def start_meeting(self):
        if self.console_type == "summary":
            await self.summary_handler.display_summary()
            return

        transcribe_client = TranscribeStreamingClient(region=self.master_config['region'])
        mic_stream, mic_client = self.mic_handler.create_stream()
        transcribe_stream = await self.setup_transcribe_stream(transcribe_client)
        transcribe_handler = self.setup_transcript_handler(transcribe_stream)

        try:
            await self.handle_streams(mic_stream, transcribe_stream, transcribe_handler)
        finally:
            self.cleanup_resources(mic_stream, mic_client)