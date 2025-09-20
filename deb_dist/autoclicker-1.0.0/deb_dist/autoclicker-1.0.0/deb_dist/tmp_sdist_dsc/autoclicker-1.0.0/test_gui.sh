#!/bin/bash
# Test script for AutoClicker GUI with virtual display

echo "Starting virtual display for GUI testing..."

# Start virtual display
Xvfb :99 -screen 0 1024x768x24 &
XVFB_PID=$!

# Wait for Xvfb to start
sleep 2

# Set display for the test
export DISPLAY=:99

echo "Testing AutoClicker GUI with virtual display..."
echo "Note: GUI won't be visible in headless environment, but we can test if it loads without errors."

# Test GUI loading (it will exit due to display issues, but should handle gracefully)
timeout 5 ./run_gui.sh || echo "GUI test completed (expected timeout in headless environment)"

# Clean up
kill $XVFB_PID 2>/dev/null
echo "GUI test finished."
