import time
import logging
import aiofiles
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SessionWriter:
    """
    Manages the writing of transcription data to both console and file outputs.

    This class handles the buffered writing of transcription data, including speaker
    identification and timestamps, with support for both immediate console output
    and buffered file writing.

    Attributes:
        master_config (dict): Configuration dictionary for the session
        transcript_file (str): Path to the current transcript file
        write_buffer (list): Buffer for storing transcript lines before writing to file
        last_write_time (float): Timestamp of the last buffer flush
    """

    def __init__(self, config: dict):
        """
        Initialize the SessionWriter with configuration and create transcript file.

        Sets up the session writer with:
        - Configuration settings from provided config dict
        - New transcript file with timestamp-based name
        - Empty write buffer for batched file operations
        - Initial write time for buffer management

        Args:
            config (dict): Configuration dictionary containing session settings

        Raises:
            FileNotFoundError: If transcript directory cannot be created
            IOError: If transcript file cannot be initialized
        """
        try:
            logger.info("Initializing SessionWriter")
            self.master_config = config
            self.transcript_file = self.setup_transcript_file()
            self.write_buffer = []
            self.last_write_time = time.time()
            logger.debug(f"SessionWriter initialized with transcript file: {self.transcript_file}")
        except Exception as e:
            logger.error(f"Failed to initialize SessionWriter: {str(e)}", exc_info=True)
            raise

    async def flush_buffer(self):
        """
        Write all buffered content to the transcript file and clear the buffer.

        Writes accumulated transcript lines to file when:
        - Buffer reaches size threshold (5 lines)
        - Time threshold exceeded (2 seconds)
        After writing, clears buffer and resets timer.

        Raises:
            IOError: If writing to transcript file fails
            Exception: For other unexpected errors during flush operation
        """
        if not self.write_buffer:
            return
            
        try:
            logger.debug(f"Flushing buffer with {len(self.write_buffer)} items")
            async with aiofiles.open(self.transcript_file, mode='a', encoding='utf-8') as f:
                await f.write('\n'.join(self.write_buffer) + '\n')
            self.write_buffer = []
            self.last_write_time = time.time()
            logger.debug("Buffer flushed successfully")
        except Exception as e:
            logger.error(f"Error flushing buffer to file: {str(e)}", exc_info=True)
            raise

    def format_line(self, timestamp, speaker, transcript):
        """
        Format a transcript line with timestamp and speaker information.

        Creates a formatted string combining:
        - Timestamp in brackets
        - Speaker identifier (if available)
        - Transcribed text

        Args:
            timestamp (str): Formatted timestamp for the transcript line
            speaker (str): Speaker identifier (or None if not available)
            transcript (str): The transcribed text

        Returns:
            str: Formatted transcript line with timestamp and speaker info

        Raises:
            ValueError: If timestamp or transcript are invalid
        """
        try:
            if speaker is not None:
                return f"[{timestamp}] Speaker {speaker}: {transcript}"
            return f"[{timestamp}] Transcript: {transcript}"
        except Exception as e:
            logger.error(f"Error formatting transcript line: {str(e)}", exc_info=True)
            raise

    def setup_transcript_file(self):
        """
        Create output directory and initialize a new transcript file.

        Creates necessary directory structure and initializes a new transcript file with:
        - Timestamp-based filename
        - Session start header
        - UTF-8 encoding

        Returns:
            str: Path to the created transcript file

        Raises:
            FileNotFoundError: If directory creation fails
            IOError: If file creation or header writing fails
        """
        try:
            Path('output/transcripts').mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M')
            file_path = f"output/transcripts/transcript_{timestamp}.txt"
            self.write_header(file_path)
            logger.debug(f"Created new transcript file: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Failed to setup transcript file: {str(e)}", exc_info=True)
            raise
    
    async def write_to_console(self, output_line):
        """
        Display a transcript line in the console.

        Prints the formatted transcript line to standard output for real-time
        monitoring of the transcription process.

        Args:
            output_line (str): Formatted transcript line to display

        Raises:
            IOError: If console output fails
        """
        try:
            print(output_line)
            logger.debug(f"Wrote to console: {output_line[:50]}...")
        except Exception as e:
            logger.error(f"Failed to write to console: {str(e)}", exc_info=True)
            raise

    async def write_to_file(self, output_line):
        """
        Write a single line directly to the transcript file.

        Appends a single transcript line to the file immediately, bypassing
        the buffer system. Used for important or time-sensitive entries.

        Args:
            output_line (str): Formatted transcript line to write

        Raises:
            IOError: If file writing operation fails
            Exception: For other unexpected file operations
        """
        try:
            async with aiofiles.open(self.transcript_file, mode='a', encoding='utf-8') as f:
                await f.write(f"{output_line}\n")
            logger.debug(f"Wrote line to file: {output_line[:50]}...")
        except Exception as e:
            logger.error(f"Failed to write to file: {str(e)}", exc_info=True)
            raise
    
    def write_header(self, file_path):
        """
        Write initial timestamp header to a new transcript file.

        Creates the transcript file and writes a header containing:
        - Session start timestamp
        - Formatting spaces
        - UTF-8 encoding

        Args:
            file_path (str): Path to the transcript file

        Raises:
            IOError: If file creation or writing fails
            Exception: For other file operation errors
        """
        try:
            header = f"Transcript started at {datetime.now().strftime('%Y-%m-%d %I:%M %p')}\n\n"
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(header)
            logger.debug(f"Wrote header to file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to write header: {str(e)}", exc_info=True)
            raise

    async def write_transcript(self, speaker, transcript):
        """
        Format and buffer a transcript line, flushing the buffer if needed.

        Processes a new transcript entry by:
        - Adding current timestamp
        - Formatting with speaker information
        - Displaying to console
        - Adding to write buffer
        - Flushing buffer if thresholds met (size >= 5 or time > 2s)

        Args:
            speaker (str): Speaker identifier (or None if not available)
            transcript (str): The transcribed text

        Raises:
            IOError: If writing operations fail
            ValueError: If transcript formatting fails
            Exception: For other unexpected errors
        """
        try:
            timestamp = datetime.now().strftime('%m-%d-%Y %I:%M %p')
            output_line = self.format_line(timestamp, speaker, transcript)
            
            await self.write_to_console(output_line)
            self.write_buffer.append(output_line)
            
            if time.time() - self.last_write_time > 2 or len(self.write_buffer) >= 5:
                await self.flush_buffer()
            
            logger.debug(f"Processed transcript line: {output_line[:50]}...")
        except Exception as e:
            logger.error(f"Failed to write transcript: {str(e)}", exc_info=True)
            raise