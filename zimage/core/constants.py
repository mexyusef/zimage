"""
Constants for ZImage Enterprise
"""
import os
from enum import Enum, auto

# Application info
APP_NAME = "ZImage Enterprise"
APP_VERSION = "1.0.0"
APP_AUTHOR = "ZImage Team"
APP_WEBSITE = "https://example.com/zimage"

# File extensions
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.tif']
RAW_EXTENSIONS = ['.raw', '.cr2', '.nef', '.arw', '.dng']
SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS + RAW_EXTENSIONS

# Default settings
DEFAULT_THUMBNAIL_SIZE = 200
DEFAULT_BRUSH_SIZE = 3
DEFAULT_BRUSH_COLOR = "#000000"
DEFAULT_BG_COLOR = "#FFFFFF"

# UI constants
THUMBNAIL_MIN_SIZE = 100
THUMBNAIL_MAX_SIZE = 400
THUMBNAIL_STEP = 10
BRUSH_SIZE_MIN = 1
BRUSH_SIZE_MAX = 100

# UI Color Theme
PRIMARY_COLOR = "#E86C00"       # Orange
PRIMARY_LIGHT_COLOR = "#FF8C30"  # Lighter orange
BG_COLOR_DARK = "#333333"       # Dark background
BG_COLOR_MEDIUM = "#444444"     # Medium background
BORDER_COLOR = "#555555"        # Border color
TEXT_COLOR_LIGHT = "#FFFFFF"    # Light text color
TEXT_COLOR_DARK = "#000000"     # Dark text color

# Application stylesheet
APP_STYLESHEET = """
    QMainWindow {
        background-color: #333333;
    }
    QTabWidget::pane {
        border: 1px solid #444444;
        background-color: #333333;
    }
    QTabBar::tab {
        background-color: #E86C00;  /* Orange */
        color: white;
        padding: 8px 15px;
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        font-weight: bold;
    }
    QTabBar::tab:selected {
        background-color: #FF8C30;  /* Lighter orange */
        font-weight: bold;
    }
    QTabBar::tab:!selected {
        margin-top: 3px;
    }
    QMenuBar {
        background-color: #E86C00;  /* Orange */
        color: white;
    }
    QMenuBar::item {
        background-color: transparent;
        color: white;
        padding: 5px 10px;
    }
    QMenuBar::item:selected {
        background-color: #FF8C30;  /* Lighter orange */
    }
    QMenu {
        background-color: #444444;
        color: white;
        border: 1px solid #555555;
    }
    QMenu::item:selected {
        background-color: #E86C00;  /* Orange */
    }
    QStatusBar {
        background-color: #333333;
        color: white;
    }
    QToolBar {
        background-color: #E86C00;
        border: none;
        spacing: 3px;
        padding: 3px;
    }
    QToolButton {
        background-color: #E86C00;
        color: white;
        border: none;
        border-radius: 3px;
        padding: 5px;
        margin: 2px;
    }
    QToolButton:hover {
        background-color: #FF8C30;
    }
    QToolButton:pressed {
        background-color: #B25400;
    }
    QPushButton {
        background-color: #E86C00;
        color: white;
        border: none;
        border-radius: 3px;
        padding: 6px 12px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #FF8C30;
    }
    QPushButton:pressed {
        background-color: #B25400;
    }
    QPushButton:disabled {
        background-color: #777777;
        color: #AAAAAA;
    }
    QLabel {
        color: white;
    }
    QLineEdit, QTextEdit, QComboBox {
        background-color: #444444;
        color: white;
        border: 1px solid #555555;
        border-radius: 3px;
        padding: 3px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 15px;
        border-left-width: 1px;
        border-left-color: #555555;
        border-left-style: solid;
    }
    QScrollBar:vertical {
        background-color: #333333;
        width: 12px;
        margin: 12px 0 12px 0;
    }
    QScrollBar::handle:vertical {
        background-color: #E86C00;
        min-height: 20px;
        border-radius: 6px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
    }
"""

# File paths
RESOURCES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources'))
ICONS_DIR = os.path.join(RESOURCES_DIR, 'icons')
THEMES_DIR = os.path.join(RESOURCES_DIR, 'themes')
STYLES_DIR = os.path.join(RESOURCES_DIR, 'styles')

