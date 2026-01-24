#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess

def system_menu():
    keys = (
        "󰤄   Suspend",
        "󰌾   Lock",
        "󰜉   Restart",
        "   UEFI Firmware",
        "󰐥   Power Off",
    )
    actions = (
        "systemctl suspend",
        "hyprlock",
        "systemctl reboot",
        "systemctl reboot --firmware-setup",
        "systemctl poweroff",
    )

    options = "\n".join(keys)

    result = subprocess.run(
        [
            "rofi",
            "-dmenu",
            "-p", "",
            "-lines", "5",
            "-theme-str", "window { width: 500px; height: 390; }"
        ],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in keys:
        subprocess.run(actions[keys.index(result)], shell=True)

if __name__ == "__main__":
    system_menu()
