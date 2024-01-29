#!/bin/bash

# Get device serial number
SERIAL_NUMBER=$(cat /proc/cpuinfo | grep Serial | cut -d ' ' -f 2)

# Set unique topics with serial number
lambda_csr_res_topic=$(echo $LAMBDA_CSR_RES_TOPIC | sed "s/+/$SERIAL_NUMBER/")
lambda_crt_ack_topic=$(echo $LAMBDA_CRT_ACK_TOPIC | sed "s/+/$SERIAL_NUMBER/")
device_csr_req_topic=$(echo $DEVICE_CSR_REQ_TOPIC | sed "s/+/$SERIAL_NUMBER/")
device_crt_topic=$(echo $DEVICE_CRT_TOPIC | sed "s/+/$SERIAL_NUMBER/")

# Install libraries
python3 -m pip install -r /app/requirements.txt

# Run application
python3 -u /app/main.py $lambda_csr_res_topic $lambda_crt_ack_topic $device_csr_req_topic $device_crt_topic $SERIAL_NUMBER