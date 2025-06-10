"""
Blur operations for the editor
"""
import logging
import traceback
from PyQt6.QtCore import QRect, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QImage, QPainter, qRed, qGreen, qBlue, qRgba, qAlpha
from PyQt6.QtCore import Qt

# Set up verbose debugging for this module
logger = logging.getLogger('zimage.editor_tab.blur')
logger.setLevel(logging.DEBUG)

class BlurWorker(QObject):
    """Worker thread for applying blur"""
    finished = pyqtSignal(QImage)
    progress = pyqtSignal(int)

    def __init__(self, source_image, rect, blur_type="gaussian", radius=10):
        super().__init__()
        self.source_image = source_image
        self.rect = rect
        self.blur_type = blur_type
        self.radius = radius

    def run(self):
        """Apply blur and emit result"""
        logger.debug(f"BlurWorker starting: {self.blur_type} blur with radius {self.radius}")
        try:
            result = apply_blur(self.source_image, self.rect, self.blur_type, self.radius, self.progress)
            self.finished.emit(result)
            logger.debug("BlurWorker finished successfully")
        except Exception as e:
            logger.error(f"Error in BlurWorker: {str(e)}\n{traceback.format_exc()}")
            # If we fail, return the original image
            self.finished.emit(self.source_image)

def apply_blur(source_image, rect, blur_type="gaussian", radius=10, progress_callback=None):
    """
    Apply blur to a region of the source image

    Args:
        source_image: QImage - The source image to blur
        rect: QRect - The rectangle region to blur
        blur_type: str - The type of blur ('gaussian', 'box', 'motion')
        radius: int - The blur radius
        progress_callback: Signal - Optional callback for progress updates

    Returns:
        QImage - The result image with blur applied
    """
    logger.debug(f"Applying {blur_type} blur with radius {radius} to rect: {rect.x()},{rect.y()},{rect.width()},{rect.height()}")

    try:
        # Make a complete copy of the source image
        source = QImage(source_image)
        logger.debug(f"Created source image copy: {source.width()}x{source.height()}")

        # Create a new result image with same dimensions
        result = QImage(source.size(), source.format())
        result.fill(Qt.GlobalColor.transparent)  # Start with transparent background
        logger.debug(f"Created result image: {result.width()}x{result.height()}")

        # Copy the entire source image to the result first
        try:
            logger.debug("Starting to copy source to result")
            painter = QPainter()
            if not painter.begin(result):
                logger.error("Failed to begin painting on result image for initial copy")
                return source_image  # Return the original image if we fail

            painter.drawImage(0, 0, source)
            painter.end()
            del painter  # Explicitly delete the painter
            logger.debug("Source image copied to result successfully")
        except Exception as e:
            logger.error(f"Error copying source to result: {str(e)}\n{traceback.format_exc()}")
            return source_image  # Return the original image if we fail

        # Extract rect coordinates
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        logger.debug(f"Processing rectangle at {x},{y} with size {w}x{h}")

        # Ensure the rectangle is valid
        x = max(0, min(x, source.width() - 1))
        y = max(0, min(y, source.height() - 1))
        w = min(w, source.width() - x)
        h = min(h, source.height() - y)
        logger.debug(f"Adjusted rectangle to {x},{y} with size {w}x{h}")

        if w <= 1 or h <= 1:
            logger.warning("Rectangle too small for blur, skipping")
            return result

        # Create temporary image for the blurred region
        temp_blur = QImage(w, h, source.format())
        temp_blur.fill(Qt.GlobalColor.transparent)  # Start with transparent background
        logger.debug(f"Created temporary blur image: {temp_blur.width()}x{temp_blur.height()}")

        # Limit radius for performance
        radius = max(1, min(20, radius))
        logger.debug(f"Using blur radius: {radius}")

        # Apply appropriate blur algorithm
        if blur_type == "gaussian" or blur_type == "box":
            logger.debug(f"Applying {blur_type} blur")
            # Box blur (simpler and more reliable)
            total_pixels = h * w
            processed_pixels = 0

            for py in range(h):
                for px in range(w):
                    # Initialize color components
                    r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
                    count = 0

                    # Calculate average of surrounding pixels
                    for dy in range(-radius, radius + 1):
                        for dx in range(-radius, radius + 1):
                            # Calculate source pixel coordinates
                            sx = x + px + dx
                            sy = y + py + dy

                            # Check if coordinates are valid
                            if 0 <= sx < source.width() and 0 <= sy < source.height():
                                # Get pixel color
                                pixel = source.pixel(sx, sy)

                                # Sum color components
                                r_sum += qRed(pixel)
                                g_sum += qGreen(pixel)
                                b_sum += qBlue(pixel)
                                a_sum += qAlpha(pixel)

                                count += 1

                    # Calculate average color
                    if count > 0:
                        r_avg = r_sum // count
                        g_avg = g_sum // count
                        b_avg = b_sum // count
                        a_avg = a_sum // count

                        # Create final pixel color
                        pixel_color = qRgba(r_avg, g_avg, b_avg, a_avg)

                        # Set pixel in temporary image
                        temp_blur.setPixel(px, py, pixel_color)

                    # Update progress every 100 pixels
                    processed_pixels += 1
                    if processed_pixels % 100 == 0 and progress_callback:
                        progress_percent = int((processed_pixels / total_pixels) * 100)
                        progress_callback.emit(progress_percent)

        elif blur_type == "motion":
            logger.debug("Applying motion blur")
            # Simple horizontal motion blur
            total_pixels = h * w
            processed_pixels = 0

            for py in range(h):
                for px in range(w):
                    # Initialize color components
                    r_sum, g_sum, b_sum, a_sum = 0, 0, 0, 0
                    count = 0

                    # Sample only horizontally for motion effect
                    for dx in range(-radius, radius + 1):
                        # Calculate source pixel coordinates
                        sx = x + px + dx
                        sy = y + py

                        # Check if coordinates are valid
                        if 0 <= sx < source.width() and 0 <= sy < source.height():
                            # Get pixel color
                            pixel = source.pixel(sx, sy)

                            # Sum color components
                            r_sum += qRed(pixel)
                            g_sum += qGreen(pixel)
                            b_sum += qBlue(pixel)
                            a_sum += qAlpha(pixel)

                            count += 1

                    # Calculate average color
                    if count > 0:
                        r_avg = r_sum // count
                        g_avg = g_sum // count
                        b_avg = b_sum // count
                        a_avg = a_sum // count

                        # Create final pixel color
                        pixel_color = qRgba(r_avg, g_avg, b_avg, a_avg)

                        # Set pixel in temporary image
                        temp_blur.setPixel(px, py, pixel_color)

                    # Update progress every 100 pixels
                    processed_pixels += 1
                    if processed_pixels % 100 == 0 and progress_callback:
                        progress_percent = int((processed_pixels / total_pixels) * 100)
                        progress_callback.emit(progress_percent)

        logger.debug("Blur calculation completed")

        # Draw the blurred region onto the result image
        try:
            logger.debug("Starting to draw blurred region onto result")
            result_painter = QPainter()
            if not result_painter.begin(result):
                logger.error("Failed to begin painting on result image for blur region")
                return source_image  # Return the original image if we fail

            result_painter.drawImage(x, y, temp_blur)
            result_painter.end()
            del result_painter  # Explicitly delete the painter
            logger.debug("Blurred region drawn onto result successfully")
        except Exception as e:
            logger.error(f"Error drawing blurred region: {str(e)}\n{traceback.format_exc()}")
            return source_image  # Return the original image if we fail

        # Important: Make sure all painter objects are fully cleaned up before returning
        temp_blur = None  # Release temp_blur
        logger.debug("Temporary resources released")

        # Signal 100% completion
        if progress_callback:
            progress_callback.emit(100)

        return result

    except Exception as e:
        logger.error(f"Error in apply_blur: {str(e)}\n{traceback.format_exc()}")
        return source_image  # Return the original image if we fail
