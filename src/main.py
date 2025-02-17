import os
import sys

# Add the src directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

import asyncio
from setup import Setup
from meeting_service import MeetingService
from console_manager import ConsoleManager

async def run_meeting(master_config, console_type):
    meeting_service = MeetingService(master_config, console_type)
    await meeting_service.start_meeting()

def main(console_type=None):

    try:
        Setup.ensure_directories()
        master_config = Setup.get_config()
        
        if console_type is None:
            console_manager = ConsoleManager()
            console_manager.launch_consoles()        
        else:
            asyncio.run(run_meeting(master_config, console_type))
        return
    except KeyboardInterrupt:
        print("\nProgram terminated by user\n")
        sys.exit(0)
    except Exception as e:
        print("\nThere was an unexpected error\n")
        sys.exit(1) 

if __name__ == "__main__":
    console_type = sys.argv[1] if len(sys.argv) > 1 else None
    main(console_type)