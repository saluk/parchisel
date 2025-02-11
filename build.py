import nicegui
from pathlib import Path
import subprocess
static_dir = Path(nicegui.__file__).parent
print(static_dir)

script = \
f"""
pyinstaller --onefile main.py --add-data="{static_dir}:nicegui"
"""
subprocess.call(script, shell=True)