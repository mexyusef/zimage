#!/usr/bin/env python3
"""
ZImage Enterprise - Professional image browser, editor, and resizer
"""
import sys
import os
import logging
import PyQt6.QtWidgets

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the core application controller
from zimage.controllers.app_controller import AppController
from zimage.core.logger import setup_logger
from zimage.core.constants import APP_NAME, APP_VERSION, APP_STYLESHEET

def main():
    """
    Application entry point
    """
    # Set up logger
    setup_logger()
    logger = logging.getLogger('zimage')

    try:
        # Create QApplication instance
        app = PyQt6.QtWidgets.QApplication(sys.argv)

        # Set application info
        app.setApplicationName(APP_NAME)
        app.setOrganizationName("ZImage")
        app.setApplicationVersion(APP_VERSION)

        # Set application style
        app.setStyleSheet(APP_STYLESHEET)

        # Create main application controller
        controller = AppController(app)

        # Start the application
        controller.start()

        # Enter the event loop
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Critical error during application startup: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
