"""
Main application window for ZImage Enterprise
"""
import os
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QHBoxLayout,
    QWidget, QLabel, QStatusBar, QToolBar, QFileDialog,
    QMenu, QMessageBox, QApplication
)
from PyQt6.QtGui import QIcon, QPixmap, QKeySequence, QAction
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from zimage.core.constants import ICONS_DIR, APP_NAME, APP_VERSION, PRIMARY_COLOR
from zimage.core.utils import get_icon
from zimage.ui.browser.browser_tab import BrowserTab
from zimage.ui.editor.editor_tab import EditorTab
from zimage.ui.resizer.resizer_tab import ResizerTab
from zimage.ui.collage.collage_tab import CollageTab
from zimage.ui.meme.meme_tab import MemeCreatorTab

logger = logging.getLogger('zimage')

class MainWindow(QMainWindow):
    """
    Main application window
    """
    # Define signals
    folder_opened = pyqtSignal(str)

    def __init__(self, config):
        """
        Initialize the main window

        Args:
            config (Config): Application configuration
        """
        super().__init__()

        self.config = config

        # Initialize UI components
        self._init_ui()

        logger.debug("Main window initialized")

    def _init_ui(self):
        """Initialize UI components"""
        # Set window properties
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(800, 600)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self.browser_tab = BrowserTab(self.config)
        self.editor_tab = EditorTab(self.config)
        self.resizer_tab = ResizerTab(self.config)
        self.collage_tab = CollageTab(self.config)
        self.meme_tab = MemeCreatorTab(self.config)

        # Add tabs to tab widget
        self.tab_widget.addTab(self.browser_tab, "Browser")
        self.tab_widget.addTab(self.editor_tab, "Editor")
        self.tab_widget.addTab(self.resizer_tab, "Resizer")
        self.tab_widget.addTab(self.collage_tab, "Collage")
        self.tab_widget.addTab(self.meme_tab, "Meme Creator")

        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status bar components
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Create toolbars
        self._create_toolbars()

        # Create menus
        self._create_menus()

        # Connect signals
        self._connect_signals()

    def _create_toolbars(self):
        """Create toolbar components"""
        # Main toolbar
        self.main_toolbar = QToolBar("Main Toolbar")
        self.main_toolbar.setIconSize(QSize(24, 24))
        self.main_toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.main_toolbar)

        # Add actions to toolbar
        # Open folder action
        self.open_folder_action = QAction(get_icon("folder.png"), "Open Folder", self)
        self.open_folder_action.setStatusTip("Open a folder of images")
        self.open_folder_action.triggered.connect(self.open_folder_dialog)
        self.main_toolbar.addAction(self.open_folder_action)

        # Open file action
        self.open_file_action = QAction(get_icon("file.png"), "Open File", self)
        self.open_file_action.setStatusTip("Open an image file")
        self.open_file_action.triggered.connect(self.open_file_dialog)
        self.main_toolbar.addAction(self.open_file_action)

        # Add separator
        self.main_toolbar.addSeparator()

        # Edit selected image action
        self.edit_image_action = QAction(get_icon("edit.png"), "Edit Image", self)
        self.edit_image_action.setStatusTip("Edit the selected image")
        self.edit_image_action.triggered.connect(self.edit_selected_image)
        self.main_toolbar.addAction(self.edit_image_action)

        # Resize selected image action
        self.resize_image_action = QAction(get_icon("resize.png"), "Resize Image", self)
        self.resize_image_action.setStatusTip("Resize the selected image")
        self.resize_image_action.triggered.connect(self.resize_selected_image)
        self.main_toolbar.addAction(self.resize_image_action)

    def _create_menus(self):
        """Create menu components"""
        # Main menu bar
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        # Open folder action
        file_menu.addAction(self.open_folder_action)
        self.open_folder_action.setShortcut(QKeySequence("Ctrl+O"))

        # Open file action
        file_menu.addAction(self.open_file_action)
        self.open_file_action.setShortcut(QKeySequence("Ctrl+F"))

        # Recent folders submenu
        self.recent_folders_menu = QMenu("Recent Folders", self)
        file_menu.addMenu(self.recent_folders_menu)
        self._update_recent_folders_menu()

        # Recent files submenu
        self.recent_files_menu = QMenu("Recent Files", self)
        file_menu.addMenu(self.recent_files_menu)
        self._update_recent_files_menu()

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")

        # Edit selected image action
        edit_menu.addAction(self.edit_image_action)
        self.edit_image_action.setShortcut(QKeySequence("Ctrl+E"))

        # Resize selected image action
        edit_menu.addAction(self.resize_image_action)
        self.resize_image_action.setShortcut(QKeySequence("Ctrl+R"))

        # View menu
        view_menu = menu_bar.addMenu("&View")

        # Switch to browser tab action
        browser_tab_action = QAction("&Browser", self)
        browser_tab_action.setShortcut(QKeySequence("Ctrl+1"))
        browser_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(0))
        view_menu.addAction(browser_tab_action)

        # Switch to editor tab action
        editor_tab_action = QAction("&Editor", self)
        editor_tab_action.setShortcut(QKeySequence("Ctrl+2"))
        editor_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(1))
        view_menu.addAction(editor_tab_action)

        # Switch to resizer tab action
        resizer_tab_action = QAction("&Resizer", self)
        resizer_tab_action.setShortcut(QKeySequence("Ctrl+3"))
        resizer_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(2))
        view_menu.addAction(resizer_tab_action)

        # Switch to collage tab action
        collage_tab_action = QAction("C&ollage", self)
        collage_tab_action.setShortcut(QKeySequence("Ctrl+4"))
        collage_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(3))
        view_menu.addAction(collage_tab_action)

        # Switch to meme creator tab action
        meme_tab_action = QAction("&Meme Creator", self)
        meme_tab_action.setShortcut(QKeySequence("Ctrl+5"))
        meme_tab_action.triggered.connect(lambda: self.tab_widget.setCurrentIndex(4))
        view_menu.addAction(meme_tab_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _connect_signals(self):
        """Connect signals to slots"""
        # Connect tab changed signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # Connect browser tab signals
        self.browser_tab.status_message.connect(self.update_status)
        self.browser_tab.image_selected.connect(self._on_image_selected)
        self.browser_tab.add_to_collage_requested.connect(self.add_to_collage)

        # Connect editor tab signals
        self.editor_tab.status_message.connect(self.update_status)

        # Connect resizer tab signals
        self.resizer_tab.status_message.connect(self.update_status)

        # Connect collage tab signals
        self.collage_tab.status_message.connect(self.update_status)

        # Connect meme creator tab signals
        self.meme_tab.status_message.connect(self.update_status)

    def _on_tab_changed(self, index):
        """Handle tab change event"""
        tab_name = self.tab_widget.tabText(index)
        logger.debug(f"Switched to {tab_name} tab")
        self.update_status(f"Switched to {tab_name} tab")

    def _on_image_selected(self, image_model):
        """Handle image selection event"""
        if image_model:
            self.update_status(f"Selected: {image_model.file_name} ({image_model.get_dimensions_str()})")
            self.edit_image_action.setEnabled(True)
            self.resize_image_action.setEnabled(True)

            # Add context menu actions for the meme creator
            self.browser_tab.add_context_menu_action("Create Meme", self.create_meme_from_image)
        else:
            self.edit_image_action.setEnabled(False)
            self.resize_image_action.setEnabled(False)

    def _update_recent_folders_menu(self):
        """Update the recent folders menu"""
        self.recent_folders_menu.clear()

        folder_history = self.config.get_folder_history()
        if not folder_history:
            no_folders_action = QAction("No Recent Folders", self)
            no_folders_action.setEnabled(False)
            self.recent_folders_menu.addAction(no_folders_action)
            return

        for folder in folder_history:
            action = QAction(folder, self)
            action.triggered.connect(lambda checked, f=folder: self.open_folder(f))
            self.recent_folders_menu.addAction(action)

        self.recent_folders_menu.addSeparator()
        clear_action = QAction("Clear Recent Folders", self)
        clear_action.triggered.connect(self._clear_folder_history)
        self.recent_folders_menu.addAction(clear_action)

    def _update_recent_files_menu(self):
        """Update the recent files menu"""
        self.recent_files_menu.clear()

        recent_files = self.config.get_recent_files()
        if not recent_files:
            no_files_action = QAction("No Recent Files", self)
            no_files_action.setEnabled(False)
            self.recent_files_menu.addAction(no_files_action)
            return

        for file_path in recent_files:
            file_name = os.path.basename(file_path)
            action = QAction(file_name, self)
            action.setStatusTip(file_path)
            action.triggered.connect(lambda checked, f=file_path: self.open_file(f))
            self.recent_files_menu.addAction(action)

        self.recent_files_menu.addSeparator()
        clear_action = QAction("Clear Recent Files", self)
        clear_action.triggered.connect(self._clear_file_history)
        self.recent_files_menu.addAction(clear_action)

    def _clear_folder_history(self):
        """Clear the folder history"""
        self.config.clear_history(history_type="folder")
        self._update_recent_folders_menu()

    def _clear_file_history(self):
        """Clear the file history"""
        self.config.clear_history(history_type="files")
        self._update_recent_files_menu()

    def open_folder_dialog(self):
        """Open a folder dialog"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Open Folder",
            self.config.get_folder_history()[0] if self.config.get_folder_history() else ""
        )

        if folder:
            self.open_folder(folder)

    def open_folder(self, folder):
        """Open a folder of images"""
        if not os.path.isdir(folder):
            QMessageBox.warning(self, "Invalid Folder", f"The folder {folder} does not exist.")
            return

        # Add to history
        self.config.add_folder_to_history(folder)

        # Update recent folders menu
        self._update_recent_folders_menu()

        # Switch to browser tab
        self.tab_widget.setCurrentIndex(0)

        # Signal folder opened
        self.folder_opened.emit(folder)

        # Update browser tab
        self.browser_tab.load_folder(folder)

        self.update_status(f"Opened folder: {folder}")

    def open_file_dialog(self):
        """Open a file dialog"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            self.config.get_folder_history()[0] if self.config.get_folder_history() else "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff);;All Files (*)"
        )

        if file_path:
            self.open_file(file_path)

    def open_file(self, file_path):
        """Open an image file"""
        if not os.path.isfile(file_path):
            QMessageBox.warning(self, "Invalid File", f"The file {file_path} does not exist.")
            return

        # Add to recent files
        self.config.add_file_to_recent(file_path)

        # Update recent files menu
        self._update_recent_files_menu()

        # Get the containing folder
        folder = os.path.dirname(file_path)

        # Add folder to history
        self.config.add_folder_to_history(folder)

        # Update recent folders menu
        self._update_recent_folders_menu()

        # Switch to browser tab
        self.tab_widget.setCurrentIndex(0)

        # Update browser tab
        self.browser_tab.load_folder(folder, selected_file=file_path)

        self.update_status(f"Opened file: {file_path}")

    def edit_selected_image(self):
        """Edit the currently selected image"""
        selected_image = self.browser_tab.get_selected_image()
        if selected_image:
            self.editor_tab.load_image(selected_image.file_path)
            self.tab_widget.setCurrentIndex(1)  # Switch to editor tab
            self.update_status(f"Editing: {selected_image.file_name}")
        else:
            QMessageBox.warning(self, "Warning", "No image selected to edit.")

    def resize_selected_image(self):
        """Resize the currently selected image"""
        selected_image = self.browser_tab.get_selected_image()
        if selected_image:
            self.resizer_tab.add_to_batch(selected_image.file_path)
            self.tab_widget.setCurrentIndex(2)  # Switch to resizer tab
            self.update_status(f"Resizing: {selected_image.file_name}")
        else:
            QMessageBox.warning(self, "Warning", "No image selected to resize.")

    def create_meme_from_image(self):
        """Create a meme from the currently selected image"""
        selected_image = self.browser_tab.get_selected_image()
        if selected_image:
            self.meme_tab.load_image(selected_image.file_path)
            self.tab_widget.setCurrentIndex(4)  # Switch to meme creator tab
            self.update_status(f"Creating meme with: {selected_image.file_name}")
        else:
            QMessageBox.warning(self, "Warning", "No image selected for meme creation.")

    def update_status(self, message):
        """Update status bar message"""
        self.status_label.setText(message)

    def show_about_dialog(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About ZImage",
            "ZImage 1.0.0\n\n"
            "A image management and editing solution.\n\n"
            "© 2025 Yusef Ulum"
        )

    def add_to_collage(self):
        """Add the selected image to the collage tab"""
        # Get the selected image
        image_model = self.browser_tab.get_selected_image()
        if not image_model:
            self.update_status("No image selected")
            return

        # Add to collage tab
        self.collage_tab.load_image(image_model)

        # Ask if user wants to switch to collage tab
        result = QMessageBox.question(
            self,
            "Add to Collage",
            f"Added {image_model.file_name} to collage. Switch to Collage tab now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if result == QMessageBox.StandardButton.Yes:
            # Switch to collage tab
            self.tab_widget.setCurrentWidget(self.collage_tab)
