import time
import logging
from amazon_transcribe.handlers import TranscriptResultStreamHandler
from session_writer import SessionWriter

logger = logging.getLogger(__name__)

class TranscribeHandler(TranscriptResultStreamHandler):
    """
    Handles real-time transcription results from Amazon Transcribe.

    This handler processes streaming transcription results, manages buffering of
    transcripts, and coordinates writing segments to output based on speaker
    changes and natural sentence boundaries.

    Attributes:
        session_writer (SessionWriter): Handles writing transcripts to output.
        speaker (str): Current speaker identifier.
        output_stream: Stream containing transcription results.
        sentence_endings (set): Set of characters that indicate sentence endings.
        buffer (list): Temporary storage for transcript segments.
        last_flush_time (float): Timestamp of last buffer flush.
        max_buffer_size (int): Maximum number of segments to buffer before forcing flush.
    """
    
    def __init__(self, output_stream, master_config):
        """
        Initialize the TranscribeHandler with output stream and configuration.

        Args:
            output_stream: Stream object for receiving transcription results.
            master_config: Configuration settings for the session writer.
        """
        try:
            logger.info("Initializing TranscribeHandler")
            super().__init__(output_stream)
            
            if not output_stream:
                raise ValueError("Output stream cannot be None")
            if not master_config:
                raise ValueError("Master configuration cannot be None")
            
            self.session_writer = SessionWriter(master_config)
            self.speaker = None
            self.output_stream = output_stream
            self.sentence_endings = {'.', '?', '!'}
            self.buffer = []
            self.last_flush_time = time.time()
            self.max_buffer_size = 10

            logger.debug(f"TranscribeHandler initialized with buffer size: {self.max_buffer_size}")
        
        except ValueError as ve:
            logger.error(f"Invalid initialization parameters: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize TranscribeHandler: {str(e)}", exc_info=True)
            raise

    async def flush_buffer(self, force=False):
        """
        [Original docstring maintained]
        """
        try:
            current_time = time.time()
            should_flush = (force or 
                          len(self.buffer) >= self.max_buffer_size or 
                          current_time - self.last_flush_time > 1)
            
            if should_flush:
                logger.debug(f"Flushing buffer with {len(self.buffer)} segments")
                
                for speaker, transcript in self.buffer:
                    await self.handle_segment(speaker, transcript)
                
                self.buffer = []
                self.last_flush_time = current_time
                logger.debug("Buffer flush completed")
        
        except Exception as e:
            logger.error(f"Error flushing buffer: {str(e)}", exc_info=True)
            raise

    def extract_speaker(self, alternative_items):
        """
        [Original docstring maintained]
        """
        try:
            for alternative_item in alternative_items:
                if hasattr(alternative_item, 'speaker'):
                    logger.debug(f"Speaker identified: {alternative_item.speaker}")
                    return alternative_item.speaker
            
            logger.debug("No speaker identified in items")
            return None
        
        except Exception as e:
            logger.error(f"Error extracting speaker: {str(e)}", exc_info=True)
            raise

    async def handle_events(self):
        """
        Process incoming transcription events from the output stream.
        
        Raises:
            Exception: For errors during event processing
        """
        try:
            logger.info("Starting transcription event handling")
            async for transcript_event in self.output_stream:
                await self.handle_transcript(transcript_event)
        
        except Exception as e:
            logger.error(f"Error handling transcription events: {str(e)}", exc_info=True)
            raise

    async def handle_segment(self, speaker, transcript):
        """
        Write transcript segment and update current speaker.

        Args:
            speaker (str): Speaker identifier for the segment.
            transcript (str): Transcribed text segment.
            
        Raises:
            ValueError: If speaker or transcript is invalid
            Exception: For errors during segment handling
        """
        try:
            if not transcript:
                raise ValueError("Empty transcript segment")
            
            logger.debug(f"Handling segment - Speaker: {speaker}, Transcript: {transcript[:50]}...")
            await self.session_writer.write_transcript(speaker, transcript)
            self.speaker = speaker
            
        except ValueError as ve:
            logger.warning(f"Invalid segment data: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error handling transcript segment: {str(e)}", exc_info=True)
            raise

    async def handle_transcript(self, transcript_event):
        """
        Process transcript results and buffer complete segments.

        Args:
            transcript_event: Event containing transcription results.
            
        Raises:
            Exception: For errors during transcript processing
        """
        try:
            if not transcript_event or not transcript_event.transcript:
                logger.debug("Received empty transcript event")
                return

            transcript_results = transcript_event.transcript.results
            logger.debug(f"Processing transcript with {len(transcript_results)} results")
            
            for transcript_result in transcript_results:
                if transcript_result.is_partial:
                    logger.debug("Skipping partial result")
                    continue
                
                for alternative in transcript_result.alternatives:
                    if not hasattr(alternative, 'items'):
                        logger.debug("Skipping alternative without items")
                        continue
                    
                    speaker = self.extract_speaker(alternative.items)
                    alternative_transcript = alternative.transcript.strip()
                    
                    if alternative_transcript and self.should_output(speaker, alternative_transcript):
                        logger.debug(f"Buffering transcript segment from speaker {speaker}")
                        self.buffer.append((speaker, alternative_transcript))
                        
                        if time.time() - self.last_flush_time > 2 or len(self.buffer) >= 5:
                            await self.flush_buffer()
        
        except Exception as e:
            logger.error(f"Error processing transcript: {str(e)}", exc_info=True)
            raise

    def should_output(self, current_speaker, alternative_transcript):
        """
        Determine if transcript segment should be output.

        Args:
            current_speaker (str): Speaker identifier for current segment.
            alternative_transcript (str): Transcribed text to evaluate.

        Returns:
            bool: True if segment should be output, False otherwise.
            
        Raises:
            ValueError: If input parameters are invalid
        """
        try:
            if not alternative_transcript:
                raise ValueError("Empty transcript")
            
            if current_speaker != self.speaker:
                logger.debug("Speaker change detected - outputting segment")
                return True
            
            should_output = alternative_transcript[-1] in self.sentence_endings
            logger.debug(f"Segment output decision: {should_output}")
            return should_output
            
        except ValueError as ve:
            logger.warning(f"Invalid output check parameters: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"Error checking output conditions: {str(e)}", exc_info=True)
            raise