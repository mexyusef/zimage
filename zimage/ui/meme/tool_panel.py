"""
Tool panel for meme creator
"""
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QSpinBox, QColorDialog, QFontDialog,
    QGroupBox, QRadioButton, QScrollArea, QSizePolicy, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QFontDatabase, QFontInfo

from zimage.core.constants import PRIMARY_COLOR, PRIMARY_LIGHT_COLOR

logger = logging.getLogger('zimage')

class ColorButton(QPushButton):
    """Custom button for color selection"""

    def __init__(self, color=Qt.GlobalColor.white, parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedSize(30, 30)
        self.update_style()

    def update_style(self):
        """Update button style to reflect the current color"""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.name()};
                border: 1px solid #555555;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid white;
            }}
        """)

    def set_color(self, color):
        """Set the button color"""
        self.color = QColor(color)
        self.update_style()

    def get_color(self):
        """Get the button color"""
        return self.color

class ToolPanel(QWidget):
    """
    Side panel with meme editing tools
    """
    # Define signals
    text_changed = pyqtSignal(object, str)  # (text_box_model, text)
    font_changed = pyqtSignal(object, object)  # (text_box_model, font)
    color_changed = pyqtSignal(object, object)  # (text_box_model, color)
    outline_color_changed = pyqtSignal(object, object)  # (text_box_model, color)
    outline_size_changed = pyqtSignal(object, int)  # (text_box_model, size)
    alignment_changed = pyqtSignal(object, object)  # (text_box_model, alignment)
    add_text_box = pyqtSignal(str, str)  # (text, position)
    clear_text_boxes = pyqtSignal()
    add_classic_format = pyqtSignal()
    export_meme = pyqtSignal(str, str)  # (path, format)
    load_image = pyqtSignal()  # Signal to request loading an image

    def __init__(self, parent=None):
        """
        Initialize the tool panel

        Args:
            parent (QWidget, optional): Parent widget
        """
        super().__init__(parent)

        # Current text box model being edited
        self.current_text_box = None

        # Initialize UI
        self._init_ui()

        logger.debug("Initialized meme tool panel")

    def _init_ui(self):
        """Initialize UI components"""
        # Set up main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Set fixed width
        self.setMinimumWidth(250)
        self.setMaximumWidth(300)

        # Apply some styling
        self.setStyleSheet(f"""
            QGroupBox {{
                border: 1px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {PRIMARY_COLOR};
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_LIGHT_COLOR};
            }}
            QLabel {{
                font-weight: bold;
            }}
        """)

        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Create content widget
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(5, 5, 5, 5)
        content_layout.setSpacing(10)

        # Create image load section first
        self._create_image_section(content_layout)

        # Create sections
        self._create_text_section(content_layout)
        self._create_font_section(content_layout)
        self._create_color_section(content_layout)
        self._create_alignment_section(content_layout)
        self._create_template_section(content_layout)
        self._create_export_section(content_layout)

        # Add spacer to push everything to the top
        content_layout.addStretch()

        # Set the content widget to the scroll area
        scroll_area.setWidget(content)

        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)

    def _create_image_section(self, layout):
        """Create image section"""
        group = QGroupBox("Image")
        group_layout = QVBoxLayout(group)

        # Load image button
        load_image_btn = QPushButton("Load Image")
        load_image_btn.clicked.connect(self.load_image.emit)
        group_layout.addWidget(load_image_btn)

        # Add section to layout
        layout.addWidget(group)

    def _create_text_section(self, layout):
        """Create text content section"""
        group = QGroupBox("Text")
        group_layout = QVBoxLayout(group)

        # Text edit
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Enter text...")
        self.text_edit.textChanged.connect(self._on_text_changed)
        group_layout.addWidget(self.text_edit)

        # Add text box buttons
        button_layout = QHBoxLayout()

        add_top_btn = QPushButton("Add Top")
        add_top_btn.clicked.connect(lambda: self.add_text_box.emit(self.text_edit.text(), "top"))
        button_layout.addWidget(add_top_btn)

        add_bottom_btn = QPushButton("Add Bottom")
        add_bottom_btn.clicked.connect(lambda: self.add_text_box.emit(self.text_edit.text(), "bottom"))
        button_layout.addWidget(add_bottom_btn)

        add_custom_btn = QPushButton("Add Custom")
        add_custom_btn.clicked.connect(lambda: self.add_text_box.emit(self.text_edit.text(), "custom"))
        group_layout.addLayout(button_layout)
        group_layout.addWidget(add_custom_btn)

        # Clear text boxes button
        clear_btn = QPushButton("Clear All Text")
        clear_btn.clicked.connect(self.clear_text_boxes.emit)
        group_layout.addWidget(clear_btn)

        layout.addWidget(group)

    def _create_font_section(self, layout):
        """Create font section"""
        group = QGroupBox("Font")
        group_layout = QVBoxLayout(group)

        # Font family
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font:"))

        self.font_combo = QComboBox()
        # Add some common meme fonts first
        meme_fonts = ["Impact", "Arial Black", "Comic Sans MS"]

        # Get all fonts using QFontDatabase static method
        all_fonts = QFontDatabase.families()

        # Add meme fonts first if available
        for font in meme_fonts:
            if font in all_fonts:
                self.font_combo.addItem(font)
                all_fonts.remove(font)

        # Add remaining fonts
        for font in all_fonts:
            self.font_combo.addItem(font)

        self.font_combo.currentTextChanged.connect(self._on_font_family_changed)
        font_layout.addWidget(self.font_combo)
        group_layout.addLayout(font_layout)

        # Font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Size:"))

        self.size_spin = QSpinBox()
        self.size_spin.setRange(8, 100)
        self.size_spin.setValue(36)
        self.size_spin.valueChanged.connect(self._on_font_size_changed)
        size_layout.addWidget(self.size_spin)
        group_layout.addLayout(size_layout)

        # Font styles
        style_layout = QHBoxLayout()

        self.bold_btn = QPushButton("B")
        self.bold_btn.setCheckable(True)
        self.bold_btn.setFixedWidth(30)
        self.bold_btn.toggled.connect(self._on_font_style_changed)
        self.bold_btn.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        style_layout.addWidget(self.bold_btn)

        self.italic_btn = QPushButton("I")
        self.italic_btn.setCheckable(True)
        self.italic_btn.setFixedWidth(30)
        self.italic_btn.toggled.connect(self._on_font_style_changed)
        italic_font = QFont("Arial", 10)
        italic_font.setItalic(True)
        self.italic_btn.setFont(italic_font)
        style_layout.addWidget(self.italic_btn)

        # Advanced font button
        self.font_btn = QPushButton("Choose Font...")
        self.font_btn.clicked.connect(self._on_choose_font)
        style_layout.addWidget(self.font_btn)

        group_layout.addLayout(style_layout)

        # Outline size
        outline_layout = QHBoxLayout()
        outline_layout.addWidget(QLabel("Outline:"))

        self.outline_spin = QSpinBox()
        self.outline_spin.setRange(0, 10)
        self.outline_spin.setValue(2)
        self.outline_spin.valueChanged.connect(self._on_outline_size_changed)
        outline_layout.addWidget(self.outline_spin)
        group_layout.addLayout(outline_layout)

        layout.addWidget(group)

    def _create_color_section(self, layout):
        """Create color section"""
        group = QGroupBox("Colors")
        group_layout = QVBoxLayout(group)

        # Text color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Text:"))

        self.text_color_btn = ColorButton(Qt.GlobalColor.white)
        self.text_color_btn.clicked.connect(lambda: self._on_choose_color(self.text_color_btn, "text"))
        color_layout.addWidget(self.text_color_btn)

        # Outline color
        color_layout.addWidget(QLabel("Outline:"))

        self.outline_color_btn = ColorButton(Qt.GlobalColor.black)
        self.outline_color_btn.clicked.connect(lambda: self._on_choose_color(self.outline_color_btn, "outline"))
        color_layout.addWidget(self.outline_color_btn)

        group_layout.addLayout(color_layout)

        layout.addWidget(group)

    def _create_alignment_section(self, layout):
        """Create alignment section"""
        group = QGroupBox("Alignment")
        group_layout = QHBoxLayout(group)

        # Left align
        self.align_left = QPushButton("Left")
        self.align_left.setCheckable(True)
        self.align_left.clicked.connect(lambda: self._on_alignment_changed(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter))
        group_layout.addWidget(self.align_left)

        # Center align
        self.align_center = QPushButton("Center")
        self.align_center.setCheckable(True)
        self.align_center.setChecked(True)
        self.align_center.clicked.connect(lambda: self._on_alignment_changed(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter))
        group_layout.addWidget(self.align_center)

        # Right align
        self.align_right = QPushButton("Right")
        self.align_right.setCheckable(True)
        self.align_right.clicked.connect(lambda: self._on_alignment_changed(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter))
        group_layout.addWidget(self.align_right)

        layout.addWidget(group)

    def _create_template_section(self, layout):
        """Create template section"""
        group = QGroupBox("Templates")
        group_layout = QVBoxLayout(group)

        # Classic meme format button
        classic_btn = QPushButton("Classic Meme Format")
        classic_btn.clicked.connect(self.add_classic_format.emit)
        group_layout.addWidget(classic_btn)

        layout.addWidget(group)

    def _create_export_section(self, layout):
        """Create export section"""
        group = QGroupBox("Export")
        group_layout = QVBoxLayout(group)

        # Format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))

        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPG"])
        format_layout.addWidget(self.format_combo)

        group_layout.addLayout(format_layout)

        # Export button
        export_btn = QPushButton("Export Meme...")
        export_btn.clicked.connect(self._on_export_clicked)
        group_layout.addWidget(export_btn)

        layout.addWidget(group)

    def update_text_properties(self, text_box_model):
        """
        Update UI to reflect selected text box

        Args:
            text_box_model (TextBoxModel): Text box model or None
        """
        # Store current text box
        self.current_text_box = text_box_model

        # Disable controls if no text box selected
        enabled = text_box_model is not None
        self.text_edit.setEnabled(enabled)
        self.font_combo.setEnabled(enabled)
        self.size_spin.setEnabled(enabled)
        self.bold_btn.setEnabled(enabled)
        self.italic_btn.setEnabled(enabled)
        self.font_btn.setEnabled(enabled)
        self.outline_spin.setEnabled(enabled)
        self.text_color_btn.setEnabled(enabled)
        self.outline_color_btn.setEnabled(enabled)
        self.align_left.setEnabled(enabled)
        self.align_center.setEnabled(enabled)
        self.align_right.setEnabled(enabled)

        if not enabled:
            return

        # Update text edit
        self.text_edit.blockSignals(True)
        self.text_edit.setText(text_box_model.text)
        self.text_edit.blockSignals(False)

        # Update font family
        self.font_combo.blockSignals(True)
        index = self.font_combo.findText(text_box_model.font_family)
        if index >= 0:
            self.font_combo.setCurrentIndex(index)
        self.font_combo.blockSignals(False)

        # Update font size
        self.size_spin.blockSignals(True)
        self.size_spin.setValue(text_box_model.font_size)
        self.size_spin.blockSignals(False)

        # Update font style
        self.bold_btn.blockSignals(True)
        self.bold_btn.setChecked(text_box_model.bold)
        self.bold_btn.blockSignals(False)

        self.italic_btn.blockSignals(True)
        self.italic_btn.setChecked(text_box_model.italic)
        self.italic_btn.blockSignals(False)

        # Update outline size
        self.outline_spin.blockSignals(True)
        self.outline_spin.setValue(text_box_model.outline_size)
        self.outline_spin.blockSignals(False)

        # Update colors
        self.text_color_btn.set_color(text_box_model.text_color)
        self.outline_color_btn.set_color(text_box_model.outline_color)

        # Update alignment
        align = text_box_model.alignment
        self.align_left.blockSignals(True)
        self.align_center.blockSignals(True)
        self.align_right.blockSignals(True)

        self.align_left.setChecked(align & Qt.AlignmentFlag.AlignLeft)
        self.align_center.setChecked(align & Qt.AlignmentFlag.AlignHCenter)
        self.align_right.setChecked(align & Qt.AlignmentFlag.AlignRight)

        self.align_left.blockSignals(False)
        self.align_center.blockSignals(False)
        self.align_right.blockSignals(False)

    def _on_text_changed(self, text):
        """Handle text changes"""
        if self.current_text_box:
            self.text_changed.emit(self.current_text_box, text)

    def _on_font_family_changed(self, family):
        """Handle font family changes"""
        if self.current_text_box:
            font = self.current_text_box.get_font()
            font.setFamily(family)
            self.font_changed.emit(self.current_text_box, font)

    def _on_font_size_changed(self, size):
        """Handle font size changes"""
        if self.current_text_box:
            font = self.current_text_box.get_font()
            font.setPointSize(size)
            self.font_changed.emit(self.current_text_box, font)

    def _on_font_style_changed(self):
        """Handle font style changes"""
        if self.current_text_box:
            font = self.current_text_box.get_font()
            font.setBold(self.bold_btn.isChecked())
            font.setItalic(self.italic_btn.isChecked())
            self.font_changed.emit(self.current_text_box, font)

    def _on_choose_font(self):
        """Open font dialog"""
        if self.current_text_box:
            current_font = self.current_text_box.get_font()
            font, ok = QFontDialog.getFont(current_font, self, "Choose Font")
            if ok:
                self.font_changed.emit(self.current_text_box, font)

                # Update UI to match selected font
                self.font_combo.blockSignals(True)
                index = self.font_combo.findText(font.family())
                if index >= 0:
                    self.font_combo.setCurrentIndex(index)
                self.font_combo.blockSignals(False)

                self.size_spin.blockSignals(True)
                self.size_spin.setValue(font.pointSize())
                self.size_spin.blockSignals(False)

                self.bold_btn.blockSignals(True)
                self.bold_btn.setChecked(font.bold())
                self.bold_btn.blockSignals(False)

                self.italic_btn.blockSignals(True)
                self.italic_btn.setChecked(font.italic())
                self.italic_btn.blockSignals(False)

    def _on_outline_size_changed(self, size):
        """Handle outline size changes"""
        if self.current_text_box:
            self.outline_size_changed.emit(self.current_text_box, size)

    def _on_choose_color(self, button, color_type):
        """Open color dialog"""
        if not self.current_text_box:
            return

        current_color = button.get_color()
        color = QColorDialog.getColor(current_color, self, f"Choose {color_type.title()} Color")

        if color.isValid():
            button.set_color(color)

            if color_type == "text":
                self.color_changed.emit(self.current_text_box, color)
            elif color_type == "outline":
                self.outline_color_changed.emit(self.current_text_box, color)

    def _on_alignment_changed(self, alignment):
        """Handle alignment changes"""
        if self.current_text_box:
            # Update button states
            self.align_left.setChecked(alignment & Qt.AlignmentFlag.AlignLeft)
            self.align_center.setChecked(alignment & Qt.AlignmentFlag.AlignHCenter)
            self.align_right.setChecked(alignment & Qt.AlignmentFlag.AlignRight)

            # Emit signal
            self.alignment_changed.emit(self.current_text_box, alignment)

    def _on_export_clicked(self):
        """Handle export button click"""
        from PyQt6.QtWidgets import QFileDialog

        format_str = self.format_combo.currentText().lower()
        file_filter = f"{format_str.upper()} Files (*.{format_str})"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Meme", "", file_filter
        )

        if file_path:
            # Add extension if not present
            if not file_path.lower().endswith(f".{format_str}"):
                file_path += f".{format_str}"

            # Emit signal
            self.export_meme.emit(file_path, format_str)
