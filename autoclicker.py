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
import threading
import keyboard
import playsound
from pynput import keyboard as pynput_keyboard

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
    def __init__(self, confidence=0.8, interval=1.0, region=None, cache_duration=0.5, logger=None,
                 safety_zones=None, max_runtime=None, emergency_stop_keys=None, click_patterns=None,
                 keyboard_inputs=None, sound_feedback=False, screenshot_debug=False, hotkeys=None):
        # Input validation
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if interval <= 0:
            raise ValueError("Interval must be positive")
        if cache_duration < 0:
            raise ValueError("Cache duration must be non-negative")
        if region and len(region) != 4:
            raise ValueError("Region must be a tuple of 4 integers (x, y, width, height)")
        if region and any(r < 0 for r in region):
            raise ValueError("Region coordinates must be non-negative")
        if max_runtime and max_runtime <= 0:
            raise ValueError("Max runtime must be positive")

        self.confidence = confidence
        self.interval = interval
        self.region = region  # Format: (x, y, width, height)
        self.stop_flag = False  # Flag to signal stopping
        self.pause_flag = False  # Flag to signal pausing
        self.logger = logger  # Logger callback function
        # Screenshot caching to reduce flickering
        self.last_screenshot = None
        self.last_screenshot_time = 0
        self.screenshot_cache_duration = cache_duration  # Cache screenshots for specified duration

        # Safety features
        self.safety_zones = safety_zones or []  # List of (x, y, w, h) tuples to avoid
        self.max_runtime = max_runtime  # Maximum runtime in seconds
        self.start_time = None
        self.emergency_stop_keys = emergency_stop_keys or ['ctrl', 'alt', 'shift']  # Default emergency stop combo

        # New features
        self.click_patterns = click_patterns or []  # List of click sequences
        self.keyboard_inputs = keyboard_inputs or []  # List of keyboard inputs to simulate
        self.sound_feedback = sound_feedback  # Enable sound feedback
        self.screenshot_debug = screenshot_debug  # Save screenshots for debugging
        self.hotkeys = hotkeys or {'start': 'f6', 'stop': 'f7', 'pause': 'f8'}  # Custom hotkeys

        # Statistics
        self.click_count = 0
        self.success_count = 0
        self.start_time_stats = None

        # Keyboard listener for hotkeys
        self.keyboard_listener = None
        self.setup_hotkeys()

        if PYAUTOGUI_AVAILABLE:
            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0.5
        else:
            error_msg = "Error: PyAutoGUI not available. Cannot initialize AutoClicker."
            if self.logger:
                self.logger(error_msg)
            else:
                print(error_msg)
            raise RuntimeError("PyAutoGUI not available")

    def setup_hotkeys(self):
        """Setup custom hotkeys for start/stop/pause"""
        try:
            # Use pynput for better cross-platform hotkey support
            self.keyboard_listener = pynput_keyboard.Listener(on_press=self.on_hotkey_press)
            self.keyboard_listener.start()
        except Exception as e:
            if self.logger:
                self.logger(f"Failed to setup hotkeys: {e}")

    def on_hotkey_press(self, key):
        """Handle hotkey presses"""
        try:
            key_str = key.name if hasattr(key, 'name') else str(key).replace("'", "")
            if key_str == self.hotkeys.get('start', 'f6'):
                if not self.running:
                    self.start_autoclicker()
            elif key_str == self.hotkeys.get('stop', 'f7'):
                self.stop()
            elif key_str == self.hotkeys.get('pause', 'f8'):
                self.toggle_pause()
        except Exception as e:
            if self.logger:
                self.logger(f"Hotkey error: {e}")

    def start_autoclicker(self):
        """Start the autoclicker (for hotkey use)"""
        # This would need to be implemented based on current mode/targets
        pass

    def toggle_pause(self):
        """Toggle pause/resume functionality"""
        self.pause_flag = not self.pause_flag
        if self.logger:
            if self.pause_flag:
                self.logger("Autoclicker paused")
            else:
                self.logger("Autoclicker resumed")

    def stop(self):
        """Signal the autoclicker to stop"""
        self.stop_flag = True

    def play_sound_feedback(self):
        """Play sound feedback for successful clicks"""
        if self.sound_feedback:
            try:
                # Play a simple beep sound
                playsound.playsound('beep.wav', block=False)
            except Exception as e:
                if self.logger:
                    self.logger(f"Sound feedback error: {e}")

    def save_debug_screenshot(self, screenshot, filename_suffix="debug"):
        """Save screenshot for debugging failed detections"""
        if self.screenshot_debug:
            try:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"debug_screenshot_{timestamp}_{filename_suffix}.png"
                cv2.imwrite(filename, screenshot)
                if self.logger:
                    self.logger(f"Debug screenshot saved: {filename}")
            except Exception as e:
                if self.logger:
                    self.logger(f"Failed to save debug screenshot: {e}")

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

        # Check supported image formats
        supported_extensions = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp']
        file_ext = os.path.splitext(template_path)[1].lower()

        if file_ext not in supported_extensions:
            if self.logger:
                self.logger(f"Unsupported image format: {file_ext}. Supported: {', '.join(supported_extensions)}")
            return None

        screen = self.capture_screen()

        # Try different flags for different image formats
        template = None
        load_flags = [cv2.IMREAD_COLOR, cv2.IMREAD_GRAYSCALE, cv2.IMREAD_UNCHANGED]

        for flag in load_flags:
            template = cv2.imread(template_path, flag)
            if template is not None:
                # Convert to 3-channel color image if necessary
                if len(template.shape) == 2:  # Grayscale
                    template = cv2.cvtColor(template, cv2.COLOR_GRAY2BGR)
                elif len(template.shape) == 3 and template.shape[2] == 4:  # RGBA
                    template = cv2.cvtColor(template, cv2.COLOR_BGRA2BGR)
                break

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

        # Save debug screenshot if enabled
        if self.screenshot_debug:
            self.save_debug_screenshot(screen, f"failed_match_{os.path.basename(template_path)}")

        return None

    def preprocess_image_for_ocr(self, image):
        """Apply preprocessing to improve OCR accuracy"""
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        # Apply different preprocessing techniques
        preprocessed_images = []

        # Original grayscale
        preprocessed_images.append(('original', gray))

        # Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        preprocessed_images.append(('blurred', blurred))

        # Thresholding - Otsu's method
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        preprocessed_images.append(('threshold', thresh))

        # Adaptive thresholding
        adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                               cv2.THRESH_BINARY, 11, 2)
        preprocessed_images.append(('adaptive_threshold', adaptive_thresh))

        # Morphological operations to clean up text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morphed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        preprocessed_images.append(('morphology', morphed))

        # Contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        preprocessed_images.append(('enhanced', enhanced))

        # Bilateral filter for noise reduction while keeping edges
        bilateral = cv2.bilateralFilter(gray, 9, 75, 75)
        preprocessed_images.append(('bilateral', bilateral))

        return preprocessed_images

    def find_text(self, target_text, use_preprocessing=True):
        """Find text on screen using OCR with optional preprocessing"""
        screen = self.capture_screen()

        if use_preprocessing:
            # Try different preprocessing methods
            preprocessed_images = self.preprocess_image_for_ocr(screen)

            for method_name, processed_img in preprocessed_images:
                try:
                    # Use pytesseract to get text data with bounding boxes
                    data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT)

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

                            if self.logger:
                                self.logger(f"Found text '{target_text}' using {method_name} preprocessing at {center_x}, {center_y}")
                            return (center_x, center_y)
                except Exception as e:
                    if self.logger:
                        self.logger(f"OCR preprocessing method '{method_name}' failed: {e}")
                    continue

            # If no preprocessing method worked, fall back to basic method
            if self.logger:
                self.logger("All OCR preprocessing methods failed, using basic OCR")

        # Basic OCR without preprocessing
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

        # Save debug screenshot if enabled
        if self.screenshot_debug:
            self.save_debug_screenshot(screen, f"failed_ocr_{target_text}")

        return None

    def is_in_safety_zone(self, position):
        """Check if position is within any safety zone"""
        if not position or not self.safety_zones:
            return False

        x, y = position
        for zone in self.safety_zones:
            zx, zy, zw, zh = zone
            if zx <= x <= zx + zw and zy <= y <= zy + zh:
                return True
        return False

    def check_time_limit(self):
        """Check if max runtime has been exceeded"""
        if self.max_runtime and self.start_time:
            elapsed = time.time() - self.start_time
            if elapsed >= self.max_runtime:
                if self.logger:
                    self.logger(f"Max runtime of {self.max_runtime}s exceeded")
                return True
        return False

    def simulate_keyboard_input(self, key_input):
        """Simulate keyboard input"""
        try:
            if isinstance(key_input, str):
                pyautogui.press(key_input)
            elif isinstance(key_input, list):
                pyautogui.hotkey(*key_input)
            if self.logger:
                self.logger(f"Simulated keyboard input: {key_input}")
        except Exception as e:
            if self.logger:
                self.logger(f"Keyboard input failed: {e}")

    def execute_click_pattern(self, pattern):
        """Execute a click pattern sequence"""
        for step in pattern:
            if self.stop_flag:
                break
            if isinstance(step, dict):
                if 'position' in step:
                    self.click_at(step['position'])
                if 'keyboard' in step:
                    self.simulate_keyboard_input(step['keyboard'])
                if 'delay' in step:
                    time.sleep(step['delay'])
            time.sleep(0.1)  # Small delay between pattern steps

    def click_at(self, position):
        """Click at the specified position with safety checks"""
        if not position:
            return False

        # Check safety zones
        if self.is_in_safety_zone(position):
            if self.logger:
                self.logger(f"Safety zone violation at {position}, skipping click")
            return False

        # Check time limit
        if self.check_time_limit():
            self.stop_flag = True
            return False

        try:
            pyautogui.moveTo(position[0], position[1])
            pyautogui.click()
            self.click_count += 1
            self.success_count += 1
            self.play_sound_feedback()  # Play sound feedback
            return True
        except Exception as e:
            if self.logger:
                self.logger(f"Click failed at {position}: {e}")
            self.click_count += 1
            return False

    def get_statistics(self):
        """Get current statistics"""
        elapsed = time.time() - self.start_time_stats if self.start_time_stats else 0
        success_rate = (self.success_count / self.click_count * 100) if self.click_count > 0 else 0
        return {
            'total_clicks': self.click_count,
            'successful_clicks': self.success_count,
            'success_rate': success_rate,
            'elapsed_time': elapsed
        }

    def run_image_clicker(self, template_paths):
        """Main loop for image-based clicking with multiple templates"""
        if isinstance(template_paths, str):
            template_paths = [template_paths]

        # Initialize timing
        self.start_time = time.time()
        self.start_time_stats = time.time()

        if self.logger:
            self.logger(f"Starting image autoclicker with {len(template_paths)} template(s)")
            for i, path in enumerate(template_paths):
                self.logger(f"  {i+1}. {path}")
            self.logger("Press Ctrl+C to stop")

        try:
            while not self.stop_flag:
                # Check time limit
                if self.check_time_limit():
                    break

                # Handle pause
                while self.pause_flag and not self.stop_flag:
                    time.sleep(0.1)

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
                stats = self.get_statistics()
                self.logger(f"Image autoclicker stopped - Stats: {stats['total_clicks']} clicks, {stats['success_rate']:.1f}% success rate, {stats['elapsed_time']:.1f}s elapsed")
            if self.logger:
                self.logger("Image autoclicker stopped")

    def run_text_clicker(self, target_texts):
        """Main loop for text-based clicking with multiple targets"""
        if isinstance(target_texts, str):
            target_texts = [target_texts]

        # Initialize timing
        self.start_time = time.time()
        self.start_time_stats = time.time()

        if self.logger:
            self.logger(f"Starting text autoclicker for {len(target_texts)} target(s)")
            for i, text in enumerate(target_texts):
                self.logger(f"  {i+1}. '{text}'")
            self.logger("Press Ctrl+C to stop")

        try:
            while not self.stop_flag:
                # Check time limit
                if self.check_time_limit():
                    break

                # Handle pause
                while self.pause_flag and not self.stop_flag:
                    time.sleep(0.1)

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
                stats = self.get_statistics()
                self.logger(f"Text autoclicker stopped - Stats: {stats['total_clicks']} clicks, {stats['success_rate']:.1f}% success rate, {stats['elapsed_time']:.1f}s elapsed")
            if self.logger:
                self.logger("Text autoclicker stopped")

    def run_mixed_clicker(self, targets):
        """Main loop for mixed image and text targets"""
        images = []
        texts = []

        for target in targets:
            if target.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp')) and os.path.exists(target):
                images.append(target)
            else:
                texts.append(target)

        # Initialize timing
        self.start_time = time.time()
        self.start_time_stats = time.time()

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
                # Check time limit
                if self.check_time_limit():
                    break

                # Handle pause
                while self.pause_flag and not self.stop_flag:
                    time.sleep(0.1)

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
                stats = self.get_statistics()
                self.logger(f"Mixed autoclicker stopped - Stats: {stats['total_clicks']} clicks, {stats['success_rate']:.1f}% success rate, {stats['elapsed_time']:.1f}s elapsed")
            if self.logger:
                self.logger("Mixed autoclicker stopped")

    def run_pattern_clicker(self, patterns):
        """Main loop for click pattern sequences"""
        if isinstance(patterns, dict):
            patterns = [patterns]

        # Initialize timing
        self.start_time = time.time()
        self.start_time_stats = time.time()

        if self.logger:
            self.logger(f"Starting pattern autoclicker with {len(patterns)} pattern(s)")
            self.logger("Press Ctrl+C to stop")

        try:
            while not self.stop_flag:
                # Check time limit
                if self.check_time_limit():
                    break

                # Handle pause
                while self.pause_flag and not self.stop_flag:
                    time.sleep(0.1)

                for pattern in patterns:
                    if self.stop_flag:
                        break
                    if self.logger:
                        self.logger(f"Executing pattern: {pattern.get('name', 'Unnamed')}")
                    self.execute_click_pattern(pattern.get('steps', []))
                    break  # Execute one pattern per cycle

                if not self.stop_flag:
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            if self.logger:
                self.logger("\nStopped by user")
        finally:
            if self.logger:
                stats = self.get_statistics()
                self.logger(f"Pattern autoclicker stopped - Stats: {stats['total_clicks']} clicks, {stats['success_rate']:.1f}% success rate, {stats['elapsed_time']:.1f}s elapsed")
            if self.logger:
                self.logger("Pattern autoclicker stopped")

