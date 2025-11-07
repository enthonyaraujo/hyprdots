#!/bin/bash

step=5  

case "$1" in
    up)

        current=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+%' | head -1 | tr -d '%')
        current=${current:-0}
        new=$((current + step))
        if [ "$new" -gt 100 ]; then
            new=100
        fi
        pactl set-sink-volume @DEFAULT_SINK@ ${new}%
        ;;
    down)
        current=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+%' | head -1 | tr -d '%')
        current=${current:-0}
        new=$((current - step))
        if [ "$new" -lt 0 ]; then
            new=0
        fi
        pactl set-sink-volume @DEFAULT_SINK@ ${new}%
        ;;
    mute)
        pactl set-sink-mute @DEFAULT_SINK@ toggle
        ;;
    *)
        echo "Uso: $0 {up|down|mute}"
        exit 1
        ;;
esac

volume=$(pactl get-sink-volume @DEFAULT_SINK@ | grep -oP '\d+%' | head -1 | tr -d '%')
volume=${volume:-0}

mute=$(pactl get-sink-mute @DEFAULT_SINK@ | grep -oP '(yes|no)')

if [ "$mute" = "yes" ]; then
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
