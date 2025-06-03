"""
Collage tab component for ZImage Enterprise
"""
import os
import logging
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QScrollArea, QFileDialog, QToolBar, QColorDialog,
    QPushButton, QSpinBox, QComboBox, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QGroupBox, QRadioButton
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap, QImage, QPainter, QColor, QCursor

from zimage.core.constants import (
    PRIMARY_COLOR, PRIMARY_LIGHT_COLOR, THUMBNAIL_MIN_SIZE, THUMBNAIL_MAX_SIZE
)
from zimage.core.utils import get_icon
from zimage.models.image import ImageModel

logger = logging.getLogger('zimage')

class ZoomablePreviewLabel(QLabel):
    """
    A label that supports zooming and panning of the displayed collage
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(400, 300)
        self.setStyleSheet("background-color: #222222; color: white;")

        # Enable mouse tracking for panning
        self.setMouseTracking(True)

        # Initialize properties
        self.zoom_factor = 1.0
        self.zoom_step = 1.2
        self.pan_start_pos = None
        self.offset = QPoint(0, 0)
        self.original_pixmap = None

        # Set cursor
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def set_pixmap(self, pixmap):
        """Set the pixmap and reset zoom/pan"""
        if pixmap is None or pixmap.isNull():
            super().setPixmap(pixmap)
            return

        self.original_pixmap = pixmap
        self.zoom_factor = 1.0
        self.offset = QPoint(0, 0)
        self.update_display()

    def update_display(self):
        """Update the display with current zoom and pan"""
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return

        # Calculate scaled size
        orig_size = self.original_pixmap.size()
        scaled_width = int(orig_size.width() * self.zoom_factor)
        scaled_height = int(orig_size.height() * self.zoom_factor)

        # Scale the pixmap
        scaled_pixmap = self.original_pixmap.scaled(
            scaled_width,
            scaled_height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        # Create a new pixmap for drawing with offset
        display_pixmap = QPixmap(self.width(), self.height())
        display_pixmap.fill(QColor(34, 34, 34))  # Dark gray background

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

        # Set the pixmap
        super().setPixmap(display_pixmap)

    def fit_to_view(self):
        """Fit the pixmap to the view"""
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return

        # Calculate ratios
        width_ratio = self.width() / self.original_pixmap.width()
        height_ratio = self.height() / self.original_pixmap.height()

        # Use smaller ratio to fit
        self.zoom_factor = min(width_ratio, height_ratio) * 0.95  # 5% margin
        self.offset = QPoint(0, 0)
        self.update_display()

    def reset_zoom(self):
        """Reset zoom to 100%"""
        self.zoom_factor = 1.0
        self.offset = QPoint(0, 0)
        self.update_display()

    def wheelEvent(self, event):
        """Handle mouse wheel for zooming"""
        if self.original_pixmap is None or self.original_pixmap.isNull():
            return

        # Get delta
        delta = event.angleDelta().y()

        # Save old zoom for position calculation
        old_zoom = self.zoom_factor

        # Calculate new zoom factor
        if delta > 0:
            # Zoom in
            self.zoom_factor *= self.zoom_step
        else:
            # Zoom out
            self.zoom_factor /= self.zoom_step

        # Limit zoom
        self.zoom_factor = max(0.1, min(10.0, self.zoom_factor))

        # Update display
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

            # Update offset
            self.offset += delta
            self.update_display()
        super().mouseMoveEvent(event)

    def resizeEvent(self, event):
        """Handle resize events"""
        super().resizeEvent(event)
        self.update_display()

class CollageTab(QWidget):
    """
    Collage tab for creating image collages
    """
    # Define signals
    status_message = pyqtSignal(str)

    def __init__(self, config):
        """
        Initialize the collage tab

        Args:
            config (Config): Application configuration
        """
        super().__init__()

        self.config = config
        self.images = []
        self.collage_result = None
        self.bg_color = QColor(Qt.GlobalColor.black)
        self.orientation = "horizontal"
        self.spacing = 10

        self._init_ui()

    def _init_ui(self):
        """Initialize UI components"""
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create toolbar
        self._create_toolbar(layout)

        # Create splitter for preview and controls
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

        # Create controls panel (left side)
        control_panel = QWidget()
        control_panel.setMaximumWidth(300)
        control_layout = QVBoxLayout(control_panel)

        # Orientation selection using radio buttons
        orientation_group = QGroupBox("Orientation:")
        orientation_layout = QHBoxLayout(orientation_group)

        self.horizontal_radio = QRadioButton("Horizontal")
        self.horizontal_radio.setChecked(True)  # Default to horizontal
        self.horizontal_radio.toggled.connect(lambda checked: self._on_orientation_changed("Horizontal" if checked else None))
        orientation_layout.addWidget(self.horizontal_radio)

        self.vertical_radio = QRadioButton("Vertical")
        self.vertical_radio.toggled.connect(lambda checked: self._on_orientation_changed("Vertical" if checked else None))
        orientation_layout.addWidget(self.vertical_radio)

        control_layout.addWidget(orientation_group)

        # Spacing control
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("Spacing:"))
        self.spacing_spin = QSpinBox()
        self.spacing_spin.setRange(0, 100)
        self.spacing_spin.setValue(self.spacing)
        self.spacing_spin.valueChanged.connect(self._on_spacing_changed)
        spacing_layout.addWidget(self.spacing_spin)
        control_layout.addLayout(spacing_layout)

        # Background color
        bg_layout = QHBoxLayout()
        bg_layout.addWidget(QLabel("Background:"))
        self.bg_button = QPushButton()
        self.bg_button.setMinimumWidth(60)
        self.bg_button.setStyleSheet(f"background-color: {self.bg_color.name()}; color: white;")
        self.bg_button.clicked.connect(self._on_bg_color_clicked)
        bg_layout.addWidget(self.bg_button)
        control_layout.addLayout(bg_layout)

        # Images list
        control_layout.addWidget(QLabel("Images:"))
        self.images_list = QListWidget()
        self.images_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.images_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.images_list.setMinimumHeight(200)
        control_layout.addWidget(self.images_list)

        # Buttons for managing images
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Images")
        add_btn.clicked.connect(self._on_add_images)
        btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._on_remove_images)
        btn_layout.addWidget(remove_btn)
        control_layout.addLayout(btn_layout)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self._on_clear_images)
        control_layout.addWidget(clear_btn)

        # Create button
        create_btn = QPushButton("Create Collage")
        create_btn.setStyleSheet(f"""
            background-color: {PRIMARY_COLOR};
            color: white;
            font-weight: bold;
            padding: 8px;
            font-size: 14px;
        """)
        create_btn.clicked.connect(self._on_create_collage)
        control_layout.addWidget(create_btn)

        # Save button
        save_btn = QPushButton("Save Collage")
        save_btn.clicked.connect(self._on_save_collage)
        control_layout.addWidget(save_btn)

        # Add spacer at the bottom
        control_layout.addStretch()

        # Add control panel to splitter
        splitter.addWidget(control_panel)

        # Create preview area (right side)
        preview_container = QScrollArea()
        preview_container.setWidgetResizable(True)
        preview_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create preview label with zoom/pan support
        self.preview_label = ZoomablePreviewLabel()
        self.preview_label.setText("No collage created yet")

        # Add preview label to container
        preview_container.setWidget(self.preview_label)

        # Add zoom controls for preview
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Preview Zoom:"))

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.clicked.connect(self._on_zoom_in)
        zoom_layout.addWidget(zoom_in_btn)

        zoom_out_btn = QPushButton("-")
        zoom_out_btn.clicked.connect(self._on_zoom_out)
        zoom_layout.addWidget(zoom_out_btn)

        fit_btn = QPushButton("Fit")
        fit_btn.clicked.connect(self._on_fit_view)
        zoom_layout.addWidget(fit_btn)

        reset_btn = QPushButton("100%")
        reset_btn.clicked.connect(self._on_reset_zoom)
        zoom_layout.addWidget(reset_btn)

        control_layout.addLayout(zoom_layout)

        # Add preview container to splitter
        splitter.addWidget(preview_container)

        # Set splitter proportions
        splitter.setSizes([300, 700])

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

        # Add label
        title_label = QLabel("Collage Creator")
        toolbar.addWidget(title_label)

    def _on_orientation_changed(self, orientation):
        """Handle orientation change"""
        self.orientation = orientation
        self.status_message.emit(f"Orientation set to {orientation}")

    def _on_spacing_changed(self, spacing):
        """Handle spacing change"""
        self.spacing = spacing
        self.status_message.emit(f"Spacing set to {spacing}px")

    def _on_bg_color_clicked(self):
        """Handle background color button click"""
        color = QColorDialog.getColor(self.bg_color, self, "Select Background Color")
        if color.isValid():
            self.bg_color = color
            self.bg_button.setStyleSheet(f"background-color: {color.name()}; color: white;")
            self.status_message.emit(f"Background color set to {color.name()}")

    def _on_add_images(self):
        """Handle add images button click"""
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "Add Images", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.webp)"
        )

        if not filenames:
            return

        for filename in filenames:
            # Create image model
            try:
                image_model = ImageModel(filename)
                self.images.append(image_model)

                # Create list item
                item = QListWidgetItem(image_model.file_name)
                item.setData(Qt.ItemDataRole.UserRole, image_model)

                # Create small thumbnail
                thumbnail = image_model.get_thumbnail(32)
                if not thumbnail.isNull():
                    item.setIcon(QIcon(thumbnail))

                self.images_list.addItem(item)
            except Exception as e:
                logger.error(f"Error adding image {filename}: {str(e)}")

        self.status_message.emit(f"Added {len(filenames)} images")

    def _on_remove_images(self):
        """Handle remove selected images button click"""
        selected_items = self.images_list.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            # Get image model
            image_model = item.data(Qt.ItemDataRole.UserRole)

            # Remove from list
            row = self.images_list.row(item)
            self.images_list.takeItem(row)

            # Remove from images list
            if image_model in self.images:
                self.images.remove(image_model)

        self.status_message.emit(f"Removed {len(selected_items)} images")

    def _on_clear_images(self):
        """Handle clear all images button click"""
        self.images_list.clear()
        self.images = []
        self.status_message.emit("Cleared all images")

    def _on_create_collage(self):
        """Handle create collage button click"""
        if not self.images:
            QMessageBox.warning(self, "No Images", "Please add images to create a collage.")
            return

        # Show busy message
        self.status_message.emit("Creating collage...")
        self.preview_label.setText("Creating collage, please wait...")

        try:
            # Create collage
            horizontal = self.orientation == "horizontal"
            spacing = self.spacing
            bg_color = self.bg_color

            # Load all images and calculate dimensions
            pixmaps = []
            total_width = 0
            total_height = 0
            max_height = 0
            max_width = 0

            for image_model in self.images:
                pixmap = image_model.get_pixmap()
                if not pixmap.isNull():
                    pixmaps.append(pixmap)

                    if horizontal:
                        total_width += pixmap.width() + spacing
                        max_height = max(max_height, pixmap.height())
                    else:  # vertical
                        total_height += pixmap.height() + spacing
                        max_width = max(max_width, pixmap.width())

            if not pixmaps:
                self.status_message.emit("No valid images to create collage")
                self.preview_label.setText("No valid images to create collage")
                return

            # Calculate collage dimensions
            if horizontal:
                total_width -= spacing  # Remove extra spacing after last image
                collage = QImage(total_width, max_height, QImage.Format.Format_ARGB32)
            else:  # vertical
                total_height -= spacing  # Remove extra spacing after last image
                collage = QImage(max_width, total_height, QImage.Format.Format_ARGB32)

            # Fill with background color
            collage.fill(bg_color)

            # Draw images
            painter = QPainter(collage)
            x_offset = 0
            y_offset = 0

            for pixmap in pixmaps:
                if horizontal:
                    # Center vertically
                    y_pos = (max_height - pixmap.height()) // 2
                    painter.drawPixmap(x_offset, y_pos, pixmap)
                    x_offset += pixmap.width() + spacing
                else:  # vertical
                    # Center horizontally
                    x_pos = (max_width - pixmap.width()) // 2
                    painter.drawPixmap(x_pos, y_offset, pixmap)
                    y_offset += pixmap.height() + spacing

            painter.end()

            # Store result
            self.collage_result = collage

            # Update preview with the new collage
            preview_pixmap = QPixmap.fromImage(collage)
            self.preview_label.set_pixmap(preview_pixmap)

            # Fit to view initially
            self.preview_label.fit_to_view()

            self.status_message.emit(f"Collage created: {collage.width()}x{collage.height()}")

        except Exception as e:
            logger.error(f"Error creating collage: {str(e)}")
            self.status_message.emit(f"Error creating collage: {str(e)}")
            self.preview_label.setText(f"Error creating collage: {str(e)}")

    def _on_save_collage(self):
        """Handle save collage button click"""
        if not self.collage_result:
            QMessageBox.warning(self, "No Collage", "Please create a collage first.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Collage", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )

        if not filename:
            return

        try:
            # Save collage
            self.collage_result.save(filename)
            self.status_message.emit(f"Collage saved to: {filename}")
        except Exception as e:
            logger.error(f"Error saving collage: {str(e)}")
            self.status_message.emit(f"Error saving collage: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error saving collage: {str(e)}")

    def load_image(self, image_model):
        """
        Load an image from another tab

        Args:
            image_model (ImageModel): Image model to add to the collage
        """
        if not image_model:
            return

        # Check if the image is already added
        for i in range(self.images_list.count()):
            item = self.images_list.item(i)
            existing_model = item.data(Qt.ItemDataRole.UserRole)
            if existing_model.file_path == image_model.file_path:
                self.status_message.emit("Image already added to collage")
                return

        # Add to images list
        self.images.append(image_model)

        # Create list item
        item = QListWidgetItem(image_model.file_name)
        item.setData(Qt.ItemDataRole.UserRole, image_model)

        # Create small thumbnail
        thumbnail = image_model.get_thumbnail(32)
        if not thumbnail.isNull():
            item.setIcon(QIcon(thumbnail))

        self.images_list.addItem(item)

        self.status_message.emit(f"Added image to collage: {image_model.file_name}")

    def get_collage(self):
        """
        Get the current collage result

        Returns:
            QImage: Collage image or None if no collage created
        """
        return self.collage_result

    def _on_zoom_in(self):
        """Handle zoom in button click"""
        if hasattr(self, 'preview_label'):
            self.preview_label.zoom_factor *= 1.2
            self.preview_label.update_display()

    def _on_zoom_out(self):
        """Handle zoom out button click"""
        if hasattr(self, 'preview_label'):
            self.preview_label.zoom_factor /= 1.2
            self.preview_label.zoom_factor = max(0.1, self.preview_label.zoom_factor)
            self.preview_label.update_display()

    def _on_fit_view(self):
        """Handle fit to view button click"""
        if hasattr(self, 'preview_label'):
            self.preview_label.fit_to_view()

    def _on_reset_zoom(self):
        """Handle reset zoom button click"""
        if hasattr(self, 'preview_label'):
            self.preview_label.reset_zoom()
