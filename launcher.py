"""
Launcher script for PyInstaller.

This script handles the import path correctly when running as a packaged executable.
"""

import sys
import os

# Add project root to path so imports work
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    bundle_dir = sys._MEIPASS
else:
    # Running in normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))

# Add bundle directory to path so 'src' package can be imported
if bundle_dir not in sys.path:
    sys.path.insert(0, bundle_dir)

# Now import and run the main application
from src.main import main

if __name__ == "__main__":
    main()
