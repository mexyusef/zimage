"""
Image model for ZImage Enterprise
"""
import os
import logging
from datetime import datetime
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QFileInfo

logger = logging.getLogger('zimage')

class ImageModel:
    """
    Model class for an image file
    """
    def __init__(self, file_path):
        """
        Initialize the image model

        Args:
            file_path (str): Path to the image file
        """
        self.file_path = file_path
        self.file_info = QFileInfo(file_path)
        self.file_name = os.path.basename(file_path)
        self.extension = os.path.splitext(file_path)[1].lower()

        # File information
        file_stat = os.stat(file_path)
        self.file_size = file_stat.st_size
        self.file_size_str = self._format_size(self.file_size)
        self.modified_time = datetime.fromtimestamp(file_stat.st_mtime)

        # Image information (lazy loaded)
        self._width = None
        self._height = None
        self._pixmap = None
        self._thumbnail_cache = {}

        logger.debug(f"Created image model for {self.file_name}")

    def _format_size(self, size_bytes):
        """
        Format file size in human-readable format

        Args:
            size_bytes (int): Size in bytes

        Returns:
            str: Formatted size
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def get_dimensions(self):
        """
        Get image dimensions

        Returns:
            tuple: (width, height) or (0, 0) if failed
        """
        if self._width is None or self._height is None:
            try:
                # Load image to get dimensions
                logger.debug(f"Loading image dimensions for {self.file_name}")
                pixmap = self.get_pixmap()
                self._width = pixmap.width()
                self._height = pixmap.height()
                logger.debug(f"Image dimensions: {self._width}x{self._height}")
            except Exception as e:
                logger.error(f"Error loading image dimensions for {self.file_name}: {str(e)}")
                self._width = 0
                self._height = 0

        return (self._width, self._height)

    def get_dimensions_str(self):
        """
        Get formatted dimensions string

        Returns:
            str: Formatted dimensions
        """
        width, height = self.get_dimensions()
        return f"{width}x{height}"

    def get_pixmap(self, force_reload=False):
        """
        Get image pixmap

        Args:
            force_reload (bool): Force reload from disk

        Returns:
            QPixmap: Image pixmap
        """
        if self._pixmap is None or force_reload:
            try:
                logger.debug(f"Loading pixmap for {self.file_name}")
                self._pixmap = QPixmap(self.file_path)

                if self._pixmap.isNull():
                    logger.error(f"Failed to load pixmap for {self.file_name}")
                else:
                    logger.debug(f"Successfully loaded pixmap ({self._pixmap.width()}x{self._pixmap.height()})")
            except Exception as e:
                logger.error(f"Error loading pixmap for {self.file_name}: {str(e)}")
                self._pixmap = QPixmap()

        return self._pixmap

    def get_thumbnail(self, size):
        """
        Get image thumbnail of specified size

        Args:
            size (int): Target size (max dimension)

        Returns:
            QPixmap: Thumbnail pixmap
        """
        # Check cache first
        if size in self._thumbnail_cache:
            logger.debug(f"Using cached thumbnail for {self.file_name} at size {size}")
            return self._thumbnail_cache[size]

        try:
            # Get original pixmap
            pixmap = self.get_pixmap()

            # If pixmap loading failed, return empty pixmap
            if pixmap.isNull():
                logger.error(f"Cannot create thumbnail for {self.file_name} - original pixmap is null")
                return QPixmap()

            # Calculate scaled size maintaining aspect ratio
            width = pixmap.width()
            height = pixmap.height()

            logger.debug(f"Creating thumbnail for {self.file_name} (original: {width}x{height}, target: {size})")

            # Only scale if needed
            if width > size or height > size:
                # Calculate target size preserving aspect ratio
                if width > height:
                    new_width = size
                    new_height = int(height * (size / width))
                else:
                    new_height = size
                    new_width = int(width * (size / height))

                # Scale pixmap
                thumbnail = pixmap.scaled(
                    new_width, new_height,
                    aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio,
                    transformMode=Qt.TransformationMode.SmoothTransformation
                )
                logger.debug(f"Scaled thumbnail to {new_width}x{new_height}")
            else:
                # No scaling needed
                thumbnail = pixmap
                logger.debug("No scaling needed for thumbnail")

            # Cache the thumbnail
            self._thumbnail_cache[size] = thumbnail

            return thumbnail
        except Exception as e:
            logger.error(f"Error creating thumbnail for {self.file_name}: {str(e)}")
            return QPixmap()

    def get_aspect_ratio(self):
        """
        Get image aspect ratio

        Returns:
            float: Aspect ratio (width/height)
        """
        width, height = self.get_dimensions()
        if height == 0:
            return 1.0
        return width / height

    def get_extension(self):
        """
        Get file extension

        Returns:
            str: File extension
        """
        return self.extension

    def get_directory(self):
        """
        Get directory containing the image

        Returns:
            str: Directory path
        """
        return os.path.dirname(self.file_path)

    def __str__(self):
        """String representation"""
        return f"ImageModel({self.file_name})"
