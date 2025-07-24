#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle Synchronization Screen
Provides tools for adjusting subtitle timing
"""

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Slider import Slider
from Components.Button import Button
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import threading


class SubtitleSyncScreen(Screen):
    """Screen for subtitle timing synchronization"""
    
    skin = """
        <screen position="center,center" size="900,650" title="Subtitle Synchronization">
            <widget name="title" position="20,20" size="860,30" font="Regular;22" halign="center" />
            <widget name="file_info" position="20,60" size="860,30" font="Regular;16" />
            
            <!-- Current subtitle display -->
            <widget name="current_sub" position="20,100" size="860,80" font="Regular;18" halign="center" valign="center" backgroundColor="#1e1e1e" />
            
            <!-- Timing controls -->
            <widget name="timing_label" position="20,200" size="200,25" font="Regular;16" />
            <widget name="timing_value" position="230,200" size="150,25" font="Regular;16" />
            <widget name="timing_slider" position="20,230" size="860,30" />
            
            <!-- Quick adjustment buttons -->
            <widget name="adjust_label" position="20,280" size="860,25" font="Regular;16" halign="center" />
            <ePixmap pixmap="skin_default/buttons/key_0.png" position="100,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_1.png" position="150,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_2.png" position="200,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_3.png" position="250,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_4.png" position="300,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_5.png" position="350,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_6.png" position="400,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_7.png" position="450,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_8.png" position="500,310" size="35,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/key_9.png" position="550,310" size="35,25" alphatest="on" />
            
            <widget name="key_help" position="20,345" size="860,40" font="Regular;14" halign="center" />
            
            <!-- Subtitle list -->
            <widget name="subtitle_list" position="20,400" size="860,180" scrollbarMode="showOnDemand" />
            
            <!-- Status and controls -->
            <widget name="status" position="20,590" size="860,25" font="Regular;14" />
            
            <!-- Action buttons -->
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,620" size="140,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="170,620" size="140,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="320,620" size="140,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="470,620" size="140,25" alphatest="on" />
            <widget name="key_red" position="20,620" size="140,25" font="Regular;16" halign="center" valign="center" />
            <widget name="key_green" position="170,620" size="140,25" font="Regular;16" halign="center" valign="center" />
            <widget name="key_yellow" position="320,620" size="140,25" font="Regular;16" halign="center" valign="center" />
            <widget name="key_blue" position="470,620" size="140,25" font="Regular;16" halign="center" valign="center" />
        </screen>
    """
    
    def __init__(self, session, subtitle_file=None, video_file=None):
        Screen.__init__(self, session)
        self.session = session
        self.subtitle_file = subtitle_file
        self.video_file = video_file
        self.subtitle_entries = []
        self.current_offset = 0  # in milliseconds
        self.selected_entry_index = 0
        
        # Initialize UI components
        self["title"] = Label("Subtitle Synchronization Tool")
        self["file_info"] = Label("")
        self["current_sub"] = Label("")
        self["timing_label"] = Label("Timing Offset:")
        self["timing_value"] = Label("0.000s")
        self["timing_slider"] = Slider(-10000, 10000)  # -10 to +10 seconds
        self["adjust_label"] = Label("Quick Adjust: [1-5] -5s to -0.1s | [6-0] +0.1s to +5s")
        self["key_help"] = Label("Use number keys for quick adjustment, Left/Right for fine tuning")
        self["subtitle_list"] = MenuList([])
        self["status"] = Label("Ready")
        
        # Button labels
        self["key_red"] = Label("Back")
        self["key_green"] = Label("Save")
        self["key_yellow"] = Label("Load")
        self["key_blue"] = Label("Reset")
        
        # Action mappings
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions", "NumberActions"],
            {
                "ok": self.show_entry_details,
                "cancel": self.close,
                "red": self.close,
                "green": self.save_subtitles,
                "yellow": self.load_subtitle_file,
                "blue": self.reset_timing,
                "up": self.list_up,
                "down": self.list_down,
                "left": self.fine_adjust_backward,
                "right": self.fine_adjust_forward,
                "0": lambda: self.quick_adjust(5000),
                "1": lambda: self.quick_adjust(-5000),
                "2": lambda: self.quick_adjust(-1000),
                "3": lambda: self.quick_adjust(-500),
                "4": lambda: self.quick_adjust(-100),
                "5": lambda: self.quick_adjust(-100),
                "6": lambda: self.quick_adjust(100),
                "7": lambda: self.quick_adjust(500),
                "8": lambda: self.quick_adjust(1000),
                "9": lambda: self.quick_adjust(5000)
            },
            -1
        )
        
        # Load subtitle file if provided
        if self.subtitle_file:
            self.load_subtitle_file_internal(self.subtitle_file)
        
        self.update_display()
    
    def update_file_info(self):
        """Update file information display"""
        info_parts = []
        
        if self.subtitle_file:
            sub_name = os.path.basename(self.subtitle_file)
            info_parts.append(f"Subtitle: {sub_name}")
        
        if self.video_file:
            vid_name = os.path.basename(self.video_file)
            info_parts.append(f"Video: {vid_name}")
        
        if not info_parts:
            info_parts.append("No files loaded")
        
        self["file_info"].setText(" | ".join(info_parts))
    
    def load_subtitle_file(self):
        """Load subtitle file via file browser"""
        def file_selected(file_path):
            if file_path and os.path.exists(file_path):
                self.load_subtitle_file_internal(file_path)
        
        from Screens.LocationBox import LocationBox
        self.session.openWithCallback(file_selected, LocationBox,
                                     currDir="/tmp/", title="Select subtitle file")
    
    def load_subtitle_file_internal(self, file_path):
        """Load and parse subtitle file"""
        try:
            from ..core.parser import SubtitleParser
            
            parser = SubtitleParser()
            self.subtitle_entries = parser.parse_file(file_path)
            self.subtitle_file = file_path
            
            if self.subtitle_entries:
                self["status"].setText(f"Loaded {len(self.subtitle_entries)} subtitle entries")
                self.update_subtitle_list()
                self.update_display()
            else:
                self["status"].setText("No subtitle entries found in file")
                
        except Exception as e:
            self["status"].setText(f"Error loading subtitle: {e}")
            self.session.open(MessageBox, f"Failed to load subtitle file:\n{e}", MessageBox.TYPE_ERROR)
    
    def update_subtitle_list(self):
        """Update the subtitle list display"""
        if not self.subtitle_entries:
            self["subtitle_list"].setList([])
            return
        
        display_items = []
        for i, entry in enumerate(self.subtitle_entries[:100]):  # Show first 100 entries
            start_time = self.format_time(entry.start_time + self.current_offset)
            end_time = self.format_time(entry.end_time + self.current_offset)
            text_preview = entry.text[:50] + "..." if len(entry.text) > 50 else entry.text
            text_preview = text_preview.replace('\n', ' ')
            
            display_text = f"{i+1:3d}. {start_time} --> {end_time} | {text_preview}"
            display_items.append(display_text)
        
        self["subtitle_list"].setList(display_items)
        
        # Show total count if there are more entries
        if len(self.subtitle_entries) > 100:
            self["status"].setText(f"Showing first 100 of {len(self.subtitle_entries)} entries")
    
    def update_display(self):
        """Update all display elements"""
        self.update_file_info()
        self.update_timing_display()
        self.update_current_subtitle()
        self.update_subtitle_list()
    
    def update_timing_display(self):
        """Update timing offset display"""
        offset_seconds = self.current_offset / 1000.0
        self["timing_value"].setText(f"{offset_seconds:+.3f}s")
        
        # Update slider position
        slider_value = max(-10000, min(10000, self.current_offset))
        self["timing_slider"].setValue(slider_value)
    
    def update_current_subtitle(self):
        """Update current subtitle preview"""
        if not self.subtitle_entries:
            self["current_sub"].setText("No subtitles loaded")
            return
        
        if 0 <= self.selected_entry_index < len(self.subtitle_entries):
            entry = self.subtitle_entries[self.selected_entry_index]
            start_time = self.format_time(entry.start_time + self.current_offset)
            end_time = self.format_time(entry.end_time + self.current_offset)
            
            display_text = f"{start_time} --> {end_time}\n{entry.text}"
            self["current_sub"].setText(display_text)
        else:
            self["current_sub"].setText("No subtitle selected")
    
    def list_up(self):
        """Move up in subtitle list"""
        self["subtitle_list"].up()
        self.selected_entry_index = self["subtitle_list"].getSelectionIndex()
        self.update_current_subtitle()
    
    def list_down(self):
        """Move down in subtitle list"""
        self["subtitle_list"].down()
        self.selected_entry_index = self["subtitle_list"].getSelectionIndex()
        self.update_current_subtitle()
    
    def quick_adjust(self, offset_ms):
        """Quick timing adjustment"""
        self.current_offset += offset_ms
        self.update_display()
        
        offset_seconds = offset_ms / 1000.0
        action = "forward" if offset_ms > 0 else "backward"
        self["status"].setText(f"Adjusted {abs(offset_seconds):.3f}s {action}")
    
    def fine_adjust_forward(self):
        """Fine adjustment forward (100ms)"""
        self.quick_adjust(100)
    
    def fine_adjust_backward(self):
        """Fine adjustment backward (100ms)"""
        self.quick_adjust(-100)
    
    def reset_timing(self):
        """Reset timing offset to zero"""
        self.current_offset = 0
        self.update_display()
        self["status"].setText("Timing reset to original")
    
    def show_entry_details(self):
        """Show detailed information about selected entry"""
        if not self.subtitle_entries or self.selected_entry_index >= len(self.subtitle_entries):
            return
        
        entry = self.subtitle_entries[self.selected_entry_index]
        
        original_start = self.format_time(entry.start_time)
        original_end = self.format_time(entry.end_time)
        adjusted_start = self.format_time(entry.start_time + self.current_offset)
        adjusted_end = self.format_time(entry.end_time + self.current_offset)
        
        details = f"""
