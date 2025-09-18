#!/usr/bin/env python3
"""
Unit tests for AutoClicker core functionality
"""

import unittest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import cv2

# Add the current directory to the path so we can import autoclicker
sys.path.insert(0, os.path.dirname(__file__))

from autoclicker import AutoClicker

class TestAutoClicker(unittest.TestCase):
    """Test cases for AutoClicker class"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger = Mock()
        self.autoclicker = AutoClicker(logger=self.logger)

    def test_initialization(self):
        """Test AutoClicker initialization with default values"""
        clicker = AutoClicker()
        self.assertEqual(clicker.confidence, 0.8)
        self.assertEqual(clicker.interval, 1.0)
        self.assertIsNone(clicker.region)
        self.assertEqual(clicker.screenshot_cache_duration, 0.5)

    def test_initialization_with_params(self):
        """Test AutoClicker initialization with custom parameters"""
        clicker = AutoClicker(
            confidence=0.9,
            interval=2.0,
            region=(100, 100, 800, 600),
            cache_duration=1.0
        )
        self.assertEqual(clicker.confidence, 0.9)
        self.assertEqual(clicker.interval, 2.0)
        self.assertEqual(clicker.region, (100, 100, 800, 600))
        self.assertEqual(clicker.screenshot_cache_duration, 1.0)

    def test_validation_confidence(self):
        """Test confidence validation"""
        with self.assertRaises(ValueError):
            AutoClicker(confidence=-0.1)
        with self.assertRaises(ValueError):
            AutoClicker(confidence=1.1)

    def test_validation_interval(self):
        """Test interval validation"""
        with self.assertRaises(ValueError):
            AutoClicker(interval=-1.0)
        with self.assertRaises(ValueError):
            AutoClicker(interval=0)

    def test_validation_region(self):
        """Test region validation"""
        with self.assertRaises(ValueError):
            AutoClicker(region=(100, 100))  # Too few values
        with self.assertRaises(ValueError):
            AutoClicker(region=(-10, 100, 800, 600))  # Negative coordinates

    def test_validation_max_runtime(self):
        """Test max runtime validation"""
        with self.assertRaises(ValueError):
            AutoClicker(max_runtime=-1)
        with self.assertRaises(ValueError):
            AutoClicker(max_runtime=0)

    def test_safety_zone_check(self):
        """Test safety zone checking"""
        clicker = AutoClicker(safety_zones=[(0, 0, 100, 100), (200, 200, 50, 50)])

        # Test points inside safety zones
        self.assertTrue(clicker.is_in_safety_zone((50, 50)))
        self.assertTrue(clicker.is_in_safety_zone((225, 225)))

        # Test points outside safety zones
        self.assertFalse(clicker.is_in_safety_zone((150, 150)))
        self.assertFalse(clicker.is_in_safety_zone((300, 300)))

        # Test with no safety zones
        clicker_no_zones = AutoClicker()
        self.assertFalse(clicker_no_zones.is_in_safety_zone((50, 50)))

    def test_statistics(self):
        """Test statistics tracking"""
        clicker = AutoClicker()
        clicker.start_time_stats = 1000.0  # Mock start time

        # Mock some clicks
        clicker.click_count = 10
        clicker.success_count = 8

        with patch('time.time', return_value=1010.0):  # 10 seconds elapsed
            stats = clicker.get_statistics()

        self.assertEqual(stats['total_clicks'], 10)
        self.assertEqual(stats['successful_clicks'], 8)
        self.assertEqual(stats['success_rate'], 80.0)
        self.assertEqual(stats['elapsed_time'], 10.0)

    def test_statistics_no_clicks(self):
        """Test statistics with no clicks"""
        clicker = AutoClicker()
        clicker.start_time_stats = 1000.0

        with patch('time.time', return_value=1010.0):
            stats = clicker.get_statistics()

        self.assertEqual(stats['total_clicks'], 0)
        self.assertEqual(stats['successful_clicks'], 0)
        self.assertEqual(stats['success_rate'], 0)
        self.assertEqual(stats['elapsed_time'], 10.0)

    @patch('pyautogui.size')
    def test_region_default(self, mock_size):
        """Test default region setting"""
        mock_size.return_value = (1920, 1080)

        clicker = AutoClicker()
        # The region should be None initially, but get_region should return None for full screen
        self.assertIsNone(clicker.region)

    def test_time_limit_check(self):
        """Test time limit checking"""
        clicker = AutoClicker(max_runtime=10)
        clicker.start_time = 1000.0

        # Test within limit
        with patch('time.time', return_value=1005.0):  # 5 seconds elapsed
            self.assertFalse(clicker.check_time_limit())

        # Test at limit
        with patch('time.time', return_value=1010.0):  # 10 seconds elapsed
            self.assertTrue(clicker.check_time_limit())

        # Test over limit
        with patch('time.time', return_value=1015.0):  # 15 seconds elapsed
            self.assertTrue(clicker.check_time_limit())

    def test_time_limit_no_limit(self):
        """Test with no time limit"""
        clicker = AutoClicker()  # No max_runtime set
        clicker.start_time = 1000.0

        with patch('time.time', return_value=2000.0):  # Long time elapsed
            self.assertFalse(clicker.check_time_limit())

    @patch('autoclicker.pyautogui.click')
    @patch('autoclicker.pyautogui.moveTo')
    def test_click_at_success(self, mock_move, mock_click):
        """Test successful clicking"""
        clicker = AutoClicker()

        result = clicker.click_at((100, 200))

        mock_move.assert_called_once_with(100, 200)
        mock_click.assert_called_once()
        self.assertTrue(result)
        self.assertEqual(clicker.click_count, 1)
        self.assertEqual(clicker.success_count, 1)

    @patch('autoclicker.pyautogui.click')
    @patch('autoclicker.pyautogui.moveTo')
    def test_click_at_failure(self, mock_move, mock_click):
        """Test failed clicking"""
        mock_click.side_effect = Exception("Click failed")
        clicker = AutoClicker()

        result = clicker.click_at((100, 200))

        mock_move.assert_called_once_with(100, 200)
        mock_click.assert_called_once()
        self.assertFalse(result)
        self.assertEqual(clicker.click_count, 1)
        self.assertEqual(clicker.success_count, 0)

    def test_click_at_safety_zone(self):
        """Test clicking blocked by safety zone"""
        clicker = AutoClicker(safety_zones=[(0, 0, 200, 200)])

        result = clicker.click_at((100, 100))  # Inside safety zone

        self.assertFalse(result)
        self.assertEqual(clicker.click_count, 0)  # No click attempted

    def test_click_at_none_position(self):
        """Test clicking with None position"""
        clicker = AutoClicker()

        result = clicker.click_at(None)

        self.assertFalse(result)
        self.assertEqual(clicker.click_count, 0)

    @patch('autoclicker.playsound.playsound')
    def test_sound_feedback_enabled(self, mock_playsound):
        """Test sound feedback when enabled"""
        clicker = AutoClicker(sound_feedback=True)

        clicker.play_sound_feedback()

        mock_playsound.assert_called_once()

    @patch('autoclicker.playsound.playsound')
    def test_sound_feedback_disabled(self, mock_playsound):
        """Test sound feedback when disabled"""
        clicker = AutoClicker(sound_feedback=False)

        clicker.play_sound_feedback()

        mock_playsound.assert_not_called()

    def test_toggle_pause(self):
        """Test pause toggle functionality"""
        clicker = AutoClicker()

        # Initially not paused
        self.assertFalse(clicker.pause_flag)

        # Toggle to paused
        clicker.toggle_pause()
        self.assertTrue(clicker.pause_flag)

        # Toggle back to resumed
        clicker.toggle_pause()
        self.assertFalse(clicker.pause_flag)

    def test_stop(self):
        """Test stop functionality"""
        clicker = AutoClicker()

        # Initially not stopped
        self.assertFalse(clicker.stop_flag)

        # Stop
        clicker.stop()
        self.assertTrue(clicker.stop_flag)

    @patch('cv2.imread')
    @patch('os.path.exists')
    def test_find_image_file_not_found(self, mock_exists, mock_imread):
        """Test find_image when file doesn't exist"""
        mock_exists.return_value = False

        clicker = AutoClicker()
        result = clicker.find_image("/nonexistent/path/image.png")

        self.assertIsNone(result)
        mock_exists.assert_called_once_with("/nonexistent/path/image.png")
        mock_imread.assert_not_called()

    @patch('cv2.imread')
    @patch('os.path.exists')
    def test_find_image_load_failure(self, mock_exists, mock_imread):
        """Test find_image when image can't be loaded"""
        mock_exists.return_value = True
        mock_imread.return_value = None

        clicker = AutoClicker()
        result = clicker.find_image("/path/to/image.png")

        self.assertIsNone(result)
        mock_exists.assert_called_once_with("/path/to/image.png")
        mock_imread.assert_called_once()

    @patch('cv2.matchTemplate')
    @patch('cv2.minMaxLoc')
    @patch('cv2.imread')
    @patch('os.path.exists')
    def test_find_image_success(self, mock_exists, mock_imread, mock_minmax, mock_match):
        """Test successful image finding"""
        mock_exists.return_value = True

        # Mock template image
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        mock_imread.return_value = template

        # Mock screen capture
        screen = np.zeros((1080, 1920, 3), dtype=np.uint8)

        # Mock template matching result
        mock_match.return_value = np.array([[0.9]])  # High confidence match
        mock_minmax.return_value = (0, 0.9, (0, 0), (100, 100))  # Match at (100, 100)

        clicker = AutoClicker()

        with patch.object(clicker, 'capture_screen', return_value=screen):
            result = clicker.find_image("/path/to/template.png")

        # Should return center of matched region: (100 + 25, 100 + 25) = (125, 125)
        self.assertEqual(result, (125, 125))

    @patch('cv2.matchTemplate')
    @patch('cv2.minMaxLoc')
    @patch('cv2.imread')
    @patch('os.path.exists')
    def test_find_image_low_confidence(self, mock_exists, mock_imread, mock_minmax, mock_match):
        """Test image finding with low confidence"""
        mock_exists.return_value = True
        template = np.zeros((50, 50, 3), dtype=np.uint8)
        mock_imread.return_value = template
        screen = np.zeros((1080, 1920, 3), dtype=np.uint8)

        # Mock low confidence match
        mock_match.return_value = np.array([[0.5]])  # Below default 0.8 threshold
        mock_minmax.return_value = (0, 0.5, (0, 0), (100, 100))

        clicker = AutoClicker()

        with patch.object(clicker, 'capture_screen', return_value=screen):
            result = clicker.find_image("/path/to/template.png")

        self.assertIsNone(result)

    @patch('pytesseract.image_to_data')
    @patch('cv2.cvtColor')
    def test_find_text_success(self, mock_cvtcolor, mock_tesseract):
        """Test successful text finding"""
        # Mock OCR data
        mock_tesseract.return_value = {
            'text': ['', 'Hello', 'World', ''],
            'left': [0, 100, 200, 0],
            'top': [0, 50, 50, 0],
            'width': [0, 50, 50, 0],
            'height': [0, 20, 20, 0]
        }

        clicker = AutoClicker()

        screen = np.zeros((1080, 1920, 3), dtype=np.uint8)
        gray = np.zeros((1080, 1920), dtype=np.uint8)
        mock_cvtcolor.return_value = gray

        with patch.object(clicker, 'capture_screen', return_value=screen):
            result = clicker.find_text("World")

        # Should return center of "World": (200 + 25, 50 + 10) = (225, 60)
        self.assertEqual(result, (225, 60))

    @patch('pytesseract.image_to_data')
    @patch('cv2.cvtColor')
    def test_find_text_not_found(self, mock_cvtcolor, mock_tesseract):
        """Test text finding when text is not found"""
        mock_tesseract.return_value = {
            'text': ['', 'Hello', 'World', ''],
            'left': [0, 100, 200, 0],
            'top': [0, 50, 50, 0],
            'width': [0, 50, 50, 0],
            'height': [0, 20, 20, 0]
        }

        clicker = AutoClicker()

        screen = np.zeros((1080, 1920, 3), dtype=np.uint8)
        gray = np.zeros((1080, 1920), dtype=np.uint8)
        mock_cvtcolor.return_value = gray

        with patch.object(clicker, 'capture_screen', return_value=screen):
            result = clicker.find_text("NotFound")

        self.assertIsNone(result)

    def test_simulate_keyboard_input_string(self):
        """Test keyboard input simulation with string"""
        clicker = AutoClicker()

        with patch('pyautogui.press') as mock_press:
            clicker.simulate_keyboard_input("enter")

        mock_press.assert_called_once_with("enter")

    def test_simulate_keyboard_input_list(self):
        """Test keyboard input simulation with key combination"""
        clicker = AutoClicker()

        with patch('pyautogui.hotkey') as mock_hotkey:
            clicker.simulate_keyboard_input(['ctrl', 'c'])

        mock_hotkey.assert_called_once_with('ctrl', 'c')

    def test_execute_click_pattern(self):
        """Test click pattern execution"""
        clicker = AutoClicker()

        pattern = [
            {'position': (100, 200)},
            {'keyboard': 'enter'},
            {'delay': 0.5}
        ]

        with patch.object(clicker, 'click_at') as mock_click, \
             patch.object(clicker, 'simulate_keyboard_input') as mock_keyboard, \
             patch('time.sleep') as mock_sleep:

            clicker.execute_click_pattern(pattern)

        mock_click.assert_called_once_with((100, 200))
        mock_keyboard.assert_called_once_with('enter')
        mock_sleep.assert_called_once_with(0.5)

    def test_execute_click_pattern_with_stop(self):
        """Test click pattern execution with stop flag"""
        clicker = AutoClicker()
        clicker.stop_flag = True

        pattern = [
            {'position': (100, 200)},
            {'keyboard': 'enter'}
        ]

        with patch.object(clicker, 'click_at') as mock_click, \
             patch.object(clicker, 'simulate_keyboard_input') as mock_keyboard:

            clicker.execute_click_pattern(pattern)

        # Should not execute any steps when stopped
        mock_click.assert_not_called()
        mock_keyboard.assert_not_called()


if __name__ == '__main__':
    unittest.main()
