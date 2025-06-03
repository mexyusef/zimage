#!/usr/bin/env python3
"""
Generate placeholder icons for ZImage Enterprise

This script creates placeholder icons for development purposes.
The icons are simple colored squares with text labels.
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path to allow importing from zimage
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, parent_dir)

# Import constants from zimage
from zimage.core.constants import ICONS_DIR

# Icon information: name and color
ICONS = [
    ("folder.png", "#4CAF50"),     # Green
    ("file.png", "#2196F3"),       # Blue
    ("edit.png", "#FFC107"),       # Amber
    ("resize.png", "#9C27B0"),     # Purple
    ("back.png", "#607D8B"),       # Blue Grey
    ("up.png", "#607D8B"),         # Blue Grey
    ("home.png", "#795548"),       # Brown
    ("refresh.png", "#00BCD4"),    # Cyan
    ("new.png", "#4CAF50"),        # Green
    ("open.png", "#2196F3"),       # Blue
    ("save.png", "#FF9800"),       # Orange
    ("save_as.png", "#FF9800"),    # Orange
    ("undo.png", "#9E9E9E"),       # Grey
    ("redo.png", "#9E9E9E"),       # Grey
    ("reset.png", "#F44336"),      # Red
    ("pen.png", "#212121"),        # Dark Grey
    ("line.png", "#212121"),       # Dark Grey
    ("rectangle.png", "#212121"),  # Dark Grey
    ("ellipse.png", "#212121"),    # Dark Grey
    ("text.png", "#212121"),       # Dark Grey
    ("presets.png", "#3F51B5"),    # Indigo
    ("zoom_in.png", "#607D8B"),    # Blue Grey
    ("zoom_out.png", "#607D8B"),   # Blue Grey
    ("zoom_reset.png", "#607D8B"), # Blue Grey
]

def create_icon(name, color, size=24):
    """
    Create a placeholder icon

    Args:
        name (str): Icon filename
        color (str): Hex color for the icon
        size (int): Icon size in pixels
    """
    # Create new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw background rounded rectangle
    draw.rectangle([(2, 2), (size-2, size-2)], fill=color)

    # Get first letter of icon name (without extension)
    letter = name.split('.')[0][0].upper()

    # Try to add text
    try:
        # Try to find a font that works
        font = None
        font_size = size // 2

        # Try some common fonts
        for font_name in ["arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf", "LiberationSans-Regular.ttf"]:
            try:
                font = ImageFont.truetype(font_name, font_size)
                break
            except IOError:
                continue

        # If no font found, use default
        if font is None:
            font = ImageFont.load_default()

        # Calculate text position to center it
        text_width = draw.textlength(letter, font=font)
        text_height = font_size  # Approximate height
        text_x = (size - text_width) // 2
        text_y = (size - text_height) // 2

        # Draw text
        draw.text((text_x, text_y), letter, fill="white", font=font)
    except Exception as e:
        print(f"Warning: Could not add text to {name}: {str(e)}")

    # Save icon
    img.save(os.path.join(ICONS_DIR, name))
    print(f"Created {name}")

def main():
    """Generate all placeholder icons"""
    # Ensure icons directory exists
    os.makedirs(ICONS_DIR, exist_ok=True)

    # Create each icon
    for name, color in ICONS:
        create_icon(name, color)

    print(f"Generated {len(ICONS)} icons in {ICONS_DIR}")

if __name__ == "__main__":
    main()
