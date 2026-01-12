#!/usr/bin/env python
"""
Build script for Ventiv to Riskonnect Migration Tool.

This script automates the process of building a standalone executable
using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    """Main build process."""
    print("=" * 60)
    print("Building Ventiv to Riskonnect Migration Tool")
    print("=" * 60)

    # Get project root
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} found")
    except ImportError:
        print("[!] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")

    # Clean previous builds
    print("\nCleaning previous builds...")
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        dir_path = project_root / dir_name
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"[OK] Removed {dir_name}/")

    # Run PyInstaller
    print("\nBuilding executable...")
    spec_file = project_root / "build.spec"

    try:
        subprocess.check_call([
            sys.executable,
            "-m",
            "PyInstaller",
            str(spec_file),
            "--clean",
            "--noconfirm"
        ])
        print("\n[OK] Build successful!")

        # Show output location
        dist_dir = project_root / "dist" / "VentivToRiskonnectMigrationTool"
        exe_name = "VentivToRiskonnectMigrationTool.exe" if sys.platform == "win32" else "VentivToRiskonnectMigrationTool"
        exe_path = dist_dir / exe_name

        if exe_path.exists():
            print(f"\n{'=' * 60}")
            print(f"Executable created at:")
            print(f"  {exe_path}")
            print(f"{'=' * 60}")
            print(f"\nTo distribute the application:")
            print(f"  1. Zip the entire folder: {dist_dir}")
            print(f"  2. Users can extract and run {exe_name}")
            print(f"\nNote: The executable requires the entire folder,")
            print(f"      not just the .exe file.")
        else:
            print(f"\n[!] Warning: Executable not found at expected location")

    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Build failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
