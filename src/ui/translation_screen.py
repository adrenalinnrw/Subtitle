#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Translation Screen for Subtitle Player Plugin
Provides interface for translating subtitles
"""

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ProgressBar import ProgressBar
import os
import threading


class TranslationScreen(Screen):
    """Screen for subtitle translation"""
    
    skin = """
        <screen position="center,center" size="900,700" title="Subtitle Translation">
            <widget name="title" position="20,20" size="860,30" font="Regular;22" halign="center" />
            <widget name="file_info" position="20,60" size="860,25" font="Regular;16" />
            <widget name="lang_info" position="20,90" size="860,25" font="Regular;16" />
            
            <!-- Source and target language selection -->
            <widget name="source_label" position="20,130" size="150,25" font="Regular;16" />
            <widget name="source_lang" position="180,130" size="200,25" font="Regular;16" />
            <widget name="target_label" position="400,130" size="150,25" font="Regular;16" />
            <widget name="target_lang" position="560,130" size="200,25" font="Regular;16" />
            
            <!-- Progress indicator -->
            <widget name="progress_label" position="20,170" size="860,20" font="Regular;14" />
            <widget name="progress" position="20,195" size="860,20" />
            
            <!-- Preview area -->
            <widget name="preview_label" position="20,230" size="860,20" font="Regular;16" />
            <widget name="original_text" position="20,255" size="420,120" font="Regular;14" valign="top" backgroundColor="#2d2d2d" />
            <widget name="translated_text" position="460,255" size="420,120" font="Regular;14" valign="top" backgroundColor="#1e3a1e" />
            
            <!-- Subtitle list -->
            <widget name="list_label" position="20,390" size="860,20" font="Regular;16" />
            <widget name="subtitle_list" position="20,415" size="860,200" scrollbarMode="showOnDemand" />
            
            <!-- Status and controls -->
            <widget name="status" position="20,625" size="860,25" font="Regular;14" />
            
            <!-- Action buttons -->
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,655" size="140,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="170,655" size="140,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="320,655" size="140,30" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="470,655" size="140,30" alphatest="on" />
            <widget name="key_red" position="20,655" size="140,30" font="Regular;16" halign="center" valign="center" />
            <widget name="key_green" position="170,655" size="140,30" font="Regular;16" halign="center" valign="center" />
            <widget name="key_yellow" position="320,655" size="140,30" font="Regular;16" halign="center" valign="center" />
            <widget name="key_blue" position="470,655" size="140,30" font="Regular;16" halign="center" valign="center" />
        </screen>
    """
    
    def __init__(self, session, subtitle_file=None):
        Screen.__init__(self, session)
        self.session = session
        self.subtitle_file = subtitle_file
        self.subtitle_entries = []
        self.translated_entries = []
        self.current_source_lang = 'auto'
        self.current_target_lang = 'en'
        self.translation_service = None
        
        # Initialize UI components
        self["title"] = Label("Subtitle Translation Service")
        self["file_info"] = Label("")
        self["lang_info"] = Label("")
        self["source_label"] = Label("Source Language:")
        self["source_lang"] = Label("Auto-detect")
        self["target_label"] = Label("Target Language:")
        self["target_lang"] = Label("English")
        self["progress_label"] = Label("")
        self["progress"] = ProgressBar()
        self["progress"].hide()
        self["preview_label"] = Label("Translation Preview:")
        self["original_text"] = Label("")
        self["translated_text"] = Label("")
        self["list_label"] = Label("Subtitle Entries:")
        self["subtitle_list"] = MenuList([])
        self["status"] = Label("Ready")
        
        # Button labels
        self["key_red"] = Label("Back")
        self["key_green"] = Label("Translate")
        self["key_yellow"] = Label("Languages")
        self["key_blue"] = Label("Save")
        
        # Action mappings
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.preview_translation,
                "cancel": self.close,
                "red": self.close,
                "green": self.start_translation,
                "yellow": self.select_languages,
                "blue": self.save_translation,
                "up": self.list_up,
                "down": self.list_down
            },
            -1
        )
        
        # Initialize translation service
        self.init_translation_service()
        
        # Load subtitle file if provided
        if self.subtitle_file:
            self.load_subtitle_file()
        else:
            self.select_subtitle_file()
    
    def init_translation_service(self):
        """Initialize translation service"""
        try:
            from ..config.settings import SettingsManager
            from ..core.translation import TranslationService
            
            settings = SettingsManager()
            self.translation_service = TranslationService(settings)
            
            # Load default target language from settings
            self.current_target_lang = settings.get('translation.target_language', 'en')
            self.update_language_display()
            
        except Exception as e:
            self["status"].setText(f"Error initializing translation service: {e}")
            print(f"Translation service init error: {e}")
    
    def select_subtitle_file(self):
        """Select subtitle file to translate"""
        def file_selected(file_path):
            if file_path and os.path.exists(file_path):
                self.subtitle_file = file_path
                self.load_subtitle_file()
        
        from Screens.LocationBox import LocationBox
        self.session.openWithCallback(file_selected, LocationBox,
                                     currDir="/tmp/", title="Select subtitle file to translate")
    
    def load_subtitle_file(self):
        """Load and parse subtitle file"""
        if not self.subtitle_file or not os.path.exists(self.subtitle_file):
            self.session.open(MessageBox, "No valid subtitle file selected", MessageBox.TYPE_ERROR)
            return
        
        try:
            from ..core.parser import SubtitleParser
            
            parser = SubtitleParser()
            self.subtitle_entries = parser.parse_file(self.subtitle_file)
            
            if self.subtitle_entries:
                self["status"].setText(f"Loaded {len(self.subtitle_entries)} subtitle entries")
                self.update_file_info()
                self.update_subtitle_list()
                self.detect_source_language()
            else:
                self["status"].setText("No subtitle entries found in file")
                
        except Exception as e:
            self["status"].setText(f"Error loading subtitle: {e}")
            self.session.open(MessageBox, f"Failed to load subtitle file:\n{e}", MessageBox.TYPE_ERROR)
    
    def update_file_info(self):
        """Update file information display"""
        if self.subtitle_file:
            filename = os.path.basename(self.subtitle_file)
            entry_count = len(self.subtitle_entries)
            self["file_info"].setText(f"File: {filename} ({entry_count} entries)")
        else:
            self["file_info"].setText("No file loaded")
    
    def update_language_display(self):
        """Update language selection display"""
        if not self.translation_service:
            return
        
        # Get language names
        supported_langs = self.translation_service.get_supported_languages()
        
        source_name = "Auto-detect" if self.current_source_lang == 'auto' else supported_langs.get(self.current_source_lang, self.current_source_lang)
        target_name = supported_langs.get(self.current_target_lang, self.current_target_lang)
        
        self["source_lang"].setText(source_name)
        self["target_lang"].setText(target_name)
        self["lang_info"].setText(f"Translation: {source_name} → {target_name}")
    
    def detect_source_language(self):
        """Detect source language of subtitles"""
        if not self.subtitle_entries or not self.translation_service:
            return
        
        self["status"].setText("Detecting source language...")
        
        def detect_thread():
            try:
                # Use first few entries for detection
                sample_text = ""
                for i, entry in enumerate(self.subtitle_entries[:5]):
                    sample_text += entry.text + " "
                    if len(sample_text) > 500:  # Sufficient sample
                        break
                
                detected_lang = self.translation_service.detect_language(sample_text)
                
                if detected_lang and detected_lang != 'unknown':
                    self.source_language_detected(detected_lang)
                else:
                    self.detection_failed()
                    
            except Exception as e:
                print(f"Language detection error: {e}")
                self.detection_failed()
        
        threading.Thread(target=detect_thread, daemon=True).start()
    
    def source_language_detected(self, language):
        """Handle successful language detection"""
        self.current_source_lang = language
        self.update_language_display()
        
        supported_langs = self.translation_service.get_supported_languages()
        lang_name = supported_langs.get(language, language)
        self["status"].setText(f"Detected source language: {lang_name}")
    
    def detection_failed(self):
        """Handle failed language detection"""
        self["status"].setText("Could not detect source language")
    
    def update_subtitle_list(self):
        """Update subtitle list display"""
        if not self.subtitle_entries:
            self["subtitle_list"].setList([])
            return
        
        display_items = []
        for i, entry in enumerate(self.subtitle_entries[:50]):  # Show first 50
            text_preview = entry.text[:60] + "..." if len(entry.text) > 60 else entry.text
            text_preview = text_preview.replace('\n', ' ')
            
            # Show translation status
            status = "✓" if i < len(self.translated_entries) else "○"
            
            display_text = f"{status} {i+1:3d}. {text_preview}"
            display_items.append(display_text)
        
        self["subtitle_list"].setList(display_items)
        
        if len(self.subtitle_entries) > 50:
            self["list_label"].setText(f"Subtitle Entries: (Showing first 50 of {len(self.subtitle_entries)})")
        else:
            self["list_label"].setText(f"Subtitle Entries: ({len(self.subtitle_entries)} total)")
    
    def list_up(self):
        """Move selection up in subtitle list"""
        self["subtitle_list"].up()
        self.update_preview()
    
    def list_down(self):
        """Move selection down in subtitle list"""
        self["subtitle_list"].down()
        self.update_preview()
    
    def update_preview(self):
        """Update translation preview"""
        selection_idx = self["subtitle_list"].getSelectionIndex()
        
        if 0 <= selection_idx < len(self.subtitle_entries):
            entry = self.subtitle_entries[selection_idx]
            self["original_text"].setText(entry.text)
            
            # Show translated version if available
            if selection_idx < len(self.translated_entries):
                translated_entry = self.translated_entries[selection_idx]
                self["translated_text"].setText(translated_entry.text)
            else:
                self["translated_text"].setText("(Translation not available)")
        else:
            self["original_text"].setText("")
            self["translated_text"].setText("")
    
    def select_languages(self):
        """Select source and target languages"""
        if not self.translation_service:
            self.session.open(MessageBox, "Translation service not available", MessageBox.TYPE_ERROR)
            return
        
        # Create language selection menu
        choices = [
            ("source", "Select Source Language"),
            ("target", "Select Target Language"),
            ("swap", "Swap Source ↔ Target")
        ]
        
        def language_action_selected(choice):
            if choice:
                action = choice[0]
                if action == "source":
                    self.select_source_language()
                elif action == "target":
                    self.select_target_language()
                elif action == "swap":
                    self.swap_languages()
        
        self.session.openWithCallback(language_action_selected, ChoiceBox,
                                     title="Language Options", list=choices)
    
    def select_source_language(self):
        """Select source language"""
        supported_langs = self.translation_service.get_supported_languages()
        
        choices = [("auto", "Auto-detect")]
        choices.extend([(code, name) for code, name in sorted(supported_langs.items())])
        
        def source_selected(choice):
            if choice:
                self.current_source_lang = choice[0]
                self.update_language_display()
                # Clear existing translations as language changed
                self.translated_entries = []
                self.update_subtitle_list()
        
        self.session.openWithCallback(source_selected, ChoiceBox,
                                     title="Select Source Language", list=choices)
    
    def select_target_language(self):
        """Select target language"""
        supported_langs = self.translation_service.get_supported_languages()
        
        choices = [(code, name) for code, name in sorted(supported_langs.items())]
        
        def target_selected(choice):
            if choice:
                self.current_target_lang = choice[0]
                self.update_language_display()
                # Clear existing translations as language changed
                self.translated_entries = []
                self.update_subtitle_list()
        
        self.session.openWithCallback(target_selected, ChoiceBox,
                                     title="Select Target Language", list=choices)
    
    def swap_languages(self):
        """Swap source and target languages"""
        if self.current_source_lang == 'auto':
            self.session.open(MessageBox, "Cannot swap with auto-detect source", MessageBox.TYPE_WARNING)
            return
        
        self.current_source_lang, self.current_target_lang = self.current_target_lang, self.current_source_lang
        self.update_language_display()
        # Clear existing translations as languages changed
        self.translated_entries = []
        self.update_subtitle_list()
    
    def preview_translation(self):
        """Preview translation for selected entry"""
        selection_idx = self["subtitle_list"].getSelectionIndex()
        
        if not (0 <= selection_idx < len(self.subtitle_entries)):
            self.session.open(MessageBox, "No subtitle entry selected", MessageBox.TYPE_WARNING)
            return
        
        if not self.translation_service:
            self.session.open(MessageBox, "Translation service not available", MessageBox.TYPE_ERROR)
            return
        
        entry = self.subtitle_entries[selection_idx]
        
        self["status"].setText("Translating preview...")
        self["progress"].show()
        
        def translate_thread():
            try:
                translated_text = self.translation_service.translate_text(
                    entry.text,
                    self.current_target_lang,
                    self.current_source_lang
                )
                
                self.preview_translation_completed(translated_text)
                
            except Exception as e:
                self.preview_translation_failed(str(e))
        
        threading.Thread(target=translate_thread, daemon=True).start()
    
    def preview_translation_completed(self, translated_text):
        """Handle completed preview translation"""
        self["progress"].hide()
        self["translated_text"].setText(translated_text)
        self["status"].setText("Preview translation completed")
    
    def preview_translation_failed(self, error_msg):
        """Handle failed preview translation"""
        self["progress"].hide()
        self["status"].setText("Preview translation failed")
        self.session.open(MessageBox, f"Translation failed: {error_msg}", MessageBox.TYPE_ERROR)
    
    def start_translation(self):
        """Start full subtitle translation"""
        if not self.subtitle_entries:
            self.session.open(MessageBox, "No subtitles to translate", MessageBox.TYPE_WARNING)
            return
        
        if not self.translation_service:
            self.session.open(MessageBox, "Translation service not available", MessageBox.TYPE_ERROR)
            return
        
        # Confirm translation
        msg = f"Translate {len(self.subtitle_entries)} subtitle entries?\n\nFrom: {self['source_lang'].getText()}\nTo: {self['target_lang'].getText()}"
        
        def confirm_translation(confirmed):
            if confirmed:
                self.perform_full_translation()
        
        self.session.openWithCallback(confirm_translation, MessageBox, msg, MessageBox.TYPE_YESNO)
    
    def perform_full_translation(self):
        """Perform translation of all subtitle entries"""
        self["progress"].show()
        self["status"].setText("Translating subtitles...")
        
        def translate_thread():
            try:
                self.translated_entries = self.translation_service.translate_subtitle_entries(
                    self.subtitle_entries,
                    self.current_target_lang,
                    self.current_source_lang
                )
                
                self.translation_completed()
                
            except Exception as e:
                self.translation_failed(str(e))
        
        threading.Thread(target=translate_thread, daemon=True).start()
    
    def translation_completed(self):
        """Handle completed translation"""
        self["progress"].hide()
        self["status"].setText(f"Translation completed ({len(self.translated_entries)} entries)")
        
        # Update UI
        self.update_subtitle_list()
        self.update_preview()
        
        # Show completion message
        msg = f"Translation completed successfully!\n\n{len(self.translated_entries)} entries translated\n\nWould you like to save the translated subtitles?"
        
        def save_prompt(confirmed):
            if confirmed:
                self.save_translation()
        
        self.session.openWithCallback(save_prompt, MessageBox, msg, MessageBox.TYPE_YESNO)
    
    def translation_failed(self, error_msg):
        """Handle failed translation"""
        self["progress"].hide()
        self["status"].setText("Translation failed")
        self.session.open(MessageBox, f"Translation failed: {error_msg}", MessageBox.TYPE_ERROR)
    
    def save_translation(self):
        """Save translated subtitles"""
        if not self.translated_entries:
            self.session.open(MessageBox, "No translated subtitles to save", MessageBox.TYPE_WARNING)
            return
        
        # Suggest filename
        if self.subtitle_file:
            base_name = os.path.splitext(self.subtitle_file)[0]
            target_lang_name = self["target_lang"].getText().lower().replace(' ', '_')
            suggested_name = f"{base_name}_{target_lang_name}.srt"
        else:
            suggested_name = f"translated_subtitles_{self.current_target_lang}.srt"
        
        def save_location_selected(file_path):
            if file_path:
                self.save_translation_to_file(file_path)
        
        from Screens.LocationBox import LocationBox
        self.session.openWithCallback(save_location_selected, LocationBox,
                                     currDir="/tmp/", title="Save translated subtitles as...",
                                     filename=suggested_name, minFree=1024)
    
    def save_translation_to_file(self, file_path):
        """Save translated subtitles to file"""
        try:
            from ..core.parser import SubtitleParser
            
            parser = SubtitleParser()
            if parser.save_srt(self.translated_entries, file_path):
                self["status"].setText(f"Saved: {os.path.basename(file_path)}")
                
                msg = f"Translated subtitles saved successfully:\n{file_path}"
                self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, title="Save Successful")
            else:
                self.session.open(MessageBox, "Failed to save translated subtitles", MessageBox.TYPE_ERROR)
                
        except Exception as e:
            self["status"].setText("Save failed")
            self.session.open(MessageBox, f"Save failed: {e}", MessageBox.TYPE_ERROR)