def main():
    # Check if help is requested first
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        parser = argparse.ArgumentParser(description='AutoClicker for Ubuntu')
        parser.add_argument('--mode', choices=['image', 'text', 'mixed', 'pattern'], required=True,
                           help='Mode: image for template matching, text for OCR, mixed for both, pattern for sequences')
        parser.add_argument('--target', action='append', required=True,
                           help='Target(s): path to template image or target text (can be used multiple times)')
        parser.add_argument('--confidence', type=float, default=0.8,
                           help='Confidence threshold for image matching (0.0-1.0)')
        parser.add_argument('--interval', type=float, default=1.0,
                           help='Check interval in seconds')
        parser.add_argument('--region', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                           help='Search region as X Y WIDTH HEIGHT (e.g., --region 100 100 800 600)')
        parser.add_argument('--sound-feedback', action='store_true',
                           help='Enable sound feedback for successful clicks')
        parser.add_argument('--screenshot-debug', action='store_true',
                           help='Save screenshots for debugging failed detections')
        parser.add_argument('--hotkey-start', type=str, default='f6',
                           help='Hotkey to start autoclicker')
        parser.add_argument('--hotkey-stop', type=str, default='f7',
                           help='Hotkey to stop autoclicker')
        parser.add_argument('--hotkey-pause', type=str, default='f8',
                           help='Hotkey to pause/resume autoclicker')
        parser.print_help()
        return

    # Check PyAutoGUI availability for actual operation
    if not PYAUTOGUI_AVAILABLE:
        print("Error: Cannot run AutoClicker without display access.")
        print("Please run this in a graphical environment or with proper X forwarding.")
        print("For help, run: ./run.sh --help")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='AutoClicker for Ubuntu')
    parser.add_argument('--mode', choices=['image', 'text', 'mixed', 'pattern'], required=True,
                       help='Mode: image for template matching, text for OCR, mixed for both, pattern for sequences')
    parser.add_argument('--target', action='append', required=True,
                       help='Target(s): path to template image or target text (can be used multiple times)')
    parser.add_argument('--confidence', type=float, default=0.8,
                       help='Confidence threshold for image matching (0.0-1.0)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Check interval in seconds')
    parser.add_argument('--region', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                       help='Search region as X Y WIDTH HEIGHT (e.g., --region 100 100 800 600)')
    parser.add_argument('--sound-feedback', action='store_true',
                       help='Enable sound feedback for successful clicks')
    parser.add_argument('--screenshot-debug', action='store_true',
                       help='Save screenshots for debugging failed detections')
    parser.add_argument('--hotkey-start', type=str, default='f6',
                       help='Hotkey to start autoclicker')
    parser.add_argument('--hotkey-stop', type=str, default='f7',
                       help='Hotkey to stop autoclicker')
    parser.add_argument('--hotkey-pause', type=str, default='f8',
                       help='Hotkey to pause/resume autoclicker')

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

    # Setup hotkeys
    hotkeys = {
        'start': args.hotkey_start,
        'stop': args.hotkey_stop,
        'pause': args.hotkey_pause
    }

    clicker = AutoClicker(
        confidence=args.confidence,
        interval=args.interval,
        region=region,
        sound_feedback=args.sound_feedback,
        screenshot_debug=args.screenshot_debug,
        hotkeys=hotkeys
    )

    if args.mode == 'image':
        clicker.run_image_clicker(targets)
    elif args.mode == 'text':
        clicker.run_text_clicker(targets)
    elif args.mode == 'mixed':
        clicker.run_mixed_clicker(targets)
    elif args.mode == 'pattern':
        # For pattern mode, targets should be pattern definitions
        patterns = []
        for target in targets:
            try:
                pattern = eval(target)  # Simple eval for pattern dict
                patterns.append(pattern)
            except:
                print(f"Invalid pattern format: {target}")
        clicker.run_pattern_clicker(patterns)

if __name__ == "__main__":
    main()
