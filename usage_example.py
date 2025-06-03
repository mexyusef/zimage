#!/usr/bin/env python3
"""
ZImage Enterprise - Usage Example

This script demonstrates how to use the ZImage Enterprise application
programmatically or integrate it into other applications.
"""
import sys
import os
from PyQt6.QtWidgets import QApplication

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from zimage.core.config import Config
from zimage.models.image import ImageModel
from zimage.ui.main_window import MainWindow

def main():
    """
    Main function demonstrating programmatic usage of ZImage Enterprise
    """
    # Create QApplication instance
    app = QApplication(sys.argv)

    # Set application info
    app.setApplicationName("ZImage Enterprise Demo")
    app.setOrganizationName("ZImage")
    app.setApplicationVersion("1.0.0")

    # Create configuration
    config = Config()

    # Create main window
    main_window = MainWindow(config)

    # Show the window
    main_window.show()

    # Example: Load a folder if specified as command line argument
    if len(sys.argv) > 1:
        path = sys.argv[1]
        if os.path.isdir(path):
            main_window.open_folder(path)
        elif os.path.isfile(path):
            main_window.open_file(path)

    # Enter the event loop
    sys.exit(app.exec())

# Programmatic API examples

def load_and_edit_image(file_path):
    """
    Example of loading and editing an image programmatically

    Args:
        file_path (str): Path to the image file
    """
    # Create ImageModel
    image_model = ImageModel(file_path)

    # Create QApplication (required for GUI components)
    app = QApplication([])

    # Create configuration
    config = Config()

    # Create editor widget
    from zimage.ui.editor.editor_tab import EditorTab
    editor = EditorTab(config)

    # Load image
    editor.load_image(image_model)

    # Show editor
    editor.show()

    # Run application
    app.exec()

def batch_resize_images(file_paths, output_dir, width, height):
    """
    Example of batch resizing images programmatically

    Args:
        file_paths (list): List of image file paths
        output_dir (str): Output directory
        width (int): Target width
        height (int): Target height
    """
    # Create QApplication (required for Qt functionality)
    app = QApplication([])

    # Create configuration
    config = Config()

    # Create resizer widget
    from zimage.ui.resizer.resizer_tab import ResizerTab
    resizer = ResizerTab(config)

    # Add images to batch
    for file_path in file_paths:
        if os.path.exists(file_path):
            image_model = ImageModel(file_path)
            resizer._add_to_batch(image_model)

    # Set output directory
    resizer.output_path_edit.setText(output_dir)

    # Set dimensions
    resizer.width_spin.setValue(width)
    resizer.height_spin.setValue(height)

    # Perform batch resize
    resizer._on_batch_resize_clicked()

    # Cleanup
    app.quit()

if __name__ == "__main__":
    main()
