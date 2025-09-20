# AutoClicker User Guide

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [User Interface Overview](#user-interface-overview)
5. [Configuration](#configuration)
6. [Advanced Features](#advanced-features)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [FAQ](#faq)

## Introduction

The AutoClicker for Ubuntu is a powerful automation tool that can find and click on images or text on your screen. It uses computer vision and OCR (Optical Character Recognition) to locate targets and perform automated mouse clicks.

### Key Features
- **Image Recognition**: Find and click on visual elements using template matching
- **Text Recognition**: Locate and click on text using OCR
- **Mixed Mode**: Combine image and text targets
- **Pattern Sequences**: Execute complex click sequences
- **Safety Features**: Prevent accidental clicks with safety zones and time limits
- **Cross-Platform**: Works on Linux (Ubuntu), with potential for other platforms

## Installation

### System Requirements
- Ubuntu Linux 18.04 or later
- Python 3.6+
- Graphical desktop environment (GNOME, KDE, etc.)
- X11 display server (or Wayland with fallback support)

### Dependencies
The autoclicker requires several system packages:

```bash
# Install system dependencies
sudo apt update
sudo apt install tesseract-ocr scrot python3-tk imagemagick

# Optional: For better OCR accuracy
sudo apt install tesseract-ocr-eng tesseract-ocr-osd
```

### Setup
1. Clone or download the repository
2. Run the diagnostic script:
   ```bash
   ./diagnose.sh
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

### Launch the GUI
```bash
./run_gui.sh
```

### Basic Usage
1. **Choose Mode**: Select Text Recognition, Image Recognition, or Pattern Sequence
2. **Add Targets**: Enter text or browse for images
3. **Configure Settings**: Adjust confidence, interval, and region
4. **Start**: Click Start (F6) or use the hotkey

### Command Line Usage
```bash
# Text mode
./run.sh --mode text --target "OK"

# Image mode
./run.sh --mode image --target /path/to/button.png

# Mixed mode
./run.sh --mode mixed --target "OK" --target /path/to/image.png
```

## User Interface Overview

### Main Window Layout
- **Menu Bar**: File operations, view options, help
- **Mode Selection**: Choose between Text, Image, Pattern, or Mixed modes
- **Target Input**: Enter targets (one per line)
- **Settings Panel**: Configure confidence, interval, regions, safety zones
- **Control Buttons**: Start, Pause, Stop with keyboard shortcuts
- **Status Display**: Real-time status and statistics
- **Log Window**: Detailed operation logs

### Keyboard Shortcuts
- **F6**: Start autoclicker
- **F7**: Stop autoclicker
- **F8**: Pause/Resume
- **Ctrl+C**: Emergency stop (terminal)

## Configuration

### Basic Settings

#### Confidence Threshold
- Range: 0.1 to 1.0
- Default: 0.8
- Higher values = more precise but may miss matches
- Lower values = more matches but higher false positive risk

#### Check Interval
- Range: 0.1 to 5.0 seconds
- Default: 1.0 seconds
- Lower values = faster response but higher CPU usage
- Higher values = slower response but better performance

#### Screenshot Cache Duration
- Range: 0.1 to 2.0 seconds
- Default: 0.5 seconds
- Reduces screen flickering by reusing recent screenshots

### Advanced Settings

#### Safety Zones
Define areas where clicking is prohibited:
```
# Format: x,y,width,height (one per line)
# Example: 0,0,100,50 (top-left corner)
# Example: 1800,1000,120,24 (close button area)
```

#### Search Region
Limit search to specific screen area:
- X, Y: Top-left coordinates
- Width, Height: Region dimensions
- Default: Full screen

#### Time Limits
- Maximum runtime in seconds
- 0 = no limit (default)
- Automatically stops after specified time

#### Hotkey Customization
Customize keyboard shortcuts:
- Start: Default F6
- Stop: Default F7
- Pause: Default F8

### Settings Management
- **Auto-save**: Settings automatically saved on exit
- **Export**: Save settings to JSON file for backup/sharing
- **Import**: Load settings from JSON file
- **Reset**: Clear all settings to defaults

## Advanced Features

### Image Recognition Mode
1. Create template images of target elements
2. Use "Browse Image" button or enter file paths
3. Supported formats: PNG, JPG, JPEG, BMP, TIFF, TIF, WebP
4. Templates should be cropped closely to target elements

### Text Recognition Mode
1. Enter target text strings
2. OCR preprocessing automatically applied for better accuracy
3. Works with various fonts and sizes
4. Case-insensitive matching

### Pattern Sequence Mode
Execute complex automation sequences:
```python
{
    'name': 'Login Sequence',
    'steps': [
        {'position': (500, 300)},  # Click username field
        {'keyboard': 'myusername'}, # Type username
        {'keyboard': ['tab']},     # Tab to password field
        {'keyboard': 'mypassword'}, # Type password
        {'keyboard': ['enter']},   # Submit
        {'delay': 2.0}             # Wait 2 seconds
    ]
}
```

### Mixed Mode
Combine image and text targets in single operation. The system will:
1. Check for image matches first
2. If no images found, check for text matches
3. Click the first successful match

### Sound Feedback
- Enable in Advanced Settings
- Plays sound on successful clicks
- Requires beep.wav file in working directory

### Debug Mode
- Save screenshots when targets are not found
- Helpful for troubleshooting recognition issues
- Files saved as: debug_screenshot_TIMESTAMP_suffix.png

## Troubleshooting

### Common Issues

#### "Can't connect to display" Error
**Symptoms**: GUI won't start, display connection errors
**Solutions**:
1. Ensure you're in a graphical environment
2. Check DISPLAY variable: `echo $DISPLAY`
3. For SSH: Use `ssh -X username@host`
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
1. Verify file path is correct
2. Use absolute paths
3. Check file permissions
4. Ensure supported format (PNG, JPG, BMP, TIFF, WebP)

#### OCR Not Finding Text
**Symptoms**: Text targets not detected
**Solutions**:
1. Increase screen resolution
2. Ensure good contrast
3. Try different preprocessing methods
4. Adjust confidence threshold
5. Check for anti-aliasing or font rendering issues

#### High CPU Usage
**Symptoms**: System becomes slow during operation
**Solutions**:
1. Increase check interval
2. Limit search region
3. Increase screenshot cache duration
4. Close unnecessary applications

#### False Positives
**Symptoms**: Clicking on wrong elements
**Solutions**:
1. Increase confidence threshold
2. Use more specific template images
3. Add safety zones around unwanted areas
4. Limit search region

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

### Log Analysis
Check the GUI log window for detailed error messages and operation status. Common log messages:

- `"Found text 'OK' using threshold preprocessing"` - OCR success
- `"No targets found, waiting..."` - Normal operation
- `"Safety zone violation"` - Click blocked by safety zone
- `"Template image not found"` - File access issue

## Best Practices

### Template Image Creation
1. **Crop tightly**: Include only the target element
2. **Consistent size**: Use same resolution as target screen
3. **Unique features**: Choose distinctive visual elements
4. **Avoid compression**: Use PNG for lossless quality
5. **Test variations**: Account for UI state changes

### Text Recognition
1. **Clear text**: Ensure good contrast and readability
2. **Consistent fonts**: Use same font/size across sessions
3. **Unique strings**: Choose distinctive text phrases
4. **Language support**: Ensure Tesseract language packs installed

### Performance Optimization
1. **Limit regions**: Use specific search areas when possible
2. **Adjust intervals**: Balance speed vs. CPU usage
3. **Cache screenshots**: Reduce screen capture frequency
4. **Batch operations**: Group similar targets

### Safety Measures
1. **Use safety zones**: Protect critical UI elements
2. **Set time limits**: Prevent runaway automation
3. **Test thoroughly**: Verify behavior before production use
4. **Monitor logs**: Watch for unexpected behavior
5. **Have manual override**: Keep emergency stop accessible

### Configuration Management
1. **Save profiles**: Export settings for different use cases
2. **Version control**: Track configuration changes
3. **Document setups**: Note target elements and conditions
4. **Backup settings**: Keep copies of working configurations

## FAQ

### General Questions

**Q: Is this safe to use?**
A: When used properly with safety zones and time limits, yes. Always test in safe environments first.

**Q: Does it work on Wayland?**
A: Limited support. X11 is recommended for best compatibility.

**Q: Can I use it on Windows/Mac?**
A: Currently Linux-only, but cross-platform support is planned.

**Q: How accurate is the OCR?**
A: Generally good with clear text. Preprocessing improves accuracy for challenging cases.

### Technical Questions

**Q: What's the best confidence setting?**
A: Start at 0.8 and adjust based on your specific use case. Higher for precision, lower for sensitivity.

**Q: Why does it use so much CPU?**
A: Screen capture and image processing are CPU-intensive. Increase intervals and limit regions to reduce usage.

**Q: Can I automate games with this?**
A: Technically possible, but not recommended. Game anti-cheat systems may detect automation.

**Q: How do I create good template images?**
A: Take screenshots, crop to target element only, use PNG format, test with different confidence levels.

### Usage Questions

**Q: Can I run multiple instances?**
A: Yes, but each needs separate configuration and may interfere with each other.

**Q: Does it work with remote desktops?**
A: Yes, with proper X forwarding or VNC setup.

**Q: Can I schedule automation?**
A: Use system cron jobs or scripts to launch at specific times.

**Q: How do I stop runaway automation?**
A: Use emergency stop (Ctrl+C), move mouse to corner, or set time limits.

### Support

For additional help:
1. Check the troubleshooting section
2. Run diagnostics: `./diagnose.sh`
3. Check logs for error details
4. Review configuration settings
5. Test with simple cases first

If you encounter bugs or need features, please check the project repository for updates and issue tracking.
