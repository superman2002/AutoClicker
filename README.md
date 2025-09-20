# AutoClicker for Ubuntu

A powerful Python-based autoclicker that can find and click on user-defined images or text on screen using computer vision and OCR. Features a comprehensive GUI interface with advanced automation capabilities.

## Features

- **Multiple Recognition Modes**:
  - Image Recognition: Uses OpenCV template matching to find images on screen
  - Text Recognition: Uses Tesseract OCR to find text on screen
  - Mixed Mode: Combine image and text targets in a single operation
  - Pattern Sequences: Execute complex click sequences and keyboard automation

- **Advanced GUI Interface**:
  - Always-on-top GUI with keyboard hotkeys (F6/F7/F8)
  - Dark mode theme support
  - Visual region selection tool
  - Real-time logging and status updates
  - Progress bars and statistics tracking
  - Export/import settings functionality
  - Customizable hotkeys

- **Safety & Reliability**:
  - Safety zones to avoid clicking in specific areas
  - Time limits with automatic stopping
  - Emergency stop with mouse corner failsafe and keyboard shortcuts
  - Click confirmation dialogs
  - Input validation and error handling
  - Screenshot debugging for failed detections

- **Performance & Compatibility**:
  - Optimized image processing and screenshot caching
  - Support for multiple image formats (PNG, JPG, JPEG, BMP, TIFF, TIF, WebP)
  - OCR preprocessing for improved text recognition accuracy
  - Cross-platform potential (currently Linux-focused)
  - Debian package support for easy installation

- **Automation Features**:
  - Click patterns and sequences
  - Keyboard input simulation
  - Pause/resume functionality during operation
  - Sound feedback for successful clicks
  - Configuration profiles for different use cases

## Requirements

- Ubuntu Linux 18.04 or later (or compatible Linux distribution)
- Python 3.8+
- Graphical desktop environment (GNOME, KDE, XFCE, etc.)
- X11 display server (or Wayland with gnome-screenshot fallback)
- Tesseract OCR (automatically installed)

### System Dependencies

The autoclicker requires screenshot capability. Install the appropriate tool for your environment:

```bash
# For X11 environments (recommended)
sudo apt install scrot tesseract-ocr python3-tk imagemagick

# For Wayland environments (Ubuntu 22.04+)
sudo apt install gnome-screenshot tesseract-ocr python3-tk imagemagick

# Optional: Additional OCR language packs
sudo apt install tesseract-ocr-eng tesseract-ocr-osd
```

## Installation

### Option 1: Debian Package (Recommended)

Download and install the Debian package from the releases:

```bash
# Download the .deb file from GitHub releases
wget https://github.com/superman2002/AutoClicker/releases/download/v1.0.0/python3-autoclicker_1.0.0-1_all.deb

# Install the package
sudo dpkg -i python3-autoclicker_1.0.0-1_all.deb

# Fix any missing dependencies
sudo apt install -f

# Launch the GUI
autoclicker-gui

# Or use command line
autoclicker --help
```

### Option 2: From Source

