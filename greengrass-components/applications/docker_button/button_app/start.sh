#!/bin/bash

# Install libraries
python3 -m pip install -r /app/requirements.txt

# Run application
python3 -u /app/main.py $DEVICE_BUTTON_TOPIC