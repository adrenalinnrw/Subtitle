#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle Parser Module
Handles parsing and manipulation of various subtitle formats
"""

import re
import os
import datetime
from typing import List, Dict, Optional, Tuple


class SubtitleEntry:
    """Represents a single subtitle entry"""
    
    def __init__(self, index: int, start_time: int, end_time: int, text: str):
        """
        Initialize subtitle entry
        
        Args:
            index: Subtitle sequence number
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
            text: Subtitle text content
        """
        self.index = index
        self.start_time = start_time
        self.end_time = end_time
        self.text = text.strip()
    
    def duration(self) -> int:
        """Get duration in milliseconds"""
        return self.end_time - self.start_time
    
    def shift_timing(self, offset_ms: int):
        """Shift timing by offset in milliseconds"""
        self.start_time += offset_ms
        self.end_time += offset_ms
        
        # Ensure times don't go negative
        if self.start_time < 0:
            self.end_time -= self.start_time
            self.start_time = 0
    
    def __str__(self):
        return f"[{self.index}] {self.ms_to_time(self.start_time)} --> {self.ms_to_time(self.end_time)}: {self.text}"
    
    @staticmethod
    def ms_to_time(ms: int) -> str:
        """Convert milliseconds to SRT time format"""
        hours = ms // 3600000
        minutes = (ms % 3600000) // 60000
        seconds = (ms % 60000) // 1000
        milliseconds = ms % 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    @staticmethod
    def time_to_ms(time_str: str) -> int:
        """Convert SRT time format to milliseconds"""
        # Handle both comma and dot as decimal separator
        time_str = time_str.replace(',', '.')
        
        # Parse time components
        time_parts = time_str.split(':')
        if len(time_parts) != 3:
            return 0
        
        hours = int(time_parts[0])
        minutes = int(time_parts[1])
        
        # Handle seconds and milliseconds
        sec_parts = time_parts[2].split('.')
        seconds = int(sec_parts[0])
        milliseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        
        # Ensure milliseconds is 3 digits
        if len(sec_parts) > 1:
            ms_str = sec_parts[1].ljust(3, '0')[:3]
            milliseconds = int(ms_str)
        
        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
        return total_ms


class SubtitleParser:
    """Main subtitle parser supporting multiple formats"""
    
    def __init__(self):
        self.supported_formats = ['srt', 'ass', 'ssa', 'vtt']
    
    def parse_file(self, file_path: str) -> List[SubtitleEntry]:
        """
        Parse subtitle file and return list of entries
        
        Args:
            file_path: Path to subtitle file
            
        Returns:
            List of SubtitleEntry objects
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Subtitle file not found: {file_path}")
        
        # Detect file format
        file_ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        
        if file_ext == 'srt':
            return self._parse_srt(file_path)
        elif file_ext in ['ass', 'ssa']:
            return self._parse_ass(file_path)
        elif file_ext == 'vtt':
            return self._parse_vtt(file_path)
        else:
            # Try to detect format from content
            return self._auto_detect_and_parse(file_path)
    
    def _parse_srt(self, file_path: str) -> List[SubtitleEntry]:
        """Parse SRT format subtitle file"""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Unable to decode subtitle file")
        
        # Split into subtitle blocks
        blocks = re.split(r'\n\s*\n', content.strip())
        
        for block in blocks:
            if not block.strip():
                continue
            
            lines = block.strip().split('\n')
            if len(lines) < 3:
                continue
            
            try:
                # Parse index
                index = int(lines[0].strip())
                
                # Parse timing
                timing_line = lines[1].strip()
                timing_match = re.match(r'(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})', timing_line)
                
                if not timing_match:
                    continue
                
                start_time = SubtitleEntry.time_to_ms(timing_match.group(1))
                end_time = SubtitleEntry.time_to_ms(timing_match.group(2))
                
                # Parse text (all remaining lines)
                text = '\n'.join(lines[2:])
                
                # Clean up text (remove HTML tags, etc.)
                text = self._clean_text(text)
                
                entry = SubtitleEntry(index, start_time, end_time, text)
                entries.append(entry)
                
            except (ValueError, IndexError) as e:
                print(f"Error parsing SRT block: {e}")
                continue
        
        return entries
    
    def _parse_ass(self, file_path: str) -> List[SubtitleEntry]:
        """Parse ASS/SSA format subtitle file"""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        
        in_events = False
        format_line = None
        index = 1
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('[Events]'):
                in_events = True
                continue
            elif line.startswith('[') and in_events:
                break
            elif not in_events:
                continue
            
            if line.startswith('Format:'):
                format_line = line[7:].strip()
                continue
            
            if line.startswith('Dialogue:') and format_line:
                try:
                    # Parse dialogue line
                    parts = line[9:].split(',', 9)  # Split into max 10 parts
                    
                    if len(parts) < 10:
                        continue
                    
                    # Map format to values
                    format_parts = [p.strip() for p in format_line.split(',')]
                    dialogue_dict = dict(zip(format_parts, parts))
                    
                    # Extract timing
                    start_time = self._ass_time_to_ms(dialogue_dict.get('Start', '0:00:00.00'))
                    end_time = self._ass_time_to_ms(dialogue_dict.get('End', '0:00:00.00'))
                    
                    # Extract text and clean it
                    text = dialogue_dict.get('Text', '')
                    text = self._clean_ass_text(text)
                    
                    if text:
                        entry = SubtitleEntry(index, start_time, end_time, text)
                        entries.append(entry)
                        index += 1
                
                except Exception as e:
                    print(f"Error parsing ASS dialogue: {e}")
                    continue
        
        return entries
    
    def _parse_vtt(self, file_path: str) -> List[SubtitleEntry]:
        """Parse WebVTT format subtitle file"""
        entries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Split into blocks
        blocks = re.split(r'\n\s*\n', content)
        index = 1
        
        for block in blocks:
            if not block.strip() or block.strip() == 'WEBVTT':
                continue
            
            lines = block.strip().split('\n')
            
            # Find timing line
            timing_line = None
            text_start = 0
            
            for i, line in enumerate(lines):
                if '-->' in line:
                    timing_line = line
                    text_start = i + 1
                    break
            
            if not timing_line:
                continue
            
            try:
                # Parse timing
                timing_match = re.search(r'(\d{2}:\d{2}[:.]\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}[:.]\d{2}[,.]\d{3})', timing_line)
                
                if not timing_match:
                    continue
                
                start_time = self._vtt_time_to_ms(timing_match.group(1))
                end_time = self._vtt_time_to_ms(timing_match.group(2))
                
                # Extract text
                text = '\n'.join(lines[text_start:])
                text = self._clean_text(text)
                
                if text:
                    entry = SubtitleEntry(index, start_time, end_time, text)
                    entries.append(entry)
                    index += 1
            
            except Exception as e:
                print(f"Error parsing VTT block: {e}")
                continue
        
        return entries
    
    def _auto_detect_and_parse(self, file_path: str) -> List[SubtitleEntry]:
        """Auto-detect subtitle format and parse"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read(1024)  # Read first 1KB
        except:
            return []
        
        content_lower = content.lower()
        
        if 'webvtt' in content_lower:
            return self._parse_vtt(file_path)
        elif '[script info]' in content_lower or 'dialogue:' in content_lower:
            return self._parse_ass(file_path)
        else:
            # Default to SRT
            return self._parse_srt(file_path)
    
    def _clean_text(self, text: str) -> str:
        """Clean subtitle text from formatting tags"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove common formatting
        text = re.sub(r'\{[^}]+\}', '', text)  # Remove {} tags
        text = re.sub(r'\[[^\]]+\]', '', text)  # Remove [] tags
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def _clean_ass_text(self, text: str) -> str:
        """Clean ASS-specific formatting"""
        # Remove ASS override tags
        text = re.sub(r'\{[^}]*\}', '', text)
        
        # Handle line breaks
        text = text.replace('\\N', '\n')
        text = text.replace('\\n', '\n')
        
        return self._clean_text(text)
    
    def _ass_time_to_ms(self, time_str: str) -> int:
        """Convert ASS time format to milliseconds"""
        # Format: H:MM:SS.cs (centiseconds)
        parts = time_str.split(':')
        if len(parts) != 3:
            return 0
        
        hours = int(parts[0])
        minutes = int(parts[1])
        
        sec_parts = parts[2].split('.')
        seconds = int(sec_parts[0])
        centiseconds = int(sec_parts[1]) if len(sec_parts) > 1 else 0
        
        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + centiseconds * 10
        return total_ms
    
    def _vtt_time_to_ms(self, time_str: str) -> int:
        """Convert WebVTT time format to milliseconds"""
        # Handle both : and . as separators
        time_str = time_str.replace('.', ':')
        return SubtitleEntry.time_to_ms(time_str.replace(':', ':', 2).replace(':', ',', 1))
    
    def save_srt(self, entries: List[SubtitleEntry], file_path: str) -> bool:
        """Save subtitle entries as SRT file"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for entry in entries:
                    f.write(f"{entry.index}\n")
                    f.write(f"{entry.ms_to_time(entry.start_time)} --> {entry.ms_to_time(entry.end_time)}\n")
                    f.write(f"{entry.text}\n\n")
            return True
        except Exception as e:
            print(f"Error saving SRT file: {e}")
            return False