1. Clone or download this repository
2. Run the diagnostic script to check your setup:
   ```bash
   ./diagnose.sh
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. (Optional) Install system-wide:
   ```bash
   sudo python3 setup.py install
   ```

## Usage

### Graphical User Interface (Recommended)

Launch the GUI for the easiest experience:

```bash
./run_gui.sh
# or if installed system-wide:
autoclicker-gui
```

#### GUI Features

- **Always-on-Top Window**: GUI stays visible above all other windows
- **Keyboard Hotkeys**: F6 to start, F7 to stop, F8 to pause/resume (works even when window is not focused)
- **Mode Selection**: Choose between Text Recognition, Image Recognition, Pattern Sequence, or Mixed modes
- **Multiple Targets**: Enter multiple targets (one per line) in the text area
- **File Browser**: Browse and select template images for image mode
- **Visual Region Picker**: Click "Select Region" to interactively choose search area with click-and-drag
- **Settings Panel**: Adjust confidence level, check interval, safety zones, and more
- **Real-time Status**: Live status updates, progress bars, and detailed logging
- **Settings Management**: Auto-save/load settings, export/import configurations
- **Dark Mode**: Toggle between light and dark themes

### Command Line Interface

For advanced users or automation scripts:

```bash
./run.sh --mode [image|text|mixed|pattern] --target [path_to_image|text_string] [options]
# or if installed system-wide:
autoclicker --mode text --target "OK"
```

#### Command Line Options

- `--mode`: Choose 'image', 'text', 'mixed', or 'pattern'
- `--target`: Path to template image file (image mode) or target text string (text mode)
- `--confidence`: Confidence threshold for matching (0.0-1.0, default: 0.8)
- `--interval`: Time between screen checks in seconds (default: 1.0)
- `--region`: Search region as X Y WIDTH HEIGHT (default: full screen)
- `--max-runtime`: Maximum runtime in seconds (default: unlimited)
- `--safety-zones`: Safety zones as x,y,width,height (can specify multiple)

#### Examples

**Image Mode:**
```bash
./run.sh --mode image --target /path/to/button.png --confidence 0.9
```

**Text Mode:**
```bash
./run.sh --mode text --target "OK" --target "Cancel"
```

**Mixed Mode:**
```bash
./run.sh --mode mixed --target "OK" --target /path/to/image.png
```

**With Region Restriction:**
```bash
./run.sh --mode text --target "Submit" --region 100 100 800 600
```

**Pattern Mode:**
```bash
./run.sh --mode pattern --target "{'name': 'Login', 'steps': [{'position': (500, 300)}, {'keyboard': 'username'}, {'keyboard': ['tab']}, {'keyboard': 'password'}, {'keyboard': ['enter']}]}"
```

### Creating Template Images

For image recognition mode:

1. Take a screenshot of the target element (button, icon, etc.)
2. Crop the image to contain only the target
3. Save as PNG format (recommended for transparency)
4. Use the absolute path to the image file

**Tip:** Template images should be as small as possible but still unique to improve matching speed and accuracy.

## Configuration

### Settings File

Settings are automatically saved to `autoclicker_settings.json` in the working directory. The file includes:

- GUI preferences and layout
- Default confidence levels and intervals
- Safety zones and regions
- Hotkey configurations
- Theme preferences

### Advanced Configuration

#### Safety Zones
Define areas where clicking is prohibited:
```
Format: x,y,width,height per line
Example:
0,0,100,50     # Top-left corner
1800,1000,120,24  # Close button area
```

#### Pattern Sequences
Create complex automation sequences:
```json
{
  "name": "Login Sequence",
  "steps": [
    {"position": [500, 300]},     // Click username field
    {"keyboard": "myusername"},   // Type username
    {"keyboard": ["tab"]},        // Tab to password
    {"keyboard": "mypassword"},   // Type password
    {"keyboard": ["enter"]},      // Submit
    {"delay": 2.0}                // Wait 2 seconds
  ]
}
```

#### Hotkey Customization
Customize keyboard shortcuts in the GUI settings:
- Start: Default F6
- Stop: Default F7
- Pause: Default F8

## Troubleshooting

### Common Issues

#### "Can't connect to display" Error
**Symptoms**: GUI won't start, display connection errors
**Solutions**:
1. Ensure you're in a graphical environment
2. Check DISPLAY variable: `echo $DISPLAY`
3. For SSH: Use `ssh -X username@hostname`
4. For VNC: Connect through VNC client first

#### PyAutoGUI Not Available
**Symptoms**: "PyAutoGUI not available" error
**Solutions**:
1. Fix X11 authentication: `xhost +local:`
2. Set DISPLAY: `export DISPLAY=:0.0`
3. Restart in graphical environment

#### Template Image Not Found
**Symptoms**: "Image file not found" error
**Solutions**:
1. Verify file path is correct (use absolute paths)
2. Check file permissions
3. Ensure supported format (PNG, JPG, BMP, TIFF, WebP)

#### OCR Not Finding Text
**Symptoms**: Text targets not detected
**Solutions**:
1. Increase screen resolution and contrast
2. Adjust confidence threshold
3. Try different preprocessing methods
4. Ensure Tesseract language packs are installed

#### High CPU Usage
**Symptoms**: System becomes slow during operation
**Solutions**:
1. Increase check interval
2. Limit search region
3. Increase screenshot cache duration
4. Close unnecessary applications

### Diagnostic Tools

#### Run Diagnostics
```bash
./diagnose.sh
```
Checks system compatibility and required dependencies.

#### Test Screenshot Capture
```bash
python3 -c "import pyautogui; print(pyautogui.screenshot())"
```
Verifies screenshot functionality.

#### Test OCR
```bash
python3 -c "import pytesseract; print(pytesseract.get_tesseract_version())"
```
Verifies Tesseract OCR installation.

### Environment-Specific Setup

#### Ubuntu Desktop (Local)
```bash
# Should work out of the box
./run_gui.sh
```

#### SSH Session with X Forwarding
```bash
# Enable X forwarding when connecting
ssh -X user@hostname

