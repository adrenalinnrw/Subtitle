#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle Search Screen
Provides UI for searching and downloading subtitles
"""

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.InputBox import InputBox
from Screens.ChoiceBox import ChoiceBox
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ProgressBar import ProgressBar
from Components.FileList import FileList
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
import os
import threading


class SubtitleSearchScreen(Screen):
    """Screen for searching and downloading subtitles"""
    
    skin = """
        <screen position="center,center" size="800,600" title="Subtitle Search">
            <widget name="title" position="20,20" size="760,30" font="Regular;22" halign="center" />
            <widget name="search_info" position="20,60" size="760,30" font="Regular;16" />
            <widget name="results" position="20,100" size="760,400" scrollbarMode="showOnDemand" />
            <widget name="status" position="20,510" size="760,30" font="Regular;14" />
            <widget name="progress" position="20,550" size="760,20" />
            <ePixmap pixmap="skin_default/buttons/red.png" position="20,575" size="140,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/green.png" position="170,575" size="140,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/yellow.png" position="320,575" size="140,25" alphatest="on" />
            <ePixmap pixmap="skin_default/buttons/blue.png" position="470,575" size="140,25" alphatest="on" />
            <widget name="key_red" position="20,575" size="140,25" font="Regular;16" halign="center" valign="center" />
            <widget name="key_green" position="170,575" size="140,25" font="Regular;16" halign="center" valign="center" />
            <widget name="key_yellow" position="320,575" size="140,25" font="Regular;16" halign="center" valign="center" />
            <widget name="key_blue" position="470,575" size="140,25" font="Regular;16" halign="center" valign="center" />
        </screen>
    """
    
    def __init__(self, session, video_file=None):
        Screen.__init__(self, session)
        self.session = session
        self.video_file = video_file
        self.search_results = []
        self.searcher = None
        
        # Initialize UI components
        self["title"] = Label("Subtitle Search")
        self["search_info"] = Label("Enter search query or select video file")
        self["status"] = Label("Ready")
        self["progress"] = ProgressBar()
        self["progress"].hide()
        
        # Button labels
        self["key_red"] = Label("Back")
        self["key_green"] = Label("Search")
        self["key_yellow"] = Label("Browse")
        self["key_blue"] = Label("Download")
        
        # Results list
        self["results"] = MenuList([])
        
        # Action mappings
        self["actions"] = ActionMap(
            ["OkCancelActions", "ColorActions", "DirectionActions"],
            {
                "ok": self.download_selected,
                "cancel": self.close,
                "red": self.close,
                "green": self.start_search,
                "yellow": self.browse_video,
                "blue": self.download_selected,
                "up": self.results_up,
                "down": self.results_down
            },
            -1
        )
        
        # Initialize searcher
        self.init_searcher()
        
        # Auto-search if video file provided
        if self.video_file:
            self.update_search_info()
            self.auto_search()
    
    def init_searcher(self):
        """Initialize subtitle searcher"""
        try:
            from ..config.settings import SettingsManager
            from ..core.search import SubtitleSearcher
            
            settings = SettingsManager()
            self.searcher = SubtitleSearcher(settings)
            
        except Exception as e:
            self["status"].setText(f"Error initializing searcher: {e}")
            print(f"Searcher init error: {e}")
    
    def update_search_info(self):
        """Update search information display"""
        if self.video_file:
            filename = os.path.basename(self.video_file)
            self["search_info"].setText(f"Video: {filename}")
        else:
            self["search_info"].setText("No video file selected")
    
    def results_up(self):
        """Move selection up in results"""
        self["results"].up()
        self.update_selection_info()
    
    def results_down(self):
        """Move selection down in results"""
        self["results"].down()
        self.update_selection_info()
    
    def update_selection_info(self):
        """Update status with selection information"""
        selection_idx = self["results"].getSelectionIndex()
        if 0 <= selection_idx < len(self.search_results):
            result = self.search_results[selection_idx]
            info = f"Rating: {result.get('rating', 'N/A')} | Downloads: {result.get('download_count', 'N/A')} | Size: {result.get('size', 'N/A')}"
            self["status"].setText(info)
        else:
            self["status"].setText("Ready")
    
    def start_search(self):
        """Start subtitle search"""
        if not self.searcher:
            self.session.open(MessageBox, "Subtitle searcher not available", MessageBox.TYPE_ERROR)
            return
        
        # Get search method
        choices = []
        
        if self.video_file:
            choices.append(("hash", "Search by video file hash (most accurate)"))
            choices.append(("filename", "Search by filename"))
        
        choices.extend([
            ("manual", "Manual search (enter query)"),
            ("imdb", "Search by IMDB ID")
        ])
        
        def search_method_selected(choice):
            if choice:
                method = choice[0]
                if method == "hash":
                    self.search_by_hash()
                elif method == "filename":
                    self.search_by_filename()
                elif method == "manual":
                    self.manual_search()
                elif method == "imdb":
                    self.imdb_search()
        
        self.session.openWithCallback(search_method_selected, ChoiceBox, 
                                     title="Select search method:", list=choices)
    
    def auto_search(self):
        """Automatically search using video file"""
        if self.video_file and self.searcher:
            self.search_by_hash()
    
    def search_by_hash(self):
        """Search subtitles by video file hash"""
        if not self.video_file or not os.path.exists(self.video_file):
            self.session.open(MessageBox, "No valid video file selected", MessageBox.TYPE_ERROR)
            return
        
        self.perform_search(video_file=self.video_file)
    
    def search_by_filename(self):
        """Search subtitles by filename"""
        if not self.video_file:
            self.session.open(MessageBox, "No video file selected", MessageBox.TYPE_ERROR)
            return
        
        filename = os.path.splitext(os.path.basename(self.video_file))[0]
        self.perform_search(query=filename)
    
    def manual_search(self):
        """Manual search with user input"""
        def search_callback(query):
            if query:
                self.perform_search(query=query)
        
        self.session.openWithCallback(search_callback, InputBox, 
                                     title="Enter search query:", text="")
    
    def imdb_search(self):
        """Search by IMDB ID"""
        def imdb_callback(imdb_id):
            if imdb_id:
                # Validate IMDB ID format
                if not imdb_id.startswith('tt'):
                    imdb_id = 'tt' + imdb_id.lstrip('tt')
                self.perform_search(imdb_id=imdb_id)
        
        self.session.openWithCallback(imdb_callback, InputBox, 
                                     title="Enter IMDB ID (e.g., tt1234567):", text="tt")
    
    def perform_search(self, video_file=None, query=None, imdb_id=None, language="en"):
        """Perform the actual search"""
        if not self.searcher:
            return
        
        # Show progress
        self["progress"].show()
        self["status"].setText("Searching...")
        self["results"].setList([])
        
        # Perform search in thread to avoid blocking UI
        def search_thread():
            try:
                results = self.searcher.search_subtitles(
                    video_file=video_file,
                    imdb_id=imdb_id,
                    query=query,
                    language=language
                )
                
                # Update UI in main thread
                self.search_completed(results)
                
            except Exception as e:
                self.search_error(str(e))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def search_completed(self, results):
        """Handle search completion"""
        self["progress"].hide()
        
        if not results:
            self["status"].setText("No subtitles found")
            return
        
        self.search_results = results
        
        # Format results for display
        display_items = []
        for result in results:
            title = result.get('title', 'Unknown')
            language = result.get('language', 'en')
            rating = result.get('rating', 0)
            downloads = result.get('download_count', 0)
            source = result.get('source', 'unknown')
            
            display_text = f"{title} [{language}] ★{rating:.1f} ↓{downloads} ({source})"
            display_items.append(display_text)
        
        self["results"].setList(display_items)
        self["status"].setText(f"Found {len(results)} subtitles")
        
        if results:
            self.update_selection_info()
    
    def search_error(self, error_msg):
        """Handle search error"""
        self["progress"].hide()
        self["status"].setText(f"Search error: {error_msg}")
        self.session.open(MessageBox, f"Search failed: {error_msg}", MessageBox.TYPE_ERROR)
    
    def browse_video(self):
        """Browse for video file"""
        def file_selected(file_path):
            if file_path and os.path.exists(file_path):
                self.video_file = file_path
                self.update_search_info()
        
        from Screens.LocationBox import LocationBox
        self.session.openWithCallback(file_selected, LocationBox, 
                                     currDir="/media/", title="Select video file")
    
    def download_selected(self):
        """Download selected subtitle"""
        selection_idx = self["results"].getSelectionIndex()
        
        if not (0 <= selection_idx < len(self.search_results)):
            self.session.open(MessageBox, "No subtitle selected", MessageBox.TYPE_WARNING)
            return
        
        result = self.search_results[selection_idx]
        
        # Show download options
        choices = [
            ("download", "Download to default location"),
            ("save_as", "Save as..."),
            ("info", "Show subtitle information")
        ]
        
        def download_action_selected(choice):
            if choice:
                action = choice[0]
                if action == "download":
                    self.download_subtitle(result)
                elif action == "save_as":
                    self.save_subtitle_as(result)
                elif action == "info":
                    self.show_subtitle_info(result)
        
        self.session.openWithCallback(download_action_selected, ChoiceBox,
                                     title=f"Action for: {result.get('title', 'Unknown')}", 
                                     list=choices)
    
    def download_subtitle(self, subtitle_info):
        """Download subtitle to default location"""
        if not self.searcher:
            return
        
        self["progress"].show()
        self["status"].setText("Downloading...")
        
        def download_thread():
            try:
                file_path = self.searcher.download_subtitle(subtitle_info)
                
                if file_path:
                    self.download_success(file_path)
                else:
                    self.download_failed("Download failed")
                    
            except Exception as e:
                self.download_failed(str(e))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def save_subtitle_as(self, subtitle_info):
        """Save subtitle with custom filename"""
        def save_location_selected(file_path):
            if file_path:
                self.download_subtitle_to_path(subtitle_info, file_path)
        
        from Screens.LocationBox import LocationBox
        default_name = f"{subtitle_info.get('title', 'subtitle')}.{subtitle_info.get('format', 'srt')}"
        
        self.session.openWithCallback(save_location_selected, LocationBox,
                                     currDir="/tmp/", title="Save subtitle as...",
                                     filename=default_name, minFree=1024)
    
    def download_subtitle_to_path(self, subtitle_info, target_path):
        """Download subtitle to specific path"""
        if not self.searcher:
            return
        
        self["progress"].show()
        self["status"].setText("Downloading...")
        
        def download_thread():
            try:
                file_path = self.searcher.download_subtitle(subtitle_info, target_path)
                
                if file_path:
                    self.download_success(file_path)
                else:
                    self.download_failed("Download failed")
                    
            except Exception as e:
                self.download_failed(str(e))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_success(self, file_path):
        """Handle successful download"""
        self["progress"].hide()
        self["status"].setText(f"Downloaded: {os.path.basename(file_path)}")
        
        # Show success message with options
        msg = f"Subtitle downloaded successfully:\n{file_path}\n\nWhat would you like to do?"
        
        choices = [
            ("open", "Open subtitle file"),
            ("sync", "Open synchronization tool"),
            ("ok", "OK")
        ]
        
        def success_action(choice):
            if choice:
                action = choice[0]
                if action == "open":
                    self.open_subtitle_file(file_path)
                elif action == "sync":
                    self.open_sync_tool(file_path)
        
        self.session.openWithCallback(success_action, ChoiceBox,
                                     title=msg, list=choices)
    
    def download_failed(self, error_msg):
        """Handle download failure"""
        self["progress"].hide()
        self["status"].setText("Download failed")
        self.session.open(MessageBox, f"Download failed: {error_msg}", MessageBox.TYPE_ERROR)
    
    def show_subtitle_info(self, subtitle_info):
        """Show detailed subtitle information"""
        info_text = f"""
