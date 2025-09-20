#!/bin/bash
# AutoClicker Display Diagnostic Script

echo "🔍 AutoClicker Display Diagnostic Tool"
echo "======================================"
echo ""

# Check if we're in a graphical environment
echo "1. Checking display environment..."
if [ -z "$DISPLAY" ]; then
    echo "❌ DISPLAY variable not set"
    echo "   This means you're in a headless environment"
else
    echo "✅ DISPLAY variable set to: $DISPLAY"
fi

# Check if X11 is available
echo ""
echo "2. Checking X11 availability..."
if command -v xset >/dev/null 2>&1; then
    if xset q >/dev/null 2>&1; then
        echo "✅ X11 server is accessible"
    else
        echo "❌ X11 server not accessible (xset failed)"
    fi
else
    echo "⚠️  xset not available (may be Wayland environment)"
fi

# Check for screenshot tools
echo ""
echo "3. Checking screenshot capabilities..."
if command -v scrot >/dev/null 2>&1; then
    echo "✅ scrot available (X11)"
elif command -v gnome-screenshot >/dev/null 2>&1; then
    echo "✅ gnome-screenshot available (Wayland)"
else
    echo "❌ No screenshot tool found"
    echo "   Install with: sudo apt install scrot  # for X11"
    echo "   Or: sudo apt install gnome-screenshot  # for Wayland"
fi

# Check Python and PyAutoGUI
echo ""
echo "4. Checking Python environment..."
if command -v python3 >/dev/null 2>&1; then
    echo "✅ Python 3 available"

    # Test PyAutoGUI import
    if python3 -c "import pyautogui; print('✅ PyAutoGUI can be imported')" 2>/dev/null; then
        echo "✅ PyAutoGUI import successful"
    else
        echo "❌ PyAutoGUI import failed"
        echo "   This is expected in headless environments"
    fi
else
    echo "❌ Python 3 not found"
fi

# Check virtual environment
echo ""
echo "5. Checking virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    if [ -f "venv/bin/activate" ]; then
        echo "✅ Virtual environment activation script found"
    else
        echo "❌ Virtual environment activation script missing"
    fi
else
    echo "❌ Virtual environment not found"
    echo "   Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

echo ""
echo "📋 RECOMMENDATIONS:"
echo "=================="

if [ -z "$DISPLAY" ]; then
    echo "• You're in a headless environment. To use the autoclicker:"
    echo "  - Run on a local Ubuntu desktop"
    echo "  - Use SSH with X forwarding: ssh -X user@hostname"
    echo "  - Set up VNC or remote desktop"
    echo "  - For testing: Xvfb :99 -screen 0 1024x768x24 & export DISPLAY=:99"
else
    echo "• You have a display environment. The autoclicker should work!"
    echo "  - Try running: ./run_gui.sh"
    echo "  - Or: ./run.sh --mode text --target \"test\""
fi

if ! command -v scrot >/dev/null 2>&1 && ! command -v gnome-screenshot >/dev/null 2>&1; then
    echo "• Install screenshot tool:"
    echo "  sudo apt install scrot          # for X11"
    echo "  sudo apt install gnome-screenshot # for Wayland"
fi

echo ""
echo "🧪 QUICK TEST:"
echo "=============="
echo "Run this to test if your display works:"
echo "  xeyes  # Should open a window with eyes following mouse"
echo ""
echo "If xeyes doesn't work, you need to fix your display setup first."
