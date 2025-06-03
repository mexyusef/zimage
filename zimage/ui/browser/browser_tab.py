"""
Browser tab component for ZImage Enterprise
"""
import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QScrollArea, QFileDialog, QMenu, QToolBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QAction, QFont

from zimage.core.constants import (
    THUMBNAIL_MIN_SIZE, THUMBNAIL_MAX_SIZE, THUMBNAIL_STEP, ICONS_DIR,
    PRIMARY_COLOR, PRIMARY_LIGHT_COLOR
)
from zimage.core.utils import get_images_in_directory, get_icon
from zimage.models.image import ImageModel
from zimage.ui.browser.thumbnail_grid import ThumbnailGrid
from zimage.ui.viewer import FullscreenViewer

logger = logging.getLogger('zimage')

class BrowserTab(QWidget):
    """
    Browser tab for image browsing
    """
    # Define signals
    status_message = pyqtSignal(str)
    image_selected = pyqtSignal(object)
    add_to_collage_requested = pyqtSignal(object)

    def __init__(self, config):
        """
        Initialize the browser tab

        Args:
            config (Config): Application configuration
        """
        super().__init__()

        self.config = config
        self.current_folder = None
        self.current_images = []
        self.selected_image = None
        self.active_viewer = None
        self.custom_context_actions = []

        self._init_ui()

    def _init_ui(self):
        """Initialize UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create toolbar
        self._create_toolbar(layout)

        # Create main content area
        content_layout = QHBoxLayout()
        layout.addLayout(content_layout)

        # Create thumbnail grid
        self.thumbnail_grid = ThumbnailGrid(self.config)

        # Add grid to a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(self.thumbnail_grid)
        content_layout.addWidget(scroll_area, 1)

        # Create bottom control bar
        control_layout = QHBoxLayout()
        layout.addLayout(control_layout)

        # Thumbnail size slider
        size_label = QLabel("Thumbnail Size:")
        size_label.setStyleSheet("color: white; font-weight: bold;")
        control_layout.addWidget(size_label)

        self.thumbnail_slider = QSlider(Qt.Orientation.Horizontal)
        self.thumbnail_slider.setMinimum(THUMBNAIL_MIN_SIZE)
        self.thumbnail_slider.setMaximum(THUMBNAIL_MAX_SIZE)
        self.thumbnail_slider.setSingleStep(THUMBNAIL_STEP)
        self.thumbnail_slider.setValue(self.config.get("thumbnail_size", 200))
        self.thumbnail_slider.valueChanged.connect(self._on_thumbnail_size_changed)
        control_layout.addWidget(self.thumbnail_slider)

        # Status label
        self.status_label = QLabel("No folder selected")
        self.status_label.setStyleSheet("color: white;")
        control_layout.addWidget(self.status_label, 1)

        # Connect signals
        self._connect_signals()

    def _create_toolbar(self, layout):
        """Create toolbar components"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {PRIMARY_COLOR};
                border: none;
                spacing: 3px;
                padding: 5px;
            }}
            QToolButton {{
                background-color: {PRIMARY_COLOR};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                margin: 2px;
                font-size: 14px;
                font-weight: bold;
            }}
            QToolButton:hover {{
                background-color: {PRIMARY_LIGHT_COLOR};
            }}
            QToolButton:pressed {{
                background-color: #B25400;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                margin-left: 10px;
                font-size: 14px;
            }}
        """)
        layout.addWidget(toolbar)

        # Back action
        self.back_action = QAction(get_icon("back.png"), "Back", self)
        self.back_action.setStatusTip("Go back to previous folder")
        self.back_action.triggered.connect(self._on_back_clicked)
        toolbar.addAction(self.back_action)

        # Up action
        self.up_action = QAction(get_icon("up.png"), "Up", self)
        self.up_action.setStatusTip("Go up to parent folder")
        self.up_action.triggered.connect(self._on_up_clicked)
        toolbar.addAction(self.up_action)

        # Home action
        self.home_action = QAction(get_icon("home.png"), "Home", self)
        self.home_action.setStatusTip("Go to home folder")
        self.home_action.triggered.connect(self._on_home_clicked)
        toolbar.addAction(self.home_action)

        # Refresh action
        self.refresh_action = QAction(get_icon("refresh.png"), "Refresh", self)
        self.refresh_action.setStatusTip("Refresh current folder")
        self.refresh_action.triggered.connect(self._on_refresh_clicked)
        toolbar.addAction(self.refresh_action)

        # Add path label
        self.path_label = QLabel("No folder selected")
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.path_label.setFont(font)
        toolbar.addWidget(self.path_label)

    def _connect_signals(self):
        """Connect signals to slots"""
        # Connect thumbnail grid signals
        self.thumbnail_grid.image_selected.connect(self._on_image_selected)
        self.thumbnail_grid.image_activated.connect(self._on_image_activated)
        self.thumbnail_grid.context_menu_requested.connect(self._on_context_menu_requested)

    def _on_thumbnail_size_changed(self, size):
        """Handle thumbnail size change"""
        self.config.set("thumbnail_size", size)
        self.thumbnail_grid.set_thumbnail_size(size)
        self.status_message.emit(f"Thumbnail size: {size}px")

    def _on_back_clicked(self):
        """Handle back button click"""
        # To be implemented: go back in history
        self.status_message.emit("Back button clicked")

    def _on_up_clicked(self):
        """Handle up button click"""
        if self.current_folder:
            parent = os.path.dirname(self.current_folder)
            if os.path.exists(parent):
                self.load_folder(parent)

    def _on_home_clicked(self):
        """Handle home button click"""
        home = os.path.expanduser("~")
        self.load_folder(home)

    def _on_refresh_clicked(self):
        """Handle refresh button click"""
        if self.current_folder:
            self.load_folder(self.current_folder)

    def _on_image_selected(self, image_model):
        """Handle image selection"""
        self.selected_image = image_model
        if image_model:
            dimensions = image_model.get_dimensions_str()
            size = image_model.file_size_str
            self.status_label.setText(f"{image_model.file_name} - {dimensions} - {size}")
            self.image_selected.emit(image_model)
        else:
            self.status_label.setText("No image selected")
            self.image_selected.emit(None)

    def _on_image_activated(self, image_model):
        """Handle image activation (double-click)"""
        if image_model:
            logger.debug(f"Image activated: {image_model.file_name}")
            self.view_image_fullscreen(image_model)

    def view_image_fullscreen(self, image_model):
        """
        View the image in fullscreen mode

        Args:
            image_model (ImageModel): Image model to view
        """
        logger.debug(f"Viewing image in fullscreen: {image_model.file_name}")

        # Close any existing viewer
        if self.active_viewer is not None:
            try:
                self.active_viewer.close()
            except Exception as e:
                logger.error(f"Error closing previous viewer: {str(e)}")
            self.active_viewer = None

        # Create and show new viewer
        self.active_viewer = FullscreenViewer(image_model, self)

        # Connect navigation signal
        self.active_viewer.navigate.connect(self._navigate_images)

        # Connect closed signal
        self.active_viewer.closed.connect(self._on_viewer_closed)

        # Show fullscreen
        self.active_viewer.showFullScreen()

    def _on_viewer_closed(self):
        """Handle viewer closed signal"""
        logger.debug("Viewer closed")
        self.active_viewer = None

    def _navigate_images(self, direction):
        """
        Navigate to next/previous image

        Args:
            direction (str): 'next' or 'previous'
        """
        if not self.selected_image or not self.current_images:
            return

        # Find current image index
        try:
            current_index = self.current_images.index(self.selected_image)
        except ValueError:
            logger.error("Cannot find current image in list")
            return

        # Calculate new index with wrap-around
        if direction == "next":
            new_index = (current_index + 1) % len(self.current_images)
        else:  # previous
            new_index = (current_index - 1) % len(self.current_images)

        # Get new image
        new_image = self.current_images[new_index]
        logger.debug(f"Navigating from image {current_index} to {new_index}: {new_image.file_name}")

        # Update selected image
        self.thumbnail_grid.select_image(new_image)

        # If active viewer exists, update it with the new image
        if self.active_viewer:
            self.active_viewer.set_image_model(new_image)

    def _on_context_menu_requested(self, pos, image_model):
        """Handle context menu request"""
        if image_model:
            menu = QMenu(self)

            # Edit action
            edit_action = menu.addAction("Edit")
            edit_action.triggered.connect(lambda: self._on_edit_image(image_model))

            # View action
            view_action = menu.addAction("View Fullscreen")
            view_action.triggered.connect(lambda: self.view_image_fullscreen(image_model))

            # Resize action
            resize_action = menu.addAction("Resize")
            resize_action.triggered.connect(lambda: self._on_resize_image(image_model))

            # Add to collage action
            add_to_collage_action = menu.addAction("Add to Collage")
            add_to_collage_action.triggered.connect(lambda: self._on_add_to_collage(image_model))

            # Add custom actions
            if self.custom_context_actions:
                menu.addSeparator()
                for action_name, action_callback in self.custom_context_actions:
                    custom_action = menu.addAction(action_name)
                    custom_action.triggered.connect(lambda checked=False, cb=action_callback: cb())

            # Show in folder action
            menu.addSeparator()
            show_in_folder_action = menu.addAction("Show in Folder")
            show_in_folder_action.triggered.connect(lambda: self._on_show_in_folder(image_model))

            menu.exec(self.thumbnail_grid.mapToGlobal(pos))

    def _on_edit_image(self, image_model):
        """Handle edit image action"""
        # To be implemented: call parent to switch to editor tab
        self.status_message.emit(f"Edit image: {image_model.file_name}")

    def _on_resize_image(self, image_model):
        """Handle resize image action"""
        # To be implemented: call parent to switch to resizer tab
        self.status_message.emit(f"Resize image: {image_model.file_name}")

    def _on_show_in_folder(self, image_model):
        """Handle show in folder action"""
        # To be implemented: open file explorer at image location
        self.status_message.emit(f"Show in folder: {image_model.file_name}")

    def _on_add_to_collage(self, image_model):
        """Handle add to collage action"""
        self.status_message.emit(f"Add to collage: {image_model.file_name}")
        self.add_to_collage_requested.emit(image_model)

    def load_folder(self, folder, selected_file=None):
        """
        Load a folder and display its images

        Args:
            folder (str): Path to the folder
            selected_file (str, optional): Path to a file to select after loading
        """
        logger.debug(f"Loading folder: {folder}")

        if not os.path.isdir(folder):
            self.status_message.emit(f"Invalid directory: {folder}")
            return

        self.current_folder = folder
        self.path_label.setText(folder)

        # Get all image files in the directory
        try:
            image_paths = get_images_in_directory(folder)

            if not image_paths:
                self.status_message.emit(f"No images found in {folder}")
                self.current_images = []
                self.thumbnail_grid.set_images([])
                return

            # Create image models
            self.current_images = []
            for path in image_paths:
                try:
                    model = ImageModel(path)
                    self.current_images.append(model)
                except Exception as e:
                    logger.error(f"Error creating image model for {path}: {str(e)}")

            # Set images in thumbnail grid
            self.thumbnail_grid.set_images(self.current_images)

            # Select image if specified
            if selected_file and os.path.exists(selected_file):
                self.thumbnail_grid.select_image_by_path(selected_file)

            self.status_message.emit(f"Loaded {len(self.current_images)} images from {folder}")

        except Exception as e:
            logger.error(f"Error loading folder: {str(e)}")
            self.status_message.emit(f"Error loading folder: {str(e)}")

    def get_selected_image(self):
        """
        Get the currently selected image

        Returns:
            ImageModel: Selected image model or None
        """
        return self.selected_image

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # View selected image when Enter is pressed
            if self.selected_image:
                self.view_image_fullscreen(self.selected_image)
        elif event.key() == Qt.Key.Key_Right:
            # Navigate to next image
            self._navigate_images("next")
        elif event.key() == Qt.Key.Key_Left:
            # Navigate to previous image
            self._navigate_images("previous")
        else:
            super().keyPressEvent(event)

    def add_context_menu_action(self, action_name, callback):
        """
        Add a custom action to the context menu

        Args:
            action_name (str): The name to display in the context menu
            callback (callable): Function to call when the action is triggered
        """
        self.custom_context_actions.append((action_name, callback))
        logger.debug(f"Added custom context menu action: {action_name}")
