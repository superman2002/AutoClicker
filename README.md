# AutoClicker for Ubuntu

A Python-based autoclicker that can find and click on user-defined images or text on screen using computer vision and OCR.

## Features

- **Image Recognition**: Uses OpenCV template matching to find images on screen
- **Text Recognition**: Uses Tesseract OCR to find text on screen
- **Mouse Automation**: Automatically moves cursor and clicks on detected targets
- **Configurable**: Adjustable confidence levels and check intervals
- **Safe**: Includes failsafe to stop with mouse in corner

## Requirements

- Ubuntu Linux with graphical desktop environment
- Python 3.6+
- Tesseract OCR (automatically installed)
- Required Python packages (automatically installed)
- X11 display server access (or Wayland with gnome-screenshot)

### System Dependencies

The autoclicker requires screenshot capability. Install the appropriate tool for your environment:

```bash
# For X11 environments
sudo apt install scrot

# For Wayland environments (Ubuntu 22.04+)
sudo apt install gnome-screenshot
```

## Installation

1. Clone or download this repository
2. Run the diagnostic script to check your setup:
   ```bash
   ./diagnose.sh
   ```
3. If everything looks good, run the setup:
   ```bash
   ./run.sh --help
   ```

All dependencies will be installed automatically.

## Usage

### Option 1: Graphical User Interface (Recommended)

For an easy-to-use graphical interface:

```bash
./run_gui.sh
```

The GUI provides:
- **Always-on-Top Window**: GUI stays visible above all other windows
- **Keyboard Hotkeys**: F6 to start, F7 to stop (works even when window is not focused)
- **Mode Selection**: Choose between Text Recognition and Image Recognition
- **Multiple Targets**: Enter multiple targets (one per line) in the text area
- **File Browser**: Browse and select template images for image mode
- **Text Input**: Enter target text for text recognition mode
- **Settings Sliders**: Adjust confidence level and check interval
- **Region Selection**: Define specific screen areas to search in (X, Y, Width, Height)
- **Visual Region Picker**: Click "Select Region" to interactively choose search area with click-and-drag
- **Start/Stop Controls**: Easy start and stop buttons
- **Real-time Status**: Live status updates and logging
- **Safety Features**: Same failsafes as command-line version

### Option 2: Command Line Interface

For advanced users or automation:

```bash
./run.sh --mode [image|text] --target [path_to_image|text_string] [options]
```

### Options

- `--mode`: Choose 'image' for template matching or 'text' for OCR
- `--target`: Path to template image file (for image mode) or target text string (for text mode)
- `--confidence`: Confidence threshold for image matching (0.0-1.0, default: 0.8)
- `--interval`: Time between screen checks in seconds (default: 1.0)

### Examples

#### Image Mode
Find and click on a specific button image:
```bash
./run.sh --mode image --target /path/to/button.png
```

With custom confidence:
```bash
./run.sh --mode image --target /path/to/button.png --confidence 0.9 --interval 0.5
```

With region restriction (search only in area 100,100 to 900,700):
```bash
./run.sh --mode text --target "OK" --region 100 100 800 600
```

Multiple targets (comma-separated):
```bash
./run.sh --mode text --target "OK,Cancel,Submit" --region 100 100 800 600
```

Multiple targets (separate arguments):
```bash
./run.sh --mode text --target "OK" --target "Cancel" --target "Submit"
```

Mixed mode (images and text):
```bash
./run.sh --mode mixed --target "OK" --target "/path/to/button.png" --target "Cancel"
```

#### Text Mode
Find and click on text containing "OK":
```bash
./run.sh --mode text --target "OK"
```

Find and click on "Submit" button:
```bash
./run.sh --mode text --target "Submit"
```

### How to Create Template Images

For image mode, you need to provide a template image of what you want to click on:

1. Take a screenshot of the target element
2. Crop the image to contain only the target (button, icon, etc.)
3. Save as PNG format (recommended for transparency support)
4. Use the path to this image as the `--target` parameter

### Safety Features

- **Failsafe**: Move mouse to any corner of the screen to stop the autoclicker
- **Confidence Threshold**: Only clicks when match confidence is above threshold
- **Keyboard Interrupt**: Press Ctrl+C in terminal to stop

### Tips

- For better OCR accuracy, ensure good screen resolution and contrast
- Template images should be as small as possible but still unique
- Adjust confidence level based on your needs (higher = more precise but may miss matches)
- Test with different intervals to balance speed and CPU usage

## Troubleshooting

### Common Issues

1. **"Can't connect to display" / "Authorization required, but no authorization protocol specified"**:
   This is the most common issue - the autoclicker requires access to a graphical display.

   **Solutions:**
   - **Local Ubuntu Desktop**: Run directly in your Ubuntu desktop environment
   - **SSH with X Forwarding**: `ssh -X username@hostname` (requires X11 on client)
   - **VNC/RDP**: Use remote desktop tools like Remmina, TeamViewer, or built-in VNC
   - **Virtual Display**: For testing, use Xvfb: `Xvfb :99 & export DISPLAY=:99`

   **Quick Test:**
   ```bash
   # Check if display is accessible
   xeyes  # Should open a window with eyes following mouse
   ```

2. **"PyAutoGUI not available"**: Same as display issue above - requires GUI environment

3. **"Template image not found"**: Check the path to your template image file

4. **"Could not load template image"**: Ensure the image file is not corrupted and is in a supported format (PNG recommended)

5. **OCR not finding text**: Check screen resolution, try adjusting text size, ensure good contrast

6. **Permission denied**: Make sure the script has execute permissions (`chmod +x run.sh`)

### Environment-Specific Setup

#### Ubuntu Desktop (Local)
```bash
# Should work out of the box
./run_gui.sh
```

#### SSH Session
```bash
# Enable X forwarding when connecting
ssh -X user@hostname

# Or set display manually
export DISPLAY=:10.0  # Adjust number as needed
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

### Dependencies

If you encounter issues with dependencies:

```bash
# System packages
sudo apt update
sudo apt install tesseract-ocr python3-tk scrot

# Python packages (in virtual environment)
source venv/bin/activate
pip install -r requirements.txt
```

## License

This project is open source. Use at your own risk.
