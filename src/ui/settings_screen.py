#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Settings Screen for Subtitle Player Plugin
Provides configuration interface for all plugin settings
"""

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ConfigList import ConfigList
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigText, ConfigInteger, ConfigYesNo, getConfigListEntry
import os


class SettingsScreen(Screen):
    """Settings configuration screen"""
    
    skin = """
        <screen position="center,center" size="800,600" title="Subtitle Player Settings">
            <widget name="title" position="20,20" size="760,30" font="Regular;22" halign="center" />
            <widget name="category" position="20,60" size="200,30" font="Regular;18" />
            <widget name="categories" position="20,100" size="200,400" scrollbarMode="showOnDemand" />
            <widget name="config" position="240,100" size="540,400" scrollbarMode="showOnDemand" />
            <widget name="description" position="20,510" size="760,40" font="Regular;14" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,560" size="140,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="170,560" size="140,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="320,560" size="140,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="470,560" size="140,30" alphatest="on" />
            <widget name="key_red" position="20,560" size="140,30" font="Regular;16" halign="center" valign="center" />
            <widget name="key_green" position="170,560" size="140,30" font="Regular;16" halign="center" valign="center" />
            <widget name="key_yellow" position="320,560" size="140,30" font="Regular;16" halign="center" valign="center" />
            <widget name="key_blue" position="470,560" size="140,30" font="Regular;16" halign="center" valign="center" />
        </screen>
    """
    
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        
        # Initialize UI components
        self["title"] = Label("Subtitle Player Settings")
        self["category"] = Label("Categories:")
        self["description"] = Label("Select a category to configure settings")
        
        # Button labels
        self["key_red"] = Label("Cancel")
        self["key_green"] = Label("Save")
        self["key_yellow"] = Label("Defaults")
        self["key_blue"] = Label("Test")
        
        # Categories list
        self.categories = [
            ("general", "General Settings"),
            ("apis", "Subtitle APIs"),
            ("appearance", "Subtitle Appearance"),
            ("sync", "Synchronization"),
            ("translation", "Translation Service"),
            ("backup", "Backup & Storage"),
            ("advanced", "Advanced Options")
        ]
        
        self["categories"] = MenuList([cat[1] for cat in self.categories])
        
        # Config list (will be populated based on category)
        self["config"] = ConfigList([])
        
        # Action mappings
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.category_selected,
                "cancel": self.cancel,
                "red": self.cancel,
                "green": self.save_settings,
                "yellow": self.reset_to_defaults,
                "blue": self.test_settings,
                "up": self.list_up,
                "down": self.list_down,
                "left": self.switch_to_categories,
                "right": self.switch_to_config
            },
            -1
        )
        
        # Load settings
        self.load_settings()
        
        # Current focus (categories or config)
        self.current_focus = "categories"
        
        # Show first category by default
        self.show_category("general")
    
    def load_settings(self):
        """Load current settings"""
        try:
            from ..config.settings import SettingsManager
            self.settings_manager = SettingsManager()
            self.original_settings = self.settings_manager.settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            self.session.open(MessageBox, f"Error loading settings: {e}", MessageBox.TYPE_ERROR)
    
    def list_up(self):
        """Move selection up"""
        if self.current_focus == "categories":
            self["categories"].up()
        else:
            self["config"].up()
        self.update_description()
    
    def list_down(self):
        """Move selection down"""
        if self.current_focus == "categories":
            self["categories"].down()
        else:
            self["config"].down()
        self.update_description()
    
    def switch_to_categories(self):
        """Switch focus to categories list"""
        self.current_focus = "categories"
        self["category"].setText("Categories: (ACTIVE)")
    
    def switch_to_config(self):
        """Switch focus to config list"""
        self.current_focus = "config"
        self["category"].setText("Categories:")
    
    def category_selected(self):
        """Handle category selection"""
        if self.current_focus == "categories":
            selection_idx = self["categories"].getSelectionIndex()
            if 0 <= selection_idx < len(self.categories):
                category_id = self.categories[selection_idx][0]
                self.show_category(category_id)
                self.switch_to_config()
    
    def show_category(self, category_id):
        """Show settings for specific category"""
        config_items = []
        
        if category_id == "general":
            config_items = self.get_general_config()
        elif category_id == "apis":
            config_items = self.get_apis_config()
        elif category_id == "appearance":
            config_items = self.get_appearance_config()
        elif category_id == "sync":
            config_items = self.get_sync_config()
        elif category_id == "translation":
            config_items = self.get_translation_config()
        elif category_id == "backup":
            config_items = self.get_backup_config()
        elif category_id == "advanced":
            config_items = self.get_advanced_config()
        
        self["config"].setList(config_items)
        self.current_category = category_id
    
    def get_general_config(self):
        """Get general settings configuration"""
        config_items = []
        
        # Theme selection
        theme_choices = [("dark", "Dark Theme"), ("light", "Light Theme")]
        current_theme = self.settings_manager.get('theme', 'dark')
        theme_config = ConfigSelection(choices=theme_choices, default=current_theme)
        config_items.append(getConfigListEntry("Interface Theme", theme_config, "Choose between dark and light interface themes"))
        
        # Language selection
        lang_choices = [("en", "English"), ("tr", "Turkish"), ("de", "German"), ("fr", "French"), ("es", "Spanish")]
        current_lang = self.settings_manager.get('language', 'en')
        lang_config = ConfigSelection(choices=lang_choices, default=current_lang)
        config_items.append(getConfigListEntry("Interface Language", lang_config, "Select interface language"))
        
        # Auto search
        auto_search = self.settings_manager.get('auto_search', True)
        auto_search_config = ConfigYesNo(default=auto_search)
        config_items.append(getConfigListEntry("Auto Search on Load", auto_search_config, "Automatically search for subtitles when video is loaded"))
        
        # Download path
        download_path = self.settings_manager.get('download_path', '/tmp/subtitles/')
        download_path_config = ConfigText(default=download_path, fixed_size=False)
        config_items.append(getConfigListEntry("Download Path", download_path_config, "Default location for downloaded subtitles"))
        
        return config_items
    
    def get_apis_config(self):
        """Get API settings configuration"""
        config_items = []
        
        # OpenSubtitles settings
        os_enabled = self.settings_manager.get('subtitle_apis.opensubtitles.enabled', True)
        os_enabled_config = ConfigYesNo(default=os_enabled)
        config_items.append(getConfigListEntry("Enable OpenSubtitles", os_enabled_config, "Enable/disable OpenSubtitles API"))
        
        os_username = self.settings_manager.get('subtitle_apis.opensubtitles.username', '')
        os_username_config = ConfigText(default=os_username, fixed_size=False)
        config_items.append(getConfigListEntry("OpenSubtitles Username", os_username_config, "OpenSubtitles account username (optional)"))
        
        os_password = self.settings_manager.get('subtitle_apis.opensubtitles.password', '')
        os_password_config = ConfigText(default=os_password, fixed_size=False)
        config_items.append(getConfigListEntry("OpenSubtitles Password", os_password_config, "OpenSubtitles account password (optional)"))
        
        # Subscene settings
        subscene_enabled = self.settings_manager.get('subtitle_apis.subscene.enabled', False)
        subscene_enabled_config = ConfigYesNo(default=subscene_enabled)
        config_items.append(getConfigListEntry("Enable Subscene", subscene_enabled_config, "Enable/disable Subscene scraping"))
        
        return config_items
    
    def get_appearance_config(self):
        """Get subtitle appearance settings"""
        config_items = []
        
        # Font size
        font_size = self.settings_manager.get('appearance.font_size', 20)
        font_size_config = ConfigInteger(default=font_size, limits=(8, 72))
        config_items.append(getConfigListEntry("Font Size", font_size_config, "Subtitle font size in pixels"))
        
        # Font color
        color_choices = [
            ("#FFFFFF", "White"),
            ("#FFFF00", "Yellow"),
            ("#00FF00", "Green"),
            ("#FF0000", "Red"),
            ("#0000FF", "Blue"),
            ("#FF00FF", "Magenta"),
            ("#00FFFF", "Cyan")
        ]
        current_color = self.settings_manager.get('appearance.font_color', '#FFFFFF')
        color_config = ConfigSelection(choices=color_choices, default=current_color)
        config_items.append(getConfigListEntry("Font Color", color_config, "Subtitle text color"))
        
        # Outline color
        outline_color = self.settings_manager.get('appearance.outline_color', '#000000')
        outline_config = ConfigSelection(choices=color_choices + [("#000000", "Black")], default=outline_color)
        config_items.append(getConfigListEntry("Outline Color", outline_config, "Subtitle text outline color"))
        
        # Background alpha
        bg_alpha = self.settings_manager.get('appearance.background_alpha', 128)
        bg_alpha_config = ConfigInteger(default=bg_alpha, limits=(0, 255))
        config_items.append(getConfigListEntry("Background Alpha", bg_alpha_config, "Subtitle background transparency (0=transparent, 255=opaque)"))
        
        # Position
        position_choices = [("bottom", "Bottom"), ("middle", "Middle"), ("top", "Top")]
        current_position = self.settings_manager.get('appearance.position', 'bottom')
        position_config = ConfigSelection(choices=position_choices, default=current_position)
        config_items.append(getConfigListEntry("Subtitle Position", position_config, "Default subtitle display position"))
        
        return config_items
    
    def get_sync_config(self):
        """Get synchronization settings"""
        config_items = []
        
        # Default offset
        default_offset = self.settings_manager.get('sync.default_offset', 0)
        offset_config = ConfigInteger(default=default_offset, limits=(-10000, 10000))
        config_items.append(getConfigListEntry("Default Offset (ms)", offset_config, "Default timing offset in milliseconds"))
        
        # Fine tune step
        fine_step = self.settings_manager.get('sync.fine_tune_step', 100)
        fine_step_config = ConfigInteger(default=fine_step, limits=(10, 1000))
        config_items.append(getConfigListEntry("Fine Tune Step (ms)", fine_step_config, "Step size for fine timing adjustments"))
        
        # Coarse tune step
        coarse_step = self.settings_manager.get('sync.coarse_tune_step', 1000)
        coarse_step_config = ConfigInteger(default=coarse_step, limits=(100, 5000))
        config_items.append(getConfigListEntry("Coarse Tune Step (ms)", coarse_step_config, "Step size for coarse timing adjustments"))
        
        return config_items
    
    def get_translation_config(self):
        """Get translation service settings"""
        config_items = []
        
        # Translation service
        service_choices = [("google", "Google Translate"), ("microsoft", "Microsoft Translator")]
        current_service = self.settings_manager.get('translation.service', 'google')
        service_config = ConfigSelection(choices=service_choices, default=current_service)
        config_items.append(getConfigListEntry("Translation Service", service_config, "Translation service provider"))
        
        # Target language
        lang_choices = [
            ("en", "English"), ("tr", "Turkish"), ("de", "German"), ("fr", "French"),
            ("es", "Spanish"), ("it", "Italian"), ("pt", "Portuguese"), ("ru", "Russian"),
            ("zh", "Chinese"), ("ja", "Japanese"), ("ko", "Korean"), ("ar", "Arabic")
        ]
        target_lang = self.settings_manager.get('translation.target_language', 'en')
        target_lang_config = ConfigSelection(choices=lang_choices, default=target_lang)
        config_items.append(getConfigListEntry("Target Language", target_lang_config, "Default translation target language"))
        
        # API key
        api_key = self.settings_manager.get('translation.api_key', '')
        api_key_config = ConfigText(default=api_key, fixed_size=False)
        config_items.append(getConfigListEntry("API Key", api_key_config, "Translation service API key (if required)"))
        
        return config_items
    
    def get_backup_config(self):
        """Get backup and storage settings"""
        config_items = []
        
        # Auto backup
        auto_backup = self.settings_manager.get('backup.auto_backup', True)
        auto_backup_config = ConfigYesNo(default=auto_backup)
        config_items.append(getConfigListEntry("Auto Backup", auto_backup_config, "Automatically backup downloaded subtitles"))
        
        # Backup path
        backup_path = self.settings_manager.get('backup.backup_path', '/tmp/subtitle_backups/')
        backup_path_config = ConfigText(default=backup_path, fixed_size=False)
        config_items.append(getConfigListEntry("Backup Path", backup_path_config, "Location for subtitle backups"))
        
        return config_items
    
    def get_advanced_config(self):
        """Get advanced settings"""
        config_items = []
        
        # Debug mode (placeholder)
        debug_config = ConfigYesNo(default=False)
        config_items.append(getConfigListEntry("Debug Mode", debug_config, "Enable debug logging (requires restart)"))
        
        # Cache settings (placeholder)
        cache_config = ConfigYesNo(default=True)
        config_items.append(getConfigListEntry("Enable Caching", cache_config, "Cache search results and downloads"))
        
        return config_items
    
    def update_description(self):
        """Update description based on current selection"""
        if self.current_focus == "config":
            current_item = self["config"].getCurrent()
            if current_item and len(current_item) > 2:
                self["description"].setText(current_item[2])
            else:
                self["description"].setText("")
        else:
            self["description"].setText("Select a category to configure settings")
    
    def save_settings(self):
        """Save all settings"""
        try:
            # Apply all config changes to settings manager
            self.apply_config_changes()
            
            # Save to file
            if self.settings_manager.save_settings():
                # Create necessary directories
                self.settings_manager.create_directories()
                
                self.session.open(MessageBox, "Settings saved successfully!", MessageBox.TYPE_INFO)
                self.close()
            else:
                self.session.open(MessageBox, "Failed to save settings", MessageBox.TYPE_ERROR)
                
        except Exception as e:
            self.session.open(MessageBox, f"Error saving settings: {e}", MessageBox.TYPE_ERROR)
    
    def apply_config_changes(self):
        """Apply configuration changes to settings manager"""
        # This is a simplified implementation
        # In a real implementation, you'd track changes to each config item
        # and apply them to the settings manager
        pass
    
    def cancel(self):
        """Cancel settings changes"""
        def confirm_cancel(confirmed):
            if confirmed:
                # Restore original settings
                self.settings_manager.settings = self.original_settings
                self.close()
        
        self.session.openWithCallback(confirm_cancel, MessageBox, 
                                     "Discard all changes?", MessageBox.TYPE_YESNO)
    
    def reset_to_defaults(self):
        """Reset settings to defaults"""
        def confirm_reset(confirmed):
            if confirmed:
                self.settings_manager.reset_to_defaults()
                self.show_category(self.current_category)
                self.session.open(MessageBox, "Settings reset to defaults", MessageBox.TYPE_INFO)
        
        self.session.openWithCallback(confirm_reset, MessageBox,
                                     "Reset all settings to defaults?", MessageBox.TYPE_YESNO)
    
    def test_settings(self):
        """Test current settings"""
        if self.current_category == "apis":
            self.test_api_settings()
        elif self.current_category == "translation":
            self.test_translation_settings()
        else:
            self.session.open(MessageBox, "No test available for this category", MessageBox.TYPE_INFO)
    
    def test_api_settings(self):
        """Test API connectivity"""
        self.session.open(MessageBox, "API test functionality will be implemented", MessageBox.TYPE_INFO)
    
    def test_translation_settings(self):
        """Test translation service"""
        self.session.open(MessageBox, "Translation test functionality will be implemented", MessageBox.TYPE_INFO)