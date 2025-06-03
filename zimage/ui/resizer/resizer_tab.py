"""
Resizer tab component for ZImage Enterprise
"""
import logging
import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QScrollArea, QToolBar, QComboBox, QLineEdit,
    QPushButton, QSpinBox, QFileDialog, QMessageBox,
    QGroupBox, QRadioButton, QCheckBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage, QAction

from zimage.core.constants import ICONS_DIR, ResizeMethod
from zimage.core.utils import create_thumbnail, get_icon
from zimage.models.image import ImageModel

logger = logging.getLogger('zimage')

class ResizerTab(QWidget):
    """
    Resizer tab for image resizing
    """
    # Define signals
    status_message = pyqtSignal(str)

    def __init__(self, config):
        """
        Initialize the resizer tab

        Args:
            config (Config): Application configuration
        """
        super().__init__()

        self.config = config
        self.current_image = None
        self.current_pixmap = None
        self.preview_pixmap = None
        self.resize_method = ResizeMethod.BICUBIC
        self.maintain_aspect_ratio = True
        self.batch_images = []

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

        # Create settings panel (left side)
        settings_panel = QWidget()
        settings_panel.setMaximumWidth(300)
        settings_layout = QVBoxLayout(settings_panel)

        # Resize options group
        resize_group = QGroupBox("Resize Options")
        resize_layout = QVBoxLayout(resize_group)

        # Dimensions
        dimensions_layout = QHBoxLayout()
        dimensions_layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(800)
        self.width_spin.valueChanged.connect(self._on_width_changed)
        dimensions_layout.addWidget(self.width_spin)

        dimensions_layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(600)
        self.height_spin.valueChanged.connect(self._on_height_changed)
        dimensions_layout.addWidget(self.height_spin)
        resize_layout.addLayout(dimensions_layout)

        # Maintain aspect ratio
        self.aspect_check = QCheckBox("Maintain Aspect Ratio")
        self.aspect_check.setChecked(self.maintain_aspect_ratio)
        self.aspect_check.stateChanged.connect(self._on_aspect_changed)
        resize_layout.addWidget(self.aspect_check)

        # Resize method
        resize_layout.addWidget(QLabel("Resize Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItem("Nearest Neighbor", ResizeMethod.NEAREST)
        self.method_combo.addItem("Bilinear", ResizeMethod.BILINEAR)
        self.method_combo.addItem("Bicubic", ResizeMethod.BICUBIC)
        self.method_combo.addItem("Lanczos", ResizeMethod.LANCZOS)
        self.method_combo.addItem("Content-Aware", ResizeMethod.CONTENT_AWARE)
        self.method_combo.setCurrentIndex(2)  # Default to Bicubic
        self.method_combo.currentIndexChanged.connect(self._on_method_changed)
        resize_layout.addWidget(self.method_combo)

        # Add resize group to settings layout
        settings_layout.addWidget(resize_group)

        # Output options group
        output_group = QGroupBox("Output Options")
        output_layout = QVBoxLayout(output_group)

        # Output format
        output_layout.addWidget(QLabel("Output Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem("PNG", "png")
        self.format_combo.addItem("JPEG", "jpg")
        self.format_combo.addItem("BMP", "bmp")
        self.format_combo.addItem("TIFF", "tiff")
        output_layout.addWidget(self.format_combo)

        # Output quality (for JPEG)
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        self.quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(90)
        quality_layout.addWidget(self.quality_slider)
        self.quality_label = QLabel("90%")
        quality_layout.addWidget(self.quality_label)
        output_layout.addLayout(quality_layout)
        self.quality_slider.valueChanged.connect(self._on_quality_changed)

        # Output path
        output_layout.addWidget(QLabel("Output Path:"))
        self.output_path_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_layout.addWidget(self.output_path_edit)
        self.output_path_button = QPushButton("...")
        self.output_path_button.clicked.connect(self._on_output_path_clicked)
        self.output_path_layout.addWidget(self.output_path_button)
        output_layout.addLayout(self.output_path_layout)

        # Add output group to settings layout
        settings_layout.addWidget(output_group)

        # Batch options group
        batch_group = QGroupBox("Batch Processing")
        batch_layout = QVBoxLayout(batch_group)

        # Batch image list
        batch_layout.addWidget(QLabel("Images to Process:"))
        self.batch_list = QListWidget()
        batch_layout.addWidget(self.batch_list)

        # Batch buttons
        batch_buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Files")
        self.add_button.clicked.connect(self._on_add_files_clicked)
        batch_buttons_layout.addWidget(self.add_button)

        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self._on_remove_selected_clicked)
        batch_buttons_layout.addWidget(self.remove_button)

        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self._on_clear_all_clicked)
        batch_buttons_layout.addWidget(self.clear_button)

        batch_layout.addLayout(batch_buttons_layout)

        # Add batch group to settings layout
        settings_layout.addWidget(batch_group)

        # Resize buttons
        button_layout = QHBoxLayout()
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self._on_preview_clicked)
        button_layout.addWidget(self.preview_button)

        self.resize_button = QPushButton("Resize")
        self.resize_button.clicked.connect(self._on_resize_clicked)
        button_layout.addWidget(self.resize_button)

        self.batch_resize_button = QPushButton("Batch Resize")
        self.batch_resize_button.clicked.connect(self._on_batch_resize_clicked)
        button_layout.addWidget(self.batch_resize_button)

        settings_layout.addLayout(button_layout)

        # Add spacer
        settings_layout.addStretch()

        # Add settings panel to content layout
        content_layout.addWidget(settings_panel)

        # Create preview area (right side)
        preview_container = QScrollArea()
        preview_container.setWidgetResizable(True)
        preview_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create preview label
        self.preview_label = QLabel("No image loaded")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumSize(400, 300)

        # Add preview to container
        preview_container.setWidget(self.preview_label)

        # Add preview container to content layout
        content_layout.addWidget(preview_container, 1)

        # Update UI state
        self._update_ui_state()

    def _create_toolbar(self, layout):
        """Create toolbar components"""
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(24, 24))
        layout.addWidget(toolbar)

        # Open action
        self.open_action = QAction(get_icon("open.png"), "Open", self)
        self.open_action.setStatusTip("Open an image")
        self.open_action.triggered.connect(self._on_open_clicked)
        toolbar.addAction(self.open_action)

        # Save action
        self.save_action = QAction(get_icon("save.png"), "Save", self)
        self.save_action.setStatusTip("Save the resized image")
        self.save_action.triggered.connect(self._on_save_clicked)
        toolbar.addAction(self.save_action)

        toolbar.addSeparator()

        # Presets menu (to be implemented)
        self.presets_action = QAction(get_icon("presets.png"), "Presets", self)
        self.presets_action.setStatusTip("Resize presets")
        self.presets_action.triggered.connect(self._on_presets_clicked)
        toolbar.addAction(self.presets_action)

        # Update enabled state
        self._update_toolbar_state()

    def _update_toolbar_state(self):
        """Update toolbar button states"""
        has_image = self.current_image is not None
        has_preview = self.preview_pixmap is not None

        self.save_action.setEnabled(has_preview)
        self.presets_action.setEnabled(True)

    def _update_ui_state(self):
        """Update UI state based on current selections"""
        has_image = self.current_image is not None
        has_batch = len(self.batch_images) > 0

        # Update preview button - only enabled when we have a current image
        self.preview_button.setEnabled(has_image)

        # Update resize button - enable if we have a current image OR batch images
        # Since the resize button should work even when viewing a batch image
        self.resize_button.setEnabled(has_image or has_batch)

        # Update batch resize button - only enabled when we have batch images
        self.batch_resize_button.setEnabled(has_batch)

        # Update remove and clear buttons
        self.remove_button.setEnabled(has_batch)
        self.clear_button.setEnabled(has_batch)

        # Update quality slider visibility
        is_jpeg = self.format_combo.currentData() == "jpg"
        self.quality_slider.setEnabled(is_jpeg)
        self.quality_label.setEnabled(is_jpeg)

    def _on_width_changed(self, width):
        """Handle width change"""
        if self.maintain_aspect_ratio and self.current_image:
            # Calculate new height based on aspect ratio
            aspect_ratio = self.current_image.get_aspect_ratio()
            new_height = int(width / aspect_ratio)

            # Update height spin box without triggering signals
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(new_height)
            self.height_spin.blockSignals(False)

        self.status_message.emit(f"Width: {width}px")

    def _on_height_changed(self, height):
        """Handle height change"""
        if self.maintain_aspect_ratio and self.current_image:
            # Calculate new width based on aspect ratio
            aspect_ratio = self.current_image.get_aspect_ratio()
            new_width = int(height * aspect_ratio)

            # Update width spin box without triggering signals
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(new_width)
            self.width_spin.blockSignals(False)

        self.status_message.emit(f"Height: {height}px")

    def _on_aspect_changed(self, state):
        """Handle aspect ratio checkbox change"""
        self.maintain_aspect_ratio = state == Qt.CheckState.Checked.value

        # If enabled, update height based on width
        if self.maintain_aspect_ratio and self.current_image:
            self._on_width_changed(self.width_spin.value())

        self.status_message.emit(f"Maintain aspect ratio: {'Yes' if self.maintain_aspect_ratio else 'No'}")

    def _on_method_changed(self, index):
        """Handle resize method change"""
        self.resize_method = self.method_combo.itemData(index)
        self.status_message.emit(f"Resize method: {self.method_combo.itemText(index)}")

    def _on_quality_changed(self, quality):
        """Handle quality slider change"""
        self.quality_label.setText(f"{quality}%")

    def _on_output_path_clicked(self):
        """Handle output path button click"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self.output_path_edit.text() or self.config.get_folder_history()[0] if self.config.get_folder_history() else ""
        )

        if folder:
            self.output_path_edit.setText(folder)
            self.status_message.emit(f"Output path: {folder}")

    def _on_add_files_clicked(self):
        """Handle add files button click"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Images",
            self.config.get_folder_history()[0] if self.config.get_folder_history() else "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )

        if file_paths:
            # Add files to batch list
            for file_path in file_paths:
                if os.path.exists(file_path):
                    # Create image model
                    image_model = ImageModel(file_path)

                    # Add to batch list
                    self._add_to_batch(image_model)

            # Update UI state
            self._update_ui_state()

            self.status_message.emit(f"Added {len(file_paths)} files to batch")

    def _add_to_batch(self, image_model):
        """
        Add an image to the batch list

        Args:
            image_model (ImageModel): Image model to add
        """
        # Create list item
        item = QListWidgetItem(f"{image_model.file_name} ({image_model.get_dimensions_str()})")
        item.setData(Qt.ItemDataRole.UserRole, image_model)

        # Add to list widget
        self.batch_list.addItem(item)

        # Add to batch images list
        self.batch_images.append(image_model)

        # If there's no current image, load the first batch image
        if not self.current_image and len(self.batch_images) == 1:
            self.load_image(image_model)

        # Update UI state
        self._update_ui_state()

    def _on_remove_selected_clicked(self):
        """Handle remove selected button click"""
        selected_items = self.batch_list.selectedItems()

        if selected_items:
            # Remove selected items
            for item in selected_items:
                # Get image model
                image_model = item.data(Qt.ItemDataRole.UserRole)

                # Remove from batch images list
                if image_model in self.batch_images:
                    self.batch_images.remove(image_model)

                # Remove from list widget
                row = self.batch_list.row(item)
                self.batch_list.takeItem(row)

            # Update UI state
            self._update_ui_state()

            self.status_message.emit(f"Removed {len(selected_items)} files from batch")

    def _on_clear_all_clicked(self):
        """Handle clear all button click"""
        # Clear batch list
        self.batch_list.clear()
        self.batch_images = []

        # Update UI state
        self._update_ui_state()

        self.status_message.emit("Cleared batch list")

    def _on_open_clicked(self):
        """Handle open button click"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            self.config.get_folder_history()[0] if self.config.get_folder_history() else "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )

        if file_path:
            self.load_file(file_path)

    def _on_save_clicked(self):
        """Handle save button click"""
        if not self.preview_pixmap:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Resized Image",
            os.path.dirname(self.current_image.file_path) if self.current_image else "",
            "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TIFF (*.tiff);;All Files (*)"
        )

        if file_path:
            self._save_preview(file_path)

    def _on_presets_clicked(self):
        """Handle presets button click"""
        # To be implemented: presets management
        self.status_message.emit("Presets (to be implemented)")

    def _on_preview_clicked(self):
        """Handle preview button click"""
        if not self.current_image:
            return

        # Get resize dimensions
        width = self.width_spin.value()
        height = self.height_spin.value()

        # Create preview
        self._create_preview(width, height)

    def _on_resize_clicked(self):
        """Handle resize button click"""
        # Use current_image if available, or first batch image if not
        image_to_resize = self.current_image

        # If no current image but we have batch images, use the first batch image
        if not image_to_resize and self.batch_images:
            image_to_resize = self.batch_images[0]

        if not image_to_resize:
            return

        # Get resize dimensions
        width = self.width_spin.value()
        height = self.height_spin.value()

        # Create preview if needed
        if not self.preview_pixmap:
            # Temporarily set current image and pixmap
            orig_current_image = self.current_image
            orig_current_pixmap = self.current_pixmap

            self.current_image = image_to_resize
            self.current_pixmap = image_to_resize.get_pixmap(force_reload=True)

            self._create_preview(width, height)

            # Restore original current image and pixmap if using batch image
            if not orig_current_image and self.batch_images:
                self.current_image = orig_current_image
                self.current_pixmap = orig_current_pixmap

        # Get output folder
        output_folder = self.output_path_edit.text()
        if not output_folder:
            # Ask for output folder
            output_folder = QFileDialog.getExistingDirectory(
                self,
                "Select Output Folder",
                self.config.get_folder_history()[0] if self.config.get_folder_history() else ""
            )

            if not output_folder:
                return

            self.output_path_edit.setText(output_folder)

        # Get output format
        output_format = self.format_combo.currentData()

        # Get file name
        file_name = os.path.basename(self.current_image.file_path)
        name, _ = os.path.splitext(file_name)
        output_file = os.path.join(output_folder, f"{name}_resized.{output_format}")

        # Save preview
        self._save_preview(output_file)

    def _on_batch_resize_clicked(self):
        """Handle batch resize button click"""
        if not self.batch_images:
            return

        # Get output folder
        output_folder = self.output_path_edit.text()
        if not output_folder:
            # Ask for output folder
            output_folder = QFileDialog.getExistingDirectory(
                self,
                "Select Output Folder",
                self.config.get_folder_history()[0] if self.config.get_folder_history() else ""
            )

            if not output_folder:
                return

            self.output_path_edit.setText(output_folder)

        # Get resize dimensions
        width = self.width_spin.value()
        height = self.height_spin.value()

        # Get output format
        output_format = self.format_combo.currentData()

        # Process each image
        success_count = 0
        for image_model in self.batch_images:
            try:
                # Create preview pixmap
                pixmap = image_model.get_pixmap(force_reload=True)

                if pixmap.isNull():
                    logger.warning(f"Failed to load image: {image_model.file_path}")
                    continue

                # Resize image
                if self.resize_method == ResizeMethod.NEAREST:
                    resized_pixmap = pixmap.scaled(
                        width, height,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.FastTransformation
                    )
                else:
                    resized_pixmap = pixmap.scaled(
                        width, height,
                        Qt.AspectRatioMode.IgnoreAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )

                # Get file name
                file_name = os.path.basename(image_model.file_path)
                name, _ = os.path.splitext(file_name)
                output_file = os.path.join(output_folder, f"{name}_resized.{output_format}")

                # Save resized image
                if output_format == "jpg":
                    quality = self.quality_slider.value()
                    success = resized_pixmap.save(output_file, "JPEG", quality)
                else:
                    success = resized_pixmap.save(output_file)

                if success:
                    success_count += 1

            except Exception as e:
                logger.error(f"Error resizing image {image_model.file_path}: {str(e)}")

        # Show result message
        self.status_message.emit(f"Batch resize: {success_count} of {len(self.batch_images)} images processed")

        # Show message box
        QMessageBox.information(
            self,
            "Batch Resize Complete",
            f"Successfully resized {success_count} of {len(self.batch_images)} images.\n\nOutput folder: {output_folder}"
        )

    def _create_preview(self, width, height):
        """
        Create a preview of the resized image

        Args:
            width (int): Target width
            height (int): Target height
        """
        if not self.current_pixmap:
            return

        try:
            # Resize image based on selected method
            if self.resize_method == ResizeMethod.NEAREST:
                self.preview_pixmap = self.current_pixmap.scaled(
                    width, height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.FastTransformation
                )
            else:
                self.preview_pixmap = self.current_pixmap.scaled(
                    width, height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )

            # Update preview
            self.preview_label.setPixmap(self.preview_pixmap)

            # Update toolbar state
            self._update_toolbar_state()

            # Update status
            self.status_message.emit(f"Preview: {width}x{height}")

        except Exception as e:
            logger.error(f"Error creating preview: {str(e)}")
            self.status_message.emit(f"Error creating preview: {str(e)}")

    def _save_preview(self, file_path):
        """
        Save the preview image

        Args:
            file_path (str): Path to save the image to
        """
        if not self.preview_pixmap:
            return

        try:
            # Ensure directory exists
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

            # Get file extension
            _, ext = os.path.splitext(file_path)
            format_name = ext.lstrip('.').upper()

            # Use JPEG format for .jpg files
            if format_name.lower() == "jpg":
                format_name = "JPEG"
                quality = self.quality_slider.value()
                success = self.preview_pixmap.save(file_path, format_name, quality)
            else:
                success = self.preview_pixmap.save(file_path)

            if success:
                self.status_message.emit(f"Image saved to: {file_path}")

                # Add to recent files
                self.config.add_file_to_recent(file_path)

                # Show success message
                QMessageBox.information(
                    self,
                    "Save Complete",
                    f"Image successfully saved to:\n{file_path}"
                )
            else:
                self.status_message.emit(f"Failed to save image to: {file_path}")

                # Show error message
                QMessageBox.warning(
                    self,
                    "Save Failed",
                    f"Failed to save image to:\n{file_path}"
                )

        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            self.status_message.emit(f"Error saving image: {str(e)}")

            # Show error message
            QMessageBox.critical(
                self,
                "Save Error",
                f"Error saving image: {str(e)}"
            )

    def load_image(self, image_model):
        """
        Load an image model for resizing

        Args:
            image_model (ImageModel): Image model to load
        """
        if not image_model:
            return

        try:
            # Store image model
            self.current_image = image_model

            # Load pixmap
            pixmap = image_model.get_pixmap(force_reload=True)

            if pixmap.isNull():
                self.status_message.emit(f"Failed to load image: {image_model.file_path}")
                return

            # Store pixmap
            self.current_pixmap = pixmap

            # Clear preview
            self.preview_pixmap = None
            self.preview_label.setText("Click 'Preview' to see the resized image")

            # Set initial dimensions based on image size
            self.width_spin.blockSignals(True)
            self.height_spin.blockSignals(True)

            self.width_spin.setValue(image_model.width)
            self.height_spin.setValue(image_model.height)

            self.width_spin.blockSignals(False)
            self.height_spin.blockSignals(False)

            # Update UI state
            self._update_ui_state()
            self._update_toolbar_state()

            # Update status
            self.status_message.emit(f"Loaded image: {image_model.file_name} ({image_model.get_dimensions_str()})")

        except Exception as e:
            logger.error(f"Error loading image for resizing: {str(e)}")
            self.status_message.emit(f"Error loading image: {str(e)}")

    def load_file(self, file_path):
        """
        Load an image file for resizing

        Args:
            file_path (str): Path to the image file
        """
        if not os.path.isfile(file_path):
            self.status_message.emit(f"Invalid file: {file_path}")
            return

        try:
            # Create image model
            image_model = ImageModel(file_path)

            # Load image
            self.load_image(image_model)

            # Add to recent files
            self.config.add_file_to_recent(file_path)

        except Exception as e:
            logger.error(f"Error loading file for resizing: {str(e)}")
            self.status_message.emit(f"Error loading file: {str(e)}")
