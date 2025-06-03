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
        if self.active_tool in [ToolType.LINE, ToolType.RECTANGLE, ToolType.ELLIPSE]:
            self.temp_pixmap = self.pixmap.copy()

        # Handle different tools
        if self.active_tool == ToolType.PEN:
            # For pen, we draw a point immediately
            self._draw_point(pos)
        elif self.active_tool == ToolType.TEXT:
            # For text, show input dialog
            text, ok = QInputDialog.getText(self, "Add Text", "Enter text:")
            if ok and text:
                painter = QPainter(self.image)
                painter.setPen(QPen(self.brush_color))
                painter.setFont(self.text_font)
                painter.drawText(pos, text)
                painter.end()

                # Update pixmap and display
                self.pixmap = QPixmap.fromImage(self.image)
                self.update_display()

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

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if not self.drawing or self.image is None or event.button() != Qt.MouseButton.LeftButton:
            return

        # Convert mouse position to image coordinates
        pos = self._map_to_image(event.pos())

        # Handle different tools
        if self.active_tool == ToolType.LINE:
            self._draw_line(self.start_point, pos)
        elif self.active_tool == ToolType.RECTANGLE:
            self._draw_rectangle(self.start_point, pos)
        elif self.active_tool == ToolType.ELLIPSE:
            self._draw_ellipse(self.start_point, pos)

        # Stop drawing
        self.drawing = False
        self.temp_pixmap = None

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

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

        painter = QPainter(self.image)
        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawPoint(pos)
        painter.end()

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

    def _draw_line(self, start, end):
        """Draw a line from start to end"""
        if self.image is None:
            return

        painter = QPainter(self.image)
        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(start, end)
        painter.end()

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

    def _draw_rectangle(self, start, end):
        """Draw a rectangle from start to end"""
        if self.image is None:
            return

        painter = QPainter(self.image)
        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawRect(QRect(start, end))
        painter.end()

        # Update pixmap and display
        self.pixmap = QPixmap.fromImage(self.image)
        self.update_display()

    def _draw_ellipse(self, start, end):
        """Draw an ellipse from start to end"""
        if self.image is None:
            return

        painter = QPainter(self.image)
        painter.setPen(QPen(self.brush_color, self.brush_size,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                          Qt.PenJoinStyle.RoundJoin))
        painter.drawEllipse(QRect(start, end))
        painter.end()

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

        # Create tool panel (left side)
        tool_panel = QWidget()
        tool_panel.setMaximumWidth(200)
        tool_panel.setStyleSheet(f"background-color: #333333; color: white; padding: 10px;")
        tool_layout = QVBoxLayout(tool_panel)

        # Tool selection header
        tools_header = QLabel("Tools:")
        tools_header.setStyleSheet("font-weight: bold; font-size: 14px; color: white;")
        tool_layout.addWidget(tools_header)

        # Tool buttons in a grid
        tools_layout = QHBoxLayout()

        # Pen tool button
        self.pen_button = QPushButton("Pen")
        self.pen_button.setCheckable(True)
        self.pen_button.setChecked(True)  # Default tool
        self.pen_button.clicked.connect(lambda: self._on_tool_selected(ToolType.PEN))
        tools_layout.addWidget(self.pen_button)

        # Line tool button
        self.line_button = QPushButton("Line")
        self.line_button.setCheckable(True)
        self.line_button.clicked.connect(lambda: self._on_tool_selected(ToolType.LINE))
        tools_layout.addWidget(self.line_button)

        tool_layout.addLayout(tools_layout)

        tools_layout2 = QHBoxLayout()

        # Rectangle tool button
        self.rect_button = QPushButton("Rectangle")
        self.rect_button.setCheckable(True)
        self.rect_button.clicked.connect(lambda: self._on_tool_selected(ToolType.RECTANGLE))
        tools_layout2.addWidget(self.rect_button)

        # Ellipse tool button
        self.ellipse_button = QPushButton("Ellipse")
        self.ellipse_button.setCheckable(True)
        self.ellipse_button.clicked.connect(lambda: self._on_tool_selected(ToolType.ELLIPSE))
        tools_layout2.addWidget(self.ellipse_button)

        tool_layout.addLayout(tools_layout2)

        # Text tool button
        self.text_button = QPushButton("Text")
        self.text_button.setCheckable(True)
        self.text_button.clicked.connect(lambda: self._on_tool_selected(ToolType.TEXT))
        tool_layout.addWidget(self.text_button)

        # Brush size
        tool_layout.addWidget(QLabel("Brush Size:"))
        brush_size_layout = QHBoxLayout()
        self.brush_size_spin = QSpinBox()
        self.brush_size_spin.setRange(BRUSH_SIZE_MIN, BRUSH_SIZE_MAX)
        self.brush_size_spin.setValue(self.brush_size)
        self.brush_size_spin.setStyleSheet("""
            background-color: #444444;
            color: white;
            border: 1px solid #555555;
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
        tool_layout.addWidget(QLabel("Brush Color:"))
        self.color_button = QPushButton()
        self.color_button.setStyleSheet(f"background-color: {self.brush_color}; min-height: 30px;")
        self.color_button.setMaximumWidth(100)
        self.color_button.clicked.connect(self._on_color_button_clicked)
        tool_layout.addWidget(self.color_button)

        # Background color
        tool_layout.addWidget(QLabel("Background Color:"))
        self.bg_color_button = QPushButton()
        self.bg_color_button.setStyleSheet(f"background-color: {self.background_color}; min-height: 30px;")
        self.bg_color_button.setMaximumWidth(100)
        self.bg_color_button.clicked.connect(self._on_bg_color_button_clicked)
        tool_layout.addWidget(self.bg_color_button)

        # Font selection for text tool
        tool_layout.addWidget(QLabel("Text Font:"))
        self.font_button = QPushButton("Choose Font")
        self.font_button.clicked.connect(self._on_font_button_clicked)
        tool_layout.addWidget(self.font_button)

        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_label = QLabel("Zoom:")
        zoom_layout.addWidget(zoom_label)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.clicked.connect(self._on_zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.clicked.connect(self._on_zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        zoom_reset_btn = QPushButton("100%")
        zoom_reset_btn.clicked.connect(self._on_zoom_reset)
        zoom_layout.addWidget(zoom_reset_btn)

        tool_layout.addLayout(zoom_layout)

        # Add spacer at the bottom
        tool_layout.addStretch()

        # Add tool panel to content layout
        content_layout.addWidget(tool_panel)

        # Create canvas area (right side)
        canvas_container = QScrollArea()
        canvas_container.setWidgetResizable(True)
        canvas_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        canvas_container.setStyleSheet("background-color: #222222;")

        # Create canvas widget
        self.canvas = CanvasWidget()

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

        # Update canvas tool
        self.canvas.set_tool(self.active_tool)

    def _on_tool_selected(self, tool):
        """Handle tool selection"""
        self.active_tool = tool
        self._update_tool_buttons()

        tool_names = {
            ToolType.PEN: "Pen",
            ToolType.LINE: "Line",
            ToolType.RECTANGLE: "Rectangle",
            ToolType.ELLIPSE: "Ellipse",
            ToolType.TEXT: "Text"
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
            self.color_button.setStyleSheet(f"background-color: {self.brush_color}; min-height: 30px;")
            self.config.set("editor.brush_color", self.brush_color)

            # Update canvas
            self.canvas.set_brush_color(color)

            self.status_message.emit(f"Brush color: {self.brush_color}")

    def _on_bg_color_button_clicked(self):
        """Handle background color button click"""
        color = QColorDialog.getColor(hex_to_qcolor(self.background_color), self, "Select Background Color")
        if color.isValid():
            self.background_color = qcolor_to_hex(color)
            self.bg_color_button.setStyleSheet(f"background-color: {self.background_color}; min-height: 30px;")
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
