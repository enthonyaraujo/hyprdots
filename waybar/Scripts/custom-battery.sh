#!/bin/bash

BAT=$(upower -i $(upower -e | grep BAT) | grep "state" | awk '{print $2}')
PERC=$(upower -i $(upower -e | grep BAT) | grep "percentage" | awk '{print $2}' | tr -d '%')

ICON="󰁹" 
if [[ $PERC -lt 10 ]]; then ICON="󰁺"
elif [[ $PERC -lt 20 ]]; then ICON="󰁻"
elif [[ $PERC -lt 30 ]]; then ICON="󰁼"
elif [[ $PERC -lt 40 ]]; then ICON="󰁽"
elif [[ $PERC -lt 50 ]]; then ICON="󰁾"
elif [[ $PERC -lt 60 ]]; then ICON="󰁿"
elif [[ $PERC -lt 70 ]]; then ICON="󰂀"
elif [[ $PERC -lt 80 ]]; then ICON="󰂁"
elif [[ $PERC -lt 90 ]]; then ICON="󰂂"
fi

if [[ $BAT == "charging" ]]; then
    ICON="󰂉"   
elif [[ $BAT == "fully-charged" ]]; then
    ICON="󰂅"   
fi

echo "{\"text\":\"$ICON \", \"tooltip\":\"$PERC% ($BAT)\"}"
