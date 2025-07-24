#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Subtitle Search Core Module
Handles subtitle search and download from various APIs
"""

import os
import json
import hashlib
import struct
import urllib.request
import urllib.parse
import urllib.error
import gzip
from xml.etree import ElementTree as ET


class SubtitleSearcher:
    """Main class for searching and downloading subtitles"""
    
    def __init__(self, settings_manager):
        self.settings = settings_manager
        self.opensubtitles_url = "https://api.opensubtitles.org/xml-rpc"
        self.user_agent = "SubtitlePlayer v1.0"
        self.token = None
    
    def search_subtitles(self, video_file=None, imdb_id=None, query=None, language="en"):
        """
        Search for subtitles using multiple methods
        
        Args:
            video_file: Path to video file for hash-based search
            imdb_id: IMDB ID for movie/show
            query: Text query for search
            language: Language code (ISO 639-1)
        
        Returns:
            List of subtitle results
        """
        results = []
        
        # Try OpenSubtitles if enabled
        if self.settings.get('subtitle_apis.opensubtitles.enabled', True):
            try:
                os_results = self._search_opensubtitles(video_file, imdb_id, query, language)
                results.extend(os_results)
            except Exception as e:
                print(f"OpenSubtitles search error: {e}")
        
        return self._deduplicate_results(results)
    
    def _search_opensubtitles(self, video_file, imdb_id, query, language):
        """Search subtitles using OpenSubtitles API"""
        results = []
        
        # Login to OpenSubtitles
        if not self._opensubtitles_login():
            return results
        
        search_params = []
        
        # Hash-based search (most accurate)
        if video_file and os.path.exists(video_file):
            file_hash = self._calculate_hash(video_file)
            file_size = os.path.getsize(video_file)
            
            search_params.append({
                'sublanguageid': language,
                'moviehash': file_hash,
                'moviebytesize': str(file_size)
            })
        
        # IMDB-based search
        if imdb_id:
            search_params.append({
                'sublanguageid': language,
                'imdbid': imdb_id
            })
        
        # Query-based search
        if query:
            search_params.append({
                'sublanguageid': language,
                'query': query
            })
        
        # If no specific parameters, use filename
        if not search_params and video_file:
            filename = os.path.basename(video_file)
            search_params.append({
                'sublanguageid': language,
                'query': filename
            })
        
        # Perform search
        for params in search_params:
            try:
                search_results = self._opensubtitles_rpc_call('SearchSubtitles', [self.token, [params]])
                
                if search_results and 'data' in search_results:
                    for sub in search_results['data']:
                        if isinstance(sub, dict):
                            result = {
                                'id': sub.get('IDSubtitleFile', ''),
                                'title': sub.get('SubFileName', 'Unknown'),
                                'language': sub.get('SubLanguageID', language),
                                'rating': float(sub.get('SubRating', '0')),
                                'download_count': int(sub.get('SubDownloadsCnt', '0')),
                                'download_url': sub.get('SubDownloadLink', ''),
                                'size': sub.get('SubSize', '0'),
                                'format': sub.get('SubFormat', 'srt'),
                                'source': 'opensubtitles',
                                'movie_title': sub.get('MovieName', ''),
                                'movie_year': sub.get('MovieYear', ''),
                                'imdb_id': sub.get('IDMovieImdb', '')
                            }
                            results.append(result)
                
                # Limit results per search method
                if len(results) >= 20:
                    break
                    
            except Exception as e:
                print(f"OpenSubtitles search error for params {params}: {e}")
                continue
        
        return results
    
    def _opensubtitles_login(self):
        """Login to OpenSubtitles API"""
        if self.token:
            return True
        
        try:
            username = self.settings.get('subtitle_apis.opensubtitles.username', '')
            password = self.settings.get('subtitle_apis.opensubtitles.password', '')
            
            # Use anonymous login if no credentials
            if not username or not password:
                username = ''
                password = ''
            
            response = self._opensubtitles_rpc_call('LogIn', [username, password, 'en', self.user_agent])
            
            if response and response.get('status') == '200 OK':
                self.token = response.get('token')
                return True
            
        except Exception as e:
            print(f"OpenSubtitles login error: {e}")
        
        return False
    
    def _opensubtitles_rpc_call(self, method, params):
        """Make RPC call to OpenSubtitles API"""
        # Simplified XML-RPC implementation
        # In a real implementation, you'd use xmlrpc.client
        try:
            # This is a placeholder for XML-RPC call
            # Real implementation would use proper XML-RPC client
            return {'status': '200 OK', 'token': 'dummy_token', 'data': []}
        except Exception as e:
            print(f"RPC call error: {e}")
            return None
    
    def download_subtitle(self, subtitle_info, target_path=None):
        """
        Download a subtitle file
        
        Args:
            subtitle_info: Subtitle information dict from search results
            target_path: Target file path (optional)
        
        Returns:
            Path to downloaded file or None if failed
        """
        if not target_path:
            download_dir = self.settings.get('download_path', '/tmp/subtitles/')
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            
            filename = f"{subtitle_info.get('title', 'subtitle')}.{subtitle_info.get('format', 'srt')}"
            target_path = os.path.join(download_dir, filename)
        
        try:
            download_url = subtitle_info.get('download_url', '')
            
            if subtitle_info.get('source') == 'opensubtitles':
                return self._download_opensubtitles_file(subtitle_info['id'], target_path)
            elif download_url:
                return self._download_file(download_url, target_path)
            
        except Exception as e:
            print(f"Download error: {e}")
        
        return None
    
    def _download_opensubtitles_file(self, subtitle_id, target_path):
        """Download subtitle file from OpenSubtitles"""
        try:
            # Get download link
            response = self._opensubtitles_rpc_call('DownloadSubtitles', [self.token, [subtitle_id]])
            
            if response and 'data' in response:
                for sub_data in response['data']:
                    if 'data' in sub_data:
                        # Decode base64 gzipped content
                        import base64
                        content = base64.b64decode(sub_data['data'])
                        content = gzip.decompress(content)
                        
                        with open(target_path, 'wb') as f:
                            f.write(content)
                        
                        return target_path
            
        except Exception as e:
            print(f"OpenSubtitles download error: {e}")
        
        return None
    
    def _download_file(self, url, target_path):
        """Download file from URL"""
        try:
            request = urllib.request.Request(url)
            request.add_header('User-Agent', self.user_agent)
            
            with urllib.request.urlopen(request) as response:
                with open(target_path, 'wb') as f:
                    f.write(response.read())
            
            return target_path
            
        except Exception as e:
            print(f"File download error: {e}")
            return None
    
    def _calculate_hash(self, file_path):
        """Calculate OpenSubtitles hash for video file"""
        try:
            longlongformat = '<q'  # little-endian long long
            bytesize = struct.calcsize(longlongformat)
            
            with open(file_path, 'rb') as f:
                filesize = os.path.getsize(file_path)
                hash_value = filesize
                
                if filesize < 65536 * 2:
                    return "SizeError"
                
                # Read first 64KB
                for x in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value = hash_value & 0xFFFFFFFFFFFFFFFF
                
                # Read last 64KB
                f.seek(max(0, filesize - 65536), 0)
                for x in range(65536 // bytesize):
                    buffer = f.read(bytesize)
                    (l_value,) = struct.unpack(longlongformat, buffer)
                    hash_value += l_value
                    hash_value = hash_value & 0xFFFFFFFFFFFFFFFF
                
                return "%016x" % hash_value
                
        except Exception as e:
            print(f"Hash calculation error: {e}")
            return None
    
    def _deduplicate_results(self, results):
        """Remove duplicate results based on title and hash"""
        seen = set()
        unique_results = []
        
        for result in results:
            # Create identifier from title and size
            identifier = f"{result.get('title', '')}_{result.get('size', '')}"
            
            if identifier not in seen:
                seen.add(identifier)
                unique_results.append(result)
        
        # Sort by rating and download count
        unique_results.sort(
            key=lambda x: (x.get('rating', 0), x.get('download_count', 0)),
            reverse=True
        )
        
        return unique_results[:50]  # Limit to top 50 results