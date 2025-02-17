import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Setup:
    """
    Handles initialization and configuration tasks for the application.

    This class provides static methods for creating necessary directories
    and loading configuration settings from a JSON file.
    """

    @staticmethod
    def create_directory(path):
        """
        Create a directory at the specified path if it doesn't exist.

        Args:
            path (str): The path where the directory should be created

        Raises:
            PermissionError: If the program lacks permission to create the directory
            OSError: If directory creation fails for other reasons
        """
        try:
            logger.debug(f"Creating directory: {path}")
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Directory created or verified: {path}")
        
        except PermissionError as pe:
            logger.error(f"Permission denied creating directory {path}: {str(pe)}")
            raise
        except OSError as ose:
            logger.error(f"Failed to create directory {path}: {str(ose)}")
            raise

    @staticmethod
    def ensure_directories():
        """
        Create all required output directories for the application.

        Creates directories for:
        - Transcripts: output/transcripts
        - Meeting notes: output/meeting_notes
        - Logs: logs

        Raises:
            OSError: If any directory creation fails
        """
        try:
            logger.info("Creating required application directories")
            required_dirs = [
                'output/transcripts',
                'output/meeting_notes',
                'logs'
            ]
            
            for directory in required_dirs:
                Setup.create_directory(directory)
            
            logger.info("All required directories created successfully")
        
        except Exception as e:
            logger.error(f"Failed to create required directories: {str(e)}")
            raise

    @staticmethod
    def get_config():
        """
        Load and return the application configuration.

        Returns:
            dict: The configuration settings loaded from config.json

        Raises:
            FileNotFoundError: If config file doesn't exist
            json.JSONDecodeError: If config file contains invalid JSON
        """
        try:
            logger.info("Loading application configuration")
            config_path = Setup.get_config_path()
            config = Setup.load_json_config(config_path)
            logger.info("Configuration loaded successfully")
            return config
        
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise
    
    @staticmethod
    def get_config_path():
        """
        Determine the path to the configuration file.

        Returns:
            Path: The path to config.json relative to this file's location

        Raises:
            FileNotFoundError: If the config directory doesn't exist
        """
        try:
            logger.debug("Determining configuration file path")
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / 'config' / 'config.json'
            
            if not (base_dir / 'config').exists():
                raise FileNotFoundError(f"Config directory not found at {base_dir / 'config'}")
            
            logger.debug(f"Configuration path determined: {config_path}")
            return config_path
        
        except Exception as e:
            logger.error(f"Failed to determine config path: {str(e)}")
            raise

    @staticmethod
    def load_json_config(config_path):
        """
        Read and parse the JSON configuration file.

        Args:
            config_path (Path): Path to the configuration file

        Returns:
            dict: The parsed configuration settings

        Raises:
            FileNotFoundError: If the config file doesn't exist
            json.JSONDecodeError: If the config file contains invalid JSON
            UnicodeDecodeError: If the file has encoding issues
        """
        try:
            logger.debug(f"Loading JSON configuration from: {config_path}")
            
            if not config_path.exists():
                raise FileNotFoundError(f"Configuration file not found: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as config_file:
                config = json.load(config_file)
                
            logger.debug("JSON configuration loaded successfully")
            return config
        
        except FileNotFoundError as fnf:
            logger.error(f"Configuration file not found: {str(fnf)}")
            raise
        except json.JSONDecodeError as jde:
            logger.error(f"Invalid JSON in configuration file: {str(jde)}")
            raise
        except UnicodeDecodeError as ude:
            logger.error(f"Configuration file encoding error: {str(ude)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {str(e)}")
            raise