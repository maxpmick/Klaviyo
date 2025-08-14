#!/usr/bin/env python3
"""
Launcher script for the Klaviyo Checkout Snapshot Sync Tool GUI
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Klaviyo GUI application"""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    main_script = script_dir / "klaviyo_gui" / "main.py"
    
    if not main_script.exists():
        print(f"Error: Could not find main.py at {main_script}")
        sys.exit(1)
    
    # Run the main application
    try:
        subprocess.run([sys.executable, str(main_script)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running application: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)

if __name__ == "__main__":
    main()