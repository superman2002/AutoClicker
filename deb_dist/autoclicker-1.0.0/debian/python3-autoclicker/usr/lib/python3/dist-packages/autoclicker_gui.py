#!/usr/bin/env python3
"""
AutoClicker GUI for Ubuntu - Graphical interface for the autoclicker
"""

import os
import sys
import subprocess
import json
import threading
import time
from tkinter import ttk
import tkinter as tk
from tkinter import filedialog, messagebox

def detect_display():
    """Detect available X11 display and set DISPLAY environment variable"""
    current_display = os.environ.get('DISPLAY', '')

    # If DISPLAY is already set and seems valid, try it
    if current_display and (current_display.startswith(':') or current_display.startswith('localhost:')):
        try:
            # Test if we can connect to the display by running a simple X11 command
            result = subprocess.run(['xset', '-q'], capture_output=True, timeout=2, env=dict(os.environ))
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            pass

    # Try to find available displays
    possible_displays = [':0', ':0.0', ':1', ':1.0', ':10.0', 'localhost:10.0', 'localhost:0.0']

    for display in possible_displays:
        try:
            # Test the display
            test_env = dict(os.environ)
            test_env['DISPLAY'] = display
            result = subprocess.run(['xset', '-q'], capture_output=True, timeout=2, env=test_env)
            if result.returncode == 0:
                os.environ['DISPLAY'] = display
                print(f"✅ Found working display: {display}")
                return True
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
            continue

    # If no display found, try to get from who command or other sources
    try:
        result = subprocess.run(['who'], capture_output=True, text=True, timeout=2)
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if '(' in line and ')' in line:
                    # Extract display from who output like "user :0 (192.168.1.1)"
                    parts = line.split('(')
                    if len(parts) > 0:
                        display_part = parts[0].strip().split()[-1]
                        if display_part.startswith(':'):
                            try:
                                test_env = dict(os.environ)
                                test_env['DISPLAY'] = display_part
                                result = subprocess.run(['xset', '-q'], capture_output=True, timeout=2, env=test_env)
                                if result.returncode == 0:
                                    os.environ['DISPLAY'] = display_part
                                    print(f"✅ Found working display from who: {display_part}")
                                    return True
                            except:
                                continue
    except:
        pass

    print("❌ No working X11 display found. Make sure you're running in a graphical environment.")
    print("💡 Try: export DISPLAY=:0.0")
    print("💡 Or: export DISPLAY=:10.0 (if using SSH)")
    return False

# Detect and set display before importing tkinter
if not detect_display():
    print("Cannot run GUI without a working X11 display.")
    print("Please run this in a graphical environment or set the DISPLAY variable manually.")
    sys.exit(1)

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time

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

# Import our autoclicker class
from autoclicker import AutoClicker

