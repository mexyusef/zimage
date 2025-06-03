"""
Canvas widget for meme creator
"""
import os
import logging
from PyQt6.QtWidgets import QWidget, QApplication, QScrollArea
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QImage, QPixmap, QPen, QTransform, QWheelEvent

from zimage.models.meme import MemeModel
from zimage.models.text_box import TextBoxModel
from zimage.ui.meme.text_box import TextBox

logger = logging.getLogger('zimage')

class MemeCanvas(QWidget):
    """
    Canvas widget for displaying and editing memes
    """
    # Define signals
    text_box_selected = pyqtSignal(object)  # TextBoxModel
    text_box_changed = pyqtSignal(object)   # TextBoxModel
    text_box_added = pyqtSignal(object)     # TextBoxModel

    def __init__(self, parent=None):
        """
        Initialize the meme canvas

        Args:
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        # Set widget properties
        self.setMinimumSize(400, 300)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)  # Track mouse movement

        # Meme properties
        self.meme_model = MemeModel()
        self.text_boxes = []  # List of TextBox objects

        # Editing state
        self.selected_text_box = None
        self.drag_active = False
        self.panning = False
        self.last_pan_pos = None

        # Zoom and transform properties
        self.zoom_factor = 1.0
        self.offset = QPoint(0, 0)

        # Set background color
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(50, 50, 50))  # Dark gray
        self.setPalette(palette)

        logger.debug("Initialized meme canvas")

    def set_meme_model(self, meme_model):
        """
        Set the meme model

        Args:
            meme_model (MemeModel): Meme model to set
        """
        self.meme_model = meme_model
        self._update_text_boxes()
        self.reset_zoom()
        self.update()
        logger.debug("Set meme model in canvas")

    def load_image(self, image_path):
        """
        Load an image into the canvas

        Args:
            image_path (str): Path to the image file

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.meme_model:
            self.meme_model = MemeModel()

        result = self.meme_model.load_image(image_path)
        if result:
            # Update canvas size to match image
            self.setMinimumSize(self.meme_model.get_size())
            self._update_text_boxes()
            self.reset_zoom()
            self.update()

        return result

    def _update_text_boxes(self):
        """Update the text box widgets from the model"""
        self.text_boxes = []

        for tb_model in self.meme_model.text_boxes:
            # Ensure text boxes have valid rectangles
            if tb_model.rect.isEmpty() and self.meme_model.image:
                tb_model.calculate_position(
                    self.meme_model.image.width(),
                    self.meme_model.image.height()
                )

            # Create text box widget
            text_box = TextBox(tb_model, self)
            self.text_boxes.append(text_box)

        # Update selection
        self.selected_text_box = None

    def add_text_box(self, text="", position="custom", rect=None):
        """
        Add a new text box to the meme

        Args:
            text (str): Text content
            position (str): Position type ("top", "bottom", "custom")
            rect (QRect, optional): Custom rectangle for "custom" position

        Returns:
            TextBox: The created text box widget
        """
        # Add text box to model
        tb_model = self.meme_model.add_text_box(text, position, rect)

        # Ensure it has a valid rectangle
        if self.meme_model.image:
            tb_model.calculate_position(
                self.meme_model.image.width(),
                self.meme_model.image.height()
            )

        # Create text box widget
        text_box = TextBox(tb_model, self)
        self.text_boxes.append(text_box)

        # Select the new text box
        self.select_text_box(text_box)

        # Emit signal
        self.text_box_added.emit(tb_model)

        # Update canvas
        self.update()

        return text_box

    def remove_text_box(self, text_box):
        """
        Remove a text box from the meme

        Args:
            text_box (TextBox): Text box to remove

        Returns:
            bool: True if removed, False if not found
        """
        if text_box in self.text_boxes:
            # Remove from model
            self.meme_model.remove_text_box(text_box.model)

            # Remove from text boxes list
            self.text_boxes.remove(text_box)

            # Update selection
            if self.selected_text_box == text_box:
                self.selected_text_box = None
                self.text_box_selected.emit(None)

            # Update canvas
            self.update()

            return True

        return False

    def clear_text_boxes(self):
        """Clear all text boxes"""
        self.meme_model.clear_text_boxes()
        self.text_boxes = []
        self.selected_text_box = None
        self.text_box_selected.emit(None)
        self.update()

    def select_text_box(self, text_box):
        """
        Select a text box

        Args:
            text_box (TextBox): Text box to select
        """
        # Deselect previous selection
        if self.selected_text_box:
            self.selected_text_box.model.selected = False

        # Set new selection
        self.selected_text_box = text_box

        if text_box:
            text_box.model.selected = True
            self.text_box_selected.emit(text_box.model)
        else:
            self.text_box_selected.emit(None)

        # Update canvas
        self.update()

    def add_classic_meme_format(self):
        """
        Add top and bottom text boxes in classic meme format

        Returns:
            tuple: (top_text_box, bottom_text_box)
        """
        # Clear existing text boxes
        self.clear_text_boxes()

        # Add classic format to model
        top_model, bottom_model = self.meme_model.add_classic_meme_format()

        # Create text box widgets
        top_box = TextBox(top_model, self)
        bottom_box = TextBox(bottom_model, self)

        # Add to text boxes list
        self.text_boxes.append(top_box)
        self.text_boxes.append(bottom_box)

        # Select the top text box
        self.select_text_box(top_box)

        # Emit signals
        self.text_box_added.emit(top_model)
        self.text_box_added.emit(bottom_model)

        # Update canvas
        self.update()

        return (top_box, bottom_box)

    def export_image(self, file_path, image_format="png"):
        """
        Export the meme as an image file

        Args:
            file_path (str): Path to save the image
            image_format (str): Image format (png, jpg, etc.)

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.meme_model or not self.meme_model.image:
            logger.error("No image to export")
            return False

        try:
            # Create a new image with the same dimensions
            image = QImage(
                self.meme_model.image.width(),
                self.meme_model.image.height(),
                QImage.Format.Format_ARGB32
            )

            # Fill with white
            image.fill(Qt.GlobalColor.white)

            # Create painter
            painter = QPainter(image)

            # Draw the base image
            painter.drawImage(0, 0, self.meme_model.image)

            # Draw text boxes
            for text_box in self.text_boxes:
                # Don't draw selection indicators
                text_box.model.selected = False
                text_box.render(painter)

            # End painting
            painter.end()

            # Save to file
            result = image.save(file_path, image_format.upper())

            # Restore selection
            if self.selected_text_box:
                self.selected_text_box.model.selected = True

            logger.debug(f"Exported meme to {file_path}")
            return result
        except Exception as e:
            logger.error(f"Error exporting meme: {str(e)}")
            return False

    def zoom(self, factor):
        """
        Zoom in or out by the given factor

        Args:
            factor (float): Zoom factor (>1 to zoom in, <1 to zoom out)
        """
        if not self.meme_model or not self.meme_model.image:
            return

        # Apply zoom factor
        old_zoom = self.zoom_factor
        self.zoom_factor *= factor

        # Limit zoom range
        self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))

        # Update the view
        self.update()

        # Emit status message
        logger.debug(f"Zoom level: {self.zoom_factor:.2f}x")

    def reset_zoom(self):
        """Reset zoom to original size and center the image"""
        self.zoom_factor = 1.0
        self.offset = QPoint(0, 0)
        self.update()
        logger.debug("Zoom reset")

    def get_transform(self):
        """
        Get the current transform for painting

        Returns:
            QTransform: Current transform
        """
        if not self.meme_model or not self.meme_model.image:
            return QTransform()

        # Get image dimensions
        img_width = self.meme_model.image.width()
        img_height = self.meme_model.image.height()

        # Calculate centered position
        x = max(0, (self.width() - img_width * self.zoom_factor) // 2)
        y = max(0, (self.height() - img_height * self.zoom_factor) // 2)

        # Create transform
        transform = QTransform()
        transform.translate(x + self.offset.x(), y + self.offset.y())
        transform.scale(self.zoom_factor, self.zoom_factor)

        return transform

    def paintEvent(self, event):
        """
        Handle paint events

        Args:
            event (QPaintEvent): Paint event
        """
        painter = QPainter(self)

        # Draw the base image
        if self.meme_model and self.meme_model.image and not self.meme_model.image.isNull():
            # Apply zoom and offset transform
            transform = self.get_transform()
            painter.setTransform(transform)

            # Draw the image
            painter.drawImage(0, 0, self.meme_model.image)

            # Draw a border around the image
            painter.setPen(QPen(Qt.GlobalColor.white, 1, Qt.PenStyle.SolidLine))
            painter.drawRect(0, 0, self.meme_model.image.width(), self.meme_model.image.height())

            # Reset transform for text boxes
            painter.resetTransform()

            # Draw text boxes with appropriate transform
            for text_box in self.text_boxes:
                # Apply zoom and offset before rendering each text box
                painter.setTransform(transform)
                text_box.render(painter)
                painter.resetTransform()
        else:
            # Draw placeholder text
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(
                self.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No image loaded"
            )

    def mousePressEvent(self, event):
        """
        Handle mouse press events

        Args:
            event (QMouseEvent): Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if clicking on a handle of the selected text box
            if self.selected_text_box:
                # Apply inverse transform to get position in image coordinates
                transform = self.get_transform().inverted()[0]
                img_pos = transform.map(event.pos())

                handle_index = self.selected_text_box.handle_at_point(img_pos)
                if handle_index is not None:
                    # Start resize drag
                    self.selected_text_box.active_handle = handle_index
                    self.selected_text_box.start_drag(img_pos)
                    self.drag_active = True
                    return

            # Check if clicking on a text box
            clicked_box = None
            # Apply inverse transform to get position in image coordinates
            transform = self.get_transform().inverted()[0]
            img_pos = transform.map(event.pos())

            for text_box in reversed(self.text_boxes):  # Check in reverse order (top to bottom)
                if text_box.contains_point(img_pos):
                    clicked_box = text_box
                    break

            if clicked_box:
                # Select the clicked text box
                self.select_text_box(clicked_box)

                # Start drag
                clicked_box.start_drag(img_pos)
                self.drag_active = True
            else:
                # Clicked on empty space - start panning or deselect
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    # Start panning with Ctrl + Left click
                    self.panning = True
                    self.last_pan_pos = event.pos()
                    self.setCursor(Qt.CursorShape.ClosedHandCursor)
                else:
                    # Just deselect
                    self.select_text_box(None)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events

        Args:
            event (QMouseEvent): Mouse event
        """
        # Handle panning
        if self.panning and self.last_pan_pos:
            # Calculate the difference
            delta = event.pos() - self.last_pan_pos
            self.offset += delta
            self.last_pan_pos = event.pos()
            self.update()
            return

        # Apply inverse transform to get position in image coordinates
        transform = self.get_transform().inverted()[0]
        img_pos = transform.map(event.pos())

        # Update cursor based on hover
        if not self.drag_active and self.selected_text_box:
            handle_index = self.selected_text_box.handle_at_point(img_pos)
            if handle_index is not None:
                # Set resize cursor based on handle
                if handle_index in [TextBox.HANDLE_TOP_LEFT, TextBox.HANDLE_BOTTOM_RIGHT]:
                    self.setCursor(Qt.CursorShape.SizeFDiagCursor)
                else:
                    self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif self.selected_text_box.contains_point(img_pos):
                # Set move cursor
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # Show hand cursor for panning when Ctrl is pressed
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            else:
                # Reset cursor
                self.setCursor(Qt.CursorShape.ArrowCursor)
        elif event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Show hand cursor for panning when Ctrl is pressed
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            # Reset cursor
            self.setCursor(Qt.CursorShape.ArrowCursor)

        # Handle drag
        if self.drag_active and self.selected_text_box:
            self.selected_text_box.drag_to(img_pos)
            self.update()
            self.text_box_changed.emit(self.selected_text_box.model)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events

        Args:
            event (QMouseEvent): Mouse event
        """
        if event.button() == Qt.MouseButton.LeftButton:
            if self.panning:
                self.panning = False
                self.last_pan_pos = None
                self.setCursor(Qt.CursorShape.ArrowCursor)
            elif self.drag_active:
                # End drag
                if self.selected_text_box:
                    self.selected_text_box.end_drag()
                self.drag_active = False

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        """
        Handle mouse wheel events for zooming

        Args:
            event (QWheelEvent): Wheel event
        """
        if not self.meme_model or not self.meme_model.image:
            return

        # Calculate zoom factor based on wheel delta
        delta = event.angleDelta().y()
        if delta > 0:
            # Zoom in
            self.zoom(1.1)
        elif delta < 0:
            # Zoom out
            self.zoom(0.9)

        event.accept()

    def keyPressEvent(self, event):
        """
        Handle key press events

        Args:
            event (QKeyEvent): Key event
        """
        if self.selected_text_box:
            if event.key() == Qt.Key.Key_Delete:
                # Delete selected text box
                self.remove_text_box(self.selected_text_box)
            elif event.key() == Qt.Key.Key_Escape:
                # Deselect
                self.select_text_box(None)
        elif event.key() == Qt.Key.Key_Space:
            # Reset zoom and pan with spacebar
            self.reset_zoom()

        super().keyPressEvent(event)
