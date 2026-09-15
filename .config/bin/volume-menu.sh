#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import subprocess
import sys

THEME_PATH = os.path.expanduser("~/.config/rofi/applet.rasi")

def notify(summary, body, urgency="normal"):
    subprocess.run(["notify-send", "-u", urgency, "-a", "Áudio", summary, body])

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

def get_volume_info():
    res = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"], capture_output=True, text=True)
    out = res.stdout.strip()
    muted = "[MUTED]" in out
    m = re.search(r"Volume:\s*([\d\.]+)", out)
    vol_pct = int(float(m.group(1)) * 100) if m else 0
    return vol_pct, muted

def get_sinks():
    out = subprocess.run(["wpctl", "status"], capture_output=True, text=True).stdout
    in_sinks = False
    sinks = []
    for line in out.splitlines():
        if "Sinks:" in line:
            in_sinks = True
            continue
        if in_sinks:
            if "Sources:" in line or "Filters:" in line or "Streams:" in line or not line.strip():
                in_sinks = False
                continue
            m = re.search(r"([*]?)\s*(\d+)\.\s+(.*?)(?:\s+\[vol:.*\])?$", line)
            if m:
                is_def = m.group(1) == "*"
                sid = m.group(2)
                name = m.group(3).strip()
                sinks.append((sid, name, is_def))
    return sinks

def main():
    vol, muted = get_volume_info()
    vol_icon = "󰝟" if muted else ("󰕾" if vol > 50 else ("󰖀" if vol > 20 else "󰕿"))
    status_label = f"{vol_icon}  Volume Atual: {vol}% {'(Mudo)' if muted else ''}"

    mute_action_label = "󰕾   Ativar Som (Desmutar)" if muted else "󰝟   Silenciar (Mudo)"

    menu_options = [
        mute_action_label,
        "󰕾   Volume 100%",
        "󰖀   Volume 75%",
        "󰖀   Volume 50%",
        "󰕿   Volume 25%",
        "󰍬   Alternar Microfone Mudo",
        "   Mixer Completo (Pavucontrol)"
    ]

    sinks = get_sinks()
    sink_map = {}
    if len(sinks) > 1:
        menu_options.append("--- Saídas de Áudio ---")
        for sid, name, is_def in sinks:
            tag = " (Padrão)" if is_def else ""
            opt_label = f"󰋋   {name}{tag}"
            menu_options.append(opt_label)
            sink_map[opt_label] = sid

    choice = run_rofi("󰕾  Áudio", menu_options)
    if not choice:
        return

    if choice == mute_action_label:
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        _, new_muted = get_volume_info()
        notify("Áudio", "Som silenciado." if new_muted else "Som ativado.")

    elif "100%" in choice:
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "1.0"])
        notify("Áudio", "Volume ajustado para 100%.")

    elif "75%" in choice:
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.75"])
        notify("Áudio", "Volume ajustado para 75%.")

    elif "50%" in choice:
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.50"])
        notify("Áudio", "Volume ajustado para 50%.")

    elif "25%" in choice:
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", "0.25"])
        notify("Áudio", "Volume ajustado para 25%.")

    elif "Microfone Mudo" in choice:
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
        notify("Microfone", "Estado do microfone alternado.")

    elif "Pavucontrol" in choice:
        subprocess.Popen(["pavucontrol"])

    elif choice in sink_map:
        sid = sink_map[choice]
        subprocess.run(["wpctl", "set-default", sid])
        notify("Áudio", f"Saída de áudio alterada.")

if __name__ == "__main__":
    main()
