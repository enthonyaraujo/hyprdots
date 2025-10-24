#!/bin/bash
TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits)

USAGE=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits | awk '{print $1}')

echo "󰢮  ${USAGE}% ${TEMP}°C"

#    ${TEMP}°C copie com o espaço
