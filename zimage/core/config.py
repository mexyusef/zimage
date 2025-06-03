"""
Configuration management for ZImage Enterprise
"""
import os
import sys
import json
import logging
import time
from pathlib import Path

logger = logging.getLogger('zimage')

class Config:
    """
    Class to handle application configuration and settings
    """
    DEFAULT_CONFIG = {
        "folder_history": [],
        "thumbnail_size": 200,
        "theme": "default",
        "recent_files": [],
        "window": {
            "width": 1200,
            "height": 800,
            "maximized": False
        },
        "browser": {
            "sort_by": "name",
            "sort_order": "ascending",
            "show_hidden": False
        },
        "editor": {
            "brush_size": 3,
            "brush_color": "#000000",
            "background_color": "#FFFFFF"
        }
    }

    def __init__(self):
        """
        Initialize the configuration manager
        """
        # Determine config file path based on platform
        if sys.platform == 'win32':
            self.config_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 'ZImage')
        else:
            self.config_dir = os.path.join(os.path.expanduser('~'), '.zimage')

        self.config_file = os.path.join(self.config_dir, "config.json")

        # Initial attempt to load config
        try:
            self.config = self._load_config()
            logger.debug("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Error loading config file: {str(e)}")
            self._backup_config_file()
            self.config = self.DEFAULT_CONFIG.copy()
            self._save_config()

        # Ensure all required keys exist (for backward compatibility)
        self._ensure_config_structure()

    def _ensure_config_structure(self):
        """Ensure all required keys exist in the config"""
        updated = False

        # Check each key in the default config
        for key, value in self.DEFAULT_CONFIG.items():
            if key not in self.config:
                self.config[key] = value
                updated = True
            elif isinstance(value, dict) and isinstance(self.config[key], dict):
                # Recursively check nested dictionaries
                for subkey, subvalue in value.items():
                    if subkey not in self.config[key]:
                        self.config[key][subkey] = subvalue
                        updated = True

        # Save if any updates were made
        if updated:
            logger.debug("Config structure updated with new default values")
            self._save_config()

    def _backup_config_file(self):
        """Create a backup of the config file if it exists and might be corrupted"""
        if os.path.exists(self.config_file):
            try:
                backup_file = f"{self.config_file}.bak.{int(time.time())}"
                logger.info(f"Creating backup of config file: {backup_file}")

                # Read the file content
                with open(self.config_file, 'r') as src_file:
                    content = src_file.read()

                # Write to backup file
                with open(backup_file, 'w') as dst_file:
                    dst_file.write(content)

                logger.info("Config file backup created successfully")
            except Exception as e:
                logger.error(f"Failed to create config backup: {str(e)}")

    def _load_config(self):
        """Load configuration from file"""
        # Create config directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            logger.info(f"Created config directory: {self.config_dir}")

        # Create default config if file doesn't exist
        if not os.path.exists(self.config_file):
            logger.info(f"Config file not found, creating default at: {self.config_file}")
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()

        # Load existing config
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                # Ensure it's a dictionary
                if not isinstance(config, dict):
                    logger.warning("Config is not a dictionary, resetting to defaults")
                    return self.DEFAULT_CONFIG.copy()
                return config
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in config file: {str(e)}")
            # The file exists but is not valid JSON
            self._backup_config_file()
            return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return self.DEFAULT_CONFIG.copy()

    def _save_config(self, config=None):
        """Save configuration to file"""
        if config is None:
            config = self.config

        try:
            # Ensure config directory exists
            Path(self.config_dir).mkdir(parents=True, exist_ok=True)

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.debug("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")

    def get(self, key, default=None):
        """Get a configuration value"""
        # Support for nested keys using dot notation (e.g., "window.width")
        if '.' in key:
            sections = key.split('.')
            config_section = self.config

            for section in sections[:-1]:
                config_section = config_section.get(section, {})
                if not isinstance(config_section, dict):
                    return default

            return config_section.get(sections[-1], default)

        return self.config.get(key, default)

    def set(self, key, value):
        """Set a configuration value"""
        # Support for nested keys using dot notation
        if '.' in key:
            sections = key.split('.')
            config_section = self.config

            for section in sections[:-1]:
                if section not in config_section:
                    config_section[section] = {}
                config_section = config_section[section]

            config_section[sections[-1]] = value
        else:
            self.config[key] = value

        self._save_config()

    def add_folder_to_history(self, folder):
        """Add folder to history, ensuring no duplicates"""
        folder_history = self.config.get("folder_history", [])

        # Normalize path
        folder = os.path.normpath(folder)

        # Remove folder if already in history (to move it to the top)
        if folder in folder_history:
            folder_history.remove(folder)

        # Add folder to beginning of history
        folder_history.insert(0, folder)

        # Limit history to 20 items
        self.config["folder_history"] = folder_history[:20]

        # Save updated config
        self._save_config()

    def get_folder_history(self):
        """Get folder history list"""
        return self.config.get("folder_history", [])

    def add_file_to_recent(self, file_path):
        """Add file to recent files list"""
        recent_files = self.config.get("recent_files", [])

        # Normalize path
        file_path = os.path.normpath(file_path)

        # Remove file if already in list (to move it to the top)
        if file_path in recent_files:
            recent_files.remove(file_path)

        # Add file to beginning of list
        recent_files.insert(0, file_path)

        # Limit list to 20 items
        self.config["recent_files"] = recent_files[:20]

        # Save updated config
        self._save_config()

    def get_recent_files(self):
        """Get recent files list"""
        return self.config.get("recent_files", [])

    def clear_history(self, history_type="folder"):
        """Clear history (folder or files)"""
        if history_type == "folder":
            self.config["folder_history"] = []
        elif history_type == "files":
            self.config["recent_files"] = []

        self._save_config()
