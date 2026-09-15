#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys

THEME_PATH = os.path.expanduser("~/.config/rofi/applet.rasi")

def notify(summary, body, urgency="normal"):
    subprocess.run(["notify-send", "-u", urgency, "-a", "Wi-Fi", summary, body])

def run_rofi(prompt, options_list, password=False):
    cmd = ["rofi", "-dmenu", "-p", prompt]
    if os.path.exists(THEME_PATH):
        cmd.extend(["-theme", THEME_PATH])
    if password:
        cmd.append("-password")
    
    proc = subprocess.run(
        cmd,
        input="\n".join(options_list),
        text=True,
        stdout=subprocess.PIPE
    )
    return proc.stdout.strip()

def get_wifi_status():
    res = subprocess.run(
        ["nmcli", "-t", "-f", "WIFI", "general", "status"],
        text=True,
        stdout=subprocess.PIPE
    )
    return "enabled" in res.stdout.lower()

def toggle_wifi(enable):
    state = "on" if enable else "off"
    subprocess.run(["nmcli", "radio", "wifi", state])
    notify("Wi-Fi", f"Wi-Fi {'ativado' if enable else 'desativado'}.")

def get_saved_connections():
    res = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
        text=True,
        stdout=subprocess.PIPE
    )
    saved = set()
    for line in res.stdout.strip().split("\n"):
        if ":802-11-wireless" in line:
            name = line.split(":802-11-wireless")[0]
            saved.add(name)
    return saved

def get_signal_icon(bars):
    if "█" in bars:
        return "󰤨"
    elif "▆" in bars:
        return "󰤥"
    elif "▄" in bars:
        return "󰤢"
    else:
        return "󰤟"

def main():
    wifi_enabled = get_wifi_status()
    if not wifi_enabled:
        choice = run_rofi("Wi-Fi Desativado", ["󰤨   Ativar Wi-Fi"])
        if "Ativar" in choice:
            toggle_wifi(True)
        return

    # Escanear redes
    scan_res = subprocess.run(
        ["nmcli", "-t", "-f", "IN-USE,SSID,BARS,SECURITY", "device", "wifi", "list"],
        text=True,
        stdout=subprocess.PIPE
    )

    current_ssid = None
    networks = []
    seen_ssids = set()

    for line in scan_res.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 4:
            continue
        in_use = parts[0].strip() == "*"
        ssid = parts[1].strip()
        bars = parts[2].strip()
        security = parts[3].strip()

        if not ssid or ssid in seen_ssids:
            continue
        seen_ssids.add(ssid)

        if in_use:
            current_ssid = ssid

        icon = get_signal_icon(bars)
        sec_icon = " " if security and security != "--" else "  "
        status_tag = " (Conectado)" if in_use else ""
        label = f"{icon}  {sec_icon}{ssid}{status_tag}"
        networks.append((label, ssid, in_use, security))

    menu_options = []
    actions = {}

    if current_ssid:
        disconnect_opt = f"󰖪   Desconectar de '{current_ssid}'"
        menu_options.append(disconnect_opt)
        actions[disconnect_opt] = ("disconnect", current_ssid)

    toggle_opt = "󰤮   Desativar Wi-Fi"
    menu_options.append(toggle_opt)
    actions[toggle_opt] = ("toggle_off", None)

    rescan_opt = "󰑓   Escanear novamente"
    menu_options.append(rescan_opt)
    actions[rescan_opt] = ("rescan", None)

    for label, ssid, in_use, security in networks:
        menu_options.append(label)
        actions[label] = ("connect", (ssid, in_use, security))

    choice = run_rofi("󰤨  Wi-Fi", menu_options)
    if not choice or choice not in actions:
        return

    action_type, data = actions[choice]

    if action_type == "disconnect":
        subprocess.run(["nmcli", "device", "disconnect", "wlan0"], stderr=subprocess.PIPE)
        subprocess.run(["nmcli", "connection", "down", "id", data], stderr=subprocess.PIPE)
        notify("Wi-Fi", f"Desconectado de '{data}'.")

    elif action_type == "toggle_off":
        toggle_wifi(False)

    elif action_type == "rescan":
        subprocess.run(["nmcli", "device", "wifi", "rescan"])
        main()

    elif action_type == "connect":
        ssid, in_use, security = data
        if in_use:
            notify("Wi-Fi", f"Você já está conectado a '{ssid}'.")
            return

        saved_conns = get_saved_connections()
        if ssid in saved_conns:
            notify("Wi-Fi", f"Conectando a '{ssid}'...")
            res = subprocess.run(
                ["nmcli", "connection", "up", "id", ssid],
                capture_output=True,
                text=True
            )
            if res.returncode == 0:
                notify("Wi-Fi", f"Conectado com sucesso a '{ssid}'.")
            else:
                notify("Wi-Fi", f"Falha ao conectar: {res.stderr.strip()}", urgency="critical")
        else:
            # Requer senha?
            if security and security != "--":
                password = run_rofi(f"Senha para '{ssid}'", [], password=True)
                if not password:
                    return
                notify("Wi-Fi", f"Conectando a '{ssid}'...")
                res = subprocess.run(
                    ["nmcli", "device", "wifi", "connect", ssid, "password", password],
                    capture_output=True,
                    text=True
                )
                if res.returncode == 0:
                    notify("Wi-Fi", f"Conectado com sucesso a '{ssid}'.")
                else:
                    notify("Wi-Fi", f"Falha ao conectar: {res.stderr.strip()}", urgency="critical")
            else:
                notify("Wi-Fi", f"Conectando à rede aberta '{ssid}'...")
                res = subprocess.run(
                    ["nmcli", "device", "wifi", "connect", ssid],
                    capture_output=True,
                    text=True
                )
                if res.returncode == 0:
                    notify("Wi-Fi", f"Conectado com sucesso a '{ssid}'.")
                else:
                    notify("Wi-Fi", f"Falha ao conectar: {res.stderr.strip()}", urgency="critical")

if __name__ == "__main__":
    main()
