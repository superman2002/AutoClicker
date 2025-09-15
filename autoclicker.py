#!/usr/bin/env python3
"""
AutoClicker for Ubuntu - Finds and clicks on user-defined images or text
"""

import sys
import time
import argparse
import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
import subprocess
import tempfile

# Try to import pyautogui and handle display connection errors
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception as e:
    print(f"PyAutoGUI Error: {e}")
    PYAUTOGUI_AVAILABLE = False
    pyautogui = None

    # Try to fix common X11 authentication issues
    if "Authorization required" in str(e):
        print("\n🔧 Attempting to fix X11 authentication...")
        print("This is a common issue. Trying solutions:")

        # Try to disable X11 authentication for local connections
        import os
        import subprocess

        try:
            # Check if we're running locally
            display = os.environ.get('DISPLAY', '')
            if display.startswith(':'):
                print("1. Trying to allow local X11 connections...")
                subprocess.run(['xhost', '+local:'], check=False, capture_output=True)

                # Try importing again
                try:
                    import pyautogui
                    PYAUTOGUI_AVAILABLE = True
                    print("✅ Fixed! PyAutoGUI is now available.")
                except:
                    print("❌ Fix attempt failed.")
        except:
            print("❌ Could not apply X11 authentication fix.")

        if not PYAUTOGUI_AVAILABLE:
            print("\n📋 Manual solutions:")
            print("• Run: xhost +local:")
            print("• Or: export XAUTHORITY=~/.Xauthority")
            print("• Or use: ssh -X user@localhost")
            print("• Or set: export DISPLAY=:0.0")

