#!/bin/bash

state=$(pactl get-source-mute @DEFAULT_SOURCE@ 2>/dev/null | awk '{print $2}')

if [ -z "$state" ]; then
    echo "Mic não encontrado"
    exit 1
fi

if [ "$state" = "yes" ]; then
    echo "󰍭"
else
    echo "󰍮"
fi
