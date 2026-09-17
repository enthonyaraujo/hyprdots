#!/bin/bash

# Extract only the NVIDIA GPU usage number
usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)

# If nvidia-smi fails or returns empty, set to 0
if [ -z "$usage" ]; then
  usage="0"
fi

# Format output in JSON for Waybar
echo "{\"text\": \"$usage%\", \"tooltip\": \"GPU Usage: $usage%\", \"class\": \"gpu\"}"
