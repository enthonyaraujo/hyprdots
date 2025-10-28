#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess

def config_menu():
    app_keys = (
        "󰫧   Variáveis de Ambiente",
        "󱊬   Atalhos de Teclado",
        "   Mouse e Teclado",
        "󰀻   Aplicativos de Inicialização",
        "󰍹   Monitores",
        "   Espaços de Trabalho",
        "   Gerenciador de Áudio",
        "   Gerenciador de Bluetooth",
        "󰈀   Gerenciador de Internet",
        "󰌑   Voltar",
    )
    
    app_actions = (
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/Configs/environment_variables.conf'",  # environment_variables
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/Configs/keybindings.conf'",  # keybindings
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/Configs/input.conf'",  # input
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/Configs/autostart.conf'",  # autostart
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/Configs/monitors.conf'",  # monitors
        "sh -c 'TERMINAL=kitty EDITOR=nano kitty -e nano ~/.config/hypr/Configs/workspaces.conf'",
        "pavucontrol",
        "blueman-manager",
        "sh -c 'TERMINAL=kitty kitty -e nmtui'",
        "back",
    )

    options = "\n".join(app_keys)
    result = subprocess.run(
        ["wofi", "--dmenu", "--prompt", "Menu Configurações", "--width", "600", "--height", "500"],
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
        "systemctl poweroff",
    )

    options = "\n".join(keys)
    result = subprocess.run(
        ["wofi", "--dmenu", "--prompt", "Power Menu", "--width", "600", "--height", "300"],
        input=options,
        text=True,
        stdout=subprocess.PIPE
    ).stdout.strip()

    if result in keys:
        subprocess.run(actions[keys.index(result)], shell=True)

def menu_main():
    keys = (
        "󰣇   Archlinux Wiki",
        "   Hyprland Wiki ",
        "󰀻   Aplicativos",
        "   Configurações",
        "   Monitor do sistema",
        "   Sistema",
        "󰚰   Atualizar",
        "   Sobre",
    )

    actions = (
        "firefox --new-tab https://wiki.archlinux.org/title/Main_page",
        "firefox --new-tab https://wiki.hypr.land/",
        "wofi --show drun", 
        config_menu,
        "sh -c 'TERMINAL=kitty kitty --start-as maximized --hold -e btop'",
        system_menu,
        "sh -c 'TERMINAL=kitty kitty --hold -e sudo pacman -Syu'",
        "sh -c 'TERMINAL=kitty kitty --hold -e fastfetch'",
        
    )
    
    options = "\n".join(keys)
    result = subprocess.run(
        ["wofi", "--dmenu", "--prompt", "", "--width", "500", "--height", "350"],
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
