"""
Canvas widget for the editor tab
"""
import logging
import traceback
from PyQt6.QtWidgets import QLabel, QInputDialog, QProgressDialog
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QThread
from PyQt6.QtGui import (
    QPixmap, QPainter, QPen, QColor, QImage, QMouseEvent,
    QWheelEvent, QTransform, QCursor, QFont, qRed, qGreen,
    qBlue, qRgba, qAlpha
)

from zimage.core.constants import ToolType
from zimage.core.utils import hex_to_qcolor, qcolor_to_hex
from .blur import apply_blur, BlurWorker

# Set up verbose debugging for this module
logger = logging.getLogger('zimage.editor_tab.canvas')
logger.setLevel(logging.DEBUG)

class CanvasWidget(QLabel):
    """
    Custom widget for the drawing canvas with direct painting support
    """
    # Define signals
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
        logger.debug("Initializing CanvasWidget")
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image = None
        self.pixmap = None
        self.original_pixmap = None
        self.drawing = False
        self.last_point = None
        self.zoom_factor = 1.0
        self.brush_size = 3
        self.brush_color = QColor(Qt.GlobalColor.black)
        self.active_tool = ToolType.PEN
        self.text_font = QFont("Arial", 12)
        self.blur_radius = 10
        self.blur_type = "gaussian"
        self.setText("No image loaded")
        self.setStyleSheet("background-color: #222222; color: white;")

        # For temporary shape preview
        self.temp_pixmap = None
        self.start_point = None
        logger.debug("CanvasWidget initialized")

    def set_image(self, image):
        """Set the canvas image"""
        logger.debug(f"Setting image: {type(image)}")
        if isinstance(image, QPixmap):
            self.pixmap = image
            self.original_pixmap = image.copy()
            self.image = image.toImage()
            logger.debug(f"Image set from QPixmap: {self.image.width()}x{self.image.height()}")
        elif isinstance(image, QImage):
            self.image = image
            self.pixmap = QPixmap.fromImage(image)
            self.original_pixmap = self.pixmap.copy()
            logger.debug(f"Image set from QImage: {self.image.width()}x{self.image.height()}")
        else:
            logger.warning(f"Unsupported image type: {type(image)}")
            return

        self.update_display()

    def set_tool(self, tool):
        """Set the active drawing tool"""
        logger.debug(f"Setting tool: {tool}")
        self.active_tool = tool

        # Set appropriate cursor
        if tool == ToolType.PEN:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.ELLIPSE]:
            self.setCursor(Qt.CursorShape.CrossCursor)
        elif tool == ToolType.TEXT:
            self.setCursor(Qt.CursorShape.IBeamCursor)
        elif tool == ToolType.BLUR:
            self.setCursor(Qt.CursorShape.CrossCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def set_brush_size(self, size):
        """Set the brush size"""
        logger.debug(f"Setting brush size: {size}")
        self.brush_size = size

    def set_brush_color(self, color):
        """Set the brush color"""
        if isinstance(color, str):
            self.brush_color = hex_to_qcolor(color)
            logger.debug(f"Setting brush color from hex: {color}")
        else:
            self.brush_color = color
            logger.debug(f"Setting brush color: {color.name()}")

    def set_font(self, font):
        """Set the text font"""
        logger.debug(f"Setting font: {font.family()}, {font.pointSize()}")
        self.text_font = font

    def set_blur_radius(self, radius):
        """Set the blur radius"""
        logger.debug(f"Setting blur radius: {radius}")
        self.blur_radius = radius

    def set_blur_type(self, blur_type):
        """Set the blur type"""
        logger.debug(f"Setting blur type: {blur_type}")
        self.blur_type = blur_type

    def update_display(self):
        """Update the display with current zoom factor"""
        logger.debug("Updating display")
        if self.pixmap is None or self.pixmap.isNull():
            logger.warning("No pixmap to display or pixmap is null")
            return

        # Create scaled pixmap
        scaled_pixmap = self.pixmap.scaled(
            int(self.pixmap.width() * self.zoom_factor),
            int(self.pixmap.height() * self.zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        logger.debug(f"Scaled pixmap: {scaled_pixmap.width()}x{scaled_pixmap.height()}")

        # Set the pixmap
        self.setPixmap(scaled_pixmap)

        # Adjust size
        self.adjustSize()
        logger.debug("Display updated")

    def reset_zoom(self):
        """Reset zoom to 100%"""
        logger.debug("Resetting zoom")
        self.zoom_factor = 1.0
        self.update_display()

    def zoom_in(self, factor=1.2):
        """Zoom in"""
        logger.debug(f"Zooming in, factor: {factor}")
        self.zoom_factor *= factor
        self.update_display()

    def zoom_out(self, factor=1.2):
        """Zoom out"""
        logger.debug(f"Zooming out, factor: {factor}")
        self.zoom_factor /= factor
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
        self.update_display()

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        logger.debug(f"Mouse press event: {event.button()}")
        if self.image is None or event.button() != Qt.MouseButton.LeftButton:
            logger.debug("Ignoring mouse press: no image or not left button")
            return

        # Start drawing
        self.drawing = True

        # Convert mouse position to image coordinates
        pos = self._map_to_image(event.pos())
        self.last_point = pos
        self.start_point = pos
        logger.debug(f"Drawing start at position: {pos.x()},{pos.y()}")

        # For tools that need a preview, make a copy of the current pixmap
        if self.active_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.ELLIPSE, ToolType.BLUR]:
            logger.debug("Creating temporary pixmap for preview")
            self.temp_pixmap = self.pixmap.copy()

        # Handle different tools
        if self.active_tool == ToolType.PEN:
            # For pen, we draw a point immediately
            logger.debug("Drawing point with pen tool")
            self._draw_point(pos)
        elif self.active_tool == ToolType.TEXT:
            # For text, show input dialog
            logger.debug("Showing text input dialog")
            text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
            if ok and text:
                logger.debug(f"Adding text: '{text}'")
                try:
                    painter = QPainter()
                    if not painter.begin(self.image):
                        logger.error("Failed to begin painting on image for text")
                        return

                    painter.setPen(QPen(self.brush_color))
                    painter.setFont(self.text_font)
                    painter.drawText(pos, text)
                    painter.end()
                    logger.debug("Text drawn successfully")

                    # Update pixmap and display
                    self.pixmap = QPixmap.fromImage(self.image)
                    self.update_display()
                except Exception as e:
                    logger.error(f"Error drawing text: {str(e)}\n{traceback.format_exc()}")
                    self.status_message.emit(f"Error drawing text: {str(e)}")

            # Reset drawing state
            self.drawing = False
        elif self.active_tool == ToolType.BLUR and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            try:
                # Status update before processing
                msg = f"Applying {self.blur_type} blur to entire image..."
                logger.debug(msg)
                self.status_message.emit(msg)

                # Apply blur to the entire image when Ctrl is pressed
                self._apply_blur_to_image()

                # Update pixmap after blur
                if self.image:
                    self.pixmap = QPixmap.fromImage(self.image)
                    self.update_display()

                # Emit status message
                msg = f"Applied {self.blur_type} blur to entire image (radius: {self.blur_radius})"
                logger.debug(msg)
                self.status_message.emit(msg)
            except Exception as e:
                logger.error(f"Error applying blur to entire image: {str(e)}\n{traceback.format_exc()}")
                self.status_message.emit(f"Error applying blur: {str(e)}")

            # Reset drawing state
            self.drawing = False

    def mouseMoveEvent(self, event):
        """Handle mouse move events"""
        if not self.drawing or self.image is None:
            return

        # Convert mouse position to image coordinates
        pos = self._map_to_image(event.pos())
        logger.debug(f"Mouse move event at position: {pos.x()},{pos.y()}")

        # Handle different tools
        if self.active_tool == ToolType.PEN:
            logger.debug("Drawing line with pen tool")
            self._draw_line(self.last_point, pos)
            self.last_point = pos
        elif self.active_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.ELLIPSE]:
            # For shapes, draw a preview on a temporary copy
            logger.debug(f"Drawing preview for tool: {self.active_tool}")
            preview = self.temp_pixmap.copy()

            try:
                painter = QPainter(preview)
                painter.setPen(QPen(self.brush_color, self.brush_size,
                                Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                                Qt.PenJoinStyle.RoundJoin))

                if self.active_tool == ToolType.LINE:
                    self._draw_preview_line(painter, self.start_point, pos)
                elif self.active_tool == ToolType.RECTANGLE:
                    self._draw_preview_rectangle(painter, self.start_point, pos)
                elif self.active_tool == ToolType.ELLIPSE:
                    self._draw_preview_ellipse(painter, self.start_point, pos)

                painter.end()
                logger.debug("Preview drawn successfully")

                # Update display with preview
                scaled_preview = preview.scaled(
                    int(preview.width() * self.zoom_factor),
                    int(preview.height() * self.zoom_factor),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_preview)
            except Exception as e:
                logger.error(f"Error drawing preview: {str(e)}\n{traceback.format_exc()}")
        elif self.active_tool == ToolType.BLUR:
            # For blur, draw a preview rectangle showing the area to be blurred
            logger.debug(f"Drawing blur preview rectangle from {self.start_point.x()},{self.start_point.y()} to {pos.x()},{pos.y()}")
            preview = self.temp_pixmap.copy()

            try:
                painter = QPainter(preview)
                # Use a dashed line for the blur preview
                pen = QPen(Qt.GlobalColor.white, 1, Qt.PenStyle.DashLine)
                pen.setDashPattern([4, 4])
                painter.setPen(pen)

                # Draw the rectangle
                painter.drawRect(QRect(self.start_point, pos))

                # Draw text inside the rectangle indicating "Blur"
                painter.setPen(QPen(Qt.GlobalColor.white))
                font = QFont("Arial", 10)
                font.setBold(True)
                painter.setFont(font)

                # Position the text in the center of the rectangle
                text_rect = QRect(
                    min(self.start_point.x(), pos.x()),
                    min(self.start_point.y(), pos.y()),
                    abs(pos.x() - self.start_point.x()),
                    abs(pos.y() - self.start_point.y())
                )

                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, f"{self.blur_type.capitalize()} Blur")
                painter.end()

                # Update display with preview
                scaled_preview = preview.scaled(
                    int(preview.width() * self.zoom_factor),
                    int(preview.height() * self.zoom_factor),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.setPixmap(scaled_preview)
                logger.debug("Blur preview updated")
            except Exception as e:
                logger.error(f"Error drawing blur preview: {str(e)}\n{traceback.format_exc()}")

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        logger.debug("Mouse release event")
        if not self.drawing or self.image is None:
            return

        # Convert mouse position to image coordinates
        pos = self._map_to_image(event.pos())
        logger.debug(f"Mouse release at position: {pos.x()},{pos.y()}")

        # Handle different tools
        if self.active_tool == ToolType.LINE:
            logger.debug("Finalizing line drawing")
            self._draw_line(self.start_point, pos)
        elif self.active_tool == ToolType.RECTANGLE:
            logger.debug("Finalizing rectangle drawing")
            self._draw_rectangle(self.start_point, pos)
        elif self.active_tool == ToolType.ELLIPSE:
            logger.debug("Finalizing ellipse drawing")
            self._draw_ellipse(self.start_point, pos)
        elif self.active_tool == ToolType.BLUR:
            logger.debug("Applying blur to region")
            self._apply_blur_to_region(self.start_point, pos)

        # Reset drawing state
        self.drawing = False
        self.update_display()

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        logger.debug(f"Wheel event: {event.angleDelta().y()}")
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _map_to_image(self, pos):
        """Convert screen coordinates to image coordinates"""
        if self.pixmap is None or self.pixmap.isNull():
            logger.warning("Cannot map coordinates: no pixmap or pixmap is null")
            return QPoint(0, 0)

        # Get the display pixmap size
        view_width = self.width()
        view_height = self.height()

        # Get the scaled pixmap size
        pixmap_width = int(self.pixmap.width() * self.zoom_factor)
        pixmap_height = int(self.pixmap.height() * self.zoom_factor)

        # Calculate the offset to center the pixmap
        x_offset = max(0, (view_width - pixmap_width) // 2)
        y_offset = max(0, (view_height - pixmap_height) // 2)

        # Calculate the image coordinates
        image_x = int((pos.x() - x_offset) / self.zoom_factor)
        image_y = int((pos.y() - y_offset) / self.zoom_factor)

        # Clamp to image bounds
        image_x = max(0, min(image_x, self.image.width() - 1))
        image_y = max(0, min(image_y, self.image.height() - 1))

        logger.debug(f"Mapped position {pos.x()},{pos.y()} to image coordinates {image_x},{image_y}")
        return QPoint(image_x, image_y)

    def _draw_point(self, pos):
        """Draw a point at the specified position"""
        logger.debug(f"Drawing point at {pos.x()},{pos.y()}")
        if self.image is None:
            logger.warning("Cannot draw point: no image")
            return

        try:
            painter = QPainter()
            logger.debug("Creating painter for point drawing")
            if not painter.begin(self.image):
                logger.error("Failed to begin painting on image for point")
                return

            painter.setPen(QPen(self.brush_color, self.brush_size,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
            painter.drawPoint(pos)
            painter.end()
            logger.debug("Point drawn successfully")

            # Update pixmap and display
            self.pixmap = QPixmap.fromImage(self.image)
            self.update_display()
        except Exception as e:
            logger.error(f"Error drawing point: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error drawing point: {str(e)}")

    def _draw_line(self, start, end):
        """Draw a line from start to end"""
        logger.debug(f"Drawing line from {start.x()},{start.y()} to {end.x()},{end.y()}")
        if self.image is None:
            logger.warning("Cannot draw line: no image")
            return

        try:
            painter = QPainter()
            logger.debug("Creating painter for line drawing")
            if not painter.begin(self.image):
                logger.error("Failed to begin painting on image for line")
                return

            painter.setPen(QPen(self.brush_color, self.brush_size,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
            painter.drawLine(start, end)
            painter.end()
            logger.debug("Line drawn successfully")

            # Update pixmap and display
            self.pixmap = QPixmap.fromImage(self.image)
            self.update_display()
        except Exception as e:
            logger.error(f"Error drawing line: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error drawing line: {str(e)}")

    def _draw_rectangle(self, start, end):
        """Draw a rectangle from start to end"""
        logger.debug(f"Drawing rectangle from {start.x()},{start.y()} to {end.x()},{end.y()}")
        if self.image is None:
            logger.warning("Cannot draw rectangle: no image")
            return

        try:
            painter = QPainter()
            logger.debug("Creating painter for rectangle drawing")
            if not painter.begin(self.image):
                logger.error("Failed to begin painting on image for rectangle")
                return

            painter.setPen(QPen(self.brush_color, self.brush_size,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
            painter.drawRect(QRect(start, end))
            painter.end()
            logger.debug("Rectangle drawn successfully")

            # Update pixmap and display
            self.pixmap = QPixmap.fromImage(self.image)
            self.update_display()
        except Exception as e:
            logger.error(f"Error drawing rectangle: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error drawing rectangle: {str(e)}")

    def _draw_ellipse(self, start, end):
        """Draw an ellipse from start to end"""
        logger.debug(f"Drawing ellipse from {start.x()},{start.y()} to {end.x()},{end.y()}")
        if self.image is None:
            logger.warning("Cannot draw ellipse: no image")
            return

        try:
            painter = QPainter()
            logger.debug("Creating painter for ellipse drawing")
            if not painter.begin(self.image):
                logger.error("Failed to begin painting on image for ellipse")
                return

            painter.setPen(QPen(self.brush_color, self.brush_size,
                            Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                            Qt.PenJoinStyle.RoundJoin))
            painter.drawEllipse(QRect(start, end))
            painter.end()
            logger.debug("Ellipse drawn successfully")

            # Update pixmap and display
            self.pixmap = QPixmap.fromImage(self.image)
            self.update_display()
        except Exception as e:
            logger.error(f"Error drawing ellipse: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error drawing ellipse: {str(e)}")

    def _draw_preview_line(self, painter, start, end):
        """Draw a preview line on the temporary pixmap"""
        logger.debug(f"Drawing preview line from {start.x()},{start.y()} to {end.x()},{end.y()}")
        painter.drawLine(start, end)

    def _draw_preview_rectangle(self, painter, start, end):
        """Draw a preview rectangle on the temporary pixmap"""
        logger.debug(f"Drawing preview rectangle from {start.x()},{start.y()} to {end.x()},{end.y()}")
        painter.drawRect(QRect(start, end))

    def _draw_preview_ellipse(self, painter, start, end):
        """Draw a preview ellipse on the temporary pixmap"""
        logger.debug(f"Drawing preview ellipse from {start.x()},{start.y()} to {end.x()},{end.y()}")
        painter.drawEllipse(QRect(start, end))

    def _apply_blur_to_region(self, start, end):
        """Apply blur to a specific region of the image"""
        logger.debug(f"Applying blur to region from {start.x()},{start.y()} to {end.x()},{end.y()}")
        try:
            # Create a rect from the start and end points
            x = min(start.x(), end.x())
            y = min(start.y(), end.y())
            width = abs(start.x() - end.x())
            height = abs(start.y() - end.y())
            rect = QRect(x, y, width, height)

            # Status update before processing
            msg = f"Applying {self.blur_type} blur to selected region..."
            logger.debug(msg)
            self.status_message.emit(msg)

            # Create progress dialog
            progress_dialog = QProgressDialog(f"Applying {self.blur_type} blur...", "Cancel", 0, 100, self.parent())
            progress_dialog.setWindowTitle("Blur Progress")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(500)  # Only show dialog if operation takes more than 500ms

            # Create a worker and thread for processing
            self.blur_thread = QThread()
            self.blur_worker = BlurWorker(self.image, rect, self.blur_type, self.blur_radius)
            self.blur_worker.moveToThread(self.blur_thread)

            # Connect signals
            self.blur_thread.started.connect(self.blur_worker.run)
            self.blur_worker.finished.connect(self._on_blur_finished)
            self.blur_worker.finished.connect(self.blur_thread.quit)
            self.blur_worker.finished.connect(self.blur_worker.deleteLater)
            self.blur_thread.finished.connect(self.blur_thread.deleteLater)
            self.blur_worker.progress.connect(progress_dialog.setValue)

            # Start the thread
            self.blur_thread.start()

            # Show the progress dialog
            progress_dialog.exec()

            # If the user canceled, terminate the thread
            if progress_dialog.wasCanceled():
                logger.debug("Blur operation canceled by user")
                self.blur_thread.terminate()
                self.blur_thread.wait()
                self.status_message.emit("Blur operation canceled")

        except Exception as e:
            logger.error(f"Error applying blur to region: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error applying blur: {str(e)}")

    def _on_blur_finished(self, result_image):
        """Handle completion of blur operation"""
        logger.debug("Blur operation completed")
        try:
            # Update the image and pixmap
            self.image = result_image
            self.pixmap = QPixmap.fromImage(self.image)
            self.update_display()

            # Emit status message
            msg = f"Applied {self.blur_type} blur to region (radius: {self.blur_radius})"
            logger.debug(msg)
            self.status_message.emit(msg)
        except Exception as e:
            logger.error(f"Error updating image after blur: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error updating image: {str(e)}")

    def _apply_blur_to_image(self):
        """Apply blur to the entire image"""
        logger.debug("Applying blur to entire image")
        try:
            # Create a rect that encompasses the entire image
            rect = QRect(0, 0, self.image.width(), self.image.height())

            # Status update before processing
            msg = f"Applying {self.blur_type} blur to entire image..."
            logger.debug(msg)
            self.status_message.emit(msg)

            # Create progress dialog
            progress_dialog = QProgressDialog(f"Applying {self.blur_type} blur...", "Cancel", 0, 100, self.parent())
            progress_dialog.setWindowTitle("Blur Progress")
            progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
            progress_dialog.setMinimumDuration(500)  # Only show dialog if operation takes more than 500ms

            # Create a worker and thread for processing
            self.blur_thread = QThread()
            self.blur_worker = BlurWorker(self.image, rect, self.blur_type, self.blur_radius)
            self.blur_worker.moveToThread(self.blur_thread)

            # Connect signals
            self.blur_thread.started.connect(self.blur_worker.run)
            self.blur_worker.finished.connect(self._on_blur_finished)
            self.blur_worker.finished.connect(self.blur_thread.quit)
            self.blur_worker.finished.connect(self.blur_worker.deleteLater)
            self.blur_thread.finished.connect(self.blur_thread.deleteLater)
            self.blur_worker.progress.connect(progress_dialog.setValue)

            # Start the thread
            self.blur_thread.start()

            # Show the progress dialog
            progress_dialog.exec()

            # If the user canceled, terminate the thread
            if progress_dialog.wasCanceled():
                logger.debug("Blur operation canceled by user")
                self.blur_thread.terminate()
                self.blur_thread.wait()
                self.status_message.emit("Blur operation canceled")

        except Exception as e:
            logger.error(f"Error applying blur to entire image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error applying blur: {str(e)}")
