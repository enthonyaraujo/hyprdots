#!/bin/bash

# pega modo atual
current=$(powerprofilesctl get)

# define ícone/label do modo atual
case "$current" in
    performance)
        status="⚡ Current: Performance"
        ;;
    balanced)
        status="🔋 Current: Balanced"
        ;;
    power-saver)
        status="🌱 Current: Power Saver"
        ;;
    *)
        status="❓ Current: Unknown"
        ;;
esac

options="⚡ Performance\n🔋 Balanced\n🌱 Power Saver"

choice=$(echo -e "$status \n $options" | rofi -dmenu -p "Power Profile" \
-theme-str 'window {width: 420px;} listview {lines: 5; spacing: 8px;}')

case "$choice" in
    "⚡ Performance")
        powerprofilesctl set performance
        ;;
    "🔋 Balanced")
        powerprofilesctl set balanced
        ;;
    "🌱 Power Saver")
        powerprofilesctl set power-saver
        ;;
esac