# Subtitle Player Plugin for Enigma2

An advanced subtitle management plugin for Enigma2 receivers with comprehensive features for searching, downloading, synchronizing, and translating subtitles.

## Features

### Core Functionality
- **Subtitle Search & Download**: Integration with OpenSubtitles API for automatic subtitle search
- **Multi-Format Support**: Compatible with SRT, ASS/SSA, and WebVTT subtitle formats
- **Real-Time Synchronization**: Fine-tune subtitle timing with millisecond precision
- **Translation Service**: Translate subtitles using Google Translate or Microsoft Translator
- **File Management**: Browse, organize, and manage local subtitle files

### User Interface
- **Modern Design**: Clean, intuitive interface optimized for TV screens
- **Theme Support**: Light and dark theme options
- **Multi-Language**: Support for multiple interface languages including Turkish
- **Easy Navigation**: Remote control friendly with clear menu structure

### Advanced Features
- **Hash-Based Search**: Most accurate subtitle matching using video file hashes
- **Automatic Detection**: Smart language detection for source subtitles
- **Backup & Storage**: Automatic backup of downloaded subtitles
- **Performance Optimized**: Lightweight design for smooth operation on set-top boxes

## Installation

### For Enigma2 Systems

1. **Download the plugin**:
   ```bash
   git clone https://github.com/adrenalinnrw/Subtitle.git
   cd Subtitle
   ```

2. **Install using setup script**:
   ```bash
   python setup.py install
   ```

3. **Manual installation**:
   - Copy the `src` directory to `/usr/lib/enigma2/python/Plugins/Extensions/SubtitlePlayer/`
   - Restart Enigma2

### For Development

1. **Clone the repository**:
   ```bash
   git clone https://github.com/adrenalinnrw/Subtitle.git
   cd Subtitle
   ```

2. **Install development dependencies**:
   ```bash
   pip install -e .[dev]
   ```

## Configuration

### OpenSubtitles API
1. Register at [OpenSubtitles.org](https://www.opensubtitles.org)
2. Go to Settings → Subtitle APIs
3. Enter your username and password (optional, anonymous access available)

### Translation Services
- **Google Translate**: Works without API key (limited)
- **Microsoft Translator**: Requires API key for full functionality

## Usage

### Basic Operations

1. **Search Subtitles**:
   - Green button from main menu
   - Select video file or enter search query
   - Choose from search results and download

2. **Synchronize Timing**:
   - Yellow button → Synchronization Tool
   - Load subtitle file
   - Use number keys for quick adjustments
   - Left/Right arrows for fine tuning

3. **Translate Subtitles**:
   - Select Translation Service from main menu
   - Choose source and target languages
   - Process entire subtitle file or preview individual entries

4. **Browse Local Files**:
   - Browse Local Subtitles from main menu
   - Navigate through directories
   - View subtitle information and content

### Keyboard Shortcuts

#### Main Interface
- **OK**: Select/Open item
- **Red**: Back/Exit
- **Green**: Search subtitles
- **Yellow**: Settings
- **Blue**: About/Info

#### Synchronization Tool
- **1-5**: Quick adjust backward (-5s to -0.1s)
- **6-0**: Quick adjust forward (+0.1s to +5s)
- **Left/Right**: Fine adjustment (±100ms)
- **Up/Down**: Navigate subtitle list

## Technical Details

### Architecture
```
src/
├── __init__.py          # Package initialization
├── plugin.py           # Main plugin entry point
├── ui/                  # User interface components
│   ├── main_screen.py   # Main menu interface
│   ├── search_screen.py # Subtitle search interface
│   ├── sync_screen.py   # Synchronization tool
│   ├── translation_screen.py # Translation interface
│   ├── settings_screen.py    # Settings configuration
│   └── browser_screen.py     # File browser
├── core/                # Core functionality
│   ├── search.py        # Subtitle search engine
│   ├── parser.py        # Subtitle format parser
│   └── translation.py   # Translation services
└── config/              # Configuration management
    └── settings.py      # Settings manager
```

### Supported Formats
- **SRT**: SubRip subtitle format
- **ASS/SSA**: Advanced SubStation Alpha
- **VTT**: WebVTT format
- **SUB**: MicroDVD format (limited support)

### API Integration
- **OpenSubtitles.org**: Primary subtitle database
- **Google Translate**: Free translation service
- **Microsoft Translator**: Premium translation service

## Compatibility

### Enigma2 Distributions
- **OpenATV**: Fully tested and supported
- **OpenPLi**: Compatible
- **OpenHDF**: Compatible
- **Other distributions**: Should work with standard Enigma2 Python environment

### Python Requirements
- **Python 3.6+**: Required for modern features
- **Standard libraries**: json, urllib, threading, os, re
- **Enigma2 libraries**: Screen, Components, Tools

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Test on actual Enigma2 hardware when possible
- Maintain compatibility with older Python versions

## Troubleshooting

### Common Issues

**Plugin not appearing in menu**:
- Check installation path: `/usr/lib/enigma2/python/Plugins/Extensions/SubtitlePlayer/`
- Restart Enigma2 completely
- Check system logs for Python errors

**Search not working**:
- Verify internet connection
- Check OpenSubtitles.org service status
- Try anonymous access (no username/password)

**Translation fails**:
- Check internet connection
- Verify API key for Microsoft Translator
- Try different source/target language combination

**Subtitle parsing errors**:
- Check file encoding (UTF-8 recommended)
- Verify subtitle format is supported
- Try with different subtitle file

### Debug Mode
Enable debug logging in Settings → Advanced → Debug Mode for detailed error information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **OpenSubtitles.org**: For providing the subtitle database API
- **Enigma2 Team**: For the excellent media center platform
- **Community Contributors**: For testing and feedback

## Support

- **Issues**: [GitHub Issues](https://github.com/adrenalinnrw/Subtitle/issues)
- **Discussions**: [GitHub Discussions](https://github.com/adrenalinnrw/Subtitle/discussions)
- **Documentation**: [Wiki](https://github.com/adrenalinnrw/Subtitle/wiki)

---

**Version**: 1.0.0  
**Author**: Subtitle Team  
**Last Updated**: 2024