class AutoClicker:
    def __init__(self, confidence=0.8, interval=1.0, region=None, cache_duration=0.5, logger=None):
        self.confidence = confidence
        self.interval = interval
        self.region = region  # Format: (x, y, width, height)
        self.stop_flag = False  # Flag to signal stopping
        self.logger = logger  # Logger callback function
        # Screenshot caching to reduce flickering
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.screenshot_cache_duration = cache_duration  # Cache screenshots for specified duration
        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.5
        else:
            error_msg = "Error: PyAutoGUI not available. Cannot initialize AutoClicker."
            if self.logger:
                self.logger(error_msg)
            else:
                print(error_msg)
            sys.exit(1)

    def stop(self):
        """Signal the autoclicker to stop"""
        self.stop_flag = True

    def capture_screen_flicker_free(self):
        """Capture screen using flicker-free methods (scrot/ImageMagick)"""
        try:
            # Try scrot first (usually flicker-free)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Try scrot with different options
            result = subprocess.run(['scrot', '--quality', '100', tmp_path],
                                  capture_output=True, timeout=3, env=dict(os.environ, DISPLAY=':0'))

            if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                time.sleep(0.1)  # Small delay to ensure file is fully written
                screenshot = cv2.imread(tmp_path)
                os.unlink(tmp_path)
                if screenshot is not None and screenshot.size > 0:
                    return screenshot

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, Exception) as e:
            if self.logger:
                self.logger(f"Scrot failed: {e}")
            pass

        try:
            # Fall back to ImageMagick import
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name

            result = subprocess.run(['import', '-window', 'root', '-quality', '100', tmp_path],
                                  capture_output=True, timeout=3, env=dict(os.environ, DISPLAY=':0'))

            if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                time.sleep(0.1)  # Small delay to ensure file is fully written
                screenshot = cv2.imread(tmp_path)
                os.unlink(tmp_path)
                if screenshot is not None and screenshot.size > 0:
                    return screenshot

        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, Exception) as e:
            if self.logger:
                self.logger(f"ImageMagick import failed: {e}")
            pass

        # Final fallback to PyAutoGUI
        if self.logger:
            self.logger("Warning: Using PyAutoGUI screenshot (may cause flicker)")
        screenshot = pyautogui.screenshot()
        return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    def capture_screen(self):
        """Capture the current screen with caching to reduce flickering"""
        current_time = time.time()

        # Use cached screenshot if it's recent enough
        if (self.last_screenshot is not None and
            current_time - self.last_screenshot_time < self.screenshot_cache_duration):
            return self.last_screenshot.copy()

        # Take new screenshot using flicker-free method
        self.last_screenshot = self.capture_screen_flicker_free()
        self.last_screenshot_time = current_time

        return self.last_screenshot.copy()

    def find_image(self, template_path):
        """Find image template on screen using OpenCV template matching"""
        if not os.path.exists(template_path):
            if self.logger:
                self.logger(f"Template image not found: {template_path}")
            return None

        screen = self.capture_screen()
        template = cv2.imread(template_path, cv2.IMREAD_COLOR)

        if template is None:
            if self.logger:
                self.logger(f"Could not load template image: {template_path}")
            return None

        # Perform template matching
        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.confidence:
            # Get center of the matched region
            template_height, template_width = template.shape[:2]
            center_x = max_loc[0] + template_width // 2
            center_y = max_loc[1] + template_height // 2
            return (center_x, center_y)

        return None

    def find_text(self, target_text):
        """Find text on screen using OCR"""
        screen = self.capture_screen()
        # Convert to grayscale for better OCR
        gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)

        # Use pytesseract to get text data with bounding boxes
        data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)

        for i, text in enumerate(data['text']):
            if target_text.lower() in text.lower():
                # Get bounding box
                x = data['left'][i]
                y = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]

                # Calculate center
                center_x = x + w // 2
                center_y = y + h // 2

                return (center_x, center_y)

        return None

    def click_at(self, position):
        """Click at the specified position"""
        if position:
            pyautogui.moveTo(position[0], position[1])
            pyautogui.click()
            return True
        return False

    def run_image_clicker(self, template_paths):
        """Main loop for image-based clicking with multiple templates"""
        if isinstance(template_paths, str):
            template_paths = [template_paths]

        if self.logger:
            self.logger(f"Starting image autoclicker with {len(template_paths)} template(s)")
            for i, path in enumerate(template_paths):
                self.logger(f"  {i+1}. {path}")
            self.logger("Press Ctrl+C to stop")

        try:
            while not self.stop_flag:
                for template_path in template_paths:
                    if self.stop_flag:
                        break
                    position = self.find_image(template_path)
                    if position:
                        if self.logger:
                            self.logger(f"Found target '{os.path.basename(template_path)}' at {position}, clicking...")
                        self.click_at(position)
                        break  # Click the first found target
                else:
                    if not self.stop_flag:
                        if self.logger:
                            self.logger("No targets found, waiting...")

                if not self.stop_flag:
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            if self.logger:
                self.logger("\nStopped by user")
        finally:
            if self.logger:
                self.logger("Image autoclicker stopped")

    def run_text_clicker(self, target_texts):
        """Main loop for text-based clicking with multiple targets"""
        if isinstance(target_texts, str):
            target_texts = [target_texts]

        if self.logger:
            self.logger(f"Starting text autoclicker for {len(target_texts)} target(s)")
            for i, text in enumerate(target_texts):
                self.logger(f"  {i+1}. '{text}'")
            self.logger("Press Ctrl+C to stop")

        try:
            while not self.stop_flag:
                for target_text in target_texts:
                    if self.stop_flag:
                        break
                    position = self.find_text(target_text)
                    if position:
                        if self.logger:
                            self.logger(f"Found text '{target_text}' at {position}, clicking...")
                        self.click_at(position)
                        break  # Click the first found target
                else:
                    if not self.stop_flag:
                        if self.logger:
                            self.logger("No targets found, waiting...")

                if not self.stop_flag:
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            if self.logger:
                self.logger("\nStopped by user")
        finally:
            if self.logger:
                self.logger("Text autoclicker stopped")

    def run_mixed_clicker(self, targets):
        """Main loop for mixed image and text targets"""
        images = []
        texts = []

        for target in targets:
            if target.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')) and os.path.exists(target):
                images.append(target)
            else:
                texts.append(target)

        if self.logger:
            self.logger(f"Starting mixed autoclicker with {len(images)} image(s) and {len(texts)} text target(s)")
            if images:
                self.logger("Images:")
                for i, img in enumerate(images):
                    self.logger(f"  {i+1}. {img}")
            if texts:
                self.logger("Texts:")
                for i, text in enumerate(texts):
                    self.logger(f"  {i+1}. '{text}'")
            self.logger("Press Ctrl+C to stop")

        try:
            while not self.stop_flag:
                # Check images first
                for image_path in images:
                    if self.stop_flag:
                        break
                    position = self.find_image(image_path)
                    if position:
                        if self.logger:
                            self.logger(f"Found image '{os.path.basename(image_path)}' at {position}, clicking...")
                        self.click_at(position)
                        break
                else:
                    # Check texts if no images found
                    for target_text in texts:
                        if self.stop_flag:
                            break
                        position = self.find_text(target_text)
                        if position:
                            if self.logger:
                                self.logger(f"Found text '{target_text}' at {position}, clicking...")
                            self.click_at(position)
                            break
                    else:
                        if not self.stop_flag:
                            if self.logger:
                                self.logger("No targets found, waiting...")

                if not self.stop_flag:
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            if self.logger:
                self.logger("\nStopped by user")
        finally:
            if self.logger:
                self.logger("Mixed autoclicker stopped")

