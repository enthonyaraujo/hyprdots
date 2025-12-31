#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess

def config_menu():
    app_keys = (
        "󰫧   Environment Variables",
        "󱊬   Keyboard Shortcuts",
        "   Mouse and Keyboard",
        "󰀻   Startup Applications",
        "󰍹   Monitors",
        "   Workspaces",
        "   Audio Manager",
        "   Bluetooth Manager",
        "󰈀   Network Manager",
        "󰌑   Back",
    )
    
    app_actions = (
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/conf.d/environment_variables.conf'",  # environment_variables
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/conf.d/keybindings.conf'",  # keybindings
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/conf.d/input.conf'",  # input
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/conf.d/autostart.conf'",  # autostart
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/conf.d/monitors.conf'",  # monitors
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/conf.d/workspaces.conf'",
        "pavucontrol",
        "blueman-manager",
        "sh -c 'TERMINAL=kitty kitty -e nmtui'",
        "back",
    )

    options = "\n".join(app_keys)
    result = subprocess.run(
        ["wofi", "--dmenu", "--prompt", "Settings...", "--width", "500", "--height", "360"],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in app_keys:
        action = app_actions[app_keys.index(result)]
        if action == "back":
            menu_main()
        elif action.startswith("sh -c"):  
            subprocess.run(['hyprctl', 'dispatch', 'exec', action])
        else:
            subprocess.run(action.split(), shell=False)

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
        ["wofi","--dmenu", "--prompt", "System...", "--width", "500", "--height", "190"],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in keys:
        subprocess.run(actions[keys.index(result)], shell=True)

def menu_main():
    keys = (
        "󰣇   Archlinux Wiki",
        "   Hyprland Wiki",
        "󰀻   Applications",
        # "   Settings",
        "   System Monitor",
        "   System",
        "󰚰   Update",
        "   About",
    )

    actions = (
        "firefox --new-tab https://wiki.archlinux.org/title/Main_page",
        "firefox --new-tab https://wiki.hypr.land",
        "wofi --show drun", 
        # config_menu,
        "sh -c 'TERMINAL=kitty kitty --start-as maximized --hold -e btop'",
        system_menu,
        "sh -c 'TERMINAL=kitty kitty --hold -e sudo pacman -Syu'",
        "sh -c 'TERMINAL=kitty kitty --hold -e fastfetch'",
        
    )
    
    options = "\n".join(keys)
    result = subprocess.run(
        ["wofi", "--dmenu", "--prompt", "Menu...", "--width", "500", "--height", "300"],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in keys:
        idx = keys.index(result)
        action = actions[idx]

        if callable(action):
            action()
        else:
            subprocess.run(['hyprctl', 'dispatch', 'exec', action])

if __name__ == "__main__":
    menu_main()
