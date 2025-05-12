#!/bin/bash

BATTERY_DIR=$(find /sys/class/power_supply/ -type d -name "BAT*" | head -n 1)

if [[ -z "$BATTERY_DIR" ]]; then
    echo "Bateria não encontrada."
    exit 1
fi

STATUS=$(cat "$BATTERY_DIR/status")
CAPACITY=$(cat "$BATTERY_DIR/capacity")

# Charging
if [[ "$STATUS" == "Charging" ]]; then
    if [ "$CAPACITY" -ge 100 ]; then icon="󰂅"
    elif [ "$CAPACITY" -ge 90 ]; then icon="󰂋"
    elif [ "$CAPACITY" -ge 80 ]; then icon="󰢞"
    elif [ "$CAPACITY" -ge 70 ]; then icon="󰢞"
    elif [ "$CAPACITY" -ge 60 ]; then icon="󰂉"
    elif [ "$CAPACITY" -ge 50 ]; then icon="󰢝"
    elif [ "$CAPACITY" -ge 40 ]; then icon="󰂈"
    elif [ "$CAPACITY" -ge 30 ]; then icon="󰂇"
    elif [ "$CAPACITY" -ge 20 ]; then icon="󰂆"
    else icon="󰂎"
    fi
else  # Discharging
    if [ "$CAPACITY" -ge 100 ]; then icon="󰁹"
    elif [ "$CAPACITY" -ge 90 ]; then icon="󰂂"
    elif [ "$CAPACITY" -ge 80 ]; then icon="󰂁"
    elif [ "$CAPACITY" -ge 70 ]; then icon="󰂀"
    elif [ "$CAPACITY" -ge 60 ]; then icon="󰁿"
    elif [ "$CAPACITY" -ge 50 ]; then icon="󰁾"
    elif [ "$CAPACITY" -ge 40 ]; then icon="󰁽"
    elif [ "$CAPACITY" -ge 30 ]; then icon="󰁼"
    elif [ "$CAPACITY" -ge 20 ]; then icon="󰁻"
    elif [ "$CAPACITY" -ge 10 ]; then icon="󰁺"
    else icon="󰂎"
    fi
fi

echo "{$icon}"
