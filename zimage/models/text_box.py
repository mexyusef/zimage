"""
Text box model for meme creator
"""
import logging
from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QFont, QColor

logger = logging.getLogger('zimage')

class TextBoxModel:
    """
    Model class for a text box in a meme
    """

    # Default text box properties
    DEFAULT_FONT = "Impact"
    DEFAULT_FONT_SIZE = 36
    DEFAULT_COLOR = QColor(255, 255, 255)  # White
    DEFAULT_OUTLINE_COLOR = QColor(0, 0, 0)  # Black
    DEFAULT_OUTLINE_SIZE = 2

    def __init__(self, text="", position="custom", rect=None):
        """
        Initialize a text box model

        Args:
            text (str): Text content
            position (str): Predefined position ("top", "bottom", "custom")
            rect (QRect, optional): Custom position and size
        """
        self.text = text
        self.position_type = position

        # Font properties
        self.font_family = self.DEFAULT_FONT
        self.font_size = self.DEFAULT_FONT_SIZE
        self.bold = False
        self.italic = False

        # Color properties
        self.text_color = self.DEFAULT_COLOR
        self.outline_color = self.DEFAULT_OUTLINE_COLOR
        self.outline_size = self.DEFAULT_OUTLINE_SIZE
        self.background_color = None  # Transparent by default

        # Alignment
        self.alignment = Qt.AlignmentFlag.AlignCenter

        # Position and size (will be calculated if not provided)
        self.rect = rect if rect else QRect()

        # State
        self.selected = False

        logger.debug(f"Created text box model with text: {text[:20]}...")

    def get_font(self):
        """
        Get the QFont object for this text box

        Returns:
            QFont: Font object with current settings
        """
        font = QFont(self.font_family, self.font_size)
        font.setBold(self.bold)
        font.setItalic(self.italic)
        return font

    def set_font(self, font):
        """
        Set font properties from a QFont object

        Args:
            font (QFont): Font object
        """
        self.font_family = font.family()
        self.font_size = font.pointSize()
        self.bold = font.bold()
        self.italic = font.italic()

    def set_position(self, position_type, rect=None):
        """
        Set the position of the text box

        Args:
            position_type (str): Position type ("top", "bottom", "custom")
            rect (QRect, optional): Custom rectangle for "custom" position
        """
        self.position_type = position_type
        if position_type == "custom" and rect:
            self.rect = rect

    def calculate_position(self, canvas_width, canvas_height):
        """
        Calculate position based on position_type and canvas size

        Args:
            canvas_width (int): Width of the canvas
            canvas_height (int): Height of the canvas
        """
        # Default width is 90% of canvas width
        width = int(canvas_width * 0.9)
        # Default height is proportional to font size
        height = self.font_size * 2

        # Position based on type
        if self.position_type == "top":
            x = (canvas_width - width) // 2
            y = int(canvas_height * 0.05)  # 5% from top
            self.rect = QRect(x, y, width, height)
        elif self.position_type == "bottom":
            x = (canvas_width - width) // 2
            y = int(canvas_height * 0.85)  # 15% from bottom
            self.rect = QRect(x, y, width, height)
        elif self.position_type == "custom" and self.rect.isEmpty():
            # Default to center if no rect specified
            x = (canvas_width - width) // 2
            y = (canvas_height - height) // 2
            self.rect = QRect(x, y, width, height)

    def contains_point(self, point):
        """
        Check if a point is within the text box

        Args:
            point (QPoint): Point to check

        Returns:
            bool: True if the point is within the text box
        """
        return self.rect.contains(point)

    def to_dict(self):
        """
        Convert model to dictionary for serialization

        Returns:
            dict: Dictionary representation
        """
        return {
            "text": self.text,
            "position_type": self.position_type,
            "font_family": self.font_family,
            "font_size": self.font_size,
            "bold": self.bold,
            "italic": self.italic,
            "text_color": self.text_color.name(QColor.NameFormat.HexRgb),
            "outline_color": self.outline_color.name(QColor.NameFormat.HexRgb),
            "outline_size": self.outline_size,
            "background_color": self.background_color.name(QColor.NameFormat.HexRgb) if self.background_color else None,
            "alignment": int(self.alignment),
            "rect": {
                "x": self.rect.x(),
                "y": self.rect.y(),
                "width": self.rect.width(),
                "height": self.rect.height()
            }
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create model from dictionary

        Args:
            data (dict): Dictionary data

        Returns:
            TextBoxModel: New text box model
        """
        model = cls(text=data.get("text", ""))
        model.position_type = data.get("position_type", "custom")
        model.font_family = data.get("font_family", cls.DEFAULT_FONT)
        model.font_size = data.get("font_size", cls.DEFAULT_FONT_SIZE)
        model.bold = data.get("bold", False)
        model.italic = data.get("italic", False)

        # Colors
        model.text_color = QColor(data.get("text_color", "#ffffff"))
        model.outline_color = QColor(data.get("outline_color", "#000000"))
        model.outline_size = data.get("outline_size", cls.DEFAULT_OUTLINE_SIZE)
        if data.get("background_color"):
            model.background_color = QColor(data.get("background_color"))

        # Alignment
        model.alignment = Qt.AlignmentFlag(data.get("alignment", int(Qt.AlignmentFlag.AlignCenter)))

        # Rectangle
        rect_data = data.get("rect", {})
        model.rect = QRect(
            rect_data.get("x", 0),
            rect_data.get("y", 0),
            rect_data.get("width", 0),
            rect_data.get("height", 0)
        )

        return model
