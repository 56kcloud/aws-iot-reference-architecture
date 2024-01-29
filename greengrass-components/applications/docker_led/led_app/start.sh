#!/bin/bash

# Get device serial number
SERIAL_NUMBER=$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2)

# Set unique topics with serial number
lambda_frequency_topic=$(echo $LAMBDA_FREQUENCY_TOPIC | sed "s/+/$SERIAL_NUMBER/")
lambda_button_topic=$(echo $LAMBDA_BUTTON_TOPIC | sed "s/+/$SERIAL_NUMBER/")
device_frequency_topic=$(echo $DEVICE_FREQUENCY_TOPIC | sed "s/+/$SERIAL_NUMBER/")

# Install libraries
python3 -m pip install -r /app/requirements.txt

# Run application
python3 -u /app/main.py $lambda_frequency_topic $lambda_button_topic $device_frequency_topic $DEVICE_BUTTON_TOPIC $FREQUENCY