Subtitle Entry #{entry.index}

Original Timing:
{original_start} --> {original_end}

Adjusted Timing:
{adjusted_start} --> {adjusted_end}

Duration: {entry.duration() / 1000.0:.3f}s

Text:
{entry.text}
        """
        
        self.session.open(MessageBox, details.strip(), MessageBox.TYPE_INFO, title="Subtitle Details")
    
    def save_subtitles(self):
        """Save synchronized subtitles"""
        if not self.subtitle_entries:
            self.session.open(MessageBox, "No subtitles to save", MessageBox.TYPE_WARNING)
            return
        
        def save_location_selected(file_path):
            if file_path:
                self.save_subtitles_to_file(file_path)
        
        # Suggest filename
        if self.subtitle_file:
            base_name = os.path.splitext(self.subtitle_file)[0]
            suggested_name = f"{base_name}_synced.srt"
        else:
            suggested_name = "synchronized_subtitles.srt"
        
        from Screens.LocationBox import LocationBox
        self.session.openWithCallback(save_location_selected, LocationBox,
                                     currDir="/tmp/", title="Save synchronized subtitles as...",
                                     filename=suggested_name, minFree=1024)
    
    def save_subtitles_to_file(self, file_path):
        """Save subtitles to specified file"""
        try:
            from ..core.parser import SubtitleParser
            
            # Apply timing offset to all entries
            adjusted_entries = []
            for entry in self.subtitle_entries:
                adjusted_entry = SubtitleEntry(
                    entry.index,
                    entry.start_time + self.current_offset,
                    entry.end_time + self.current_offset,
                    entry.text
                )
                adjusted_entries.append(adjusted_entry)
            
            # Save to file
            parser = SubtitleParser()
            if parser.save_srt(adjusted_entries, file_path):
                self["status"].setText(f"Saved to: {os.path.basename(file_path)}")
                
                msg = f"Subtitles saved successfully to:\n{file_path}\n\nTiming offset applied: {self.current_offset/1000.0:+.3f}s"
                self.session.open(MessageBox, msg, MessageBox.TYPE_INFO, title="Save Successful")
            else:
                self.session.open(MessageBox, "Failed to save subtitle file", MessageBox.TYPE_ERROR)
                
        except Exception as e:
            self["status"].setText("Save failed")
            self.session.open(MessageBox, f"Save failed:\n{e}", MessageBox.TYPE_ERROR)
    
    @staticmethod
    def format_time(ms):
        """Format milliseconds as HH:MM:SS.mmm"""
        if ms < 0:
            ms = 0
        
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        milliseconds = ms % 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"


# Import SubtitleEntry for the sync screen
from ..core.parser import SubtitleEntry