"""
Utility functions for ZImage Enterprise
"""
import os
import sys
import logging
from PyQt6.QtGui import QPixmap, QImage, QColor, QIcon
from PyQt6.QtCore import Qt, QSize

from zimage.core.constants import SUPPORTED_EXTENSIONS

logger = logging.getLogger('zimage')

def is_image_file(file_path):
    """
    Check if a file is a supported image

    Args:
        file_path (str): Path to the file

    Returns:
        bool: True if file is a supported image, False otherwise
    """
    if not os.path.isfile(file_path):
        return False

    _, ext = os.path.splitext(file_path.lower())
    return ext in SUPPORTED_EXTENSIONS

def get_files_in_directory(directory, file_filter=None, include_hidden=False):
    """
    Get a list of files in a directory with optional filtering

    Args:
        directory (str): Directory path
        file_filter (callable, optional): Filter function for files
        include_hidden (bool, optional): Whether to include hidden files

    Returns:
        list: List of file paths
    """
    if not os.path.isdir(directory):
        logger.error(f"Invalid directory: {directory}")
        return []

    try:
        files = []
        for filename in os.listdir(directory):
            # Skip hidden files if not included
            if not include_hidden and filename.startswith('.'):
                continue

            file_path = os.path.join(directory, filename)

            # Skip directories
            if os.path.isdir(file_path):
                continue

            # Apply filter if provided
            if file_filter and not file_filter(file_path):
                continue

            files.append(file_path)

        return sorted(files)
    except Exception as e:
        logger.error(f"Error reading directory {directory}: {str(e)}")
        return []

def get_images_in_directory(directory, include_hidden=False):
    """
    Get a list of image files in a directory

    Args:
        directory (str): Directory path
        include_hidden (bool, optional): Whether to include hidden files

    Returns:
        list: List of image file paths
    """
    return get_files_in_directory(
        directory,
        file_filter=is_image_file,
        include_hidden=include_hidden
    )

def create_thumbnail(image_path, size, maintain_aspect=True):
    """
    Create a thumbnail from an image file

    Args:
        image_path (str): Path to the image
        size (int or QSize): Size of the thumbnail
        maintain_aspect (bool, optional): Whether to maintain aspect ratio

    Returns:
        QPixmap: The thumbnail pixmap
    """
    try:
        pixmap = QPixmap(image_path)

        if pixmap.isNull():
            logger.warning(f"Failed to load image for thumbnail: {image_path}")
            # Create a blank pixmap with error indicator
            error_pixmap = QPixmap(size, size) if isinstance(size, int) else QPixmap(size)
            error_pixmap.fill(QColor(240, 240, 240))
            return error_pixmap

        # Convert size to QSize if it's an integer
        if isinstance(size, int):
            size = QSize(size, size)

        # Scale pixmap
        if maintain_aspect:
            scaled_pixmap = pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        else:
            scaled_pixmap = pixmap.scaled(
                size,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

        return scaled_pixmap
    except Exception as e:
        logger.error(f"Error creating thumbnail for {image_path}: {str(e)}")
        # Return blank pixmap on error
        error_pixmap = QPixmap(size, size) if isinstance(size, int) else QPixmap(size)
        error_pixmap.fill(QColor(255, 200, 200))  # Light red to indicate error
        return error_pixmap

def qimage_to_pixmap(image):
    """
    Convert QImage to QPixmap

    Args:
        image (QImage): Image to convert

    Returns:
        QPixmap: Converted pixmap
    """
    return QPixmap.fromImage(image)

def pixmap_to_qimage(pixmap):
    """
    Convert QPixmap to QImage

    Args:
        pixmap (QPixmap): Pixmap to convert

    Returns:
        QImage: Converted image
    """
    return pixmap.toImage()

def get_file_size_str(file_path):
    """
    Get human-readable file size

    Args:
        file_path (str): Path to the file

    Returns:
        str: Human-readable file size
    """
    try:
        size_bytes = os.path.getsize(file_path)

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0

        return f"{size_bytes:.2f} PB"
    except:
        return "Unknown"

def hex_to_qcolor(hex_str):
    """
    Convert hex color string to QColor

    Args:
        hex_str (str): Hex color string (e.g., "#FF0000")

    Returns:
        QColor: Qt color object
    """
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 6:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return QColor(r, g, b)
    elif len(hex_str) == 8:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        a = int(hex_str[6:8], 16)
        return QColor(r, g, b, a)
    else:
        return QColor(0, 0, 0)

def qcolor_to_hex(color):
    """
    Convert QColor to hex string

    Args:
        color (QColor): Qt color object

    Returns:
        str: Hex color string
    """
    return f"#{color.red():02x}{color.green():02x}{color.blue():02x}"

def get_icon(icon_name, fallback_icon=None, icon_dir=None):
    """
    Safely load an icon with fallback support

    Args:
        icon_name (str): Icon filename
        fallback_icon (QIcon, optional): Fallback icon if file not found
        icon_dir (str, optional): Directory to look for icon

    Returns:
        QIcon: The loaded icon or a blank icon if not found
    """
    from zimage.core.constants import ICONS_DIR

    # If no icon_dir specified, use default
    if not icon_dir:
        icon_dir = ICONS_DIR

    # Build icon path
    icon_path = os.path.join(icon_dir, icon_name)

    # Try to load icon
    if os.path.exists(icon_path):
        return QIcon(icon_path)
    else:
        # Log warning
        logger.warning(f"Icon not found: {icon_path}")

        # Return fallback if provided
        if fallback_icon:
            return fallback_icon

        # Create a blank icon as last resort
        blank_pixmap = QPixmap(24, 24)
        blank_pixmap.fill(Qt.GlobalColor.transparent)
        return QIcon(blank_pixmap)
