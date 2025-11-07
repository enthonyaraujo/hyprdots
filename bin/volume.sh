#!/bin/bash

step=5 

case "$1" in
    up)
       
        wpctl set-volume @DEFAULT_AUDIO_SINK@ ${step}%+
        ;;
    down)
       
        wpctl set-volume @DEFAULT_AUDIO_SINK@ ${step}%-
        ;;
    mute)
       
        wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
        ;;
    *)
        echo "Uso: $0 {up|down|mute}"
        exit 1
        ;;
esac


volume=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | awk '{print int($2 * 100)}')
volume=${volume:-0}

mute=$(wpctl get-volume @DEFAULT_AUDIO_SINK@ | grep -o '\[MUTED\]')

if [ -n "$mute" ]; then
    icon="󰝟"
    msg="Mudo"
    level=0
else
    if [ "$volume" -eq 0 ]; then
        icon="󰕿"
    elif [ "$volume" -lt 50 ]; then
        icon="󰖀"
    else
        icon="󰕾"
    fi
    msg="${volume}%"
    level=$volume
fi

dunstify -a "Volume" \
         -u low \
         -r 9998 \
         -h int:value:"$level" \
         "$icon ${msg}"
