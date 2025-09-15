#!/usr/bin/env python3
"""
AutoClicker GUI for Ubuntu - Graphical interface for the autoclicker
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import time
import os
import sys
import json

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
    def __init__(self, root):
        self.root = root
        self.root.title("AutoClicker for Ubuntu")
        self.root.geometry("500x600")
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
        self.log("Hotkeys: F6=Start, F7=Stop")

        # Bind window close event to save settings
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        # Mode selection
        mode_frame = ttk.LabelFrame(self.root, text="Mode", padding=10)
        mode_frame.pack(fill="x", padx=10, pady=5)

        self.mode_var = tk.StringVar(value="text")
        ttk.Radiobutton(mode_frame, text="Text Recognition", variable=self.mode_var,
                       value="text", command=self.update_mode).pack(side="left", padx=10)
        ttk.Radiobutton(mode_frame, text="Image Recognition", variable=self.mode_var,
                       value="image", command=self.update_mode).pack(side="left", padx=10)

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

        # Region selection
        ttk.Label(settings_frame, text="Region (X,Y,W,H):").grid(row=3, column=0, sticky="w", pady=2)
        region_frame = ttk.Frame(settings_frame)
        region_frame.grid(row=3, column=1, columnspan=2, sticky="w", pady=2)

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

        ttk.Button(settings_frame, text="Select Region", command=self.select_region).grid(row=4, column=0, columnspan=3, pady=5)

        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.pack(fill="x", padx=10, pady=10)

        self.start_button = ttk.Button(control_frame, text="Start (F6)", command=self.start_autoclicker)
        self.start_button.pack(side="left", padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop (F7)", command=self.stop_autoclicker, state="disabled")
        self.stop_button.pack(side="left", padx=5)

        # Status
        status_frame = ttk.LabelFrame(self.root, text="Status", padding=10)
        status_frame.pack(fill="x", padx=10, pady=5)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, foreground="blue")
        self.status_label.pack(anchor="w")

        # Log
        log_frame = ttk.LabelFrame(self.root, text="Log", padding=10)
        log_frame.pack(fill="x", padx=10, pady=5)

        self.log_text = tk.Text(log_frame, height=6, wrap="word", state="disabled")
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
            else:
                self.target_text.insert("1.0", "# Enter text targets (one per line):\n# OK\n# Cancel\n# Submit")

    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select Template Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"), ("All files", "*.*")]
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
        """Add message to log"""
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
            self.autoclicker = AutoClicker(
                confidence=self.confidence_var.get(),
                interval=self.interval_var.get(),
                region=region,
                cache_duration=self.cache_var.get()
            )

            self.running = True
            self.start_button.config(state="disabled")
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

    def stop_autoclicker(self):
        if not self.running:
            return

        self.running = False
        # Signal the autoclicker to stop
        if self.autoclicker:
            self.autoclicker.stop()

        self.start_button.config(state="normal")
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
        self.stop_button.config(state="disabled")
        self.status_var.set("Ready")
        self.status_label.config(foreground="blue")

    def save_settings(self):
        """Save current settings to JSON file"""
        try:
            # Separate text targets from image targets
            all_targets = self.get_targets()
            text_targets = []
            image_targets = []

            for target in all_targets:
                if target.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')) and os.path.exists(target):
                    image_targets.append(target)
                else:
                    text_targets.append(target)

            settings = {
                "mode": self.mode_var.get(),
                "confidence": self.confidence_var.get(),
                "interval": self.interval_var.get(),
                "cache_duration": self.cache_var.get(),
                "region": {
                    "x": self.region_vars[0].get(),
                    "y": self.region_vars[1].get(),
                    "width": self.region_vars[2].get(),
                    "height": self.region_vars[3].get()
                },
                "text_targets": text_targets,
                "image_targets": image_targets,
                "targets_text": self.target_text.get("1.0", "end-1c")  # Keep original text for display
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

                if "region" in settings:
                    region = settings["region"]
                    self.region_vars[0].set(region.get("x", 0))
                    self.region_vars[1].set(region.get("y", 0))
                    self.region_vars[2].set(region.get("width", pyautogui.size()[0]))
                    self.region_vars[3].set(region.get("height", pyautogui.size()[1]))

                # Load targets - handle both old and new formats
                self.target_text.delete("1.0", "end")

                if "targets_text" in settings:
                    # New format with separate text/image targets
                    self.target_text.insert("1.0", settings["targets_text"])
                elif "targets" in settings:
                    # Old format - single targets string
                    self.target_text.insert("1.0", settings["targets"])
                else:
                    # No targets - use default
                    self.target_text.insert("1.0", "# Enter targets here (one per line):\n# Images: /path/to/image.png\n# Text: OK\n# Mixed: both supported")

        except Exception as e:
            print(f"Error loading settings: {e}")

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
        self.selector_window.attributes('-alpha', 0.3)  # Semi-transparent
        self.selector_window.configure(bg='gray')

        # Create canvas for drawing selection rectangle
        self.canvas = tk.Canvas(self.selector_window, bg='gray', highlightthickness=0)
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
            outline='red', fill='red', stipple='gray50', width=2
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
    root = tk.Tk()
    app = AutoClickerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
