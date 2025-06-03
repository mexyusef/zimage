"""
Fullscreen image viewer for ZImage Enterprise
"""
import os
import logging
from PyQt6.QtWidgets import QLabel, QApplication
from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap, QColor, QPainter, QWheelEvent

logger = logging.getLogger('zimage')

class FullscreenViewer(QLabel):
    """
    Fullscreen image display with zooming and panning functionality
    """
    # Define signals
    closed = pyqtSignal()
    navigate = pyqtSignal(str)

    def __init__(self, image_model=None, parent=None):
        """
        Initialize the fullscreen viewer

        Args:
            image_model (ImageModel, optional): Image model to display
            parent (QWidget, optional): Parent widget
        """
        logger.debug("Initializing fullscreen viewer")
        super().__init__(parent)

        # Store the image model
        self.image_model = image_model

        # Initialize pixmap early to avoid errors
        self.original_pixmap = QPixmap()

        # Image viewing properties
        self.zoom_factor = 1.0
        self.zoom_step = 1.2  # 20% zoom per step
        self.pan_start_pos = None
        self.offset = QPoint(0, 0)

        # Configure for fullscreen
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint)
        self.setWindowState(Qt.WindowState.WindowFullScreen)

        # Black background
        self.setStyleSheet("background-color: black;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Enable mouse tracking for panning
        self.setMouseTracking(True)

        # Set cursor for panning
        self.setCursor(Qt.CursorShape.OpenHandCursor)

        # Set initial window title with instructions
        self.setWindowTitle("Mouse drag: Pan | +/-: Zoom | F: Fit | R: Reset | Esc: Close | ←/→: Navigate")

        # Load image if provided
        if image_model:
            self.set_image_model(image_model)

    def set_image_model(self, image_model):
        """
        Set the image model to display

        Args:
            image_model (ImageModel): Image model
        """
        self.image_model = image_model
        logger.debug(f"Loading image: {image_model.file_path}")

        # Load pixmap
        self.original_pixmap = image_model.get_pixmap(force_reload=True)

        if self.original_pixmap.isNull():
            logger.error("Error: Pixmap is null")
        else:
            logger.debug(f"Pixmap loaded: {self.original_pixmap.width()}x{self.original_pixmap.height()}")

        # Calculate screen dimensions
        self.screen = QApplication.primaryScreen().size()
        logger.debug(f"Screen size: {self.screen.width()}x{self.screen.height()}")

        # Reset zoom and pan
        self.zoom_factor = 1.0
        self.offset = QPoint(0, 0)

        # Update display immediately
        self.update_display()

    def update_display(self):
        """Update the displayed image with current zoom and pan"""
        if self.original_pixmap.isNull():
            return

        # Calculate the scaled size
        orig_size = self.original_pixmap.size()
        scaled_width = int(orig_size.width() * self.zoom_factor)
        scaled_height = int(orig_size.height() * self.zoom_factor)

        # Scale the image
        scaled_pixmap = self.original_pixmap.scaled(
            scaled_width, scaled_height,
            aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
            transformMode=Qt.TransformationMode.SmoothTransformation
        )

        # Create a new pixmap for drawing with offset
        display_pixmap = QPixmap(self.width(), self.height())
        display_pixmap.fill(QColor(0, 0, 0))  # Pure black background

        # Calculate centered position
        x = max(0, (self.width() - scaled_width) // 2)
        y = max(0, (self.height() - scaled_height) // 2)

        # Apply panning offset
        x += self.offset.x()
        y += self.offset.y()

        # Draw the scaled image with offset
        painter = QPainter(display_pixmap)
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()

        # Set the pixmap to display
        self.setPixmap(display_pixmap)

        # Update window title with zoom level
        if self.image_model:
            filename = self.image_model.file_name
            self.setWindowTitle(f"{filename} ({int(self.zoom_factor * 100)}%)")

    def fit_to_screen(self):
        """Fit image to screen dimensions"""
        if self.original_pixmap.isNull():
            return

        # Get dimensions
        img_width = self.original_pixmap.width()
        img_height = self.original_pixmap.height()

        if img_width <= 0 or img_height <= 0:
            return

        # Calculate ratios
        width_ratio = (self.width() - 20) / img_width  # Leave small margin
        height_ratio = (self.height() - 20) / img_height

        # Use smaller ratio to fit screen
        self.zoom_factor = min(width_ratio, height_ratio)

        # Reset panning
        self.offset = QPoint(0, 0)

        # Update the display
        self.update_display()

    def showEvent(self, event):
        """Track when the widget is shown"""
        super().showEvent(event)
        # Fit to screen when first shown - use QTimer to ensure widget is fully initialized
        QTimer.singleShot(100, self.fit_to_screen)

    def resizeEvent(self, event):
        """Handle window resize"""
        super().resizeEvent(event)
        # Update display only if we already have a valid pixmap
        if hasattr(self, 'original_pixmap') and not self.original_pixmap.isNull():
            self.update_display()

    def zoom_in(self):
        """Zoom in on the image"""
        self.zoom_factor *= self.zoom_step
        self.update_display()

    def zoom_out(self):
        """Zoom out from the image"""
        self.zoom_factor /= self.zoom_step
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1  # Minimum zoom
        self.update_display()

    def mousePressEvent(self, event):
        """Handle mouse press for panning"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.pan_start_pos = event.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release for panning"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.pan_start_pos = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move for panning"""
        if self.pan_start_pos:
            # Calculate how far mouse has moved
            delta = event.pos() - self.pan_start_pos
            self.pan_start_pos = event.pos()

            # Update panning offset
            self.offset += delta
            self.update_display()
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming

        Args:
            event (QWheelEvent): Wheel event
        """
        # Calculate zoom direction based on wheel delta
        delta = event.angleDelta().y()

        # Determine zoom center point (where mouse is pointing)
        pos = event.position().toPoint()

        # Store old zoom factor
        old_zoom = self.zoom_factor

        # Adjust zoom factor based on wheel direction
        if delta > 0:
            # Zoom in
            self.zoom_factor *= self.zoom_step
        else:
            # Zoom out
            self.zoom_factor /= self.zoom_step
            if self.zoom_factor < 0.1:
                self.zoom_factor = 0.1  # Minimum zoom

        # Update display
        self.update_display()

        # Accept the event
        event.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Plus or event.key() == Qt.Key.Key_Equal:
            self.zoom_in()
        elif event.key() == Qt.Key.Key_Minus:
            self.zoom_out()
        elif event.key() == Qt.Key.Key_F:
            self.fit_to_screen()
        elif event.key() == Qt.Key.Key_R:
            self.zoom_factor = 1.0
            self.offset = QPoint(0, 0)
            self.update_display()
        elif event.key() == Qt.Key.Key_Right:
            self.navigate.emit("next")
        elif event.key() == Qt.Key.Key_Left:
            self.navigate.emit("previous")

        super().keyPressEvent(event)

    def closeEvent(self, event):
        """Handle close event"""
        logger.debug("Closing fullscreen viewer")
        self.closed.emit()
        super().closeEvent(event)
