"""
Main application controller for ZImage Enterprise
"""
import logging
import os
import sys
from PyQt6.QtWidgets import QMainWindow, QApplication, QMessageBox
from PyQt6.QtCore import Qt

from zimage.core.config import Config
from zimage.ui.main_window import MainWindow

logger = logging.getLogger('zimage')

class AppController:
    """
    Main application controller
    """
    def __init__(self, app):
        """
        Initialize the application controller

        Args:
            app (QApplication): The Qt application instance
        """
        self.app = app
        self.config = Config()
        self.main_window = None
        self.browser_controller = None
        self.editor_controller = None
        self.resizer_controller = None

        # Initialize services
        self._init_services()

        # Set up exception handling
        sys.excepthook = self._handle_exception

    def _init_services(self):
        """Initialize application services"""
        # Future implementation: Initialize services here
        pass

    def start(self):
        """Start the application"""
        try:
            # Create main window
            self.main_window = MainWindow(self.config)

            # Set window size from config
            width = self.config.get("window.width", 1200)
            height = self.config.get("window.height", 800)
            maximized = self.config.get("window.maximized", False)

            self.main_window.resize(width, height)
            if maximized:
                self.main_window.showMaximized()
            else:
                self.main_window.show()

            # Connect window signals
            self._connect_signals()

            logger.info("Application started successfully")

        except Exception as e:
            logger.critical(f"Failed to start application: {str(e)}", exc_info=True)
            self._show_critical_error("Failed to start application", str(e))
            sys.exit(1)

    def _connect_signals(self):
        """Connect signals to slots"""
        # Connect window close event
        self.main_window.closeEvent = self._handle_close_event

    def _handle_close_event(self, event):
        """Handle window close event"""
        try:
            # Save window state to config
            if self.main_window.isMaximized():
                self.config.set("window.maximized", True)
            else:
                self.config.set("window.maximized", False)
                self.config.set("window.width", self.main_window.width())
                self.config.set("window.height", self.main_window.height())

            # Allow the close event to proceed
            event.accept()

        except Exception as e:
            logger.error(f"Error during application close: {str(e)}")
            event.accept()  # Still close even if there's an error

    def _handle_exception(self, exc_type, exc_value, exc_traceback):
        """Global exception handler"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle keyboard interrupt normally
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the exception
        logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))

        # Show error message if GUI is available
        if self.main_window is not None and self.main_window.isVisible():
            self._show_critical_error("Unhandled Exception", str(exc_value))

    def _show_critical_error(self, title, message):
        """Show critical error message box"""
        try:
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setWindowTitle(title)
            error_box.setText(message)
            error_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_box.exec()
        except:
            # If showing the dialog fails, fall back to console
            print(f"CRITICAL ERROR: {title} - {message}", file=sys.stderr)