class AutoClickerGUI:
    def __init__(self, root, args=None):
        self.root = root
        self.root.title("AutoClicker for Ubuntu")
        self.root.geometry("500x700")
        self.root.resizable(False, False)

        # Make window always on top
        self.root.attributes('-topmost', True)

        # Settings file path
        self.settings_file = os.path.join(os.path.dirname(__file__), "autoclicker_settings.json")

        # Initialize variables
        self.autoclicker = None
        self.running = False
        self.thread = None

        # Check PyAutoGUI availability
        if not PYAUTOGUI_AVAILABLE:
            messagebox.showerror("Error", "PyAutoGUI not available. Please run in a graphical environment.")
            sys.exit(1)

        self.setup_ui()
        self.setup_hotkeys()
        self.load_settings()  # Load saved settings

        # Apply command-line arguments if provided
        if args:
            self.apply_args(args)

        self.log("Hotkeys: F6=Start, F7=Stop")

        # Bind window close event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def apply_args(self, args):
        """Apply command-line arguments to pre-populate the GUI"""
        if args.mode:
            self.mode_var.set(args.mode)
            self.update_mode()

        if args.target:
            # Clear example text
            self.target_text.delete("1.0", "end")
            # Add targets
            for target in args.target:
                self.target_text.insert("end", target + "\n")

        if args.confidence:
            self.confidence_var.set(args.confidence)

        if args.interval:
            self.interval_var.set(args.interval)

        if args.region:
            x, y, w, h = args.region
            self.region_vars[0].set(x)  # X
            self.region_vars[1].set(y)  # Y
            self.region_vars[2].set(w)  # Width
            self.region_vars[3].set(h)  # Height

    def setup_menu(self):
        """Set up the menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Settings", command=self.export_settings)
        file_menu.add_command(label="Import Settings", command=self.import_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_dark_mode)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def setup_ui(self):
        # Create menu bar
        self.setup_menu()

        # Mode selection
        mode_frame = ttk.LabelFrame(self.root, text="Mode", padding=10)
        mode_frame.pack(fill="x", padx=10, pady=5)

        self.mode_var = tk.StringVar(value="text")
        ttk.Radiobutton(mode_frame, text="Text Recognition", variable=self.mode_var,
                       value="text", command=self.update_mode).pack(side="left", padx=10)
        ttk.Radiobutton(mode_frame, text="Image Recognition", variable=self.mode_var,
                       value="image", command=self.update_mode).pack(side="left", padx=10)
        ttk.Radiobutton(mode_frame, text="Pattern Sequence", variable=self.mode_var,
                       value="pattern", command=self.update_mode).pack(side="left", padx=10)

        # Target input
        target_frame = ttk.LabelFrame(self.root, text="Targets (one per line)", padding=10)
        target_frame.pack(fill="x", padx=10, pady=5)

        self.target_text = tk.Text(target_frame, height=4, wrap="word")
        scrollbar = ttk.Scrollbar(target_frame, orient="vertical", command=self.target_text.yview)
        self.target_text.configure(yscrollcommand=scrollbar.set)

        self.target_text.pack(side="left", padx=5, fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Add some example text
        self.target_text.insert("1.0", "# Enter targets here (one per line):\n# Images: /path/to/image.png\n# Text: OK\n# Mixed: both supported")

        button_frame = ttk.Frame(target_frame)
        button_frame.pack(fill="x", pady=5)

        self.browse_button = ttk.Button(button_frame, text="Browse Image", command=self.browse_file)
        self.browse_button.pack(side="left", padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_targets)
        self.clear_button.pack(side="right", padx=5)

        # Settings
        settings_frame = ttk.LabelFrame(self.root, text="Settings", padding=10)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Confidence
        ttk.Label(settings_frame, text="Confidence:").grid(row=0, column=0, sticky="w", pady=2)
        self.confidence_var = tk.DoubleVar(value=0.8)
        confidence_scale = ttk.Scale(settings_frame, from_=0.1, to=1.0, variable=self.confidence_var,
                                   orient="horizontal", length=150)
        confidence_scale.grid(row=0, column=1, padx=5, pady=2)
        self.confidence_label = ttk.Label(settings_frame, text="0.80")
        self.confidence_label.grid(row=0, column=2, padx=5, pady=2)
        self.confidence_var.trace("w", self.update_confidence_label)

        # Interval
        ttk.Label(settings_frame, text="Interval (sec):").grid(row=1, column=0, sticky="w", pady=2)
        self.interval_var = tk.DoubleVar(value=1.0)
        interval_scale = ttk.Scale(settings_frame, from_=0.1, to=5.0, variable=self.interval_var,
                                 orient="horizontal", length=150)
        interval_scale.grid(row=1, column=1, padx=5, pady=2)
        self.interval_label = ttk.Label(settings_frame, text="1.00")
        self.interval_label.grid(row=1, column=2, padx=5, pady=2)
        self.interval_var.trace("w", self.update_interval_label)

        # Screenshot cache duration
        ttk.Label(settings_frame, text="Cache (sec):").grid(row=2, column=0, sticky="w", pady=2)
        self.cache_var = tk.DoubleVar(value=0.5)
        cache_scale = ttk.Scale(settings_frame, from_=0.1, to=2.0, variable=self.cache_var,
                               orient="horizontal", length=150)
        cache_scale.grid(row=2, column=1, padx=5, pady=2)
        self.cache_label = ttk.Label(settings_frame, text="0.50")
        self.cache_label.grid(row=2, column=2, padx=5, pady=2)
        self.cache_var.trace("w", self.update_cache_label)

        # Max runtime
        ttk.Label(settings_frame, text="Max Runtime (sec):").grid(row=3, column=0, sticky="w", pady=2)
        self.max_runtime_var = tk.IntVar(value=0)  # 0 means no limit
        max_runtime_entry = ttk.Entry(settings_frame, textvariable=self.max_runtime_var, width=10)
        max_runtime_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")
        ttk.Label(settings_frame, text="(0 = no limit)").grid(row=3, column=2, padx=5, pady=2, sticky="w")

        # Safety zones
        ttk.Label(settings_frame, text="Safety Zones:").grid(row=4, column=0, sticky="w", pady=2)
        safety_frame = ttk.Frame(settings_frame)
        safety_frame.grid(row=4, column=1, columnspan=2, sticky="w", pady=2)

        self.safety_zones_text = tk.Text(safety_frame, height=2, width=30, wrap="word")
        safety_scrollbar = ttk.Scrollbar(safety_frame, orient="vertical", command=self.safety_zones_text.yview)
        self.safety_zones_text.configure(yscrollcommand=safety_scrollbar.set)
        self.safety_zones_text.pack(side="left", fill="both", expand=True)
        safety_scrollbar.pack(side="right", fill="y")
        self.safety_zones_text.insert("1.0", "# Format: x,y,width,height per line\n# Example: 0,0,100,50")

        # Region selection
        ttk.Label(settings_frame, text="Region (X,Y,W,H):").grid(row=5, column=0, sticky="w", pady=2)
        region_frame = ttk.Frame(settings_frame)
        region_frame.grid(row=5, column=1, columnspan=2, sticky="w", pady=2)

        self.region_vars = []
        for i, label in enumerate(['X:', 'Y:', 'W:', 'H:']):
            ttk.Label(region_frame, text=label).grid(row=0, column=i*2, padx=2)
            var = tk.IntVar()
            entry = ttk.Entry(region_frame, textvariable=var, width=5)
            entry.grid(row=0, column=i*2+1, padx=2)
            self.region_vars.append(var)

        # Set default region (full screen)
        screen_width, screen_height = pyautogui.size()
        self.region_vars[0].set(0)  # X
        self.region_vars[1].set(0)  # Y
        self.region_vars[2].set(screen_width)  # Width
        self.region_vars[3].set(screen_height)  # Height

        ttk.Button(settings_frame, text="Select Region", command=self.select_region).grid(row=6, column=0, columnspan=3, pady=5)

        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_button = ttk.Button(control_frame, text="Start (F6)", command=self.start_autoclicker)
        self.start_button.pack(side="left", padx=5)

        self.pause_button = ttk.Button(control_frame, text="Pause (F8)", command=self.pause_autoclicker, state="disabled")
        self.pause_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop (F7)", command=self.stop_autoclicker, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        # Advanced settings
        advanced_frame = ttk.LabelFrame(self.root, text="Advanced Settings", padding=10)
        advanced_frame.pack(fill="x", padx=10, pady=5)

        # Sound feedback
        self.sound_feedback_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Sound Feedback", variable=self.sound_feedback_var).grid(row=0, column=0, sticky="w", pady=2)

        # Screenshot debug
        self.screenshot_debug_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(advanced_frame, text="Screenshot Debug", variable=self.screenshot_debug_var).grid(row=0, column=1, sticky="w", pady=2)

        # Hotkey customization
        ttk.Label(advanced_frame, text="Hotkeys:").grid(row=1, column=0, sticky="w", pady=2)
        hotkey_frame = ttk.Frame(advanced_frame)
        hotkey_frame.grid(row=1, column=1, sticky="w", pady=2)

        ttk.Label(hotkey_frame, text="Start:").grid(row=0, column=0)
        self.hotkey_start_var = tk.StringVar(value="f6")
        ttk.Entry(hotkey_frame, textvariable=self.hotkey_start_var, width=5).grid(row=0, column=1, padx=2)

        ttk.Label(hotkey_frame, text="Stop:").grid(row=0, column=2)
        self.hotkey_stop_var = tk.StringVar(value="f7")
        ttk.Entry(hotkey_frame, textvariable=self.hotkey_stop_var, width=5).grid(row=0, column=3, padx=2)

        ttk.Label(hotkey_frame, text="Pause:").grid(row=0, column=4)
        self.hotkey_pause_var = tk.StringVar(value="f8")
        ttk.Entry(hotkey_frame, textvariable=self.hotkey_pause_var, width=5).grid(row=0, column=5, padx=2)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=5)

        # Status
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(anchor="w")

        # Log
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="x", padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=12, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Initialize mode
        self.update_mode()

    def setup_hotkeys(self):
        """Set up keyboard hotkeys for start/stop"""
        # Bind F6 to start autoclicker
        self.root.bind('<F6>', lambda e: self.start_autoclicker())
        # Bind F7 to stop autoclicker
        self.root.bind('<F7>', lambda e: self.stop_autoclicker())

    def update_mode(self):
        mode = self.mode_var.get()
        # Clear example text when user changes mode
        current_text = self.target_text.get("1.0", "end-1c").strip()
        if current_text.startswith("#"):
            self.target_text.delete("1.0", "end")
            if mode == "image":
                self.target_text.insert("1.0", "# Enter image paths (one per line):\n# /path/to/image1.png\n# /path/to/image2.png")
            elif mode == "pattern":
                self.target_text.insert("1.0", "# Enter pattern definitions (one per line):\n# {'name': 'My Pattern', 'steps': [{'position': (100, 200)}, {'keyboard': 'enter'}]}")
            else:
                self.target_text.insert("1.0", "# Enter text targets (one per line):\n# OK\n# Cancel\n# Submit")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Template Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp"), ("All files", "*.*")]
        )
        if filename:
            # Clear example text if present
            current_text = self.target_text.get("1.0", "end-1c").strip()
            if current_text.startswith("#"):
                self.target_text.delete("1.0", "end")

            # Add the file to the text area
            current_content = self.target_text.get("1.0", "end-1c")
            if current_content and not current_content.endswith("\n"):
                self.target_text.insert("end", "\n")
            self.target_text.insert("end", filename + "\n")

    def clear_targets(self):
        """Clear all targets from the text area"""
        self.target_text.delete("1.0", "end")
        self.target_text.insert("1.0", "# Enter targets here (one per line)")

    def update_confidence_label(self, *args):
        self.confidence_label.config(text=f"{self.confidence_var.get():.2f}")

    def update_interval_label(self, *args):
        self.interval_label.config(text=f"{self.interval_var.get():.2f}")

    def update_cache_label(self, *args):
        self.cache_label.config(text=f"{self.cache_var.get():.2f}")

    def log(self, message):
        """Add message to log (thread-safe)"""
        self.root.after(0, lambda: self._log(message))

    def _log(self, message):
        """Internal log method - must be called from main thread"""
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def select_region(self):
        """Allow user to select a region by clicking and dragging"""
        try:
            self.log("Opening region selector...")

            # Create a full-screen region selector window
            selector = RegionSelector(self.root, self.on_region_selected)
            selector.start_selection()

        except Exception as e:
            self.log(f"Region selection error: {e}")

    def on_region_selected(self, region_coords):
        """Callback when region is selected"""
        if region_coords:
            x, y, w, h = region_coords
            self.region_vars[0].set(x)  # X
            self.region_vars[1].set(y)  # Y
            self.region_vars[2].set(w)  # Width
            self.region_vars[3].set(h)  # Height
            self.log(f"Region selected: {x},{y} {w}x{h}")
        else:
            self.log("Region selection cancelled")

    def get_region(self):
        """Get the current region settings"""
        x = self.region_vars[0].get()
        y = self.region_vars[1].get()
        w = self.region_vars[2].get()
        h = self.region_vars[3].get()

        # Return None if it's the full screen (default)
        screen_width, screen_height = pyautogui.size()
        if x == 0 and y == 0 and w == screen_width and h == screen_height:
            return None

        return (x, y, w, h)

    def get_targets(self):
        """Get targets from the text area, filtering out comments and empty lines"""
        content = self.target_text.get("1.0", "end-1c")
        lines = content.split('\n')
        targets = []

        for line in lines:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                targets.append(line)

        return targets

    def get_safety_zones(self):
        """Parse safety zones from the text area"""
        content = self.safety_zones_text.get("1.0", "end-1c")
        lines = content.split('\n')
        safety_zones = []

        for line in lines:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                try:
                    # Parse x,y,width,height format
                    parts = line.split(',')
                    if len(parts) == 4:
                        x, y, w, h = map(int, [p.strip() for p in parts])
                        if x >= 0 and y >= 0 and w > 0 and h > 0:
                            safety_zones.append((x, y, w, h))
                        else:
                            self.log(f"Invalid safety zone coordinates: {line}")
                    else:
                        self.log(f"Invalid safety zone format: {line}")
                except ValueError as e:
                    self.log(f"Error parsing safety zone '{line}': {e}")

        return safety_zones

    def start_autoclicker(self):
        if self.running:
            return

        mode = self.mode_var.get()
        targets = self.get_targets()

        if not targets:
            messagebox.showerror("Error", "Please specify at least one target")
            return

        # Validate image targets if in image mode
        if mode == "image":
            for target in targets:
                if not os.path.exists(target):
                    messagebox.showerror("Error", f"Image file not found: {target}")
                    return

        try:
            region = self.get_region()
            safety_zones = self.get_safety_zones()
            max_runtime = self.max_runtime_var.get() if self.max_runtime_var.get() > 0 else None

            # Setup hotkeys
            hotkeys = {
                'start': self.hotkey_start_var.get(),
                'stop': self.hotkey_stop_var.get(),
                'pause': self.hotkey_pause_var.get()
            }

            self.autoclicker = AutoClicker(
                confidence=self.confidence_var.get(),
                interval=self.interval_var.get(),
                region=region,
                cache_duration=self.cache_var.get(),
                logger=self.log,
                safety_zones=safety_zones,
                max_runtime=max_runtime,
                sound_feedback=self.sound_feedback_var.get(),
                screenshot_debug=self.screenshot_debug_var.get(),
                hotkeys=hotkeys
            )

            self.running = True
            self.start_button.config(state="disabled")
            self.pause_button.config(state="normal")
            self.stop_button.config(state="normal")
            self.status_var.set("Running...")
            self.status_label.config(foreground="green")

            self.log(f"Starting autoclicker with {len(targets)} target(s)...")

            # Start in a separate thread
            self.thread = threading.Thread(target=self.run_autoclicker, args=(mode, targets), daemon=True)
            self.thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start autoclicker: {e}")
            self.log(f"Error: {e}")

    def pause_autoclicker(self):
        if not self.running or not self.autoclicker:
            return

        # Toggle pause
        if self.autoclicker.pause_flag:
            # Resume
            self.autoclicker.toggle_pause()
            self.status_var.set("Running...")
            self.status_label.config(foreground="green")
            self.pause_button.config(text="Pause (F8)")
        else:
            # Pause
            self.autoclicker.toggle_pause()
            self.status_var.set("Paused")
            self.status_label.config(foreground="orange")
            self.pause_button.config(text="Resume (F8)")

    def stop_autoclicker(self):
        if not self.running:
            return

        self.running = False
        # Signal the autoclicker to stop
        if self.autoclicker:
            self.autoclicker.stop()

        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.status_var.set("Stopping...")
        self.status_label.config(foreground="orange")
        self.log("Stopping autoclicker...")

    def run_autoclicker(self, mode, targets):
        try:
            if mode == "image":
                self.autoclicker.run_image_clicker(targets)
            elif mode == "text":
                self.autoclicker.run_text_clicker(targets)
            elif mode == "pattern":
                # Parse pattern targets
                patterns = []
                for target in targets:
                    try:
                        pattern = eval(target)  # Simple eval for pattern dict
                        patterns.append(pattern)
                    except:
                        self.log(f"Invalid pattern format: {target}")
                if patterns:
                    self.autoclicker.run_pattern_clicker(patterns)
            else:  # mixed mode
                self.autoclicker.run_mixed_clicker(targets)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log(f"Error during execution: {e}")
        finally:
            self.running = False
            self.root.after(0, self.reset_ui)

    def reset_ui(self):
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.status_var.set("Ready")
        self.status_label.config(foreground="blue")
        self.pause_button.config(text="Pause (F8)")

    def save_settings(self):
        """Save current settings to JSON file"""
        try:
            settings = {
                "mode": self.mode_var.get(),
                "confidence": self.confidence_var.get(),
                "interval": self.interval_var.get(),
                "cache_duration": self.cache_var.get(),
                "max_runtime": self.max_runtime_var.get(),
                "safety_zones": self.safety_zones_text.get("1.0", "end-1c"),
                "region": {
                    "x": self.region_vars[0].get(),
                    "y": self.region_vars[1].get(),
                    "width": self.region_vars[2].get(),
                    "height": self.region_vars[3].get()
                },
                "targets": self.target_text.get("1.0", "end-1c"),
                "sound_feedback": self.sound_feedback_var.get(),
                "screenshot_debug": self.screenshot_debug_var.get(),
                "hotkeys": {
                    "start": self.hotkey_start_var.get(),
                    "stop": self.hotkey_stop_var.get(),
                    "pause": self.hotkey_pause_var.get()
                }
            }

            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)

        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        """Load settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)

                # Apply loaded settings
                if "mode" in settings:
                    self.mode_var.set(settings["mode"])
                    self.update_mode()

                if "confidence" in settings:
                    self.confidence_var.set(settings["confidence"])

                if "interval" in settings:
                    self.interval_var.set(settings["interval"])

                if "cache_duration" in settings:
                    self.cache_var.set(settings["cache_duration"])

                if "max_runtime" in settings:
                    self.max_runtime_var.set(settings["max_runtime"])

                if "safety_zones" in settings:
                    self.safety_zones_text.delete("1.0", "end")
                    self.safety_zones_text.insert("1.0", settings["safety_zones"])

                if "region" in settings:
                    region = settings["region"]
                    self.region_vars[0].set(region.get("x", 0))
                    self.region_vars[1].set(region.get("y", 0))
                    self.region_vars[2].set(region.get("width", pyautogui.size()[0]))
                    self.region_vars[3].set(region.get("height", pyautogui.size()[1]))

                if "targets" in settings:
                    self.target_text.delete("1.0", "end")
                    self.target_text.insert("1.0", settings["targets"])

                if "sound_feedback" in settings:
                    self.sound_feedback_var.set(settings["sound_feedback"])

                if "screenshot_debug" in settings:
                    self.screenshot_debug_var.set(settings["screenshot_debug"])

                if "hotkeys" in settings:
                    hotkeys = settings["hotkeys"]
                    self.hotkey_start_var.set(hotkeys.get("start", "f6"))
                    self.hotkey_stop_var.set(hotkeys.get("stop", "f7"))
                    self.hotkey_pause_var.set(hotkeys.get("pause", "f8"))

        except Exception as e:
            print(f"Error loading settings: {e}")

    def export_settings(self):
        """Export settings to a JSON file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Export Settings"
        )
        if filename:
            try:
                settings = {
                    "mode": self.mode_var.get(),
                    "confidence": self.confidence_var.get(),
                    "interval": self.interval_var.get(),
                    "cache_duration": self.cache_var.get(),
                    "max_runtime": self.max_runtime_var.get(),
                    "safety_zones": self.safety_zones_text.get("1.0", "end-1c"),
                    "region": {
                        "x": self.region_vars[0].get(),
                        "y": self.region_vars[1].get(),
                        "width": self.region_vars[2].get(),
                        "height": self.region_vars[3].get()
                    },
                    "targets": self.target_text.get("1.0", "end-1c"),
                    "sound_feedback": self.sound_feedback_var.get(),
                    "screenshot_debug": self.screenshot_debug_var.get(),
                    "hotkeys": {
                        "start": self.hotkey_start_var.get(),
                        "stop": self.hotkey_stop_var.get(),
                        "pause": self.hotkey_pause_var.get()
                    }
                }

                with open(filename, 'w') as f:
                    json.dump(settings, f, indent=2)

                messagebox.showinfo("Export Successful", f"Settings exported to {filename}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export settings: {e}")

    def import_settings(self):
        """Import settings from a JSON file"""
        filename = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Import Settings"
        )
        if filename:
            try:
                with open(filename, 'r') as f:
                    settings = json.load(f)

                # Apply loaded settings
                if "mode" in settings:
                    self.mode_var.set(settings["mode"])
                    self.update_mode()

                if "confidence" in settings:
                    self.confidence_var.set(settings["confidence"])

                if "interval" in settings:
                    self.interval_var.set(settings["interval"])

                if "cache_duration" in settings:
                    self.cache_var.set(settings["cache_duration"])

                if "max_runtime" in settings:
                    self.max_runtime_var.set(settings["max_runtime"])

                if "safety_zones" in settings:
                    self.safety_zones_text.delete("1.0", "end")
                    self.safety_zones_text.insert("1.0", settings["safety_zones"])

                if "region" in settings:
                    region = settings["region"]
                    self.region_vars[0].set(region.get("x", 0))
                    self.region_vars[1].set(region.get("y", 0))
                    self.region_vars[2].set(region.get("width", pyautogui.size()[0]))
                    self.region_vars[3].set(region.get("height", pyautogui.size()[1]))

                if "targets" in settings:
                    self.target_text.delete("1.0", "end")
                    self.target_text.insert("1.0", settings["targets"])

                messagebox.showinfo("Import Successful", f"Settings imported from {filename}")

            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import settings: {e}")

    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        # Simple dark mode implementation
        current_bg = self.root.cget('bg')
        if current_bg == 'SystemButtonFace' or current_bg == '':  # Light mode
            # Switch to dark mode
            self.root.configure(bg='#2b2b2b')
            self.log_text.configure(bg='#1e1e1e', fg='#ffffff')
        else:
            # Switch to light mode
            self.root.configure(bg='SystemButtonFace')
            self.log_text.configure(bg='white', fg='black')

    def show_about(self):
        """Show about dialog"""
        about_text = """AutoClicker for Ubuntu

