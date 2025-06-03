"""
Thumbnail grid widget for the browser tab
"""
import logging
from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QSizePolicy, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QPixmap, QColor

from zimage.core.constants import PRIMARY_COLOR

logger = logging.getLogger('zimage')

class ThumbnailWidget(QWidget):
    """
    Widget for displaying a single image thumbnail
    """
    # Define signals
    clicked = pyqtSignal(object)
    double_clicked = pyqtSignal(object)
    context_menu_requested = pyqtSignal(QPoint, object)

    def __init__(self, image_model, thumbnail_size, parent=None):
        """
        Initialize the thumbnail widget

        Args:
            image_model (ImageModel): Image model
            thumbnail_size (int): Size of the thumbnail
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        self.image_model = image_model
        self.thumbnail_size = thumbnail_size
        self.selected = False

        self._init_ui()

    def _init_ui(self):
        """Initialize UI components"""
        # Set fixed size for the widget
        self.setFixedSize(self.thumbnail_size, self.thumbnail_size)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)

        # Simple styling - white background with gray border
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid gray;
                padding: 4px;
            }
        """)

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)

        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Text label for filename
        self.text_label = QLabel(self.image_model.file_name)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setWordWrap(True)

        # Add to layout
        layout.addWidget(self.image_label, 1)
        layout.addWidget(self.text_label, 0)

        # Set tooltip
        tooltip = f"{self.image_model.file_name}\n{self.image_model.get_dimensions_str()}\n{self.image_model.file_size_str}"
        self.setToolTip(tooltip)

        # Load thumbnail
        self._load_thumbnail()

        # Connect signals
        self.customContextMenuRequested.connect(self._on_context_menu_requested)

    def _load_thumbnail(self):
        """Load the thumbnail image"""
        try:
            # Get thumbnail from image model
            logger.debug(f"Loading thumbnail for {self.image_model.file_name}")
            thumbnail = self.image_model.get_thumbnail(self.thumbnail_size - 20)  # Fixed margin

            if thumbnail.isNull():
                logger.error(f"Thumbnail is null for {self.image_model.file_name}")
                self.text_label.setText(f"Error:\n{self.image_model.file_name}")
                return

            # Set pixmap to image label
            self.image_label.setPixmap(thumbnail)
            logger.debug(f"Thumbnail loaded successfully: {thumbnail.width()}x{thumbnail.height()}")

        except Exception as e:
            logger.error(f"Error loading thumbnail: {str(e)}")
            self.text_label.setText(f"Error:\n{self.image_model.file_name}")

    def set_selected(self, selected):
        """
        Set selection state

        Args:
            selected (bool): Whether the thumbnail is selected
        """
        self.selected = selected

        # Update style
        if selected:
            self.setStyleSheet(f"""
                QWidget {{
                    background-color: #d0d9ff;
                    border: 3px solid {PRIMARY_COLOR};
                    padding: 4px;
                }}
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border: 1px solid gray;
                    padding: 4px;
                }
            """)

    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.MouseButton.LeftButton:
            logger.debug(f"Thumbnail clicked: {self.image_model.file_name}")
            self.clicked.emit(self.image_model)

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click event"""
        if event.button() == Qt.MouseButton.LeftButton:
            logger.debug(f"Thumbnail double-clicked: {self.image_model.file_name}")
            self.double_clicked.emit(self.image_model)

        super().mouseDoubleClickEvent(event)

    def _on_context_menu_requested(self, pos):
        """Handle context menu request"""
        self.context_menu_requested.emit(pos, self.image_model)

    def update_thumbnail_size(self, size):
        """
        Update thumbnail size

        Args:
            size (int): New thumbnail size
        """
        self.thumbnail_size = size
        self.setFixedSize(size, size)

        # Reload thumbnail
        self._load_thumbnail()

class ThumbnailGrid(QWidget):
    """
    Grid layout for displaying image thumbnails
    """
    # Define signals
    image_selected = pyqtSignal(object)
    image_activated = pyqtSignal(object)
    context_menu_requested = pyqtSignal(QPoint, object)

    def __init__(self, config, parent=None):
        """
        Initialize the thumbnail grid

        Args:
            config (Config): Application configuration
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        self.config = config
        self.images = []
        self.thumbnails = []
        self.selected_thumbnail = None
        self.thumbnail_size = self.config.get("thumbnail_size", 200)

        self._init_ui()

    def _init_ui(self):
        """Initialize UI components"""
        # Set widget properties
        self.setMinimumSize(200, 200)

        # Create layout - simple grid with fixed spacing
        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        self.layout.setSpacing(10)

        # Style the grid background
        self.setStyleSheet("""
            QWidget {
                background-color: #333333;
            }
        """)

    def set_thumbnail_size(self, size):
        """
        Set thumbnail size

        Args:
            size (int): Thumbnail size
        """
        self.thumbnail_size = size

        # Update existing thumbnails
        for thumbnail in self.thumbnails:
            thumbnail.update_thumbnail_size(size)

        # Force layout update
        self.layout.update()

    def set_images(self, images):
        """
        Set images to display

        Args:
            images (list): List of ImageModel objects
        """
        # Clear existing thumbnails
        self._clear_thumbnails()

        # Store images
        self.images = images

        # Create thumbnails
        for i, image in enumerate(images):
            # Fixed grid with 4 columns
            row, col = i // 4, i % 4
            thumbnail = ThumbnailWidget(image, self.thumbnail_size, self)

            # Connect signals
            thumbnail.clicked.connect(self._on_thumbnail_clicked)
            thumbnail.double_clicked.connect(self._on_thumbnail_double_clicked)
            thumbnail.context_menu_requested.connect(self._on_context_menu_requested)

            # Add to layout and list
            self.layout.addWidget(thumbnail, row, col)
            self.thumbnails.append(thumbnail)

    def _clear_thumbnails(self):
        """Clear all thumbnails"""
        # Remove from layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)

        # Clear lists
        self.thumbnails = []
        self.selected_thumbnail = None

        # Emit signal
        self.image_selected.emit(None)

    def _on_thumbnail_clicked(self, image_model):
        """
        Handle thumbnail click

        Args:
            image_model (ImageModel): Image model
        """
        # Deselect previous thumbnail
        if self.selected_thumbnail:
            self.selected_thumbnail.set_selected(False)

        # Find and select new thumbnail
        for thumbnail in self.thumbnails:
            if thumbnail.image_model == image_model:
                thumbnail.set_selected(True)
                self.selected_thumbnail = thumbnail
                break

        # Emit signal
        self.image_selected.emit(image_model)

    def _on_thumbnail_double_clicked(self, image_model):
        """
        Handle thumbnail double-click

        Args:
            image_model (ImageModel): Image model
        """
        self.image_activated.emit(image_model)

    def _on_context_menu_requested(self, pos, image_model):
        """
        Handle context menu request

        Args:
            pos (QPoint): Position
            image_model (ImageModel): Image model
        """
        self.context_menu_requested.emit(pos, image_model)

    def select_image_by_path(self, path):
        """
        Select an image by its file path

        Args:
            path (str): Path to the image file

        Returns:
            bool: True if the image was found and selected, False otherwise
        """
        for thumbnail in self.thumbnails:
            if thumbnail.image_model.file_path == path:
                self._on_thumbnail_clicked(thumbnail.image_model)
                return True

        return False

    def select_image(self, image_model):
        """
        Select an image model

        Args:
            image_model (ImageModel): Image model to select

        Returns:
            bool: True if the image was found and selected, False otherwise
        """
        # Deselect previous thumbnail
        if self.selected_thumbnail:
            self.selected_thumbnail.set_selected(False)

        # Find the thumbnail that matches the image model
        for thumbnail in self.thumbnails:
            if thumbnail.image_model == image_model:
                thumbnail.set_selected(True)
                self.selected_thumbnail = thumbnail
                self.image_selected.emit(image_model)
                return True

        return False
