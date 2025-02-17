import pyaudio
import logging

logger = logging.getLogger(__name__)

class MicrophoneHandler:
    """
    Handles microphone initialization and audio stream configuration for real-time audio capture.

    This class manages the setup and configuration of audio input devices using PyAudio,
    providing a standardized interface for capturing audio from the default microphone.

    Attributes:
        audio_format (int): Audio format specification (16-bit PCM)
        channel_count (int): Number of audio channels (1 for mono)
        sample_rate (int): Audio sampling rate in Hz
        chunk_size (int): Size of each audio chunk in frames
        buffer_size (int): Size of the audio buffer
        mic_interface (PyAudio): PyAudio instance for audio I/O
        mic_stream (PyAudio.Stream): Active microphone stream
    """

    def __init__(self):
        """
        Initialize the MicrophoneHandler with default audio configuration settings.
        
        Sets up basic audio parameters required for AWS Transcribe compatibility:
        - 16-bit PCM audio format
        - Mono channel
        - 16kHz sample rate
        - 1024 frame chunks
        - 8192 byte buffer
        """
        try:
            logger.info("Initializing MicrophoneHandler")
            self.audio_format = pyaudio.paInt16
            self.channel_count = 1
            self.sample_rate = 16000
            self.chunk_size = 1024
            self.buffer_size = 8192
            self.mic_interface = None
            self.mic_stream = None

            logger.debug(f"Audio configuration set: "
                        f"format={self.audio_format}, "
                        f"channels={self.channel_count}, "
                        f"rate={self.sample_rate}, "
                        f"chunk_size={self.chunk_size}, "
                        f"buffer_size={self.buffer_size}")

        except Exception as e:
            logger.error(f"Failed to initialize MicrophoneHandler: {str(e)}", exc_info=True)
            raise

    def create_stream(self):
        """
        Initialize and configure the audio interface and microphone stream.

        Creates a PyAudio instance, configures it with the default input device,
        and opens a stream with the predetermined audio parameters.

        Returns:
            tuple: A pair containing:
                - The active microphone stream (PyAudio.Stream)
                - The PyAudio interface instance (PyAudio)

        Raises:
            PyAudioError: If there's an error initializing the audio interface
            IOError: If there's an error opening the microphone stream
        """
        try:
            logger.info("Creating audio stream")
            
            # Initialize PyAudio interface
            logger.debug("Initializing PyAudio interface")
            self.mic_interface = pyaudio.PyAudio()
            
            # Get default input device
            logger.debug("Getting default input device")
            mic_device = self.mic_interface.get_default_input_device_info()
            logger.debug(f"Using input device: {mic_device['name']} (index: {mic_device['index']})")
            
            # Open audio stream
            logger.debug("Opening audio stream")
            self.mic_stream = self.mic_interface.open(
                format=self.audio_format,
                channels=self.channel_count,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=mic_device['index'],
                stream_callback=None
            )
            
            # Start the stream
            logger.debug("Starting audio stream")
            self.mic_stream.start_stream()
            
            logger.info("Audio stream successfully created and started")
            return self.mic_stream, self.mic_interface

        except pyaudio.PyAudioError as pae:
            logger.error(f"PyAudio initialization error: {str(pae)}", exc_info=True)
            raise
        except IOError as ioe:
            logger.error(f"Error opening microphone stream: {str(ioe)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating audio stream: {str(e)}", exc_info=True)
            raise