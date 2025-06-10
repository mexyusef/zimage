"""
Editor tab component for ZImage Enterprise
"""
import os
import logging
import traceback
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QScrollArea, QToolBar, QColorDialog, QComboBox,
    QPushButton, QSpinBox, QFileDialog, QMessageBox, QInputDialog, QFontDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QColor, QImage, QAction, QFont

from zimage.core.constants import (
    ICONS_DIR, BRUSH_SIZE_MIN, BRUSH_SIZE_MAX, ToolType,
    PRIMARY_COLOR, PRIMARY_LIGHT_COLOR, TEXT_COLOR
)
from zimage.core.utils import hex_to_qcolor, qcolor_to_hex, qimage_to_pixmap, get_icon
from zimage.models.image import ImageModel
from .canvas import CanvasWidget

# Set up verbose debugging for this module
logger = logging.getLogger('zimage.editor_tab.main')
logger.setLevel(logging.DEBUG)

class EditorTab(QWidget):
    """
    Editor tab for image editing
    """
    # Define signals
    status_message = pyqtSignal(str)

    def __init__(self, config):
        logger.debug("Initializing EditorTab")
        super().__init__()
        self.config = config
        self.canvas = None
        self.image_model = None
        self.file_path = None
        self.is_modified = False
        self.tool_buttons = {}
        self.color_button = None
        self.bg_color_button = None
        self.brush_size_slider = None
        self.brush_size_label = None
        self.blur_radius_slider = None
        self.blur_radius_label = None
        self.blur_type_combo = None

        # Initialize UI
        self._init_ui()
        logger.debug("EditorTab initialized")

    def _init_ui(self):
        """Initialize the user interface"""
        logger.debug("Initializing UI")

        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create toolbar
        self._create_toolbar(main_layout)

        # Create canvas scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_area.setStyleSheet("background-color: #333333;")

        # Create canvas widget
        self.canvas = CanvasWidget()
        self.canvas.status_message.connect(self._on_canvas_status_message)
        scroll_area.setWidget(self.canvas)

        # Add canvas to layout
        main_layout.addWidget(scroll_area, 1)

        # Set the layout
        self.setLayout(main_layout)

        # Update UI state
        self._update_actions()
        logger.debug("UI initialized")

    def _create_toolbar(self, layout):
        """Create the toolbar with all editor tools"""
        logger.debug("Creating toolbar")

        # Create toolbar container
        toolbar_container = QWidget()
        toolbar_container.setStyleSheet(f"background-color: {PRIMARY_COLOR}; color: {TEXT_COLOR};")
        toolbar_layout = QVBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(0)

        # Create main toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {PRIMARY_COLOR};
                border: none;
                spacing: 5px;
                padding: 5px;
            }}
            QToolButton {{
                background-color: {PRIMARY_COLOR};
                color: {TEXT_COLOR};
                border: none;
                border-radius: 3px;
                padding: 5px;
            }}
            QToolButton:hover {{
                background-color: {PRIMARY_LIGHT_COLOR};
            }}
            QToolButton:checked {{
                background-color: {PRIMARY_LIGHT_COLOR};
                border: 1px solid #cccccc;
            }}
        """)

        # File actions
        new_action = QAction(get_icon("new.png"), "New Image", self)
        new_action.triggered.connect(self._on_new_clicked)
        toolbar.addAction(new_action)

        open_action = QAction(get_icon("open.png"), "Open Image", self)
        open_action.triggered.connect(self._on_open_clicked)
        toolbar.addAction(open_action)

        save_action = QAction(get_icon("save.png"), "Save Image", self)
        save_action.triggered.connect(self._on_save_clicked)
        toolbar.addAction(save_action)

        save_as_action = QAction(get_icon("save_as.png"), "Save Image As", self)
        save_as_action.triggered.connect(self._on_save_as_clicked)
        toolbar.addAction(save_as_action)

        reset_action = QAction(get_icon("reset.png"), "Reset Image", self)
        reset_action.triggered.connect(self._on_reset_clicked)
        toolbar.addAction(reset_action)

        toolbar.addSeparator()

        # Drawing tools
        # Pen tool
        pen_action = QAction(get_icon("pen.png"), "Pen Tool", self)
        pen_action.setCheckable(True)
        pen_action.setChecked(True)
        pen_action.triggered.connect(lambda: self._on_tool_selected(ToolType.PEN))
        toolbar.addAction(pen_action)
        self.tool_buttons[ToolType.PEN] = pen_action

        # Line tool
        line_action = QAction(get_icon("line.png"), "Line Tool", self)
        line_action.setCheckable(True)
        line_action.triggered.connect(lambda: self._on_tool_selected(ToolType.LINE))
        toolbar.addAction(line_action)
        self.tool_buttons[ToolType.LINE] = line_action

        # Rectangle tool
        rect_action = QAction(get_icon("rectangle.png"), "Rectangle Tool", self)
        rect_action.setCheckable(True)
        rect_action.triggered.connect(lambda: self._on_tool_selected(ToolType.RECTANGLE))
        toolbar.addAction(rect_action)
        self.tool_buttons[ToolType.RECTANGLE] = rect_action

        # Ellipse tool
        ellipse_action = QAction(get_icon("ellipse.png"), "Ellipse Tool", self)
        ellipse_action.setCheckable(True)
        ellipse_action.triggered.connect(lambda: self._on_tool_selected(ToolType.ELLIPSE))
        toolbar.addAction(ellipse_action)
        self.tool_buttons[ToolType.ELLIPSE] = ellipse_action

        # Text tool
        text_action = QAction(get_icon("text.png"), "Text Tool", self)
        text_action.setCheckable(True)
        text_action.triggered.connect(lambda: self._on_tool_selected(ToolType.TEXT))
        toolbar.addAction(text_action)
        self.tool_buttons[ToolType.TEXT] = text_action

        # Blur tool
        blur_action = QAction(get_icon("blur.png"), "Blur Tool", self)
        blur_action.setCheckable(True)
        blur_action.triggered.connect(lambda: self._on_tool_selected(ToolType.BLUR))
        toolbar.addAction(blur_action)
        self.tool_buttons[ToolType.BLUR] = blur_action

        toolbar.addSeparator()

        # Zoom tools
        zoom_in_action = QAction(get_icon("zoom_in.png"), "Zoom In", self)
        zoom_in_action.triggered.connect(self._on_zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction(get_icon("zoom_out.png"), "Zoom Out", self)
        zoom_out_action.triggered.connect(self._on_zoom_out)
        toolbar.addAction(zoom_out_action)

        zoom_reset_action = QAction(get_icon("zoom_reset.png"), "Reset Zoom", self)
        zoom_reset_action.triggered.connect(self._on_zoom_reset)
        toolbar.addAction(zoom_reset_action)

        toolbar_layout.addWidget(toolbar)

        # Create tool options bar
        options_bar = QWidget()
        options_bar.setStyleSheet(f"background-color: {PRIMARY_LIGHT_COLOR}; color: {TEXT_COLOR};")
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(10, 5, 10, 5)

        # Color button
        color_label = QLabel("Color:")
        options_layout.addWidget(color_label)

        self.color_button = QPushButton()
        self.color_button.setFixedSize(24, 24)
        self.color_button.setStyleSheet("background-color: #000000; border: 1px solid #cccccc;")
        self.color_button.clicked.connect(self._on_color_button_clicked)
        options_layout.addWidget(self.color_button)

        # Background color button
        bg_color_label = QLabel("Bg Color:")
        options_layout.addWidget(bg_color_label)

        self.bg_color_button = QPushButton()
        self.bg_color_button.setFixedSize(24, 24)
        self.bg_color_button.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc;")
        self.bg_color_button.clicked.connect(self._on_bg_color_button_clicked)
        options_layout.addWidget(self.bg_color_button)

        options_layout.addSpacing(10)

        # Brush size slider
        size_label = QLabel("Size:")
        options_layout.addWidget(size_label)

        self.brush_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.brush_size_slider.setMinimum(BRUSH_SIZE_MIN)
        self.brush_size_slider.setMaximum(BRUSH_SIZE_MAX)
        self.brush_size_slider.setValue(3)
        self.brush_size_slider.setFixedWidth(100)
        self.brush_size_slider.valueChanged.connect(self._on_brush_size_changed)
        options_layout.addWidget(self.brush_size_slider)

        self.brush_size_label = QLabel("3")
        self.brush_size_label.setFixedWidth(30)
        options_layout.addWidget(self.brush_size_label)

        options_layout.addSpacing(10)

        # Font button
        font_button = QPushButton("Font")
        font_button.clicked.connect(self._on_font_button_clicked)
        options_layout.addWidget(font_button)

        options_layout.addSpacing(10)

        # Blur radius slider
        blur_radius_label = QLabel("Blur Radius:")
        options_layout.addWidget(blur_radius_label)

        self.blur_radius_slider = QSlider(Qt.Orientation.Horizontal)
        self.blur_radius_slider.setMinimum(1)
        self.blur_radius_slider.setMaximum(20)
        self.blur_radius_slider.setValue(10)
        self.blur_radius_slider.setFixedWidth(100)
        self.blur_radius_slider.valueChanged.connect(self._on_blur_radius_changed)
        options_layout.addWidget(self.blur_radius_slider)

        self.blur_radius_label = QLabel("10")
        self.blur_radius_label.setFixedWidth(30)
        options_layout.addWidget(self.blur_radius_label)

        # Blur type combo
        blur_type_label = QLabel("Blur Type:")
        options_layout.addWidget(blur_type_label)

        self.blur_type_combo = QComboBox()
        self.blur_type_combo.addItems(["gaussian", "box", "motion"])
        self.blur_type_combo.setCurrentText("gaussian")
        self.blur_type_combo.currentTextChanged.connect(self._on_blur_type_changed)
        options_layout.addWidget(self.blur_type_combo)

        options_layout.addStretch()

        options_bar.setLayout(options_layout)
        toolbar_layout.addWidget(options_bar)

        toolbar_container.setLayout(toolbar_layout)
        layout.addWidget(toolbar_container)
        logger.debug("Toolbar created")

    def _update_actions(self):
        """Update the enabled state of actions"""
        logger.debug("Updating actions")
        has_image = self.canvas and self.canvas.image is not None
        # Update actions here if needed

    def _update_tool_buttons(self):
        """Update the checked state of tool buttons"""
        logger.debug(f"Updating tool buttons, active tool: {self.canvas.active_tool}")
        for tool_type, button in self.tool_buttons.items():
            button.setChecked(tool_type == self.canvas.active_tool)

    def _on_canvas_status_message(self, message):
        """Handle status messages from the canvas"""
        logger.debug(f"Canvas status message: {message}")
        self.status_message.emit(message)

    def _on_tool_selected(self, tool):
        """Handle tool selection"""
        logger.debug(f"Tool selected: {tool}")
        self.canvas.set_tool(tool)
        self._update_tool_buttons()

        # Update status message
        tool_name = tool.name.capitalize()
        if tool == ToolType.BLUR:
            self.status_message.emit(f"{tool_name} Tool: Drag to blur a region. Ctrl+Click to blur entire image.")
        else:
            self.status_message.emit(f"{tool_name} Tool selected")

    def _on_brush_size_changed(self, size):
        """Handle brush size change"""
        logger.debug(f"Brush size changed: {size}")
        self.brush_size_label.setText(str(size))
        self.canvas.set_brush_size(size)

        # Update status message
        self.status_message.emit(f"Brush size: {size}")

    def _on_color_button_clicked(self):
        """Handle color button click"""
        logger.debug("Color button clicked")
        current_color = self.color_button.palette().button().color()
        color = QColorDialog.getColor(current_color, self, "Select Color")

        if color.isValid():
            logger.debug(f"New color selected: {color.name()}")
            self.color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #cccccc;")
            self.canvas.set_brush_color(color)

            # Update status message
            self.status_message.emit(f"Color: {color.name()}")

    def _on_bg_color_button_clicked(self):
        """Handle background color button click"""
        logger.debug("Background color button clicked")
        current_color = self.bg_color_button.palette().button().color()
        color = QColorDialog.getColor(current_color, self, "Select Background Color")

        if color.isValid():
            logger.debug(f"New background color selected: {color.name()}")
            self.bg_color_button.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #cccccc;")

            # Apply background color change if needed
            # Note: This would typically create a new image with the selected background color

    def _on_zoom_in(self):
        """Handle zoom in action"""
        logger.debug("Zoom in")
        self.canvas.zoom_in()

    def _on_zoom_out(self):
        """Handle zoom out action"""
        logger.debug("Zoom out")
        self.canvas.zoom_out()

    def _on_zoom_reset(self):
        """Handle zoom reset action"""
        logger.debug("Zoom reset")
        self.canvas.reset_zoom()

    def _on_new_clicked(self):
        """Handle new image action"""
        logger.debug("New image clicked")
        try:
            # Show dialog to get image size
            width, ok1 = QInputDialog.getInt(self, "Image Width", "Enter width:", 800, 1, 4000)
            if not ok1:
                return

            height, ok2 = QInputDialog.getInt(self, "Image Height", "Enter height:", 600, 1, 4000)
            if not ok2:
                return

            # Create new image
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.white)

            # Set the image
            self.canvas.set_image(image)
            self.image_model = ImageModel(image=image)
            self.file_path = None
            self.is_modified = False

            # Update UI
            self._update_actions()

            # Update status message
            self.status_message.emit(f"Created new image: {width}x{height}")
            logger.debug(f"Created new image: {width}x{height}")
        except Exception as e:
            logger.error(f"Error creating new image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error creating new image: {str(e)}")

    def _on_open_clicked(self):
        """Handle open image action"""
        logger.debug("Open image clicked")
        try:
            file_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif)")
            if file_path:
                self.load_file(file_path)
        except Exception as e:
            logger.error(f"Error opening image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error opening image: {str(e)}")

    def _on_save_clicked(self):
        """Handle save image action"""
        logger.debug("Save image clicked")
        try:
            if self.file_path:
                self.save_image(self.file_path)
            else:
                self._on_save_as_clicked()
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error saving image: {str(e)}")

    def _on_save_as_clicked(self):
        """Handle save image as action"""
        logger.debug("Save image as clicked")
        try:
            file_path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp)")
            if file_path:
                self.save_image(file_path)
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error saving image: {str(e)}")

    def _on_reset_clicked(self):
        """Handle reset image action"""
        logger.debug("Reset image clicked")
        if self.canvas and self.canvas.original_pixmap:
            self.canvas.set_image(self.canvas.original_pixmap)
            self.status_message.emit("Image reset to original")

    def _on_font_button_clicked(self):
        """Handle font button click"""
        logger.debug("Font button clicked")
        current_font = self.canvas.text_font
        font, ok = QFontDialog.getFont(current_font, self, "Select Font")
        if ok:
            logger.debug(f"New font selected: {font.family()}, {font.pointSize()}")
            self.canvas.set_font(font)
            self.status_message.emit(f"Font: {font.family()}, {font.pointSize()}")

    def _on_blur_radius_changed(self, radius):
        """Handle blur radius change"""
        logger.debug(f"Blur radius changed: {radius}")
        self.blur_radius_label.setText(str(radius))
        self.canvas.set_blur_radius(radius)

        # Update status message
        blur_type = self.blur_type_combo.currentText()
        self.status_message.emit(f"{blur_type.capitalize()} blur, radius: {radius}")

    def _on_blur_type_changed(self, blur_type):
        """Handle blur type change"""
        logger.debug(f"Blur type changed: {blur_type}")
        self.canvas.set_blur_type(blur_type)

        # Update status message
        radius = self.blur_radius_slider.value()
        self.status_message.emit(f"{blur_type.capitalize()} blur, radius: {radius}")

    def load_image(self, image_model):
        """Load an image from an image model"""
        logger.debug(f"Loading image from model: {image_model}")
        try:
            self.image_model = image_model

            # Get the image from the model
            if image_model.pixmap:
                logger.debug("Using pixmap from model")
                self.canvas.set_image(image_model.pixmap)
            elif image_model.image:
                logger.debug("Using image from model")
                self.canvas.set_image(image_model.image)
            elif image_model.file_path:
                logger.debug(f"Loading image from file: {image_model.file_path}")
                self.file_path = image_model.file_path
                pixmap = QPixmap(image_model.file_path)
                if pixmap.isNull():
                    logger.error(f"Failed to load image from file: {image_model.file_path}")
                    QMessageBox.critical(self, "Error", f"Failed to load image: {image_model.file_path}")
                    return False

                self.canvas.set_image(pixmap)
            else:
                logger.error("Image model does not contain valid image data")
                QMessageBox.critical(self, "Error", "Invalid image data")
                return False

            # Update UI
            self._update_actions()

            # Update status message
            w = self.canvas.image.width()
            h = self.canvas.image.height()
            file_info = f" from {os.path.basename(self.file_path)}" if self.file_path else ""
            self.status_message.emit(f"Loaded image{file_info}: {w}x{h}")
            logger.debug(f"Loaded image{file_info}: {w}x{h}")

            return True
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error loading image: {str(e)}")
            return False

    def load_file(self, file_path):
        """Load an image from a file"""
        logger.debug(f"Loading file: {file_path}")
        try:
            # Create image model
            image_model = ImageModel(file_path=file_path)

            # Load the image
            if self.load_image(image_model):
                self.file_path = file_path
                self.is_modified = False
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading file: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error loading file: {str(e)}")
            return False

    def save_image(self, file_path):
        """Save the current image to a file"""
        logger.debug(f"Saving image to: {file_path}")
        try:
            if not self.canvas or not self.canvas.image:
                logger.error("No image to save")
                QMessageBox.warning(self, "Warning", "No image to save")
                return False

            # Save the image
            success = self.canvas.image.save(file_path)

            if success:
                self.file_path = file_path
                self.is_modified = False
                self.status_message.emit(f"Image saved to: {file_path}")
                logger.debug(f"Image saved successfully to: {file_path}")
                return True
            else:
                logger.error(f"Failed to save image to: {file_path}")
                QMessageBox.critical(self, "Error", f"Failed to save image to: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}\n{traceback.format_exc()}")
            self.status_message.emit(f"Error saving image: {str(e)}")
            return False
