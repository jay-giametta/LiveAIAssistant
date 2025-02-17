import pyaudio

class MicrophoneHandler:
    def __init__(self):
        self.audio_format = pyaudio.paInt16
        self.channel_count = 1
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.buffer_size = 8192
        self.mic_interface = None
        self.mic_stream = None

    def create_stream(self):
        self.mic_interface = pyaudio.PyAudio()
        mic_device = self.mic_interface.get_default_input_device_info()
        
        self.mic_stream = self.mic_interface.open(
            format=self.audio_format,
            channels=self.channel_count,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            input_device_index=mic_device['index'],
            stream_callback=None
        )
        
        self.mic_stream.start_stream()
        return self.mic_stream, self.mic_interface