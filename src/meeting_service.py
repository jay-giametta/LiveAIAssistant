import asyncio
import uuid
import boto3
import logging
from amazon_transcribe.client import TranscribeStreamingClient
from microphone_handler import MicrophoneHandler
from summary_handler import SummaryHandler
from transcribe_handler import TranscribeHandler

logger = logging.getLogger(__name__)

class MeetingService:
    """
    A service class that manages real-time audio transcription for meetings using AWS Transcribe.

    This class coordinates audio capture from a microphone, streaming to AWS Transcribe,
    and handling of transcription results. It can also display meeting summaries for
    previously recorded sessions.

    Attributes:
        master_config (dict): Configuration dictionary containing AWS credentials and settings.
            Must include 'aws_access_key_id', 'aws_secret_access_key', and 'region'.
        console_type (str): Determines the operation mode.
            Either 'summary' for viewing past meetings or None for live transcription.
        mic_handler (MicrophoneHandler): Handles microphone input operations.
        summary_handler (SummaryHandler): Manages meeting summary generation and display.
        audio_queue (asyncio.Queue): Queue for managing audio chunks before transmission.
            Limited to 10 chunks maximum to prevent memory overflow.
    """

    def __init__(self, config: dict, console_type=None):
        """
        Initialize the MeetingService with configuration and console type.

        Args:
            config (dict): AWS and application configuration settings.
                Must contain AWS credentials and region information.
            console_type (str, optional): Type of console to run.
                Use 'summary' for summary view, None for live transcription.

        Raises:
            ValueError: If required configuration is missing or invalid
            Exception: For any unexpected initialization errors
        """
        try:
            logger.info(f"Initializing MeetingService with console type: {console_type}")
            self.master_config = config
            self.console_type = console_type
            self.mic_handler = MicrophoneHandler()
            self.summary_handler = SummaryHandler(config, console_type)
            self.audio_queue = asyncio.Queue(maxsize=10)
            self.setup_aws_session()
            logger.debug("MeetingService initialization complete")
        except Exception as e:
            logger.error(f"Failed to initialize MeetingService: {str(e)}", exc_info=True)
            raise

    def cleanup_resources(self, mic_stream, mic_client):
        """
        Clean up microphone resources and terminate the audio client.

        Ensures proper shutdown of audio resources by stopping and closing
        the microphone stream and terminating the client.

        Args:
            mic_stream: The active microphone stream to be closed.
            mic_client: The microphone client to be terminated.

        Raises:
            Exception: If there's an error during resource cleanup
        """
        try:
            logger.info("Cleaning up microphone resources")
            mic_stream.stop_stream()
            mic_stream.close()
            mic_client.terminate()
            logger.debug("Microphone resources cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during resource cleanup: {str(e)}", exc_info=True)
            raise

    async def handle_audio_stream(self, mic_stream):
        """
        Continuously read audio from the microphone and add it to the processing queue.

        Manages real-time audio capture and buffering, handling potential overflow
        conditions and maintaining continuous audio flow.

        Args:
            mic_stream: The active microphone stream to read from.
                Must be initialized and ready for reading.

        Raises:
            asyncio.TimeoutError: If the audio queue is full
            Exception: For errors during audio capture or processing
        """
        logger.info("Starting audio stream handling")
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
                        logger.debug("Audio queue full, skipping chunk")
                        continue
            except Exception as e:
                logger.error(f"Error reading audio: {str(e)}")
                await asyncio.sleep(0.1)

    async def handle_streams(self, mic_stream, transcribe_stream, transcribe_handler):
        """
        Coordinate the concurrent processing of audio input, transcription, and event handling.

        Manages the asynchronous operation of multiple streams including microphone input,
        AWS Transcribe processing, and result handling.

        Args:
            mic_stream: The active microphone stream for audio capture.
            transcribe_stream: The AWS Transcribe streaming session for processing audio.
            transcribe_handler: Handler for processing transcription results.

        Raises:
            asyncio.CancelledError: If the stream processing is interrupted
            Exception: For any errors during stream coordination
        """
        try:
            logger.info("Starting stream coordination")
            await asyncio.gather(
                self.handle_audio_stream(mic_stream),
                self.process_audio_queue(transcribe_stream),
                transcribe_handler.handle_events()
            )
        except Exception as e:
            logger.error(f"Error in stream coordination: {str(e)}", exc_info=True)
            raise

    async def process_audio_queue(self, transcribe_stream):
        """
        Process audio chunks from the queue and send them to AWS Transcribe.

        Continuously monitors the audio queue, sending chunks to AWS Transcribe
        for processing while handling backpressure and potential errors.

        Args:
            transcribe_stream: The AWS Transcribe streaming session.
                Must be initialized and ready for receiving audio.

        Raises:
            asyncio.QueueEmpty: If the audio queue is empty
            Exception: For errors in audio processing or transmission
        """
        logger.info("Starting audio queue processing")
        while True:
            try:
                audio_chunk = await self.audio_queue.get()
                await transcribe_stream.input_stream.send_audio_event(audio_chunk=audio_chunk)
                self.audio_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing audio chunk: {str(e)}")
                await asyncio.sleep(0.1)

    def setup_aws_session(self):
        """
        Configure AWS credentials using the provided configuration.

        Initializes the AWS session with credentials from the master configuration,
        setting up access for AWS Transcribe services.

        Raises:
            ValueError: If required AWS credentials are missing
            boto3.exceptions.BotoCoreError: For AWS configuration errors
            Exception: For any unexpected configuration errors
        """
        try:
            logger.info("Setting up AWS session")
            boto3.setup_default_session(
                aws_access_key_id=self.master_config['aws_access_key_id'],
                aws_secret_access_key=self.master_config['aws_secret_access_key'],
                region_name=self.master_config['region']
            )
            logger.debug("AWS session configured successfully")
        except Exception as e:
            logger.error(f"Failed to setup AWS session: {str(e)}", exc_info=True)
            raise

    async def setup_transcribe_stream(self, transcribe_client):
        """
        Configure and initialize an AWS Transcribe streaming session.

        Sets up a new transcription stream with specified parameters for
        real-time audio processing and speaker identification.

        Args:
            transcribe_client: The AWS Transcribe client instance.
                Must be initialized with proper credentials.

        Returns:
            The configured transcription stream ready for use.

        Raises:
            boto3.exceptions.BotoCoreError: For AWS service errors
            Exception: For stream initialization failures
        """
        try:
            logger.info("Setting up AWS Transcribe stream")
            stream = await transcribe_client.start_stream_transcription(
                language_code="en-US",
                media_sample_rate_hz=16000,
                media_encoding="pcm",
                show_speaker_label=True,
                session_id=str(uuid.uuid4())
            )
            logger.debug("Transcribe stream setup complete")
            return stream
        except Exception as e:
            logger.error(f"Failed to setup transcribe stream: {str(e)}", exc_info=True)
            raise

    def setup_transcript_handler(self, transcribe_stream):
        """
        Initialize the transcript handler and configure summary handling.

        Creates and configures the handler for processing transcription results
        and managing the connection with summary generation.

        Args:
            transcribe_stream: The active AWS Transcribe stream.
                Must be properly initialized and running.

        Returns:
            TranscribeHandler: The configured handler instance.

        Raises:
            ValueError: If the transcribe stream is invalid
            Exception: For handler setup failures
        """
        try:
            logger.info("Setting up transcript handler")
            transcribe_handler = TranscribeHandler(
                transcribe_stream.output_stream,
                self.master_config
            )
            self.summary_handler.transcript_file = transcribe_handler.session_writer.transcript_file
            logger.debug("Transcript handler setup complete")
            return transcribe_handler
        except Exception as e:
            logger.error(f"Failed to setup transcript handler: {str(e)}", exc_info=True)
            raise
        
    async def start_meeting(self):
        """
        Start the meeting service, either displaying a summary or beginning a new transcription session.

        Main entry point for the service that handles the complete workflow including
        initialization, execution, and cleanup of all meeting components.

        The behavior depends on the console_type:
        - If 'summary': Displays historical meeting summaries
        - If None: Starts a new live transcription session

        Raises:
            ValueError: If service configuration is invalid
            boto3.exceptions.BotoCoreError: For AWS service errors
            Exception: For any unexpected errors during execution

        Note:
            Ensures proper cleanup of resources even if errors occur during execution.
        """
        logger.info("Starting meeting service")
        
        if self.console_type == "summary":
            logger.info("Running in summary mode")
            await self.summary_handler.display_summary()
            return

        try:
            logger.info("Initializing meeting components")
            transcribe_client = TranscribeStreamingClient(region=self.master_config['region'])
            mic_stream, mic_client = self.mic_handler.create_stream()
            transcribe_stream = await self.setup_transcribe_stream(transcribe_client)
            transcribe_handler = self.setup_transcript_handler(transcribe_stream)

            logger.info("Starting stream handling")
            await self.handle_streams(mic_stream, transcribe_stream, transcribe_handler)
            
        except Exception as e:
            logger.error(f"Error during meeting: {str(e)}", exc_info=True)
            raise
        finally:
            logger.info("Cleaning up meeting resources")
            self.cleanup_resources(mic_stream, mic_client)