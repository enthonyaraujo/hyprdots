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
        actions.append(f"󰂲   Disconnect from '{name}'")
    else:
        actions.append(f"󰂱   Connect to '{name}'")
    
    actions.append(f"󰌾   Trust / Pair")
    actions.append(f"󰆴   Remove device")
    actions.append("󰌑   Back")

    choice = run_rofi(name, actions)
    if not choice:
        return

    if "Disconnect" in choice:
        notify("Bluetooth", f"Disconnecting from {name}...")
        res = subprocess.run(["bluetoothctl", "disconnect", mac], capture_output=True, text=True)
        if res.returncode == 0:
            notify("Bluetooth", f"Disconnected from {name}.")
        else:
            notify("Bluetooth", f"Error disconnecting: {res.stderr.strip()}", urgency="critical")

    elif "Connect" in choice:
        notify("Bluetooth", f"Connecting to {name}...")
        res = subprocess.run(["bluetoothctl", "connect", mac], capture_output=True, text=True)
        if "Connection successful" in res.stdout or res.returncode == 0:
            notify("Bluetooth", f"Successfully connected to {name}!")
        else:
            notify("Bluetooth", f"Failed to connect to {name}.", urgency="critical")

    elif "Trust" in choice:
        subprocess.run(["bluetoothctl", "trust", mac])
        subprocess.run(["bluetoothctl", "pair", mac])
        notify("Bluetooth", f"Device {name} paired and trusted.")

    elif "Remove" in choice:
        subprocess.run(["bluetoothctl", "remove", mac])
        notify("Bluetooth", f"Device {name} removed.")

def scan_devices():
    notify("Bluetooth", "Scanning for new devices for 8 seconds...")
    try:
        proc = subprocess.Popen(["bluetoothctl", "scan", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(8)
        proc.terminate()
        subprocess.run(["bluetoothctl", "scan", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        notify("Bluetooth", "Scan completed.")
    except Exception as e:
        pass

def main():
    if not is_powered():
        choice = run_rofi("Bluetooth Off", ["󰂯   Turn on Bluetooth"])
        if "Turn on" in choice:
            toggle_power(True)
        return

    devices = get_devices()

    menu_options = [
        "󰂲   Turn off Bluetooth",
        "󰑓   Scan for new devices",
        "   More Bluetooth Settings",
    ]

    dev_map = {}
    for dev in devices:
        status = " (Connected)" if dev["connected"] else ""
        label = f"{dev['icon']}   {dev['name']}{status}"
        menu_options.append(label)
        dev_map[label] = dev

    choice = run_rofi("󰂯  Bluetooth", menu_options)
    if not choice:
        return

    if "Turn off Bluetooth" in choice:
        toggle_power(False)
    elif "Scan for new devices" in choice:
        scan_devices()
        main()
    elif "More Bluetooth Settings" in choice:
        subprocess.Popen(["blueman-manager"])
    elif choice in dev_map:
        device_submenu(dev_map[choice])

if __name__ == "__main__":
    main()
