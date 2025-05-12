#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
import os


def run_menu():
    keys = (
        "\uf186   Suspender",
        "󰂭   Bloquear",
        "\uf021   Reiniciar",
        "\uf021   UEFI Firmware",
        "\uf011   Desligar",
    )

    actions = (
        "systemctl suspend",
        "hyprlock",
        "systemctl reboot",
        "systemctl reboot --firmware-setup",
        "systemctl poweroff",
    )

    options = "\n".join(keys)
    choice = (
        os.popen(
            "echo -e '"
            + options
            + "' | wofi -d -i -p 'Power Menu' -W 600 -H 300 -k /dev/null"
        )
        .readline()
        .strip()
    )
    if choice in keys:
        os.popen(actions[keys.index(choice)])


run_menu() 
'''
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess

def run_menu():
    keys = (
        "󰤄   Suspender",
        "󰌾   Bloquear",
        "󰜉   Reiniciar",
        "   UEFI Firmware",
        "󰐥   Desligar",
    )

    actions = (
        "systemctl suspend",
        "hyprlock",
        "systemctl reboot",
        "systemctl reboot --firmware-setup",
        "sudo /usr/bin/systemctl poweroff"
,
    )

    options = "\n".join(keys)
    result = subprocess.run(
        ["wofi", "-d", "-i", "Power Menu", "-W", "600", "-H", "300", "-k", "/dev/null"],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in keys:
        subprocess.run(actions[keys.index(result)], shell=True)

run_menu()