def main():
    # Check if help is requested first
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        parser = argparse.ArgumentParser(description='AutoClicker for Ubuntu')
        parser.add_argument('--mode', choices=['image', 'text', 'mixed'], required=True,
                           help='Mode: image for template matching, text for OCR, mixed for both')
        parser.add_argument('--target', action='append', required=True,
                           help='Target(s): path to template image or target text (can be used multiple times)')
        parser.add_argument('--confidence', type=float, default=0.8,
                           help='Confidence threshold for image matching (0.0-1.0)')
        parser.add_argument('--interval', type=float, default=1.0,
                           help='Check interval in seconds')
        parser.add_argument('--region', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                           help='Search region as X Y WIDTH HEIGHT (e.g., --region 100 100 800 600)')
        parser.print_help()
        return

    # Check PyAutoGUI availability for actual operation
    if not PYAUTOGUI_AVAILABLE:
        print("Error: Cannot run AutoClicker without display access.")
        print("Please run this in a graphical environment or with proper X forwarding.")
        print("For help, run: ./run.sh --help")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='AutoClicker for Ubuntu')
    parser.add_argument('--mode', choices=['image', 'text', 'mixed'], required=True,
                       help='Mode: image for template matching, text for OCR, mixed for both')
    parser.add_argument('--target', action='append', required=True,
                       help='Target(s): path to template image or target text (can be used multiple times)')
    parser.add_argument('--confidence', type=float, default=0.8,
                       help='Confidence threshold for image matching (0.0-1.0)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Check interval in seconds')
    parser.add_argument('--region', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                       help='Search region as X Y WIDTH HEIGHT (e.g., --region 100 100 800 600)')

    args = parser.parse_args()

    # Parse targets (flatten if needed)
    targets = []
    for target in args.target:
        # Split comma-separated values
        targets.extend([t.strip() for t in target.split(',') if t.strip()])

    print(f"Targets: {targets}")

    # Parse region if provided
    region = None
    if args.region:
        region = tuple(args.region)
        print(f"Using search region: {region}")

    clicker = AutoClicker(confidence=args.confidence, interval=args.interval, region=region)

    if args.mode == 'image':
        clicker.run_image_clicker(targets)
    elif args.mode == 'text':
        clicker.run_text_clicker(targets)
    elif args.mode == 'mixed':
        clicker.run_mixed_clicker(targets)

if __name__ == "__main__":
    main()
