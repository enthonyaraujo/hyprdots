#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys

THEME_PATH = os.path.expanduser("~/.config/rofi/applet.rasi")

def notify(summary, body, urgency="normal"):
    subprocess.run(["notify-send", "-u", urgency, "-a", "Energia", summary, body])

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

def get_battery_info():
    devices = subprocess.run(["upower", "-e"], capture_output=True, text=True).stdout
    bat_path = None
    for line in devices.splitlines():
        if "battery" in line:
            bat_path = line.strip()
            break
    
    pct = "100"
    state = "Carregada"
    health = ""
    
    if bat_path:
        out = subprocess.run(["upower", "-i", bat_path], capture_output=True, text=True).stdout
        m_pct = re.search(r"percentage:\s*(\d+)%", out)
        if m_pct:
            pct = m_pct.group(1)
        
        m_state = re.search(r"state:\s*(\S+)", out)
        if m_state:
            raw_state = m_state.group(1).lower()
            if "charging" in raw_state and "dis" not in raw_state:
                state = "Carregando"
            elif "discharging" in raw_state:
                state = "Descarregando"
            elif "fully" in raw_state:
                state = "Completa"
            else:
                state = raw_state

        m_cap = re.search(r"capacity:\s*([\d,\.]+)%", out)
        if m_cap:
            health = f"Saúde: {m_cap.group(1)}%"

    return pct, state, health

def get_current_profile():
    res = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True)
    return res.stdout.strip()

def main():
    pct, state, health = get_battery_info()
    cur_profile = get_current_profile()
    
    perf_tag = " (Ativo)" if cur_profile == "performance" else ""
    bal_tag = " (Ativo)" if cur_profile == "balanced" else ""
    saver_tag = " (Ativo)" if cur_profile == "power-saver" else ""

    info_str = f"󰁹   Bateria: {pct}% [{state}]"
    if health:
        info_str += f" | {health}"

    menu_options = [
        f"⚡   Perfil: Desempenho{perf_tag}",
        f"🔋   Perfil: Equilibrado{bal_tag}",
        f"🌱   Perfil: Economia de Energia{saver_tag}",
    ]

    choice = run_rofi(f"󰁹  {pct}%", menu_options)
    if not choice:
        return

    if "Desempenho" in choice:
        subprocess.run(["powerprofilesctl", "set", "performance"])
        notify("Perfil de Energia", "Modo Desempenho ativado.")

    elif "Equilibrado" in choice:
        subprocess.run(["powerprofilesctl", "set", "balanced"])
        notify("Perfil de Energia", "Modo Equilibrado ativado.")

    elif "Economia de Energia" in choice:
        subprocess.run(["powerprofilesctl", "set", "power-saver"])
        notify("Perfil de Energia", "Modo Economia de Energia ativado.")

if __name__ == "__main__":
    main()