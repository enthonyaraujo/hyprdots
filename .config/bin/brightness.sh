#!/bin/bash

step=5  

case "$1" in
    up)
        brightnessctl set ${step}%+
        ;;
    down)
        brightnessctl set ${step}%-
        ;;
    *)
        echo "Uso: $0 {up|down}"
        exit 1
        ;;
esac

brightness=$(brightnessctl get)
max_brightness=$(brightnessctl max)
percent=$((100 * brightness / max_brightness))



if [ "$percent" -lt 30 ]; then
    icon="󰃞"    
elif [ "$percent" -lt 70 ]; then
    icon="󰃟"    
else
    icon="󰃠"    
fi

dunstify -a "Brilho" \
         -u low \
         -r 9999 \
         -h int:value:"$percent" \
         "$icon ${percent}%"
