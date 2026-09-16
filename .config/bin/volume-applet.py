#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applet moderno de áudio com controle deslizante (slider) nativo em GTK3 para Hyprland.
Estilo translúcido Catppuccin/Breeze com bordas arredondadas e integração ao PipeWire (WirePlumber).
"""
import os
import sys
import re
import subprocess
import signal

# Single instance / Toggle behavior
PID_FILE = "/tmp/hypr_audio_applet.pid"
if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
        if old_pid != os.getpid():
            os.kill(old_pid, signal.SIGTERM)
            os.remove(PID_FILE)
            sys.exit(0)
    except Exception:
        pass

with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

CSS_DATA = """
window.audio-window {
    background-color: rgba(35, 38, 41, 0.96);
    border: 2px solid #3daee9;
    border-radius: 12px;
}

label.header-title {
    color: #3daee9;
    font-family: 'FiraCode Nerd Font';
    font-size: 13px;
    font-weight: bold;
}

label.badge-vol {
    color: #eff0f1;
    font-family: 'FiraCode Nerd Font';
    font-size: 12px;
    font-weight: 600;
}

scale trough {
    background-color: #2a2e32;
    border-radius: 6px;
    min-height: 8px;
    border: none;
}

scale highlight {
    background-color: #3daee9;
    border-radius: 6px;
    min-height: 8px;
}

scale slider {
    background-color: #eff0f1;
    border-radius: 50%;
    min-width: 18px;
    min-height: 18px;
    margin: -5px 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.4);
}

scale slider:hover {
    background-color: #3daee9;
}

button.action-btn {
    background-color: transparent;
    color: #eff0f1;
    border: none;
    border-radius: 8px;
    padding: 8px 12px;
    font-family: 'FiraCode Nerd Font';
    font-size: 12px;
    outline: none;
    transition: all 0.15s ease;
}

button.action-btn:hover {
    background-color: #3daee9;
    color: #141618;
}

label.section-sep {
    color: #7f8c8d;
    font-family: 'FiraCode Nerd Font';
    font-size: 11px;
    margin-top: 4px;
}
"""

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

class AudioApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_wmclass("audio-applet", "audio-applet")
        self.set_title("Controle de Volume")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(360, -1)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.set_app_paintable(True)
        self.get_style_context().add_class("audio-window")

        self.updating_slider = False
        vol, muted = get_volume_info()
        self.current_vol = vol
        self.is_muted = muted

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(14)
        main_box.set_margin_start(14)
        main_box.set_margin_end(14)
        self.add(main_box)

        # Cabeçalho
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.icon_label = Gtk.Label(label="󰕾  Áudio")
        self.icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(self.icon_label, False, False, 0)

        self.badge_vol = Gtk.Label(label=f"{self.current_vol}%" if not self.is_muted else "Mudo")
        self.badge_vol.get_style_context().add_class("badge-vol")
        header_box.pack_end(self.badge_vol, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        # Barra Deslizante (Slider)
        slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.adj = Gtk.Adjustment(value=self.current_vol, lower=0, upper=100, step_increment=1, page_increment=5)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj)
        self.scale.set_draw_value(False)
        self.scale.set_hexpand(True)
        self.scale.connect("value-changed", self.on_slider_changed)
        slider_box.pack_start(self.scale, True, True, 0)
        main_box.pack_start(slider_box, False, False, 4)

        # Botão Silenciar (Mudo)
        mute_label = "󰕾   Ativar Som (Desmutar)" if self.is_muted else "󰝟   Silenciar (Mudo)"
        self.btn_mute = Gtk.Button(label=mute_label)
        self.btn_mute.get_style_context().add_class("action-btn")
        self.btn_mute.set_alignment(0.0, 0.5)
        self.btn_mute.connect("clicked", self.on_mute_clicked)
        main_box.pack_start(self.btn_mute, False, False, 0)

        # Botão Microfone Mudo
        self.btn_mic = Gtk.Button(label="󰍬   Alternar Microfone Mudo")
        self.btn_mic.get_style_context().add_class("action-btn")
        self.btn_mic.set_alignment(0.0, 0.5)
        self.btn_mic.connect("clicked", self.on_mic_clicked)
        main_box.pack_start(self.btn_mic, False, False, 0)

        # Botão Pavucontrol
        self.btn_pavu = Gtk.Button(label="   Mixer Completo (Pavucontrol)")
        self.btn_pavu.get_style_context().add_class("action-btn")
        self.btn_pavu.set_alignment(0.0, 0.5)
        self.btn_pavu.connect("clicked", self.on_pavu_clicked)
        main_box.pack_start(self.btn_pavu, False, False, 0)

        # Saídas de áudio
        sinks = get_sinks()
        if len(sinks) > 1:
            sep_label = Gtk.Label(label="─── Saídas de Áudio ───")
            sep_label.get_style_context().add_class("section-sep")
            main_box.pack_start(sep_label, False, False, 4)

            for sid, name, is_def in sinks:
                tag = " ✓" if is_def else ""
                sink_btn = Gtk.Button(label=f"󰋋   {name}{tag}")
                sink_btn.get_style_context().add_class("action-btn")
                sink_btn.set_alignment(0.0, 0.5)
                sink_btn.connect("clicked", self.on_sink_clicked, sid)
                main_box.pack_start(sink_btn, False, False, 0)

        # Eventos de fechamento
        self.connect("key-press-event", self.on_key_press)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("destroy", self.cleanup)

    def on_slider_changed(self, scale):
        if self.updating_slider:
            return
        vol = int(scale.get_value())
        self.current_vol = vol
        self.badge_vol.set_text(f"{vol}%" if not self.is_muted else "Mudo")
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{vol/100.0:.2f}"])

    def on_mute_clicked(self, btn):
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        vol, muted = get_volume_info()
        self.is_muted = muted
        self.badge_vol.set_text("Mudo" if muted else f"{vol}%")
        self.btn_mute.set_label("󰕾   Ativar Som (Desmutar)" if muted else "󰝟   Silenciar (Mudo)")

    def on_mic_clicked(self, btn):
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
        subprocess.run(["notify-send", "-a", "Áudio", "Microfone", "Estado do microfone alternado."])
        self.close_app()

    def on_pavu_clicked(self, btn):
        subprocess.Popen(["pavucontrol"])
        self.close_app()

    def on_sink_clicked(self, btn, sid):
        subprocess.run(["wpctl", "set-default", sid])
        self.close_app()

    def on_key_press(self, widget, event):
        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            self.close_app()
            return True
        return False

    def on_focus_out(self, widget, event):
        self.close_app()
        return False

    def close_app(self):
        self.cleanup()
        Gtk.main_quit()

    def cleanup(self, *args):
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass

def main():
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS_DATA.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    app = AudioApplet()
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
