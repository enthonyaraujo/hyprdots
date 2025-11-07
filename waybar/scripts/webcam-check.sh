#!/bin/bash

if fuser /dev/video* &> /dev/null; then  
    echo '{"text": "󰖠 ", "class": "camera-on", "tooltip": "Webcam em uso"}'
else
    echo '{}'
fi