# Tool types
class ToolType(Enum):
    """Enum for drawing tool types"""
    PEN = auto()
    LINE = auto()
    RECTANGLE = auto()
    ELLIPSE = auto()
    TEXT = auto()
    SELECT = auto()
    CROP = auto()
    EYEDROPPER = auto()

# Sort options
class SortType(Enum):
    """Enum for sort types"""
    NAME = auto()
    DATE = auto()
    SIZE = auto()
    TYPE = auto()

# Sort order
class SortOrder(Enum):
    """Enum for sort order"""
    ASCENDING = auto()
    DESCENDING = auto()

# Image resize methods
class ResizeMethod(Enum):
    """Enum for resize methods"""
    NEAREST = auto()
    BILINEAR = auto()
    BICUBIC = auto()
    LANCZOS = auto()
    CONTENT_AWARE = auto()

# UI Colors
PRIMARY_COLOR = "#E86C00"  # Orange
PRIMARY_LIGHT_COLOR = "#FF8C30"  # Lighter orange
BACKGROUND_COLOR = "#333333"  # Dark gray
SECONDARY_BACKGROUND = "#444444"  # Slightly lighter gray
TEXT_COLOR = "#FFFFFF"  # White
BORDER_COLOR = "#555555"  # Light gray for borders

# Application stylesheet
APP_STYLESHEET = f"""
QMainWindow, QDialog {{
    background-color: {BACKGROUND_COLOR};
}}

QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    background-color: {BACKGROUND_COLOR};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {PRIMARY_COLOR};
    color: {TEXT_COLOR};
    padding: 8px 15px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    font-weight: bold;
}}

QTabBar::tab:selected {{
    background-color: {PRIMARY_LIGHT_COLOR};
    font-weight: bold;
}}

QTabBar::tab:!selected {{
    margin-top: 3px;
}}

QMenuBar {{
    background-color: {PRIMARY_COLOR};
    color: {TEXT_COLOR};
}}

QMenuBar::item {{
    background-color: transparent;
    color: {TEXT_COLOR};
    padding: 5px 10px;
}}

QMenuBar::item:selected {{
    background-color: {PRIMARY_LIGHT_COLOR};
}}

QMenu {{
    background-color: {SECONDARY_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
}}

QMenu::item:selected {{
    background-color: {PRIMARY_COLOR};
}}

QStatusBar {{
    background-color: {BACKGROUND_COLOR};
    color: {TEXT_COLOR};
}}

QToolBar {{
    background-color: {PRIMARY_COLOR};
    border: none;
    spacing: 3px;
    padding: 3px;
}}

QToolButton {{
    background-color: {PRIMARY_COLOR};
    color: {TEXT_COLOR};
    border: none;
    border-radius: 3px;
    padding: 5px;
    margin: 2px;
    font-weight: bold;
}}

QToolButton:hover {{
    background-color: {PRIMARY_LIGHT_COLOR};
}}

QToolButton:pressed {{
    background-color: #B25400;
}}

QPushButton {{
    background-color: {PRIMARY_COLOR};
    color: {TEXT_COLOR};
    border: none;
    border-radius: 4px;
    padding: 6px 12px;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {PRIMARY_LIGHT_COLOR};
}}

QPushButton:disabled {{
    background-color: #777777;
    color: #AAAAAA;
}}

QLineEdit, QSpinBox, QComboBox {{
    background-color: {SECONDARY_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 2px;
    padding: 3px;
}}

QLabel {{
    color: {TEXT_COLOR};
}}

QCheckBox {{
    color: {TEXT_COLOR};
}}

QGroupBox {{
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 5px;
    margin-top: 1em;
    padding-top: 10px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
}}

QSlider::groove:horizontal {{
    border: 1px solid {BORDER_COLOR};
    height: 8px;
    background: {SECONDARY_BACKGROUND};
    margin: 2px 0;
    border-radius: 4px;
}}

QSlider::handle:horizontal {{
    background: {PRIMARY_COLOR};
    border: 1px solid {PRIMARY_COLOR};
    width: 18px;
    margin: -2px 0;
    border-radius: 9px;
}}

QSlider::handle:horizontal:hover {{
    background: {PRIMARY_LIGHT_COLOR};
}}

QScrollArea {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
}}

QListWidget {{
    background-color: {SECONDARY_BACKGROUND};
    color: {TEXT_COLOR};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {PRIMARY_COLOR};
}}
"""
