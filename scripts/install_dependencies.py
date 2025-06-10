#!/usr/bin/env python3
"""
Install dependencies for ZImage blur functionality
"""
import sys
import subprocess
import os

def install_packages():
    """Install required Python packages"""
    print("Installing required packages for ZImage blur functionality...")

    # List of required packages
    packages = [
        "opencv-python",
        "numpy"
    ]

    # Install packages using pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + packages)
        print("Successfully installed required packages.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        return False

if __name__ == "__main__":
    if install_packages():
        print("Installation completed successfully.")
        print("\nYou can now use the blur functionality in ZImage.")
        print("To use it:")
        print("1. Select the Blur tool in the editor")
        print("2. Adjust blur radius and type as needed")
        print("3. Drag to select a region to blur, or")
        print("4. Hold Ctrl and click to blur the entire image")
    else:
        print("Installation failed. Please try installing manually:")
        print("pip install opencv-python numpy")
