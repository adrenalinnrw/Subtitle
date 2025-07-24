#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Setup script for Subtitle Player Plugin
"""

import os
import shutil
from setuptools import setup, find_packages

# Read version from package
exec(open('src/__init__.py').read())

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Plugin installation directory for Enigma2
ENIGMA2_PLUGIN_DIR = '/usr/lib/enigma2/python/Plugins/Extensions/SubtitlePlayer'

def install_enigma2_plugin():
    """Install plugin to Enigma2 plugins directory"""
    try:
        # Create plugin directory
        os.makedirs(ENIGMA2_PLUGIN_DIR, exist_ok=True)
        
        # Copy source files
        src_dir = 'src'
        for root, dirs, files in os.walk(src_dir):
            for file in files:
                if file.endswith('.py'):
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, src_dir)
                    dest_path = os.path.join(ENIGMA2_PLUGIN_DIR, rel_path)
                    
                    # Create directory if needed
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(src_path, dest_path)
                    print(f"Installed: {dest_path}")
        
        print(f"Plugin installed to: {ENIGMA2_PLUGIN_DIR}")
        print("Please restart Enigma2 to load the plugin.")
        
    except Exception as e:
        print(f"Installation failed: {e}")
        return False
    
    return True

setup(
    name='subtitle-player',
    version=__version__,
    author=__author__,
    description=__description__,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/adrenalinnrw/Subtitle',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Multimedia :: Video',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.6',
    install_requires=[
        # Core dependencies are kept minimal for Enigma2 compatibility
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'flake8',
            'black',
        ],
    },
    entry_points={
        'console_scripts': [
            'subtitle-player-install=setup:install_enigma2_plugin',
        ],
    },
    include_package_data=True,
    package_data={
        'subtitle_player': [
            'resources/*',
            'config/*.conf',
        ],
    },
)