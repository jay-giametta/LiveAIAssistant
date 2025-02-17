import subprocess
from pathlib import Path

class ConsoleManager:
    def __init__(self):
        self.script_path = Path(__file__).resolve()
        self.project_root = self.script_path.parent.parent
        self.main_path = self.project_root / 'src' / 'main.py'

    def launch_consoles(self):
        self.open_console("Transcript", "transcript")
        self.open_console("Summary", "summary")

    def open_console(self, title, window_type):
        cmd = f'start "{title}" cmd /k python "{self.main_path}" {window_type}'
        subprocess.Popen(cmd, shell=True)