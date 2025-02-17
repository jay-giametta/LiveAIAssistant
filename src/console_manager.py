from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)

class ConsoleManager:
    """
    Manages the creation and launching of separate console windows for the application.

    This class handles the initialization and launching of multiple console windows,
    each serving different purposes in the application (transcript and summary views).
    It manages file paths and system commands needed to create these windows.

    Attributes:
        script_path (Path): Absolute path to the current script file.
        project_root (Path): Root directory of the project.
        main_path (Path): Path to the main application script.
    """

    def __init__(self):
        """
        Initialize the ConsoleManager with required file paths.

        Sets up the necessary path attributes by resolving the current script location
        and calculating relative paths to other required files.

        Raises:
            FileNotFoundError: If the main script file cannot be located
            Exception: For any unexpected initialization errors
        """
        try:
            self.script_path = Path(__file__).resolve()
            self.project_root = self.script_path.parent.parent
            self.main_path = self.project_root / 'src' / 'main.py'
            
            logger.debug(f"Initialized ConsoleManager with paths:")
            logger.debug(f"Script path: {self.script_path}")
            logger.debug(f"Project root: {self.project_root}")
            logger.debug(f"Main path: {self.main_path}")

            if not self.main_path.exists():
                raise FileNotFoundError(f"Main script not found at: {self.main_path}")

        except Exception as e:
            logger.error(f"Error initializing ConsoleManager: {str(e)}", exc_info=True)
            raise

    def launch_consoles(self):
        """
        Launch both transcript and summary console windows.

        Creates two separate console windows: one for displaying transcripts
        and another for displaying summaries. Each window runs an instance
        of the main script with different parameters.

        Raises:
            Exception: If there's an error launching either console window
            subprocess.SubprocessError: If there's an error creating the processes
        """
        try:
            logger.info("Launching multiple console windows")
            self.open_console("Transcript", "transcript")
            self.open_console("Summary", "summary")
            logger.info("Successfully launched both console windows")

        except Exception as e:
            logger.error(f"Error launching consoles: {str(e)}", exc_info=True)
            raise

    def open_console(self, title: str, window_type: str):
        """
        Open a new console window with specified parameters.

        Creates a new command prompt window and executes the main script
        with the specified window type. The window is given a custom title
        for easy identification.

        Args:
            title (str): The title to display in the console window's title bar.
            window_type (str): The type of console to open ('transcript' or 'summary').
                             This parameter is passed to the main script to determine
                             the window's behavior.

        Raises:
            ValueError: If window_type is invalid
            subprocess.SubprocessError: If there's an error launching the console
        """
        try:
            if window_type not in ['transcript', 'summary']:
                raise ValueError(f"Invalid window type: {window_type}")

            logger.info(f"Opening new console window - Title: {title}, Type: {window_type}")
            cmd = f'start "{title}" cmd /k python "{self.main_path}" {window_type}'
            
            logger.debug(f"Executing command: {cmd}")
            subprocess.Popen(cmd, shell=True)
            logger.info(f"Successfully launched {title} console")

        except ValueError as ve:
            logger.error(f"Invalid window configuration: {str(ve)}")
            raise
        except subprocess.SubprocessError as se:
            logger.error(f"Failed to launch console process: {str(se)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error opening console: {str(e)}", exc_info=True)
            raise