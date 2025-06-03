# ZImage Enterprise - Quick Start Tutorial

Welcome to ZImage Enterprise! This tutorial will help you get started with the application and explore its features.

## Installation

First, make sure you have Python 3.7 or newer installed. Then install ZImage Enterprise using pip:

```bash
pip install -r requirements.txt
```

## Starting the Application

You can start ZImage Enterprise in several ways:

1. Using the batch file (Windows):

```
zimage.bat
```

2. Using Python:

```bash
python -m zimage.main
```

3. Directly from the main script:

```bash
python zimage/main.py
```

## Basic Usage

ZImage Enterprise has three main tabs:

1. **Browser** - For browsing and viewing images
2. **Editor** - For editing and drawing on images
3. **Resizer** - For resizing and batch processing images

### Browser Tab

1. Open a folder of images using the "Open Folder" button or Ctrl+O
2. Browse through the thumbnails to find your images
3. Click on an image to select it
4. Double-click on an image to view it in fullscreen
5. Use the slider at the bottom to adjust thumbnail size

### Editor Tab

1. Select an image in the Browser tab
2. Click the "Edit" button or press Ctrl+E to open it in the Editor
3. Choose a drawing tool from the left panel
4. Adjust brush size and color
5. Draw on the image
6. Save your changes using the "Save" or "Save As" buttons

### Resizer Tab

1. Select an image in the Browser tab
2. Click the "Resize" button or press Ctrl+R to open it in the Resizer
3. Set the desired dimensions
4. Choose a resize method
5. Select output format and quality
6. Click "Preview" to see the result
7. Click "Resize" to save the resized image

## Batch Processing

The Resizer tab also supports batch processing:

1. Click "Add Files" to add multiple images
2. Set the desired dimensions and other options
3. Set the output folder
4. Click "Batch Resize" to process all images

## Keyboard Shortcuts

- **Ctrl+O**: Open folder
- **Ctrl+F**: Open file
- **Ctrl+E**: Edit selected image
- **Ctrl+R**: Resize selected image
- **Ctrl+1**: Switch to Browser tab
- **Ctrl+2**: Switch to Editor tab
- **Ctrl+3**: Switch to Resizer tab
- **Ctrl+Q**: Exit application

## Advanced Usage

Check out the `usage_example.py` file for examples of how to use ZImage Enterprise programmatically or integrate it into your own applications.

## Getting Help

If you need assistance, please refer to the full documentation or open an issue in the GitHub repository.
