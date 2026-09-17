#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import subprocess

def system_menu():
    theme_path = os.path.expanduser("~/.config/rofi/powermenu.rasi")

    menu_items = [
        ("󰌾   Lock Screen", "hyprlock"),
        ("󰤄   Suspend", "systemctl suspend"),
        ("󰍃   Log Out", "hyprctl dispatch exit"),
        ("󰜉   Restart", "systemctl reboot"),
        ("   UEFI Firmware", "systemctl reboot --firmware-setup"),
        ("󰐥   Power Off", "systemctl poweroff"),
    ]

    keys = [item[0] for item in menu_items]
    actions = [item[1] for item in menu_items]
    options = "\n".join(keys)

    cmd = ["rofi", "-dmenu", "-p", "⏻  Power Menu"]
    if os.path.exists(theme_path):
        cmd.extend(["-theme", theme_path])

    res = subprocess.run(
        cmd,
        input=options,
        text=True,
        stdout=subprocess.PIPE
    )

    choice = res.stdout.strip()
    if choice in keys:
        idx = keys.index(choice)
        action = actions[idx]
        if action.startswith("hyprctl"):
            subprocess.run(action.split())
        else:
            subprocess.run(action, shell=True)

if __name__ == "__main__":
    system_menu()