Subtitle Information:

Title: {subtitle_info.get('title', 'Unknown')}
Language: {subtitle_info.get('language', 'Unknown')}
Format: {subtitle_info.get('format', 'Unknown')}
Rating: {subtitle_info.get('rating', 'N/A')}
Downloads: {subtitle_info.get('download_count', 'N/A')}
Size: {subtitle_info.get('size', 'N/A')} bytes
Source: {subtitle_info.get('source', 'Unknown')}

Movie: {subtitle_info.get('movie_title', 'Unknown')}
Year: {subtitle_info.get('movie_year', 'Unknown')}
IMDB ID: {subtitle_info.get('imdb_id', 'N/A')}
        """
        
        self.session.open(MessageBox, info_text.strip(), MessageBox.TYPE_INFO, title="Subtitle Information")
    
    def open_subtitle_file(self, file_path):
        """Open subtitle file for viewing/editing"""
        # This would open a subtitle viewer/editor
        # For now, just show the file path
        self.session.open(MessageBox, f"Subtitle file: {file_path}", MessageBox.TYPE_INFO)
    
    def open_sync_tool(self, file_path):
        """Open synchronization tool with subtitle file"""
        try:
            from .sync_screen import SubtitleSyncScreen
            self.session.open(SubtitleSyncScreen, subtitle_file=file_path, video_file=self.video_file)
        except ImportError:
            self.session.open(MessageBox, "Sync tool not available yet", MessageBox.TYPE_INFO)