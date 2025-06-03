"""
Meme creator tab for ZImage
"""
import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QFileDialog,
    QMessageBox, QPushButton, QToolBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction

from zimage.core.utils import get_icon
from zimage.models.meme import MemeModel
from zimage.models.text_box import TextBoxModel
from zimage.ui.meme.meme_canvas import MemeCanvas
from zimage.ui.meme.tool_panel import ToolPanel

logger = logging.getLogger('zimage')

class MemeCreatorTab(QWidget):
    """
    Main tab for meme creation
    """
    # Define signals
    status_message = pyqtSignal(str)

    def __init__(self, config, parent=None):
        """
        Initialize the meme creator tab

        Args:
            config (Config): Application configuration
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        self.config = config

        # Initialize canvas and tool panel first
        self.canvas = MemeCanvas()
        self.tool_panel = ToolPanel()

        # Initialize UI
        self._init_ui()

        # Connect signals
        self._connect_signals()

        logger.debug("Initialized meme creator tab")

    def _init_ui(self):
        """Initialize UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create toolbar
        toolbar = QToolBar("Meme Creator Toolbar")
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))

        # Load image action
        self.load_image_action = QAction(get_icon("open.png"), "Load Image", self)
        self.load_image_action.setStatusTip("Load an image for your meme")
        self.load_image_action.triggered.connect(self.open_image_dialog)
        toolbar.addAction(self.load_image_action)

        # Add zoom controls
        toolbar.addSeparator()
        self.zoom_in_action = QAction(get_icon("zoom_in.png"), "Zoom In", self)
        self.zoom_in_action.setStatusTip("Zoom in on the image")
        self.zoom_in_action.triggered.connect(lambda: self.canvas.zoom(1.2))
        toolbar.addAction(self.zoom_in_action)

        self.zoom_out_action = QAction(get_icon("zoom_out.png"), "Zoom Out", self)
        self.zoom_out_action.setStatusTip("Zoom out from the image")
        self.zoom_out_action.triggered.connect(lambda: self.canvas.zoom(0.8))
        toolbar.addAction(self.zoom_out_action)

        self.reset_zoom_action = QAction(get_icon("zoom_reset.png"), "Reset Zoom", self)
        self.reset_zoom_action.setStatusTip("Reset zoom to original size")
        self.reset_zoom_action.triggered.connect(self.canvas.reset_zoom)
        toolbar.addAction(self.reset_zoom_action)

        # Add toolbar to layout
        layout.addWidget(toolbar)

        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Add widgets to splitter
        splitter.addWidget(self.canvas)
        splitter.addWidget(self.tool_panel)

        # Set initial sizes
        splitter.setSizes([700, 300])

        # Add splitter to layout
        layout.addWidget(splitter)

    def _connect_signals(self):
        """Connect signals between components"""
        # Canvas signals
        self.canvas.text_box_selected.connect(self.tool_panel.update_text_properties)

        # Tool panel signals
        self.tool_panel.text_changed.connect(self._on_text_changed)
        self.tool_panel.font_changed.connect(self._on_font_changed)
        self.tool_panel.color_changed.connect(self._on_color_changed)
        self.tool_panel.outline_color_changed.connect(self._on_outline_color_changed)
        self.tool_panel.outline_size_changed.connect(self._on_outline_size_changed)
        self.tool_panel.alignment_changed.connect(self._on_alignment_changed)
        self.tool_panel.add_text_box.connect(self._on_add_text_box)
        self.tool_panel.clear_text_boxes.connect(self._on_clear_text_boxes)
        self.tool_panel.add_classic_format.connect(self._on_add_classic_format)
        self.tool_panel.export_meme.connect(self._on_export_meme)

        # Add a direct load image button to the tool panel
        self.tool_panel.load_image.connect(self.open_image_dialog)

    def load_image(self, path):
        """
        Load an image into the meme canvas

        Args:
            path (str): Path to the image file

        Returns:
            bool: True if successful, False otherwise
        """
        result = self.canvas.load_image(path)

        if result:
            self.status_message.emit(f"Loaded image: {os.path.basename(path)}")
        else:
            self.status_message.emit(f"Failed to load image: {os.path.basename(path)}")

        return result

    def load_image_from_browser(self, image_model):
        """
        Load an image from the browser tab

        Args:
            image_model: Image model from browser

        Returns:
            bool: True if successful, False otherwise
        """
        if hasattr(image_model, 'file_path') and os.path.exists(image_model.file_path):
            return self.load_image(image_model.file_path)
        return False

    def open_image_dialog(self):
        """
        Open a file dialog to select an image

        Returns:
            bool: True if an image was loaded, False otherwise
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )

        if file_path:
            return self.load_image(file_path)

        return False

    def save_meme(self, file_path=None):
        """
        Save the meme project to a file

        Args:
            file_path (str, optional): Path to save the file

        Returns:
            bool: True if successful, False otherwise
        """
        if not file_path:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Meme Project",
                "",
                "Meme Project Files (*.meme)"
            )

        if not file_path:
            return False

        # Add extension if not present
        if not file_path.lower().endswith(".meme"):
            file_path += ".meme"

        # Save to file
        result = self.canvas.meme_model.save_to_file(file_path)

        if result:
            self.status_message.emit(f"Saved meme project to: {os.path.basename(file_path)}")
        else:
            self.status_message.emit("Failed to save meme project")

        return result

    def load_meme(self, file_path=None):
        """
        Load a meme project from a file

        Args:
            file_path (str, optional): Path to the file

        Returns:
            bool: True if successful, False otherwise
        """
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Open Meme Project",
                "",
                "Meme Project Files (*.meme)"
            )

        if not file_path:
            return False

        # Load from file
        meme_model = MemeModel.load_from_file(file_path)

        if meme_model:
            self.canvas.set_meme_model(meme_model)
            self.status_message.emit(f"Loaded meme project from: {os.path.basename(file_path)}")
            return True
        else:
            self.status_message.emit("Failed to load meme project")
            return False

    def _on_text_changed(self, text_box_model, text):
        """Handle text change signal"""
        text_box_model.text = text
        self.canvas.update()

    def _on_font_changed(self, text_box_model, font):
        """Handle font change signal"""
        text_box_model.set_font(font)
        self.canvas.update()

    def _on_color_changed(self, text_box_model, color):
        """Handle color change signal"""
        text_box_model.text_color = color
        self.canvas.update()

    def _on_outline_color_changed(self, text_box_model, color):
        """Handle outline color change signal"""
        text_box_model.outline_color = color
        self.canvas.update()

    def _on_outline_size_changed(self, text_box_model, size):
        """Handle outline size change signal"""
        text_box_model.outline_size = size
        self.canvas.update()

    def _on_alignment_changed(self, text_box_model, alignment):
        """Handle alignment change signal"""
        text_box_model.alignment = alignment
        self.canvas.update()

    def _on_add_text_box(self, text, position):
        """Handle add text box signal"""
        self.canvas.add_text_box(text, position)
        self.status_message.emit(f"Added text box: {text}")

    def _on_clear_text_boxes(self):
        """Handle clear text boxes signal"""
        self.canvas.clear_text_boxes()
        self.status_message.emit("Cleared all text boxes")

    def _on_add_classic_format(self):
        """Handle add classic format signal"""
        self.canvas.add_classic_meme_format()
        self.status_message.emit("Added classic meme format")

    def _on_export_meme(self, file_path, format_str):
        """Handle export meme signal"""
        result = self.canvas.export_image(file_path, format_str)

        if result:
            self.status_message.emit(f"Exported meme to: {os.path.basename(file_path)}")
        else:
            self.status_message.emit("Failed to export meme")

            # Show error message
            QMessageBox.warning(
                self,
                "Export Failed",
                "Failed to export the meme image. Please make sure you have a valid image loaded."
            )
