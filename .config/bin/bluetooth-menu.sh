#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import subprocess
import time

THEME_PATH = os.path.expanduser("~/.config/rofi/applet.rasi")

def notify(summary, body, urgency="normal"):
    subprocess.run(["notify-send", "-u", urgency, "-a", "Bluetooth", summary, body])

def run_rofi(prompt, options_list):
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if os.path.exists(THEME_PATH):
        cmd.extend(["-theme", THEME_PATH])
    proc = subprocess.run(
        cmd,
        input="\n".join(options_list),
        text=True,
        stdout=subprocess.PIPE
    )
    return proc.stdout.strip()

def is_powered():
    res = subprocess.run(["bluetoothctl", "show"], text=True, capture_output=True)
    return "Powered: yes" in res.stdout

def toggle_power(enable):
    state = "on" if enable else "off"
    subprocess.run(["bluetoothctl", "power", state])
    notify("Bluetooth", f"Bluetooth {'ativado' if enable else 'desativado'}.")

def get_devices():
    res = subprocess.run(["bluetoothctl", "devices"], text=True, capture_output=True)
    devices = []
    for line in res.stdout.strip().split("\n"):
        if not line.startswith("Device "):
            continue
        parts = line.split(" ", 2)
        if len(parts) < 3:
            continue
        mac = parts[1]
        name = parts[2]
        
        info_res = subprocess.run(["bluetoothctl", "info", mac], text=True, capture_output=True)
        info = info_res.stdout
        connected = "Connected: yes" in info
        paired = "Paired: yes" in info
        
        icon = "󰂱"
        if "audio-headset" in info or "audio-card" in info or "headphones" in name.lower() or "pods" in name.lower():
            icon = "󰋋"
        elif "keyboard" in info or "keyboard" in name.lower():
            icon = "󰌌"
        elif "mouse" in info or "mouse" in name.lower():
            icon = "󰍽"
        elif "gaming" in info or "controller" in name.lower() or "gamepad" in name.lower():
            icon = "󰊴"
        elif "phone" in info:
            icon = "󰄡"

        devices.append({
            "mac": mac,
            "name": name,
            "connected": connected,
            "paired": paired,
            "icon": icon
        })
    return devices

def device_submenu(dev):
    mac = dev["mac"]
    name = dev["name"]
    connected = dev["connected"]
    
    actions = []
    if connected:
        actions.append(f"󰂲   Desconectar de '{name}'")
    else:
        actions.append(f"󰂱   Conectar a '{name}'")
    
    actions.append(f"󰌾   Confiar / Emparelhar")
    actions.append(f"󰆴   Remover dispositivo")
    actions.append("󰌑   Voltar")

    choice = run_rofi(name, actions)
    if not choice:
        return

    if "Desconectar" in choice:
        notify("Bluetooth", f"Desconectando de {name}...")
        res = subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, text=True)
        if res.returncode == 0:
            notify("Bluetooth", f"Desconectado de {name}.")
        else:
            notify("Bluetooth", f"Erro ao desconectar: {res.stderr.strip()}", urgency="critical")

    elif "Conectar" in choice:
        notify("Bluetooth", f"Conectando a {name}...")
        res = subprocess.run(["bluetoothctl", "connect", mac], capture_output=True, text=True)
        if "Connection successful" in res.stdout or res.returncode == 0:
            notify("Bluetooth", f"Conectado com sucesso a {name}!")
        else:
            notify("Bluetooth", f"Falha ao conectar a {name}.", urgency="critical")

    elif "Confiar" in choice:
        subprocess.run(["bluetoothctl", "trust", mac])
        subprocess.run(["bluetoothctl", "pair", mac])
        notify("Bluetooth", f"Dispositivo {name} pareado e confiado.")

    elif "Remover" in choice:
        subprocess.run(["bluetoothctl", "remove", mac])
        notify("Bluetooth", f"Dispositivo {name} removido.")

def scan_devices():
    notify("Bluetooth", "Escaneando novos dispositivos por 8 segundos...")
    # Executa bluetoothctl scan on por 8 segundos em background
    try:
        proc = subprocess.Popen(["bluetoothctl", "scan", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(8)
        proc.terminate()
        subprocess.run(["bluetoothctl", "scan", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        notify("Bluetooth", "Escaneamento concluído.")
    except Exception as e:
        pass

def main():
    if not is_powered():
        choice = run_rofi("Bluetooth Desligado", ["󰂯   Ligar Bluetooth"])
        if "Ligar" in choice:
            toggle_power(True)
        return

    devices = get_devices()

    menu_options = [
        "󰂲   Desligar Bluetooth",
        "󰑓   Buscar novos dispositivos",
    ]

    dev_map = {}
    for dev in devices:
        status = " (Conectado)" if dev["connected"] else ""
        label = f"{dev['icon']}   {dev['name']}{status}"
        menu_options.append(label)
        dev_map[label] = dev

    choice = run_rofi("󰂯  Bluetooth", menu_options)
    if not choice:
        return

    if "Desligar Bluetooth" in choice:
        toggle_power(False)
    elif "Buscar novos dispositivos" in choice:
        scan_devices()
        main()
    elif choice in dev_map:
        device_submenu(dev_map[choice])

if __name__ == "__main__":
    main()
