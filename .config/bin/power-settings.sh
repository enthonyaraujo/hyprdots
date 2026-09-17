#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys

THEME_PATH = os.path.expanduser("~/.config/rofi/applet.rasi")

def notify(summary, body, urgency="normal"):
    subprocess.run(["notify-send", "-u", urgency, "-a", "Power", summary, body])

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
    state = "Full"
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
                state = "Charging"
            elif "discharging" in raw_state:
                state = "Discharging"
            elif "fully" in raw_state:
                state = "Full"
            else:
                state = raw_state.capitalize()

        m_cap = re.search(r"capacity:\s*([\d,\.]+)%", out)
        if m_cap:
            health = f"Health: {m_cap.group(1)}%"

    return pct, state, health

def get_current_profile():
    res = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True)
    return res.stdout.strip()

def main():
    pct, state, health = get_battery_info()
    cur_profile = get_current_profile()
    
    perf_tag = " (Active)" if cur_profile == "performance" else ""
    bal_tag = " (Active)" if cur_profile == "balanced" else ""
    saver_tag = " (Active)" if cur_profile == "power-saver" else ""

    info_str = f"󰁹   Battery: {pct}% [{state}]"
    if health:
        info_str += f" | {health}"

    menu_options = [
        f"⚡   Profile: Performance{perf_tag}",
        f"🔋   Profile: Balanced{bal_tag}",
        f"🌱   Profile: Power Saver{saver_tag}",
    ]

    choice = run_rofi(f"󰁹  {pct}%", menu_options)
    if not choice:
        return

    if "Performance" in choice:
        subprocess.run(["powerprofilesctl", "set", "performance"])
        notify("Power Profile", "Performance mode activated.")

    elif "Balanced" in choice:
        subprocess.run(["powerprofilesctl", "set", "balanced"])
        notify("Power Profile", "Balanced mode activated.")

    elif "Power Saver" in choice:
        subprocess.run(["powerprofilesctl", "set", "power-saver"])
        notify("Power Profile", "Power Saver mode activated.")

if __name__ == "__main__":
    main()