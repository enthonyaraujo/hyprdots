#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess

def config_menu():
    app_keys = (
        "󰍹   Monitors",
        "󰫧   Environment Variables",
        "   Mouse and Keyboard",
        "󰀻   Programs",
        "   Workspaces",
        "   Audio Manager",
        "   Bluetooth Manager",
    )
    
    app_actions = (
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/monitors.conf'",  # monitors
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/environmentvariables.conf'",  # environment_variables
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/input_keybinds.conf'",  # input and keybindings
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/my_programs.conf'",  # autostart
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/window_workspaces.conf'",
        "pavucontrol",
        "blueman-manager",
    )
    options = "\n".join(app_keys)
    result = subprocess.run(
        [
            "rofi",
            "-dmenu",
            "-p", "",
            "-lines", "5",
            "-theme-str", "window { width: 500px; height: 500; }"
        ],
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
        [
            "rofi",
            "-dmenu",
            "-p", "",
            "-lines", "5",
            "-theme-str", "window { width: 500px; height: 550; }"
        ],
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
        "   Switch theme",
        "   Settings",
        "   System Monitor",
        "   System",
        "󰚰   Update",
        "   About",
    )

    actions = (
        "firefox --new-tab https://wiki.archlinux.org/title/Main_page",
        "firefox --new-tab https://wiki.hypr.land",
        "rofi -show drun",
        "$HOME/.config/bin/switch-theme.sh", 
        config_menu,
        "sh -c 'TERMINAL=kitty kitty --start-as maximized --hold -e btop'",
        system_menu,
        "sh -c 'TERMINAL=kitty kitty --hold -e sudo pacman -Syu'",
        "sh -c 'TERMINAL=kitty kitty --hold -e fastfetch'",
        
    )
    
    options = "\n".join(keys)
    result = subprocess.run(
        [
            "rofi",
            "-dmenu",
            "-p", "",
            "-lines", "5",
            "-theme-str", "window { width: 500px; height: 550; }"
        ],
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
