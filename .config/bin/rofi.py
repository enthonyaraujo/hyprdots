#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
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
        "sh -c 'TERMINAL=kitty EDITOR=nvim kitty nvim ~/.config/hypr/monitors.conf'",  # monitors
        "sh -c 'TERMINAL=kitty EDITOR=nvim kitty nvim ~/.config/hypr/environmentvariables.conf'",  # environment_variables
        "sh -c 'TERMINAL=kitty EDITOR=nvim kitty nvim ~/.config/hypr/input_keybinds.conf'",  # input and keybindings
        "sh -c 'TERMINAL=kitty EDITOR=nvim kitty nvim ~/.config/hypr/my_programs.conf'",  # autostart
        "sh -c 'TERMINAL=kitty EDITOR=nvim kitty nvim ~/.config/hypr/window_workspaces.conf'",
        "pavucontrol",
        "blueman-manager",
    )
    options = "\n".join(app_keys)
    result = subprocess.run(
        [
            "rofi",
            "-dmenu",
            "-p", "",
            "-lines", str(len(app_keys)),
            "-theme-str", "window { width: 450px; }"
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
            "-lines", str(len(keys)),
            "-theme-str", "window { width: 420px; }"
        ],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in keys:
        subprocess.run(actions[keys.index(result)], shell=True)

def theme_menu():
    theme_file = os.path.expanduser("~/.config/theme.mode")
    current_mode = "dark"
    if os.path.exists(theme_file):
        try:
            with open(theme_file, "r") as f:
                current_mode = f.read().strip()
        except Exception:
            pass

    is_white = current_mode in ("white", "light")

    keys = (
        "󰖨   White Theme" + ("  (Ativo)" if is_white else ""),
        "󰃭   Dark Theme" + ("  (Ativo)" if not is_white else ""),
    )
    actions = (
        "~/.config/bin/switch-theme-mode.sh white",
        "~/.config/bin/switch-theme-mode.sh dark",
    )

    options = "\n".join(keys)
    result = subprocess.run(
        [
            "rofi",
            "-dmenu",
            "-p", "",
            "-lines", str(len(keys)),
            "-theme-str", "window { width: 380px; }"
        ],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in keys:
        idx = keys.index(result)
        cmd = os.path.expanduser(actions[idx])
        subprocess.run(cmd, shell=True)

def menu_main():
    keys = (
        "󰣇   Archlinux Wiki",
        "   Hyprland Wiki",
        "󰀻   Applications",
        "   Switch Wallpaper",
        "󰔎   Switch Theme",
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
        theme_menu,
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
            "-lines", str(len(keys)),
            "-theme-str", "window { width: 450px; }"
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
