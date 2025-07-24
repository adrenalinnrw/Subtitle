#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Translation Service Module
Provides subtitle translation functionality using various APIs
"""

import urllib.request
import urllib.parse
import json
import re
from typing import List, Optional


class TranslationService:
    """Main translation service class"""
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.supported_services = ['google', 'microsoft']
    
    def translate_subtitle_entries(self, entries, target_language='en', source_language='auto'):
        """
        Translate a list of subtitle entries
        
        Args:
            entries: List of SubtitleEntry objects
            target_language: Target language code
            source_language: Source language code ('auto' for detection)
        
        Returns:
            List of translated SubtitleEntry objects
        """
        service = self.settings.get('translation.service', 'google')
        
        if service not in self.supported_services:
            raise ValueError(f"Unsupported translation service: {service}")
        
        translated_entries = []
        
        for entry in entries:
            try:
                translated_text = self.translate_text(
                    entry.text, 
                    target_language, 
                    source_language
                )
                
                # Create new entry with translated text
                from .parser import SubtitleEntry
                translated_entry = SubtitleEntry(
                    entry.index,
                    entry.start_time,
                    entry.end_time,
                    translated_text
                )
                translated_entries.append(translated_entry)
                
            except Exception as e:
                print(f"Translation error for entry {entry.index}: {e}")
                # Keep original entry if translation fails
                translated_entries.append(entry)
        
        return translated_entries
    
    def translate_text(self, text, target_language='en', source_language='auto'):
        """
        Translate a single text string
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code
        
        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text
        
        # Clean text for translation
        clean_text = self._clean_text_for_translation(text)
        
        service = self.settings.get('translation.service', 'google')
        
        if service == 'google':
            return self._translate_google(clean_text, target_language, source_language)
        elif service == 'microsoft':
            return self._translate_microsoft(clean_text, target_language, source_language)
        else:
            raise ValueError(f"Unsupported translation service: {service}")
    
    def _translate_google(self, text, target_lang, source_lang='auto'):
        """Translate using Google Translate (unofficial API)"""
        try:
            # Clean language codes for Google
            if target_lang == 'auto':
                target_lang = 'en'
            
            # Google Translate URL
            base_url = "https://translate.googleapis.com/translate_a/single"
            
            params = {
                'client': 'gtx',
                'sl': source_lang,
                'tl': target_lang,
                'dt': 't',
                'q': text
            }
            
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'SubtitlePlayer/1.0')
            
            with urllib.request.urlopen(request, timeout=10) as response:
                result = response.read().decode('utf-8')
            
            # Parse JSON response
            try:
                data = json.loads(result)
                if data and len(data) > 0 and data[0]:
                    # Extract translated text from response
                    translated_parts = []
                    for part in data[0]:
                        if part and len(part) > 0:
                            translated_parts.append(part[0])
                    
                    translated_text = ''.join(translated_parts)
                    return self._restore_text_formatting(translated_text, text)
                
            except (json.JSONDecodeError, IndexError, TypeError) as e:
                print(f"Error parsing Google Translate response: {e}")
                return text
            
        except Exception as e:
            print(f"Google Translate error: {e}")
            return text
    
    def _translate_microsoft(self, text, target_lang, source_lang='auto'):
        """Translate using Microsoft Translator API"""
        try:
            api_key = self.settings.get('translation.api_key', '')
            
            if not api_key:
                raise ValueError("Microsoft Translator API key not configured")
            
            # Microsoft Translator endpoint
            endpoint = "https://api.cognitive.microsofttranslator.com/translate"
            
            params = {
                'api-version': '3.0',
                'to': target_lang
            }
            
            if source_lang and source_lang != 'auto':
                params['from'] = source_lang
            
            url = f"{endpoint}?{urllib.parse.urlencode(params)}"
            
            headers = {
                'Ocp-Apim-Subscription-Key': api_key,
                'Content-Type': 'application/json',
                'User-Agent': 'SubtitlePlayer/1.0'
            }
            
            body = json.dumps([{'text': text}]).encode('utf-8')
            
            request = urllib.request.Request(url, data=body, headers=headers)
            
            with urllib.request.urlopen(request, timeout=10) as response:
                result = response.read().decode('utf-8')
            
            # Parse response
            data = json.loads(result)
            
            if data and len(data) > 0 and 'translations' in data[0]:
                translations = data[0]['translations']
                if translations and len(translations) > 0:
                    translated_text = translations[0]['text']
                    return self._restore_text_formatting(translated_text, text)
            
        except Exception as e:
            print(f"Microsoft Translator error: {e}")
            return text
    
    def _clean_text_for_translation(self, text):
        """Clean subtitle text before translation"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        
        # Remove subtitle formatting
        clean_text = re.sub(r'\{[^}]+\}', '', clean_text)
        clean_text = re.sub(r'\[[^\]]+\]', '', clean_text)
        
        # Preserve line breaks but clean extra whitespace
        clean_text = re.sub(r'[ \t]+', ' ', clean_text)
        clean_text = clean_text.strip()
        
        return clean_text
    
    def _restore_text_formatting(self, translated_text, original_text):
        """Restore basic formatting from original text"""
        # Preserve line breaks if they existed in original
        if '\n' in original_text:
            # Try to maintain line structure
            original_lines = original_text.split('\n')
            translated_lines = translated_text.split(' ')
            
            # Simple heuristic: if original had 2 lines, try to split translation
            if len(original_lines) == 2 and len(translated_lines) > 2:
                mid_point = len(translated_lines) // 2
                line1 = ' '.join(translated_lines[:mid_point])
                line2 = ' '.join(translated_lines[mid_point:])
                return f"{line1}\n{line2}"
        
        return translated_text
    
    def detect_language(self, text):
        """
        Detect the language of given text
        
        Args:
            text: Text to analyze
        
        Returns:
            Language code or 'unknown'
        """
        service = self.settings.get('translation.service', 'google')
        
        if service == 'google':
            return self._detect_language_google(text)
        elif service == 'microsoft':
            return self._detect_language_microsoft(text)
        else:
            return 'unknown'
    
    def _detect_language_google(self, text):
        """Detect language using Google Translate"""
        try:
            base_url = "https://translate.googleapis.com/translate_a/single"
            
            params = {
                'client': 'gtx',
                'sl': 'auto',
                'tl': 'en',
                'dt': 't',
                'q': text[:500]  # Limit text length for detection
            }
            
            url = f"{base_url}?{urllib.parse.urlencode(params)}"
            
            request = urllib.request.Request(url)
            request.add_header('User-Agent', 'SubtitlePlayer/1.0')
            
            with urllib.request.urlopen(request, timeout=5) as response:
                result = response.read().decode('utf-8')
            
            data = json.loads(result)
            
            # Language detection is in data[2]
            if data and len(data) > 2 and data[2]:
                return data[2]
            
        except Exception as e:
            print(f"Language detection error: {e}")
        
        return 'unknown'
    
    def _detect_language_microsoft(self, text):
        """Detect language using Microsoft Translator"""
        try:
            api_key = self.settings.get('translation.api_key', '')
            
            if not api_key:
                return 'unknown'
            
            endpoint = "https://api.cognitive.microsofttranslator.com/detect"
            
            params = {'api-version': '3.0'}
            url = f"{endpoint}?{urllib.parse.urlencode(params)}"
            
            headers = {
                'Ocp-Apim-Subscription-Key': api_key,
                'Content-Type': 'application/json'
            }
            
            body = json.dumps([{'text': text[:500]}]).encode('utf-8')
            
            request = urllib.request.Request(url, data=body, headers=headers)
            
            with urllib.request.urlopen(request, timeout=5) as response:
                result = response.read().decode('utf-8')
            
            data = json.loads(result)
            
            if data and len(data) > 0 and 'language' in data[0]:
                return data[0]['language']
            
        except Exception as e:
            print(f"Microsoft language detection error: {e}")
        
        return 'unknown'
    
    def get_supported_languages(self):
        """Get list of supported languages for translation"""
        return {
            'af': 'Afrikaans',
            'ar': 'Arabic',
            'bg': 'Bulgarian',
            'ca': 'Catalan',
            'cs': 'Czech',
            'da': 'Danish',
            'de': 'German',
            'el': 'Greek',
            'en': 'English',
            'es': 'Spanish',
            'et': 'Estonian',
            'fi': 'Finnish',
            'fr': 'French',
            'he': 'Hebrew',
            'hi': 'Hindi',
            'hr': 'Croatian',
            'hu': 'Hungarian',
            'id': 'Indonesian',
            'it': 'Italian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'lt': 'Lithuanian',
            'lv': 'Latvian',
            'nl': 'Dutch',
            'no': 'Norwegian',
            'pl': 'Polish',
            'pt': 'Portuguese',
            'ro': 'Romanian',
            'ru': 'Russian',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'sv': 'Swedish',
            'th': 'Thai',
            'tr': 'Turkish',
            'uk': 'Ukrainian',
            'vi': 'Vietnamese',
            'zh': 'Chinese'
        }