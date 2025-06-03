"""
Meme model for meme creator
"""
import os
import json
import logging
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QSize

from zimage.models.text_box import TextBoxModel

logger = logging.getLogger('zimage')

class MemeModel:
    """
    Model class for a meme
    """

    def __init__(self, image_path=None):
        """
        Initialize a meme model

        Args:
            image_path (str, optional): Path to the image file
        """
        self.image_path = image_path
        self.image = None
        self.text_boxes = []
        self.template_name = None
        self.template_category = None

        # Load image if provided
        if image_path:
            self.load_image(image_path)

    def load_image(self, image_path):
        """
        Load an image for the meme

        Args:
            image_path (str): Path to the image file

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            return False

        try:
            self.image = QImage(image_path)
            if self.image.isNull():
                logger.error(f"Failed to load image: {image_path}")
                return False

            self.image_path = image_path
            logger.debug(f"Loaded meme image: {image_path} ({self.image.width()}x{self.image.height()})")
            return True
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            return False

    def add_text_box(self, text="", position="custom", rect=None):
        """
        Add a text box to the meme

        Args:
            text (str): Text content
            position (str): Predefined position ("top", "bottom", "custom")
            rect (QRect, optional): Custom position and size

        Returns:
            TextBoxModel: The created text box
        """
        text_box = TextBoxModel(text, position, rect)

        # Calculate position if image is loaded
        if self.image and not self.image.isNull():
            text_box.calculate_position(self.image.width(), self.image.height())

        self.text_boxes.append(text_box)
        logger.debug(f"Added text box: {text}")
        return text_box

    def remove_text_box(self, text_box):
        """
        Remove a text box from the meme

        Args:
            text_box (TextBoxModel): Text box to remove

        Returns:
            bool: True if removed, False if not found
        """
        if text_box in self.text_boxes:
            self.text_boxes.remove(text_box)
            logger.debug(f"Removed text box: {text_box.text[:20]}...")
            return True
        return False

    def clear_text_boxes(self):
        """Clear all text boxes"""
        self.text_boxes = []
        logger.debug("Cleared all text boxes")

    def add_classic_meme_format(self):
        """
        Add top and bottom text boxes in classic meme format

        Returns:
            tuple: (top_text_box, bottom_text_box)
        """
        # Remove any existing text boxes
        self.clear_text_boxes()

        # Add top and bottom text boxes
        top = self.add_text_box("TOP TEXT", "top")
        bottom = self.add_text_box("BOTTOM TEXT", "bottom")

        return (top, bottom)

    def get_pixmap(self):
        """
        Get a QPixmap of the meme image

        Returns:
            QPixmap: The meme image as a pixmap
        """
        if not self.image or self.image.isNull():
            return QPixmap()

        return QPixmap.fromImage(self.image)

    def get_size(self):
        """
        Get the size of the meme image

        Returns:
            QSize: The size of the image
        """
        if not self.image or self.image.isNull():
            return QSize(0, 0)

        return QSize(self.image.width(), self.image.height())

    def save_to_file(self, file_path):
        """
        Save the meme model to a file

        Args:
            file_path (str): Path to save the file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            data = {
                "image_path": self.image_path,
                "template_name": self.template_name,
                "template_category": self.template_category,
                "text_boxes": [tb.to_dict() for tb in self.text_boxes]
            }

            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved meme to file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving meme to file: {str(e)}")
            return False

    @classmethod
    def load_from_file(cls, file_path):
        """
        Load a meme model from a file

        Args:
            file_path (str): Path to the file

        Returns:
            MemeModel: The loaded meme model or None if failed
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            model = cls()

            # Load image if path is valid
            image_path = data.get("image_path")
            if image_path and os.path.exists(image_path):
                model.load_image(image_path)
            else:
                logger.warning(f"Image file not found: {image_path}")

            # Set template info
            model.template_name = data.get("template_name")
            model.template_category = data.get("template_category")

            # Load text boxes
            for tb_data in data.get("text_boxes", []):
                text_box = TextBoxModel.from_dict(tb_data)
                model.text_boxes.append(text_box)

            logger.debug(f"Loaded meme from file: {file_path}")
            return model
        except Exception as e:
            logger.error(f"Error loading meme from file: {str(e)}")
            return None

    def export_image(self, file_path, image_format="png"):
        """
        Export the meme as an image file

        Args:
            file_path (str): Path to save the image
            image_format (str): Image format (png, jpg, etc.)

        Returns:
            bool: True if successful, False otherwise
        """
        # This will be implemented by the MemeCanvas widget
        # since it needs to render the text boxes on the image
        logger.warning("export_image() must be called through MemeCanvas")
        return False
