#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle Browser Screen
Provides interface for browsing and managing local subtitle files
"""

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.FileList import FileList
from Components.MenuList import MenuList
import os
import datetime


class SubtitleBrowserScreen(Screen):
    """Screen for browsing local subtitle files"""
    
    skin = """
        <screen position="center,center" size="900,650" title="Subtitle Browser">
            <widget name="title" position="20,20" size="860,30" font="Regular;22" halign="center" />
            <widget name="path_label" position="20,60" size="100,25" font="Regular;16" />
            <widget name="current_path" position="130,60" size="730,25" font="Regular;16" />
            
            <!-- File list -->
            <widget name="file_list" position="20,100" size="860,400" scrollbarMode="showOnDemand" />
            
            <!-- File info panel -->
            <widget name="info_label" position="20,510" size="860,20" font="Regular;16" />
            <widget name="file_info" position="20,535" size="860,60" font="Regular;14" backgroundColor="#2d2d2d" />
            
            <!-- Status and controls -->
            <widget name="status" position="20,605" size="860,20" font="Regular;14" />
            
            <!-- Action buttons -->
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,625" size="140,20" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="170,625" size="140,20" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="320,625" size="140,20" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="470,625" size="140,20" alphatest="on" />
            <widget name="key_red" position="20,625" size="140,20" font="Regular;14" halign="center" valign="center" />
            <widget name="key_green" position="170,625" size="140,20" font="Regular;14" halign="center" valign="center" />
            <widget name="key_yellow" position="320,625" size="140,20" font="Regular;14" halign="center" valign="center" />
            <widget name="key_blue" position="470,625" size="140,20" font="Regular;14" halign="center" valign="center" />
        </screen>
    """
    
    def __init__(self, session, initial_path="/tmp/"):
        Screen.__init__(self, session)
        self.session = session
        self.current_path = initial_path
        self.subtitle_extensions = ['.srt', '.ass', '.ssa', '.vtt', '.sub']
        
        # Initialize UI components
        self["title"] = Label("Subtitle File Browser")
        self["path_label"] = Label("Path:")
        self["current_path"] = Label("")
        self["info_label"] = Label("File Information:")
        self["file_info"] = Label("")
        self["status"] = Label("Ready")
        
        # Button labels
        self["key_red"] = Label("Back")
        self["key_green"] = Label("Open")
        self["key_yellow"] = Label("Actions")
        self["key_blue"] = Label("Sync")
        
        # File list
        self["file_list"] = MenuList([])
        
        # Action mappings
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.open_selected,
                "cancel": self.close,
                "red": self.go_back,
                "green": self.open_selected,
                "yellow": self.show_actions,
                "blue": self.open_sync_tool,
                "up": self.list_up,
                "down": self.list_down
            },
            -1
        )
        
        # Load initial directory
        self.refresh_file_list()
    
    def refresh_file_list(self):
        """Refresh the file list for current directory"""
        try:
            if not os.path.exists(self.current_path):
                self.current_path = "/tmp/"
            
            self["current_path"].setText(self.current_path)
            
            # Get directory contents
            items = []
            
            # Add parent directory entry if not at root
            if self.current_path != "/":
                items.append(("📁 ..", "directory", ".."))
            
            # Get files and directories
            try:
                entries = os.listdir(self.current_path)
                entries.sort()
                
                # Separate directories and files
                directories = []
                subtitle_files = []
                other_files = []
                
                for entry in entries:
                    full_path = os.path.join(self.current_path, entry)
                    
                    if os.path.isdir(full_path):
                        directories.append(entry)
                    elif os.path.isfile(full_path):
                        _, ext = os.path.splitext(entry.lower())
                        if ext in self.subtitle_extensions:
                            subtitle_files.append(entry)
                        else:
                            other_files.append(entry)
                
                # Add to display list
                for directory in directories:
                    items.append((f"📁 {directory}", "directory", directory))
                
                for subtitle in subtitle_files:
                    items.append((f"📄 {subtitle}", "subtitle", subtitle))
                
                for other_file in other_files:
                    items.append((f"📄 {other_file}", "file", other_file))
                
            except PermissionError:
                self["status"].setText("Permission denied")
                items.append(("❌ Permission denied", "error", ""))
            except Exception as e:
                self["status"].setText(f"Error reading directory: {e}")
                items.append((f"❌ Error: {e}", "error", ""))
            
            # Update file list
            self["file_list"].setList([item[0] for item in items])
            self.file_items = items
            
            # Update status
            subtitle_count = len([item for item in items if item[1] == "subtitle"])
            self["status"].setText(f"Found {subtitle_count} subtitle files")
            
            # Update file info for first item
            if items:
                self.update_file_info(0)
            else:
                self["file_info"].setText("Directory is empty")
            
        except Exception as e:
            self["status"].setText(f"Error: {e}")
            print(f"File list refresh error: {e}")
    
    def list_up(self):
        """Move selection up"""
        self["file_list"].up()
        self.update_file_info()
    
    def list_down(self):
        """Move selection down"""
        self["file_list"].down()
        self.update_file_info()
    
    def update_file_info(self, index=None):
        """Update file information display"""
        if index is None:
            index = self["file_list"].getSelectionIndex()
        
        if not (0 <= index < len(self.file_items)):
            self["file_info"].setText("")
            return
        
        item = self.file_items[index]
        file_name = item[2]
        file_type = item[1]
        
        if file_type == "error" or file_name == "..":
            self["file_info"].setText("")
            return
        
        try:
            full_path = os.path.join(self.current_path, file_name)
            
            if not os.path.exists(full_path):
                self["file_info"].setText("File not found")
                return
            
            # Get file statistics
            stat = os.stat(full_path)
            
            # Format file size
            size = stat.st_size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            # Format modification time
            mod_time = datetime.datetime.fromtimestamp(stat.st_mtime)
            mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M:%S")
            
            if file_type == "directory":
                try:
                    item_count = len(os.listdir(full_path))
                    info_text = f"Directory: {item_count} items\nModified: {mod_time_str}"
                except:
                    info_text = f"Directory\nModified: {mod_time_str}"
            elif file_type == "subtitle":
                # Get subtitle-specific information
                info_text = f"Subtitle File\nSize: {size_str}\nModified: {mod_time_str}"
                
                # Try to get subtitle entry count
                try:
                    entry_count = self.get_subtitle_entry_count(full_path)
                    if entry_count > 0:
                        info_text += f"\nEntries: {entry_count}"
                except:
                    pass
            else:
                info_text = f"File\nSize: {size_str}\nModified: {mod_time_str}"
            
            self["file_info"].setText(info_text)
            
        except Exception as e:
            self["file_info"].setText(f"Error getting file info: {e}")
    
    def get_subtitle_entry_count(self, file_path):
        """Get number of subtitle entries in file"""
        try:
            from ..core.parser import SubtitleParser
            
            parser = SubtitleParser()
            entries = parser.parse_file(file_path)
            return len(entries)
        except:
            return 0
    
    def open_selected(self):
        """Open selected file or directory"""
        selection_idx = self["file_list"].getSelectionIndex()
        
        if not (0 <= selection_idx < len(self.file_items)):
            return
        
        item = self.file_items[selection_idx]
        file_name = item[2]
        file_type = item[1]
        
        if file_type == "directory":
            if file_name == "..":
                self.go_up_directory()
            else:
                self.enter_directory(file_name)
        elif file_type == "subtitle":
            self.open_subtitle_file(file_name)
        else:
            self["status"].setText("Cannot open this file type")
    
    def go_back(self):
        """Go back to parent directory or exit"""
        if self.current_path == "/":
            self.close()
        else:
            self.go_up_directory()
    
    def go_up_directory(self):
        """Go to parent directory"""
        parent_path = os.path.dirname(self.current_path.rstrip('/'))
        if not parent_path:
            parent_path = "/"
        
        self.current_path = parent_path
        self.refresh_file_list()
    
    def enter_directory(self, directory_name):
        """Enter selected directory"""
        new_path = os.path.join(self.current_path, directory_name)
        
        if os.path.isdir(new_path):
            self.current_path = new_path
            self.refresh_file_list()
        else:
            self["status"].setText("Directory not found")
    
    def open_subtitle_file(self, file_name):
        """Open subtitle file with actions"""
        full_path = os.path.join(self.current_path, file_name)
        
        choices = [
            ("view", "View Subtitle Content"),
            ("sync", "Open Synchronization Tool"),
            ("translate", "Translate Subtitles"),
            ("info", "Show Detailed Information")
        ]
        
        def action_selected(choice):
            if choice:
                action = choice[0]
                if action == "view":
                    self.view_subtitle_content(full_path)
                elif action == "sync":
                    self.open_sync_tool_with_file(full_path)
                elif action == "translate":
                    self.open_translation_tool(full_path)
                elif action == "info":
                    self.show_subtitle_info(full_path)
        
        self.session.openWithCallback(action_selected, ChoiceBox,
                                     title=f"Actions for: {file_name}", list=choices)
    
    def view_subtitle_content(self, file_path):
        """View subtitle file content"""
        try:
            from ..core.parser import SubtitleParser
            
            parser = SubtitleParser()
            entries = parser.parse_file(file_path)
            
            if not entries:
                self.session.open(MessageBox, "No subtitle entries found", MessageBox.TYPE_INFO)
                return
            
            # Show first few entries
            content = f"Subtitle File: {os.path.basename(file_path)}\n"
            content += f"Total Entries: {len(entries)}\n\n"
            
            for i, entry in enumerate(entries[:10]):  # Show first 10
                start_time = self.format_time(entry.start_time)
                end_time = self.format_time(entry.end_time)
                content += f"{i+1}. {start_time} --> {end_time}\n"
                content += f"   {entry.text}\n\n"
            
            if len(entries) > 10:
                content += f"... and {len(entries) - 10} more entries"
            
            self.session.open(MessageBox, content, MessageBox.TYPE_INFO, title="Subtitle Content")
            
        except Exception as e:
            self.session.open(MessageBox, f"Error reading subtitle file:\n{e}", MessageBox.TYPE_ERROR)
    
    def show_actions(self):
        """Show available actions"""
        choices = [
            ("refresh", "Refresh File List"),
            ("goto", "Go to Directory"),
            ("new_folder", "Create Folder"),
            ("cleanup", "Clean Up Downloads")
        ]
        
        def action_selected(choice):
            if choice:
                action = choice[0]
                if action == "refresh":
                    self.refresh_file_list()
                elif action == "goto":
                    self.goto_directory()
                elif action == "new_folder":
                    self.create_folder()
                elif action == "cleanup":
                    self.cleanup_downloads()
        
        self.session.openWithCallback(action_selected, ChoiceBox,
                                     title="Browser Actions", list=choices)
    
    def goto_directory(self):
        """Go to specific directory"""
        def path_entered(path):
            if path and os.path.isdir(path):
                self.current_path = path
                self.refresh_file_list()
            elif path:
                self.session.open(MessageBox, "Directory not found", MessageBox.TYPE_ERROR)
        
        from Screens.InputBox import InputBox
        self.session.openWithCallback(path_entered, InputBox,
                                     title="Enter directory path:", text=self.current_path)
    
    def create_folder(self):
        """Create new folder"""
        def folder_name_entered(name):
            if name:
                new_path = os.path.join(self.current_path, name)
                try:
                    os.makedirs(new_path, exist_ok=True)
                    self.refresh_file_list()
                    self["status"].setText(f"Created folder: {name}")
                except Exception as e:
                    self.session.open(MessageBox, f"Failed to create folder:\n{e}", MessageBox.TYPE_ERROR)
        
        from Screens.InputBox import InputBox
        self.session.openWithCallback(folder_name_entered, InputBox,
                                     title="Enter folder name:", text="")
    
    def cleanup_downloads(self):
        """Clean up old download files"""
        # This is a placeholder for cleanup functionality
        self.session.open(MessageBox, "Cleanup functionality will be implemented", MessageBox.TYPE_INFO)
    
    def open_sync_tool(self):
        """Open sync tool with selected subtitle"""
        selection_idx = self["file_list"].getSelectionIndex()
        
        if not (0 <= selection_idx < len(self.file_items)):
            self.session.open(MessageBox, "No subtitle file selected", MessageBox.TYPE_WARNING)
            return
        
        item = self.file_items[selection_idx]
        
        if item[1] != "subtitle":
            self.session.open(MessageBox, "Please select a subtitle file", MessageBox.TYPE_WARNING)
            return
        
        full_path = os.path.join(self.current_path, item[2])
        self.open_sync_tool_with_file(full_path)
    
    def open_sync_tool_with_file(self, file_path):
        """Open synchronization tool with specific file"""
        try:
            from .sync_screen import SubtitleSyncScreen
            self.session.open(SubtitleSyncScreen, subtitle_file=file_path)
        except ImportError:
            self.session.open(MessageBox, "Sync tool not available", MessageBox.TYPE_ERROR)
    
    def open_translation_tool(self, file_path):
        """Open translation tool with specific file"""
        try:
            from .translation_screen import TranslationScreen
            self.session.open(TranslationScreen, subtitle_file=file_path)
        except ImportError:
            self.session.open(MessageBox, "Translation tool not available", MessageBox.TYPE_ERROR)
    
    def show_subtitle_info(self, file_path):
        """Show detailed subtitle information"""
        try:
            from ..core.parser import SubtitleParser
            
            parser = SubtitleParser()
            entries = parser.parse_file(file_path)
            
            if not entries:
                self.session.open(MessageBox, "No subtitle entries found", MessageBox.TYPE_INFO)
                return
            
            # Calculate statistics
            total_duration = 0
            total_characters = 0
            
            for entry in entries:
                total_duration += entry.duration()
                total_characters += len(entry.text)
            
            # Format statistics
            total_duration_str = self.format_time(total_duration)
            avg_duration = total_duration / len(entries) if entries else 0
            avg_duration_str = f"{avg_duration / 1000:.1f}s"
            avg_characters = total_characters / len(entries) if entries else 0
            
            # File information
            stat = os.stat(file_path)
            file_size = stat.st_size
            mod_time = datetime.datetime.fromtimestamp(stat.st_mtime)
            
            info_text = f"""
Subtitle File Information

File: {os.path.basename(file_path)}
Size: {file_size} bytes
Modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}

Subtitle Statistics:
Total Entries: {len(entries)}
Total Duration: {total_duration_str}
Average Entry Duration: {avg_duration_str}
Total Characters: {total_characters}
Average Characters per Entry: {avg_characters:.1f}

First Entry: {self.format_time(entries[0].start_time)} - {entries[0].text[:50]}...
Last Entry: {self.format_time(entries[-1].start_time)} - {entries[-1].text[:50]}...
            """
            
            self.session.open(MessageBox, info_text.strip(), MessageBox.TYPE_INFO, title="Subtitle Information")
            
        except Exception as e:
            self.session.open(MessageBox, f"Error analyzing subtitle file:\n{e}", MessageBox.TYPE_ERROR)
    
    @staticmethod
    def format_time(ms):
        """Format milliseconds as HH:MM:SS"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"