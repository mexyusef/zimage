"""
Editor tab component for ZImage Enterprise
"""
import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QScrollArea, QToolBar, QColorDialog, QComboBox,
    QPushButton, QSpinBox, QFileDialog, QMessageBox, QInputDialog, QFontDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QPen, QColor, QImage, QAction,
    QMouseEvent, QWheelEvent, QTransform, QCursor, QFont
)

# Import low-level color functions
from PyQt6.QtGui import qRed, qGreen, qBlue, qRgba, qAlpha

from zimage.core.constants import (
    ICONS_DIR, BRUSH_SIZE_MIN, BRUSH_SIZE_MAX, ToolType,
    PRIMARY_COLOR, PRIMARY_LIGHT_COLOR, TEXT_COLOR
)
from zimage.core.utils import hex_to_qcolor, qcolor_to_hex, qimage_to_pixmap, get_icon
from zimage.models.image import ImageModel

logger = logging.getLogger('zimage')

class CanvasWidget(QLabel):
    """
    Custom widget for the drawing canvas with direct painting support
    """
    # Define signals
    status_message = pyqtSignal(str)

    def __init__(self, parent=None):
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

    def set_image(self, image):
        """Set the canvas image"""
        if isinstance(image, QPixmap):
            self.pixmap = image
            self.original_pixmap = image.copy()
            self.image = image.toImage()
        elif isinstance(image, QImage):
            self.image = image
            self.pixmap = QPixmap.fromImage(image)
            self.original_pixmap = self.pixmap.copy()
        else:
            return

        self.update_display()

    def set_tool(self, tool):
        """Set the active drawing tool"""
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
        self.brush_size = size

    def set_brush_color(self, color):
        """Set the brush color"""
        if isinstance(color, str):
            self.brush_color = hex_to_qcolor(color)
        else:
            self.brush_color = color

    def set_font(self, font):
        """Set the text font"""
        self.text_font = font

    def set_blur_radius(self, radius):
        """Set the blur radius"""
        self.blur_radius = radius

    def set_blur_type(self, blur_type):
        """Set the blur type"""
        self.blur_type = blur_type

    def update_display(self):
        """Update the display with current zoom factor"""
        if self.pixmap is None or self.pixmap.isNull():
            return

        # Create scaled pixmap
        scaled_pixmap = self.pixmap.scaled(
            int(self.pixmap.width() * self.zoom_factor),
            int(self.pixmap.height() * self.zoom_factor),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Set the pixmap
        self.setPixmap(scaled_pixmap)

        # Adjust size
        self.adjustSize()

    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_factor = 1.0
        self.update_display()

    def zoom_in(self, factor=1.2):
        """Zoom in"""
        self.zoom_factor *= factor
        self.update_display()

    def zoom_out(self, factor=1.2):
        """Zoom out"""
        self.zoom_factor /= factor
        if self.zoom_factor < 0.1:
            self.zoom_factor = 0.1
        self.update_display()

    def mousePressEvent(self, event):
        """Handle mouse press events"""
        if self.image is None or event.button() != Qt.MouseButton.LeftButton:
            return

        # Start drawing
        self.drawing = True

        # Convert mouse position to image coordinates
        pos = self._map_to_image(event.pos())
        self.last_point = pos
        self.start_point = pos

        # For tools that need a preview, make a copy of the current pixmap
        if self.active_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.ELLIPSE, ToolType.BLUR]:
            self.temp_pixmap = self.pixmap.copy()

        # Handle different tools
        if self.active_tool == ToolType.PEN:
            # For pen, we draw a point immediately
            self._draw_point(pos)
        elif self.active_tool == ToolType.TEXT:
            # For text, show input dialog
            text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
            if ok and text:
                painter = QPainter()
                if not painter.begin(self.image):
                    logger.error("Failed to begin painting on image for text")
                    return

                painter.setPen(QPen(self.brush_color))
                painter.setFont(self.text_font)
                painter.drawText(pos, text)
                painter.end()
                del painter  # Explicitly delete the painter

                # Update pixmap and display
                self.pixmap = QPixmap.fromImage(self.image)
                self.update_display()

            # Reset drawing state
            self.drawing = False
        elif self.active_tool == ToolType.BLUR and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            try:
                # Status update before processing
                self.status_message.emit(f"Applying {self.blur_type} blur to entire image...")

                # Apply blur to the entire image when Ctrl is pressed
                self._apply_blur_to_image()

                # Update pixmap after blur
                if self.image:
                    self.pixmap = QPixmap.fromImage(self.image)
                    self.update_display()

                # Emit status message
                self.status_message.emit(f"Applied {self.blur_type} blur to entire image (radius: {self.blur_radius})")
            except Exception as e:
                import traceback
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

        # Handle different tools
        if self.active_tool == ToolType.PEN:
            self._draw_line(self.last_point, pos)
            self.last_point = pos
        elif self.active_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.ELLIPSE]:
            # For shapes, draw a preview on a temporary copy
            preview = self.temp_pixmap.copy()
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

            # Update display with preview
            scaled_preview = preview.scaled(
                int(preview.width() * self.zoom_factor),
                int(preview.height() * self.zoom_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_preview)
        elif self.active_tool == ToolType.BLUR:
            # For blur, draw a preview of the blur region
            preview = self.temp_pixmap.copy()
            painter = QPainter(preview)
            painter.setPen(QPen(QColor(255, 255, 0), 1, Qt.PenStyle.DashLine))

            # Draw the blur region rectangle
            rect = QRect(
                min(self.start_point.x(), pos.x()),
                min(self.start_point.y(), pos.y()),
                abs(pos.x() - self.start_point.x()),
                abs(pos.y() - self.start_point.y())
            )
            painter.drawRect(rect)

            # Update display with preview
            scaled_preview = preview.scaled(
                int(preview.width() * self.zoom_factor),
                int(preview.height() * self.zoom_factor),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.setPixmap(scaled_preview)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if not self.drawing or self.image is None:
            return

        # Convert mouse position to image coordinates
        pos = self._map_to_image(event.pos())

        try:
            # Handle different tools
            if self.active_tool == ToolType.LINE:
                self._draw_line(self.start_point, pos)
            elif self.active_tool == ToolType.RECTANGLE:
                self._draw_rectangle(self.start_point, pos)
            elif self.active_tool == ToolType.ELLIPSE:
                self._draw_ellipse(self.start_point, pos)
            elif self.active_tool == ToolType.BLUR:
                # Make sure we're handling a minimum size selection
                if abs(pos.x() - self.start_point.x()) < 5 or abs(pos.y() - self.start_point.y()) < 5:
                    # Selection too small, don't apply blur
                    self.status_message.emit("Selection too small for blur. Please select a larger area.")
                else:
                    try:
                        # Get region size for status message
                        width = abs(pos.x() - self.start_point.x())
                        height = abs(pos.y() - self.start_point.y())

                        # Status update before processing
                        self.status_message.emit(f"Applying {self.blur_type} blur to region...")

                        # Apply blur
                        self._apply_blur_to_region(self.start_point, pos)

                        # Update pixmap only after blur is complete
                        if self.image:  # Make sure image still exists
                            self.pixmap = QPixmap.fromImage(self.image)
                            self.update_display()

                        # Send status message
                        self.status_message.emit(f"Applied {self.blur_type} blur to region {width}x{height} (radius: {self.blur_radius})")
                    except Exception as e:
                        import traceback
                        logger.error(f"Error applying region blur: {str(e)}\n{traceback.format_exc()}")
                        self.status_message.emit(f"Error applying blur: {str(e)}")

            # Update pixmap and display for non-blur tools
            if self.active_tool != ToolType.BLUR and self.image:
                self.pixmap = QPixmap.fromImage(self.image)
                self.update_display()

        except Exception as e:
            import traceback
            logger.error(f"Error in mouseReleaseEvent: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error processing action: {str(e)}")

        # End drawing
        self.drawing = False
        self.temp_pixmap = None

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        # Get degrees delta
        delta = event.angleDelta().y()

        # Zoom in or out based on direction
        if delta > 0:
            self.zoom_in(1.1)  # Smaller factor for smoother zooming
        else:
            self.zoom_out(1.1)  # Smaller factor for smoother zooming

    def _map_to_image(self, pos):
        """Map widget coordinates to image coordinates"""
        if self.pixmap is None or self.pixmap.isNull():
            return pos

        # Get widget size and actual displayed pixmap size
        widget_size = self.size()
        displayed_pixmap_size = self.pixmap.size() * self.zoom_factor

        # Calculate offset to center pixmap in widget
        x_offset = max(0, (widget_size.width() - displayed_pixmap_size.width()) / 2)
        y_offset = max(0, (widget_size.height() - displayed_pixmap_size.height()) / 2)

        # Adjust position for offset and zoom
        x = (pos.x() - x_offset) / self.zoom_factor
        y = (pos.y() - y_offset) / self.zoom_factor

        # Round to nearest pixel
        x = round(x)
        y = round(y)

        # Ensure coordinates are within image bounds
        x = max(0, min(x, self.image.width() - 1))
        y = max(0, min(y, self.image.height() - 1))

        return QPoint(x, y)

    def _draw_point(self, pos):
        """Draw a point at the specified position"""
        if self.image is None:
            return

        painter = QPainter()
        if not painter.begin(self.image):
            logger.error("Failed to begin painting on image for point")
            return

        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawPoint(pos)
        painter.end()
        del painter  # Explicitly delete the painter

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

    def _draw_line(self, start, end):
        """Draw a line from start to end"""
        if self.image is None:
            return

        painter = QPainter()
        if not painter.begin(self.image):
            logger.error("Failed to begin painting on image for line")
            return

        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(start, end)
        painter.end()
        del painter  # Explicitly delete the painter

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

    def _draw_rectangle(self, start, end):
        """Draw a rectangle from start to end"""
        if self.image is None:
            return

        painter = QPainter()
        if not painter.begin(self.image):
            logger.error("Failed to begin painting on image for rectangle")
            return

        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawRect(QRect(start, end))
        painter.end()
        del painter  # Explicitly delete the painter

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

    def _draw_ellipse(self, start, end):
        """Draw an ellipse from start to end"""
        if self.image is None:
            return

        painter = QPainter()
        if not painter.begin(self.image):
            logger.error("Failed to begin painting on image for ellipse")
            return

        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawEllipse(QRect(start, end))
        painter.end()
        del painter  # Explicitly delete the painter

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

    def _draw_preview_line(self, painter, start, end):
        """Draw a preview line"""
        painter.drawLine(start, end)

    def _draw_preview_rectangle(self, painter, start, end):
        """Draw a preview rectangle"""
        painter.drawRect(QRect(start, end))

    def _draw_preview_ellipse(self, painter, start, end):
        """Draw a preview ellipse"""
        painter.drawEllipse(QRect(start, end))

    def _apply_blur_to_region(self, start, end):
        """Apply blur to a specific region of the image"""
        if self.image is None:
            return

        try:
            # Create rectangle from selection points
            rect = QRect(
                min(start.x(), end.x()),
                min(start.y(), end.y()),
                abs(end.x() - start.x()),
                abs(end.y() - start.y())
            )

            # Apply the simple blur algorithm
            self._very_simple_blur(rect)
        except Exception as e:
            import traceback
            logger.error(f"Error in _apply_blur_to_region: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error applying blur: {str(e)}")

    def _apply_blur_to_image(self):
        """Apply blur to the entire image"""
        if self.image is None:
            return

        try:
            # Create rectangle for entire image
            rect = QRect(0, 0, self.image.width(), self.image.height())

            # Apply the simple blur algorithm
            self._very_simple_blur(rect)
        except Exception as e:
            import traceback
            logger.error(f"Error in _apply_blur_to_image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error applying blur: {str(e)}")

    def _very_simple_blur(self, rect):
        """Extremely simple and reliable blur implementation"""
        try:
            # Make a complete copy of the source image
            source = QImage(self.image)

            # Create a new result image with same dimensions
            result = QImage(source.size(), source.format())
            result.fill(Qt.GlobalColor.transparent)  # Start with transparent background

            # Copy the entire source image to the result first
            painter = QPainter()
            if not painter.begin(result):
                logger.error("Failed to begin painting on result image")
                return

            painter.drawImage(0, 0, source)
            painter.end()
            del painter  # Explicitly delete the painter

            # Extract rect coordinates
            x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()

            # Ensure the rectangle is valid
            x = max(0, min(x, source.width() - 1))
            y = max(0, min(y, source.height() - 1))
            w = min(w, source.width() - x)
            h = min(h, source.height() - y)

            if w <= 1 or h <= 1:
                return

            # Create temporary image for the blurred region
            temp_blur = QImage(w, h, source.format())
            temp_blur.fill(Qt.GlobalColor.transparent)  # Start with transparent background

            # Define blur radius based on type
            radius = self.blur_radius
            if radius < 1:
                radius = 1
            elif radius > 20:
                radius = 20  # Limit for performance

            # Apply appropriate blur algorithm
            if self.blur_type == "gaussian" or self.blur_type == "box":
                # Box blur (simpler and more reliable)
                for py in range(h):
                    for px in range(w):
                        # Initialize color components
                        r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
                        count = 0

                        # Calculate average of surrounding pixels
                        for dy in range(-radius, radius + 1):
                            for dx in range(-radius, radius + 1):
                                # Calculate source pixel coordinates
                                sx = x + px + dx
                                sy = y + py + dy

                                # Check if coordinates are valid
                                if 0 <= sx < source.width() and 0 <= sy < source.height():
                                    # Get pixel color
                                    pixel = source.pixel(sx, sy)

                                    # Sum color components
                                    r_sum += qRed(pixel)
                                    g_sum += qGreen(pixel)
                                    b_sum += qBlue(pixel)
                                    a_sum += qAlpha(pixel)

                                    count += 1

                        # Calculate average color
                        if count > 0:
                            r_avg = r_sum // count
                            g_avg = g_sum // count
                            b_avg = b_sum // count
                            a_avg = a_sum // count

                            # Create final pixel color
                            pixel_color = qRgba(r_avg, g_avg, b_avg, a_avg)

                            # Set pixel in temporary image
                            temp_blur.setPixel(px, py, pixel_color)

            elif self.blur_type == "motion":
                # Simple horizontal motion blur
                for py in range(h):
                    for px in range(w):
                        # Initialize color components
                        r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
                        count = 0

                        # Sample only horizontally for motion effect
                        for dx in range(-radius, radius + 1):
                            # Calculate source pixel coordinates
                            sx = x + px + dx
                            sy = y + py

                            # Check if coordinates are valid
                            if 0 <= sx < source.width() and 0 <= sy < source.height():
                                # Get pixel color
                                pixel = source.pixel(sx, sy)

                                # Sum color components
                                r_sum += qRed(pixel)
                                g_sum += qGreen(pixel)
                                b_sum += qBlue(pixel)
                                a_sum += qAlpha(pixel)

                                count += 1

                        # Calculate average color
                        if count > 0:
                            r_avg = r_sum // count
                            g_avg = g_sum // count
                            b_avg = b_sum // count
                            a_avg = a_sum // count

                            # Create final pixel color
                            pixel_color = qRgba(r_avg, g_avg, b_avg, a_avg)

                            # Set pixel in temporary image
                            temp_blur.setPixel(px, py, pixel_color)

            # Draw the blurred region onto the result image
            result_painter = QPainter()
            if not result_painter.begin(result):
                logger.error("Failed to begin painting on result image for blur region")
                return

            result_painter.drawImage(x, y, temp_blur)
            result_painter.end()
            del result_painter  # Explicitly delete the painter

            # Important: Make sure all painter objects are fully cleaned up before replacing the image
            temp_blur = None  # Release temp_blur

            # Replace the original image with the result
            self.image = result

            # Update the pixmap from the new image
            self.pixmap = QPixmap.fromImage(self.image)

        except Exception as e:
            import traceback
            logger.error(f"Error in _very_simple_blur: {str(e)}\n{traceback.format_exc()}")
            raise

    # Add back stubs for the original functions for compatibility
    def _apply_gaussian_blur(self, rect):
        """Apply Gaussian blur to a region of the image"""
        self._very_simple_blur(rect)

    def _apply_box_blur(self, rect):
        """Apply box blur to a region of the image"""
        self._very_simple_blur(rect)

    def _apply_motion_blur(self, rect):
        """Apply motion blur to a region of the image"""
        self._very_simple_blur(rect)

class EditorTab(QWidget):
    """
    Editor tab for image editing
    """
    # Define signals
    status_message = pyqtSignal(str)

    def __init__(self, config):
        """
        Initialize the editor tab

        Args:
            config (Config): Application configuration
        """
        super().__init__()

        self.config = config
        self.current_image = None
        self.current_pixmap = None
        self.original_pixmap = None
        self.active_tool = ToolType.PEN
        self.brush_size = self.config.get("editor.brush_size", 3)
        self.brush_color = self.config.get("editor.brush_color", "#000000")
        self.background_color = self.config.get("editor.background_color", "#FFFFFF")

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

        # Create tool panel (left side) with scrollable area
        tool_panel_container = QScrollArea()
        tool_panel_container.setWidgetResizable(True)
        tool_panel_container.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        tool_panel_container.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        tool_panel_container.setStyleSheet("""
            QScrollArea {
                background-color: #333333;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #444444;
                width: 12px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #666666;
                min-height: 20px;
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)

        tool_panel = QWidget()
        tool_panel.setMinimumWidth(180)
        tool_panel.setMaximumWidth(200)
        tool_panel.setStyleSheet(f"background-color: #333333; color: white;")
        tool_layout = QVBoxLayout(tool_panel)
        tool_layout.setSpacing(12)  # Increase spacing between elements
        tool_layout.setContentsMargins(10, 15, 10, 15)  # Add more padding

        tool_panel_container.setWidget(tool_panel)

        # Tool selection header
        tools_header = QLabel("Tools:")
        tools_header.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        tool_layout.addWidget(tools_header)

        # Button style sheets
        button_style = """
            QPushButton {
                background-color: #444444;
                color: white;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 8px 12px;
                font-weight: bold;
                min-width: 80px;
                text-align: center;
            }
            QPushButton:hover {
                background-color: #555555;
                border: 1px solid #666666;
            }
            QPushButton:pressed, QPushButton:checked {
                background-color: #E86C00;
                border: 1px solid #FF8C30;
            }
        """

        # Tool buttons in a grid
        tools_layout = QHBoxLayout()

        # Pen tool button
        self.pen_button = QPushButton("Pen")
        self.pen_button.setCheckable(True)
        self.pen_button.setChecked(True)  # Default tool
        self.pen_button.setStyleSheet(button_style)
        self.pen_button.clicked.connect(lambda: self._on_tool_selected(ToolType.PEN))
        tools_layout.addWidget(self.pen_button)

        # Line tool button
        self.line_button = QPushButton("Line")
        self.line_button.setCheckable(True)
        self.line_button.setStyleSheet(button_style)
        self.line_button.clicked.connect(lambda: self._on_tool_selected(ToolType.LINE))
        tools_layout.addWidget(self.line_button)

        tool_layout.addLayout(tools_layout)

        tools_layout2 = QHBoxLayout()

        # Rectangle tool button
        self.rect_button = QPushButton("Rectangle")
        self.rect_button.setCheckable(True)
        self.rect_button.setStyleSheet(button_style)
        self.rect_button.clicked.connect(lambda: self._on_tool_selected(ToolType.RECTANGLE))
        tools_layout2.addWidget(self.rect_button)

        # Ellipse tool button
        self.ellipse_button = QPushButton("Ellipse")
        self.ellipse_button.setCheckable(True)
        self.ellipse_button.setStyleSheet(button_style)
        self.ellipse_button.clicked.connect(lambda: self._on_tool_selected(ToolType.ELLIPSE))
        tools_layout2.addWidget(self.ellipse_button)

        tool_layout.addLayout(tools_layout2)

        # Text tool button
        self.text_button = QPushButton("Text")
        self.text_button.setCheckable(True)
        self.text_button.setStyleSheet(button_style)
        self.text_button.clicked.connect(lambda: self._on_tool_selected(ToolType.TEXT))
        tool_layout.addWidget(self.text_button)

        # Blur tool button
        self.blur_button = QPushButton("Blur")
        self.blur_button.setCheckable(True)
        self.blur_button.setStyleSheet(button_style)
        self.blur_button.clicked.connect(lambda: self._on_tool_selected(ToolType.BLUR))
        tool_layout.addWidget(self.blur_button)

        # Add a separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #555555;")
        tool_layout.addWidget(separator)

        # Brush size
        brush_size_label = QLabel("Brush Size:")
        brush_size_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        tool_layout.addWidget(brush_size_label)

        brush_size_layout = QHBoxLayout()
        self.brush_size_spin = QSpinBox()
        self.brush_size_spin.setRange(BRUSH_SIZE_MIN, BRUSH_SIZE_MAX)
        self.brush_size_spin.setValue(self.brush_size)
        self.brush_size_spin.setStyleSheet("""
            background-color: #444444;
            color: white;
            border: 1px solid #555555;
            padding: 3px;
        """)
        self.brush_size_spin.valueChanged.connect(self._on_brush_size_changed)
        brush_size_layout.addWidget(self.brush_size_spin)

        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setRange(BRUSH_SIZE_MIN, BRUSH_SIZE_MAX)
        self.brush_size_slider.setValue(self.brush_size)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        brush_size_layout.addWidget(self.brush_size_slider)
        tool_layout.addLayout(brush_size_layout)

        # Color selection
        color_label = QLabel("Brush Color:")
        color_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        tool_layout.addWidget(color_label)

        self.color_button = QPushButton()
        self.color_button.setStyleSheet(f"""
            background-color: {self.brush_color};
            min-height: 30px;
            border: 2px solid #555555;
            border-radius: 4px;
        """)
        self.color_button.setMaximumWidth(100)
        self.color_button.clicked.connect(self._on_color_button_clicked)
        tool_layout.addWidget(self.color_button)

        # Background color
        bg_color_label = QLabel("Background Color:")
        bg_color_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        tool_layout.addWidget(bg_color_label)

        self.bg_color_button = QPushButton()
        self.bg_color_button.setStyleSheet(f"""
            background-color: {self.background_color};
            min-height: 30px;
            border: 2px solid #555555;
            border-radius: 4px;
        """)
        self.bg_color_button.setMaximumWidth(100)
        self.bg_color_button.clicked.connect(self._on_bg_color_button_clicked)
        tool_layout.addWidget(self.bg_color_button)

        # Add another separator before blur properties
        separator2 = QWidget()
        separator2.setFixedHeight(1)
        separator2.setStyleSheet("background-color: #555555;")
        tool_layout.addWidget(separator2)

        # Blur properties (initially hidden)
        self.blur_properties = QWidget()
        blur_layout = QVBoxLayout(self.blur_properties)
        blur_layout.setSpacing(10)

        # Blur radius
        blur_radius_label = QLabel("Blur Radius:")
        blur_radius_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        blur_layout.addWidget(blur_radius_label)

        blur_radius_layout = QHBoxLayout()
        blur_radius_layout.setSpacing(6)

        self.blur_radius_spin = QSpinBox()
        self.blur_radius_spin.setRange(1, 50)
        self.blur_radius_spin.setValue(10)  # Default
        self.blur_radius_spin.setStyleSheet("""
            background-color: #444444;
            color: white;
            border: 1px solid #555555;
            padding: 3px;
        """)
        self.blur_radius_spin.valueChanged.connect(self._on_blur_radius_changed)
        blur_radius_layout.addWidget(self.blur_radius_spin)

        self.blur_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_radius_slider.setRange(1, 50)
        self.blur_radius_slider.setValue(10)  # Default
        self.blur_radius_slider.valueChanged.connect(self._on_blur_radius_changed)
        blur_radius_layout.addWidget(self.blur_radius_slider)

        blur_layout.addLayout(blur_radius_layout)

        # Blur type
        blur_type_label = QLabel("Blur Type:")
        blur_type_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        blur_layout.addWidget(blur_type_label)

        self.blur_type_combo = QComboBox()
        self.blur_type_combo.addItems(["gaussian", "box", "motion"])
        self.blur_type_combo.currentTextChanged.connect(self._on_blur_type_changed)
        self.blur_type_combo.setStyleSheet("""
            background-color: #444444;
            color: white;
            border: 1px solid #555555;
            padding: 5px;
            min-height: 25px;
        """)
        blur_layout.addWidget(self.blur_type_combo)

        # Blur instructions
        instructions_label = QLabel("Instructions:")
        instructions_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        blur_layout.addWidget(instructions_label)

        blur_instructions = QLabel("1. Draw a region to blur specific area\n2. Hold Ctrl+click to blur the entire image")
        blur_instructions.setWordWrap(True)
        blur_instructions.setStyleSheet("color: #CCCCCC;")
        blur_layout.addWidget(blur_instructions)

        tool_layout.addWidget(self.blur_properties)
        self.blur_properties.setVisible(False)

        # Add another separator before font section
        separator3 = QWidget()
        separator3.setFixedHeight(1)
        separator3.setStyleSheet("background-color: #555555;")
        tool_layout.addWidget(separator3)

        # Font selection for text tool
        font_label = QLabel("Text Font:")
        font_label.setStyleSheet("font-weight: bold; margin-top: 5px;")
        tool_layout.addWidget(font_label)

        self.font_button = QPushButton("Choose Font")
        self.font_button.setStyleSheet(button_style)
        self.font_button.clicked.connect(self._on_font_button_clicked)
        tool_layout.addWidget(self.font_button)

        # Zoom controls
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        tool_layout.addWidget(zoom_label)

        zoom_layout = QHBoxLayout()
        zoom_layout.setSpacing(6)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setStyleSheet(button_style)
        zoom_in_btn.setFixedWidth(40)
        zoom_in_btn.clicked.connect(self._on_zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setStyleSheet(button_style)
        zoom_out_btn.setFixedWidth(40)
        zoom_out_btn.clicked.connect(self._on_zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        zoom_reset_btn = QPushButton("100%")
        zoom_reset_btn.setStyleSheet(button_style)
        zoom_reset_btn.clicked.connect(self._on_zoom_reset)
        zoom_layout.addWidget(zoom_reset_btn)

        tool_layout.addLayout(zoom_layout)

        # Add spacer at the bottom
        tool_layout.addStretch()

        # Add tool panel to content layout
        content_layout.addWidget(tool_panel_container)

        # Create canvas area (right side)
        canvas_container = QScrollArea()
        canvas_container.setWidgetResizable(True)
        canvas_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_container.setStyleSheet("background-color: #222222;")

        # Create canvas widget
        self.canvas = CanvasWidget()

        # Connect canvas signals
        self.canvas.status_message.connect(self.status_message)

        # Add canvas to container
        canvas_container.setWidget(self.canvas)

        # Add canvas container to content layout
        content_layout.addWidget(canvas_container, 1)

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

        # New action
        self.new_action = QAction(get_icon("new.png"), "New", self)
        self.new_action.setStatusTip("Create a new image")
        self.new_action.triggered.connect(self._on_new_clicked)
        toolbar.addAction(self.new_action)

        # Open action
        self.open_action = QAction(get_icon("open.png"), "Open", self)
        self.open_action.setStatusTip("Open an image")
        self.open_action.triggered.connect(self._on_open_clicked)
        toolbar.addAction(self.open_action)

        # Save action
        self.save_action = QAction(get_icon("save.png"), "Save", self)
        self.save_action.setStatusTip("Save the current image")
        self.save_action.triggered.connect(self._on_save_clicked)
        toolbar.addAction(self.save_action)

        # Save As action
        self.save_as_action = QAction(get_icon("save_as.png"), "Save As", self)
        self.save_as_action.setStatusTip("Save the current image with a new name")
        self.save_as_action.triggered.connect(self._on_save_as_clicked)
        toolbar.addAction(self.save_as_action)

        toolbar.addSeparator()

        # Reset action
        self.reset_action = QAction(get_icon("reset.png"), "Reset", self)
        self.reset_action.setStatusTip("Reset to original image")
        self.reset_action.triggered.connect(self._on_reset_clicked)
        toolbar.addAction(self.reset_action)

        # Add label
        title_label = QLabel("Image Editor")
        toolbar.addWidget(title_label)

        # Enable/disable actions
        self._update_actions()

    def _update_actions(self):
        """Update action enabled states"""
        has_image = self.current_image is not None
        self.save_action.setEnabled(has_image)
        self.save_as_action.setEnabled(has_image)
        self.reset_action.setEnabled(has_image)

    def _update_tool_buttons(self):
        """Update tool button states"""
        self.pen_button.setChecked(self.active_tool == ToolType.PEN)
        self.line_button.setChecked(self.active_tool == ToolType.LINE)
        self.rect_button.setChecked(self.active_tool == ToolType.RECTANGLE)
        self.ellipse_button.setChecked(self.active_tool == ToolType.ELLIPSE)
        self.text_button.setChecked(self.active_tool == ToolType.TEXT)
        self.blur_button.setChecked(self.active_tool == ToolType.BLUR)

        # Update canvas tool
        self.canvas.set_tool(self.active_tool)

        # Show/hide tool-specific properties
        self.blur_properties.setVisible(self.active_tool == ToolType.BLUR)

    def _on_tool_selected(self, tool):
        """Handle tool selection"""
        self.active_tool = tool
        self._update_tool_buttons()

        tool_names = {
            ToolType.PEN: "Pen",
            ToolType.LINE: "Line",
            ToolType.RECTANGLE: "Rectangle",
            ToolType.ELLIPSE: "Ellipse",
            ToolType.TEXT: "Text",
            ToolType.BLUR: "Blur"
        }

        self.status_message.emit(f"Selected tool: {tool_names.get(tool, 'Unknown')}")

    def _on_brush_size_changed(self, size):
        """Handle brush size change"""
        # Update both controls
        self.brush_size_spin.blockSignals(True)
        self.brush_size_slider.blockSignals(True)

        self.brush_size_spin.setValue(size)
        self.brush_size_slider.setValue(size)

        self.brush_size_spin.blockSignals(False)
        self.brush_size_slider.blockSignals(False)

        # Update state
        self.brush_size = size
        self.config.set("editor.brush_size", size)

        # Update canvas
        self.canvas.set_brush_size(size)

        self.status_message.emit(f"Brush size: {size}")

    def _on_color_button_clicked(self):
        """Handle color button click"""
        color = QColorDialog.getColor(hex_to_qcolor(self.brush_color), self, "Select Brush Color")
        if color.isValid():
            self.brush_color = qcolor_to_hex(color)
            self.color_button.setStyleSheet(f"""
                background-color: {self.brush_color};
                min-height: 30px;
                border: 2px solid #555555;
                border-radius: 4px;
            """)
            self.config.set("editor.brush_color", self.brush_color)

            # Update canvas
            self.canvas.set_brush_color(color)

            self.status_message.emit(f"Brush color: {self.brush_color}")

    def _on_bg_color_button_clicked(self):
        """Handle background color button click"""
        color = QColorDialog.getColor(hex_to_qcolor(self.background_color), self, "Select Background Color")
        if color.isValid():
            self.background_color = qcolor_to_hex(color)
            self.bg_color_button.setStyleSheet(f"""
                background-color: {self.background_color};
                min-height: 30px;
                border: 2px solid #555555;
                border-radius: 4px;
            """)
            self.config.set("editor.background_color", self.background_color)
            self.status_message.emit(f"Background color: {self.background_color}")

    def _on_zoom_in(self):
        """Handle zoom in button click"""
        if self.canvas:
            self.canvas.zoom_in()

    def _on_zoom_out(self):
        """Handle zoom out button click"""
        if self.canvas:
            self.canvas.zoom_out()

    def _on_zoom_reset(self):
        """Handle zoom reset button click"""
        if self.canvas:
            self.canvas.reset_zoom()

    def _on_new_clicked(self):
        """Handle new button click"""
        # Simple implementation - could be enhanced with a dialog for dimensions
        width, ok = QInputDialog.getInt(self, "New Image Width", "Width:", 800, 100, 5000)
        if not ok:
            return

        height, ok = QInputDialog.getInt(self, "New Image Height", "Height:", 600, 100, 5000)
        if not ok:
            return

        # Create new blank image
        new_image = QImage(width, height, QImage.Format.Format_ARGB32)
        bg_color = hex_to_qcolor(self.background_color)
        new_image.fill(bg_color)

        # Set as current image
        self.current_image = None  # No file path yet
        self.current_pixmap = QPixmap.fromImage(new_image)
        self.original_pixmap = self.current_pixmap.copy()

        # Update canvas
        self.canvas.set_image(new_image)

        # Update actions
        self._update_actions()

        self.status_message.emit(f"Created new image: {width}x{height}")

    def _on_open_clicked(self):
        """Handle open button click"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )

        if file_path:
            self.load_file(file_path)

    def _on_save_clicked(self):
        """Handle save button click"""
        if self.current_image:
            # If we have a file path, save to it
            file_path = self.current_image.file_path
            self.save_image(file_path)
        else:
            # Otherwise, prompt for save location
            self._on_save_as_clicked()

    def _on_save_as_clicked(self):
        """Handle save as button click"""
        if not self.canvas.image:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image As", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )

        if file_path:
            self.save_image(file_path)

    def _on_reset_clicked(self):
        """Handle reset button click"""
        if self.original_pixmap:
            # Reset to original image
            self.canvas.set_image(self.original_pixmap)
            self.status_message.emit("Reset to original image")

    def _on_font_button_clicked(self):
        """Handle font button click"""
        current_font = self.canvas.text_font
        font, ok = QFontDialog.getFont(current_font, self, "Select Text Font")
        if ok:
            self.canvas.set_font(font)
            self.status_message.emit(f"Font set to {font.family()}, {font.pointSize()}pt")

    def _on_blur_radius_changed(self, radius):
        """Handle blur radius change"""
        # Update both controls
        self.blur_radius_spin.blockSignals(True)
        self.blur_radius_slider.blockSignals(True)

        self.blur_radius_spin.setValue(radius)
        self.blur_radius_slider.setValue(radius)

        self.blur_radius_spin.blockSignals(False)
        self.blur_radius_slider.blockSignals(False)

        # Update canvas
        self.canvas.set_blur_radius(radius)

        self.status_message.emit(f"Blur radius: {radius}")

    def _on_blur_type_changed(self, blur_type):
        """Handle blur type change"""
        # Update canvas
        self.canvas.set_blur_type(blur_type)

        self.status_message.emit(f"Blur type: {blur_type}")

    def load_image(self, image_model):
        """
        Load an image from an image model

        Args:
            image_model (ImageModel): Image model to load
        """
        if not image_model:
            return

        try:
            # Get the pixmap
            pixmap = image_model.get_pixmap(force_reload=True)

            if pixmap.isNull():
                self.status_message.emit(f"Failed to load image: {image_model.file_path}")
                return

            # Store image info
            self.current_image = image_model
            self.current_pixmap = pixmap
            self.original_pixmap = pixmap.copy()

            # Set canvas image
            self.canvas.set_image(pixmap)

            # Update actions
            self._update_actions()

            # Update message
            self.status_message.emit(f"Loaded image: {image_model.file_name} ({image_model.get_dimensions_str()})")

        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            self.status_message.emit(f"Error loading image: {str(e)}")

    def load_file(self, file_path):
        """
        Load an image from a file path

        Args:
            file_path (str): Path to the image file
        """
        try:
            # Create image model
            image_model = ImageModel(file_path)

            # Load the image
            self.load_image(image_model)

        except Exception as e:
            logger.error(f"Error loading file: {str(e)}")
            self.status_message.emit(f"Error loading file: {str(e)}")

    def save_image(self, file_path):
        """
        Save the current image to a file

        Args:
            file_path (str): Path to save the image to
        """
        if not self.canvas.image:
            return

        try:
            # Save the image
            self.canvas.image.save(file_path)

            # Update current image
            self.current_image = ImageModel(file_path)
            self.current_pixmap = QPixmap.fromImage(self.canvas.image)
            self.original_pixmap = self.current_pixmap.copy()

            # Update message
            self.status_message.emit(f"Saved image to: {file_path}")

        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            self.status_message.emit(f"Error saving image: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error saving image: {str(e)}")
