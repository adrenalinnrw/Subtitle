#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Settings Manager for Subtitle Player Plugin
Handles configuration storage and retrieval
"""

import os
import json
from Tools.Directories import resolveFilename, SCOPE_CONFIG


class SettingsManager:
    """Manages plugin settings and configuration"""
    
    def __init__(self):
        self.config_file = resolveFilename(SCOPE_CONFIG, "subtitle_player.conf")
        self.default_settings = {
            "theme": "dark",  # dark, light
            "language": "en",
            "auto_search": True,
            "download_path": "/tmp/subtitles/",
            "subtitle_apis": {
                "opensubtitles": {
                    "enabled": True,
                    "username": "",
                    "password": "",
                    "api_key": ""
                },
                "subscene": {
                    "enabled": False
                }
            },
            "appearance": {
                "font_size": 20,
                "font_color": "#FFFFFF",
                "outline_color": "#000000",
                "background_alpha": 128,
                "position": "bottom"  # top, middle, bottom
            },
            "sync": {
                "default_offset": 0,
                "fine_tune_step": 100,  # milliseconds
                "coarse_tune_step": 1000  # milliseconds
            },
            "translation": {
                "service": "google",  # google, microsoft
                "target_language": "en",
                "api_key": ""
            },
            "backup": {
                "auto_backup": True,
                "backup_path": "/tmp/subtitle_backups/"
            }
        }
        self.settings = self.load_settings()
    
    def load_settings(self):
        """Load settings from configuration file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = self.default_settings.copy()
                self._deep_update(settings, loaded_settings)
                return settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self):
        """Save current settings to configuration file"""
        try:
            # Ensure config directory exists
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get(self, key, default=None):
        """Get a setting value using dot notation (e.g., 'appearance.font_size')"""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key, value):
        """Set a setting value using dot notation"""
        keys = key.split('.')
        current = self.settings
        
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        current[keys[-1]] = value
    
    def reset_to_defaults(self):
        """Reset all settings to default values"""
        self.settings = self.default_settings.copy()
        return self.save_settings()
    
    def _deep_update(self, base_dict, update_dict):
        """Recursively update nested dictionaries"""
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    def create_directories(self):
        """Create necessary directories for the plugin"""
        dirs_to_create = [
            self.get('download_path'),
            self.get('backup.backup_path')
        ]
        
        for directory in dirs_to_create:
            if directory and not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                except Exception as e:
                    print(f"Error creating directory {directory}: {e}")
    
    def get_theme_settings(self):
        """Get theme-specific settings"""
        theme = self.get('theme', 'dark')
        
        theme_settings = {
            'dark': {
                'background_color': '#1e1e1e',
                'text_color': '#ffffff',
                'accent_color': '#007acc',
                'border_color': '#333333'
            },
            'light': {
                'background_color': '#ffffff',
                'text_color': '#000000',
                'accent_color': '#0066cc',
                'border_color': '#cccccc'
            }
        }
        
        return theme_settings.get(theme, theme_settings['dark'])