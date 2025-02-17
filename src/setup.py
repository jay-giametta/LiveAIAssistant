import json
from pathlib import Path

class Setup:
    def create_directory(path):
        Path(path).mkdir(parents=True, exist_ok=True)

    @staticmethod
    def ensure_directories():
        Setup.create_directory('output/transcripts')
        Setup.create_directory('output/meeting_notes')

    @staticmethod
    def get_config():
        config_path = Setup.get_config_path()
        return Setup.load_json_config(config_path)
    
    def get_config_path():
        base_dir = Path(__file__).parent.parent
        return base_dir / 'config' / 'config.json'

    def load_json_config(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)