Version: 2.0
A powerful autoclicker with image and text recognition capabilities.

Features:
- Image template matching
- OCR text recognition
- Mixed mode operation
- Safety zones
- Time limits
- Statistics tracking

Created with safety and reliability in mind."""
        messagebox.showinfo("About AutoClicker", about_text)

    def on_closing(self):
        """Handle window close event"""
        self.save_settings()
        self.root.destroy()


class RegionSelector:
    """Full-screen region selection tool"""
    def __init__(self, parent, callback):
        self.parent = parent
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.selector_window = None

    def start_selection(self):
        """Start the region selection process"""
        # Create full-screen selector window
        self.selector_window = tk.Toplevel(self.parent)
        self.selector_window.attributes('-fullscreen', True)
        self.selector_window.attributes('-topmost', True)
        self.selector_window.attributes('-alpha', 0.2)  # Light transparent
        self.selector_window.configure(bg='white')

        # Create canvas for drawing selection rectangle
        self.canvas = tk.Canvas(self.selector_window, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        # Instructions label
        instructions = tk.Label(self.selector_window,
                              text="Click and drag to select region\nPress ESC to cancel",
                              font=('Arial', 14, 'bold'),
                              bg='yellow',
                              fg='black',
                              relief='raised')
        instructions.place(relx=0.5, rely=0.1, anchor='center')

        # Bind mouse events
        self.canvas.bind('<ButtonPress-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        self.selector_window.bind('<Escape>', self.cancel_selection)
        self.selector_window.focus_set()

    def on_mouse_down(self, event):
        """Handle mouse button press"""
        self.start_x = event.x
        self.start_y = event.y

        # Remove any existing rectangle
        if self.rect:
            self.canvas.delete(self.rect)

        # Create new rectangle
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', fill='', width=2
        )

    def on_mouse_drag(self, event):
        """Handle mouse drag"""
        if self.rect and self.start_x is not None:
            # Update rectangle coordinates
            x1, y1 = min(self.start_x, event.x), min(self.start_y, event.y)
            x2, y2 = max(self.start_x, event.x), max(self.start_y, event.y)

            self.canvas.coords(self.rect, x1, y1, x2, y2)

    def on_mouse_up(self, event):
        """Handle mouse button release"""
        if self.start_x is not None:
            # Calculate final region coordinates
            x = min(self.start_x, event.x)
            y = min(self.start_y, event.y)
            w = abs(event.x - self.start_x)
            h = abs(event.y - self.start_y)

            # Close selector window
            self.selector_window.destroy()

            # Call callback with region coordinates
            self.callback((x, y, w, h))

    def cancel_selection(self, event=None):
        """Cancel region selection"""
        if self.selector_window:
            self.selector_window.destroy()
        self.callback(None)

def main():
    print("GUI starting...")
    import argparse

    parser = argparse.ArgumentParser(description='AutoClicker GUI for Ubuntu')
    parser.add_argument('--mode', choices=['image', 'text', 'mixed', 'pattern'],
                       help='Pre-select mode: image, text, mixed, or pattern')
    parser.add_argument('--target', action='append',
                       help='Pre-load target(s): path to template image or target text (can be used multiple times)')
    parser.add_argument('--confidence', type=float, default=0.8,
                       help='Pre-set confidence threshold (0.0-1.0)')
    parser.add_argument('--interval', type=float, default=1.0,
                       help='Pre-set check interval in seconds')
    parser.add_argument('--region', nargs=4, type=int, metavar=('X', 'Y', 'WIDTH', 'HEIGHT'),
                       help='Pre-set search region as X Y WIDTH HEIGHT')

    args = parser.parse_args()

    root = tk.Tk()
    gui = AutoClickerGUI(root, args)
    root.lift()  # Bring window to front
    root.mainloop()

if __name__ == "__main__":
    main()
