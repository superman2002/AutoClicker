#!/bin/bash
# AutoClicker Runner Script

# Activate virtual environment
source venv/bin/activate

# Run the autoclicker with provided arguments
python3 autoclicker.py "$@"

# Deactivate when done
deactivate
