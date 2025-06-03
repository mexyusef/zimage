"""
Text box widget for meme creator
"""
import logging
from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QPainter, QPen, QBrush, QPainterPath, QFont, QFontMetrics

from zimage.models.text_box import TextBoxModel

logger = logging.getLogger('zimage')

class TextBox:
    """
    Widget class for a text box in the meme canvas

    This is not a QWidget, but a helper class that renders and handles
    interaction with a text box on the meme canvas.
    """

    # Handle size for resize handles
    HANDLE_SIZE = 8

    # Handle positions
    HANDLE_TOP_LEFT = 0
    HANDLE_TOP_RIGHT = 1
    HANDLE_BOTTOM_LEFT = 2
    HANDLE_BOTTOM_RIGHT = 3

    def __init__(self, model, parent=None):
        """
        Initialize a text box widget

        Args:
            model (TextBoxModel): Text box model
            parent: Parent widget (usually MemeCanvas)
        """
        self.model = model
        self.parent = parent
        self.active_handle = None
        self.drag_start_pos = None
        self.drag_start_rect = None

        logger.debug(f"Created text box widget for text: {model.text[:20]}...")

    def render(self, painter):
        """
        Render the text box on the canvas

        Args:
            painter (QPainter): Painter to use for rendering
        """
        # Ensure we have a valid rect
        if self.model.rect.isEmpty():
            return

        # Save painter state
        painter.save()

        # Draw background if specified
        if self.model.background_color:
            painter.fillRect(self.model.rect, self.model.background_color)

        # Draw selection border if selected
        if self.model.selected:
            # Draw selection border
            pen = QPen(Qt.GlobalColor.blue, 1, Qt.PenStyle.DashLine)
            painter.setPen(pen)
            painter.drawRect(self.model.rect)

            # Draw resize handles
            self._draw_handles(painter)

        # Set up font
        font = self.model.get_font()
        painter.setFont(font)

        # Set up text path for outlined text
        if self.model.outline_size > 0:
            self._render_outlined_text(painter)
        else:
            # Simple text rendering
            painter.setPen(self.model.text_color)
            painter.drawText(
                self.model.rect,
                self.model.alignment,
                self.model.text
            )

        # Restore painter state
        painter.restore()

    def _render_outlined_text(self, painter):
        """
        Render text with outline

        Args:
            painter (QPainter): Painter to use for rendering
        """
        # Create text path
        font = self.model.get_font()
        metrics = QFontMetrics(font)
        path = QPainterPath()

        # Calculate text position based on alignment and rect
        rect = self.model.rect
        text_lines = self.model.text.split('\n')

        # Get total text height
        line_height = metrics.height()
        total_height = line_height * len(text_lines)

        # Calculate vertical starting position
        if self.model.alignment & Qt.AlignmentFlag.AlignBottom:
            y = rect.bottom() - total_height
        elif self.model.alignment & Qt.AlignmentFlag.AlignVCenter:
            y = rect.top() + (rect.height() - total_height) // 2
        else:  # AlignTop or default
            y = rect.top()

        # Render each line of text
        for line in text_lines:
            # Calculate line width
            line_width = metrics.horizontalAdvance(line)

            # Calculate horizontal position
            if self.model.alignment & Qt.AlignmentFlag.AlignRight:
                x = rect.right() - line_width
            elif self.model.alignment & Qt.AlignmentFlag.AlignHCenter:
                x = rect.left() + (rect.width() - line_width) // 2
            else:  # AlignLeft or default
                x = rect.left()

            # Add text to path
            path.addText(x, y + metrics.ascent(), font, line)

            # Move to next line
            y += line_height

        # Draw outline
        painter.setPen(QPen(self.model.outline_color, self.model.outline_size, Qt.PenStyle.SolidLine))
        painter.setBrush(QBrush(self.model.text_color))
        painter.drawPath(path)

    def _draw_handles(self, painter):
        """
        Draw resize handles for the text box

        Args:
            painter (QPainter): Painter to use for rendering
        """
        handles = self._get_handle_rects()

        # Draw handles
        painter.setPen(Qt.GlobalColor.black)
        painter.setBrush(QBrush(Qt.GlobalColor.white))

        for handle_rect in handles:
            painter.drawRect(handle_rect)

    def _get_handle_rects(self):
        """
        Get rectangles for the resize handles

        Returns:
            list: List of QRect objects for the handles
        """
        rect = self.model.rect
        half_size = self.HANDLE_SIZE // 2

        # Create handle rectangles
        tl = QRect(
            rect.left() - half_size,
            rect.top() - half_size,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE
        )

        tr = QRect(
            rect.right() - half_size,
            rect.top() - half_size,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE
        )

        bl = QRect(
            rect.left() - half_size,
            rect.bottom() - half_size,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE
        )

        br = QRect(
            rect.right() - half_size,
            rect.bottom() - half_size,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE
        )

        return [tl, tr, bl, br]

    def contains_point(self, point):
        """
        Check if the text box contains a point

        Args:
            point (QPoint): Point to check

        Returns:
            bool: True if the text box contains the point
        """
        return self.model.rect.contains(point)

    def handle_at_point(self, point):
        """
        Get the handle index at a specific point

        Args:
            point (QPoint): Point to check

        Returns:
            int: Handle index or None if no handle at point
        """
        if not self.model.selected:
            return None

        handles = self._get_handle_rects()

        for i, handle_rect in enumerate(handles):
            if handle_rect.contains(point):
                return i

        return None

    def start_drag(self, point):
        """
        Start dragging the text box

        Args:
            point (QPoint): Starting point for drag
        """
        self.drag_start_pos = point
        self.drag_start_rect = QRect(self.model.rect)

    def drag_to(self, point):
        """
        Drag the text box to a new position

        Args:
            point (QPoint): Current drag point
        """
        if not self.drag_start_pos:
            return

        # Calculate delta
        delta = point - self.drag_start_pos

        # Check if dragging a handle or the whole text box
        if self.active_handle is not None:
            self._resize_by_handle(point)
        else:
            # Move the entire text box
            self.model.rect.moveTopLeft(self.drag_start_rect.topLeft() + delta)

    def _resize_by_handle(self, point):
        """
        Resize the text box using a handle

        Args:
            point (QPoint): Current drag point
        """
        if self.active_handle is None or not self.drag_start_pos:
            return

        new_rect = QRect(self.drag_start_rect)

        # Calculate delta
        delta = point - self.drag_start_pos

        # Update rectangle based on handle
        if self.active_handle == self.HANDLE_TOP_LEFT:
            new_rect.setTopLeft(new_rect.topLeft() + delta)
        elif self.active_handle == self.HANDLE_TOP_RIGHT:
            new_rect.setTopRight(new_rect.topRight() + delta)
        elif self.active_handle == self.HANDLE_BOTTOM_LEFT:
            new_rect.setBottomLeft(new_rect.bottomLeft() + delta)
        elif self.active_handle == self.HANDLE_BOTTOM_RIGHT:
            new_rect.setBottomRight(new_rect.bottomRight() + delta)

        # Ensure minimum size
        min_size = 20
        if new_rect.width() < min_size:
            if self.active_handle in [self.HANDLE_TOP_LEFT, self.HANDLE_BOTTOM_LEFT]:
                new_rect.setLeft(new_rect.right() - min_size)
            else:
                new_rect.setRight(new_rect.left() + min_size)

        if new_rect.height() < min_size:
            if self.active_handle in [self.HANDLE_TOP_LEFT, self.HANDLE_TOP_RIGHT]:
                new_rect.setTop(new_rect.bottom() - min_size)
            else:
                new_rect.setBottom(new_rect.top() + min_size)

        self.model.rect = new_rect

    def end_drag(self):
        """End the current drag operation"""
        self.drag_start_pos = None
        self.drag_start_rect = None
        self.active_handle = None
