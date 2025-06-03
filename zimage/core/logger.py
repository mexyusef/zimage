"""
Logging functionality for ZImage Enterprise
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

def setup_logger():
    """
    Set up the application logger
    """
    # Create a logger
    logger = logging.getLogger('zimage')
    logger.setLevel(logging.DEBUG)

    # Determine log file directory
    if sys.platform == 'win32':
        log_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'ZImage', 'logs')
    else:
        log_dir = os.path.join(os.path.expanduser('~'), '.zimage', 'logs')

    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Create log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_file = os.path.join(log_dir, f"zimage-{timestamp}.log")

    # Create handlers
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s')
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')

    # Set formatters for handlers
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Log initial message
    logger.info(f"Logging initialized - Log file: {log_file}")

    return logger
