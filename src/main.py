import os
import sys
import asyncio
import logging
import time
from typing import Optional
from pathlib import Path

# Adds the current directory to Python's path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from setup import Setup
from meeting_service import MeetingService
from console_manager import ConsoleManager

def configure_logging(console_type: Optional[str] = None):
    """
    Configure logging for the application.

    Sets up file logging for all processes and console logging only for the main window.
    Uses a single log file that's shared across all processes.

    Args:
        console_type (str, optional): Type of console ('transcript', 'summary', or None for main)
            None: Main console - logs to both file and console
            'transcript'/'summary': Child consoles - logs only to file

    Raises:
        OSError: If unable to create log directory or file
        PermissionError: If lacking permissions to write to log file
    """
    # Create logs directory
    Setup.create_directory('logs')
    
    # Use a fixed log file name for the current session
    log_file = Path('logs') / 'current_session.log'
    
    # Set up formatters
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Add handlers based on console type with retry logic
    max_retries = 3
    retry_delay = 0.1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Add file handler
            file_handler = logging.FileHandler(log_file, mode='a', delay=True)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            break
        except PermissionError as pe:
            if attempt == max_retries - 1:  # Last attempt
                raise PermissionError(f"Unable to access log file after {max_retries} attempts: {pe}")
            time.sleep(retry_delay)
        except OSError as oe:
            if attempt == max_retries - 1:  # Last attempt
                raise OSError(f"Unable to create log file after {max_retries} attempts: {oe}")
            time.sleep(retry_delay)
    
    # Only show logs in console for main window
    if console_type is None:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

async def run_meeting(master_config: dict, console_type: str) -> None:
    """
    Creates and runs a meeting service instance.

    Args:
        master_config (dict): Configuration settings for the meeting
        console_type (str): Type of console to run ('transcript' or 'summary')

    Raises:
        ValueError: If console_type is invalid
        Exception: For any unexpected errors during meeting execution
    """
    try:
        logger = logging.getLogger(__name__)
        logger.info(f"Starting meeting with console type: {console_type}")
        
        if console_type not in ['transcript', 'summary']:
            raise ValueError(f"Invalid console type: {console_type}")
        
        meeting_service = MeetingService(master_config, console_type)
        await meeting_service.start_meeting()
        logger.info(f"Meeting completed successfully for console type: {console_type}")
    
    except ValueError as ve:
        logger.error(f"Invalid configuration: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Error running meeting: {str(e)}", exc_info=True)
        raise

def main(console_type: Optional[str] = None) -> None:
    """
    Main program entry point that sets up and runs the meeting service.

    Args:
        console_type (str, optional): Type of console to run. Defaults to None.
            If None, launches both transcript and summary consoles.
            If specified, runs single console of that type.

    Raises:
        KeyboardInterrupt: When user terminates the program
        Exception: For any unexpected errors during execution
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Starting main application")
        
        # Set up directories and load configuration
        Setup.ensure_directories()
        master_config = Setup.get_config()
        
        # Either launch multiple consoles or run a single meeting
        if console_type is None:
            logger.info("Launching multiple consoles")
            console_manager = ConsoleManager()
            console_manager.launch_consoles()
            # Keep the main process alive
            try:
                async def keep_alive():
                    while True:
                        await asyncio.sleep(1)
                asyncio.run(keep_alive())
            except KeyboardInterrupt:
                logger.info("Main process terminated by user")
                raise
        else:
            logger.info(f"Running single meeting with console type: {console_type}")
            asyncio.run(run_meeting(master_config, console_type))
        
        logger.info("Application completed successfully")
    
    except KeyboardInterrupt:
        print("\nProgram terminated by user\n")
        sys.exit(0)
    
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}", exc_info=True)
        print("\nThere was an unexpected error\n")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Clean up existing log file when starting main process
        if len(sys.argv) <= 1:  # Only for main console
            log_file = Path('logs') / 'current_session.log'
            try:
                if log_file.exists():
                    log_file.unlink()
            except PermissionError:
                # If file is locked, just append to it instead
                pass
        
        console_type = sys.argv[1] if len(sys.argv) > 1 else None
        configure_logging(console_type)
        
        logger = logging.getLogger(__name__)
        logger.info(f"Starting application with console type: {console_type}")
        main(console_type)
    
    except Exception as e:
        logging.critical("Critical error in main execution", exc_info=True)
        sys.exit(1)