# Or set display manually
export DISPLAY=:10.0  # Adjust as needed
./run_gui.sh
```

#### Remote Server with VNC
```bash
# Install VNC server
sudo apt install tightvncserver

# Start VNC server
vncserver :1

# Connect from client and run autoclicker
./run_gui.sh
```

#### Headless Testing
```bash
# For development/testing only
sudo apt install xvfb
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
./run_gui.sh
```

## Development

### Project Structure
```
autoclicker/
├── autoclicker.py          # Core autoclicker functionality
├── autoclicker_gui.py      # GUI interface
├── setup.py               # Package configuration
├── requirements.txt       # Python dependencies
├── test_autoclicker.py    # Unit tests
├── run.sh                 # CLI launcher
├── run_gui.sh            # GUI launcher
├── diagnose.sh           # Diagnostic script
├── README.md             # This file
├── USER_GUIDE.md         # Detailed user guide
├── TODO.md               # Development roadmap
└── deb_dist/             # Debian packaging
```

### Running Tests
```bash
python3 -m pytest test_autoclicker.py -v
```

### Building Debian Package
```bash
./build_deb.sh
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add comprehensive error handling
- Include unit tests for new features
- Update documentation for changes
- Test on multiple Ubuntu versions when possible

## License

This project is open source and available under the MIT License. See the LICENSE file for details.

## Changelog

### Version 1.0.0 (Latest)
- Complete GUI overhaul with modern interface
- Pattern sequence automation
- Advanced safety features and validation
- Debian packaging support
- Comprehensive unit test suite
- Dark mode theme
- Multiple image format support
- OCR preprocessing improvements
- Settings persistence and export/import
- Visual region selection tool
- Progress bars and statistics tracking
- Sound feedback system
- Customizable hotkeys
- Comprehensive user guide and documentation

### Previous Versions
- Initial release with basic image and text recognition
- Added GUI interface
- Implemented safety features
- Added configuration management

## Support

For additional help:
1. Check the [User Guide](USER_GUIDE.md) for detailed instructions
2. Run diagnostics: `./diagnose.sh`
3. Check logs for error details
4. Review configuration settings
5. Test with simple cases first

### Bug Reports and Feature Requests
Please use the GitHub issue tracker to report bugs or request features. Include:
- Ubuntu version and desktop environment
- Python version
- Error messages and logs
- Steps to reproduce the issue

## Disclaimer

This tool is provided as-is for legitimate automation purposes. Users are responsible for ensuring compliance with applicable laws and terms of service. The developers are not responsible for any misuse or consequences arising from the use of this software.

---

**Version:** 1.0.0
**Python:** 3.8+
**License:** MIT
**Repository:** https://github.com/superman2002/AutoClicker
