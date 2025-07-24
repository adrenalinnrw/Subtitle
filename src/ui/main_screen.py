#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Main Screen for Subtitle Player Plugin
Provides the primary user interface for subtitle operations
"""

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Button import Button
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os


class SubtitlePlayerMainScreen(Screen):
    """Main screen for the Subtitle Player plugin"""
    
    skin = """
        <screen position="center,center" size="720,480" title="Subtitle Player">
            <widget name="title" position="20,20" size="680,40" font="Regular;24" halign="center" />
            <widget name="menu" position="20,80" size="680,300" scrollbarMode="showOnDemand" />
            <widget name="info" position="20,400" size="680,40" font="Regular;16" halign="center" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,440" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="160,440" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="300,440" size="140,40" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="440,440" size="140,40" alphatest="on" />
            <widget name="key_red" position="20,440" size="140,40" font="Regular;18" halign="center" valign="center" />
            <widget name="key_green" position="160,440" size="140,40" font="Regular;18" halign="center" valign="center" />
            <widget name="key_yellow" position="300,440" size="140,40" font="Regular;18" halign="center" valign="center" />
            <widget name="key_blue" position="440,440" size="140,40" font="Regular;18" halign="center" valign="center" />
        </screen>
    """
    
    def __init__(self, session):
        Screen.__init__(self, session)
        self.session = session
        self.setTitle("Subtitle Player v1.0")
        
        # Initialize UI components
        self["title"] = Label("Subtitle Player - Main Menu")
        self["info"] = Label("Select an option from the menu below")
        self["key_red"] = Label("Exit")
        self["key_green"] = Label("Search")
        self["key_yellow"] = Label("Settings")
        self["key_blue"] = Label("About")
        
        # Create menu items
        self.menu_items = [
            ("Search Subtitles", self.search_subtitles),
            ("Browse Local Subtitles", self.browse_local),
            ("Synchronization Tool", self.sync_tool),
            ("Translation Service", self.translation),
            ("Settings", self.open_settings),
            ("About", self.show_about)
        ]
        
        self["menu"] = MenuList([item[0] for item in self.menu_items])
        
        # Action mappings
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.menu_ok,
                "cancel": self.exit,
                "red": self.exit,
                "green": self.search_subtitles,
                "yellow": self.open_settings,
                "blue": self.show_about,
                "up": self.menu_up,
                "down": self.menu_down
            },
            -1
        )
        
        # Load configuration
        self.load_config()
    
    def load_config(self):
        """Load plugin configuration"""
        from ..config.settings import SettingsManager
        self.settings = SettingsManager()
    
    def menu_ok(self):
        """Handle OK button press on menu item"""
        selection = self["menu"].getSelectionIndex()
        if selection < len(self.menu_items):
            self.menu_items[selection][1]()
    
    def menu_up(self):
        """Move menu selection up"""
        self["menu"].up()
    
    def menu_down(self):
        """Move menu selection down"""
        self["menu"].down()
    
    def search_subtitles(self):
        """Open subtitle search screen"""
        from .search_screen import SubtitleSearchScreen
        self.session.open(SubtitleSearchScreen)
    
    def browse_local(self):
        """Browse local subtitle files"""
        from .browser_screen import SubtitleBrowserScreen
        self.session.open(SubtitleBrowserScreen)
    
    def sync_tool(self):
        """Open synchronization tool"""
        from .sync_screen import SubtitleSyncScreen
        self.session.open(SubtitleSyncScreen)
    
    def translation(self):
        """Open translation service"""
        from .translation_screen import TranslationScreen
        self.session.open(TranslationScreen)
    
    def open_settings(self):
        """Open settings screen"""
        from .settings_screen import SettingsScreen
        self.session.open(SettingsScreen)
    
    def show_about(self):
        """Show about dialog"""
        about_text = """
Subtitle Player v1.0.0

Advanced subtitle management for Enigma2

Features:
• Subtitle search and download
• Real-time synchronization
• Translation support
• Modern user interface
• Multi-language support

© 2024 Subtitle Team
        """
        self.session.open(MessageBox, about_text, MessageBox.TYPE_INFO, title="About Subtitle Player")
    
    def exit(self):
        """Exit the plugin"""
        self.close()