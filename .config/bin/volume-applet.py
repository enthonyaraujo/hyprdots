#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern GTK3 audio applet with native slider for Hyprland.
Translucent Catppuccin/Breeze styling with rounded corners and PipeWire (WirePlumber) integration.
"""
import os
import sys
import re
import json
import subprocess
import signal
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Single instance / Toggle behavior
PID_FILE = "/tmp/hypr_audio_applet.pid"
ALL_PID_FILES = [
    "/tmp/hypr_audio_applet.pid",
    "/tmp/hypr_calendar_applet.pid",
    "/tmp/hypr_wifi_applet.pid",
    "/tmp/hypr_bluetooth_applet.pid",
    "/tmp/hypr_power_applet.pid",
    "/tmp/hypr_session_applet.pid",
]

if os.path.exists(PID_FILE):
    try:
        with open(PID_FILE, "r") as f:
            old_pid = int(f.read().strip())
        if old_pid != os.getpid():
            os.kill(old_pid, signal.SIGTERM)
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
            sys.exit(0)
    except ProcessLookupError:
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
    except Exception:
        pass

for pid_f in ALL_PID_FILES:
    if pid_f != PID_FILE and os.path.exists(pid_f):
        try:
            with open(pid_f, "r") as f:
                p = int(f.read().strip())
            os.kill(p, signal.SIGTERM)
        except Exception:
            pass
        try:
            os.remove(pid_f)
        except Exception:
            pass

with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

GLib.set_prgname("volume-applet")
GLib.set_application_name("volume-applet")

CSS_FILE = os.path.expanduser("~/.config/gtk-3.0/applets.css")

def load_styles():
    provider = Gtk.CssProvider()
    if os.path.exists(CSS_FILE):
        provider.load_from_path(CSS_FILE)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

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

def align_to_top_right(app_win=None):
    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]))
        focused = next((m for m in monitors if m.get("focused")), monitors[0])
        mon_x = focused["x"]
        mon_y = focused["y"]
        mon_w = int(focused["width"] / focused["scale"])

        # Standardized 380px width matching applet.rasi
        win_w = 380
        margin_right = 12
        target_x = mon_x + mon_w - win_w - margin_right
        target_y = mon_y + 32
        subprocess.run(["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(volume-applet)$"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    return False

class AudioApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("volume-applet")
        self.set_title("Volume Control")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(380, -1)
        self.set_size_request(380, -1)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.get_style_context().add_class("audio-window")

        self.updating_slider = False
        vol, muted = get_volume_info()
        self.current_vol = vol
        self.is_muted = muted

        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.get_style_context().add_class("main-box")
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(14)
        main_box.set_margin_start(14)
        main_box.set_margin_end(14)
        self.add(main_box)

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")
        self.icon_label = Gtk.Label(label="󰕾  Audio")
        self.icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(self.icon_label, False, False, 0)

        # Close and badge
        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.badge_vol = Gtk.Label(label=f"{self.current_vol}%" if not self.is_muted else "Muted")
        self.badge_vol.get_style_context().add_class("badge-vol")
        right_header.pack_start(self.badge_vol, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_header.pack_start(btn_close, False, False, 0)

        header_box.pack_end(right_header, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        # Slider
        slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.adj = Gtk.Adjustment(value=self.current_vol, lower=0, upper=100, step_increment=1, page_increment=5)
        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adj)
        self.scale.set_can_focus(False)
        self.scale.set_draw_value(False)
        self.scale.set_hexpand(True)
        self.scale.connect("value-changed", self.on_slider_changed)
        slider_box.pack_start(self.scale, True, True, 0)
        main_box.pack_start(slider_box, False, False, 4)

        # Helper
        def make_action_btn(label, callback):
            btn = Gtk.Button()
            btn.set_can_focus(False)
            btn.get_style_context().add_class("action-btn")
            btn.set_halign(Gtk.Align.FILL)
            lbl = Gtk.Label(label=label)
            lbl.set_xalign(0.0)
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            lbl.set_max_width_chars(28)
            lbl.set_hexpand(True)
            btn.add(lbl)
            btn.connect("clicked", callback)
            return btn, lbl

        # Mute button
        mute_text = "󰕾   Unmute Audio" if self.is_muted else "󰝟   Mute Audio"
        self.btn_mute, self.lbl_mute = make_action_btn(mute_text, self.on_mute_clicked)
        main_box.pack_start(self.btn_mute, False, False, 0)

        # Microphone Mute button
        self.btn_mic, _ = make_action_btn("󰍬   Toggle Microphone Mute", self.on_mic_clicked)
        main_box.pack_start(self.btn_mic, False, False, 0)

        # Pavucontrol button
        self.btn_pavu, _ = make_action_btn("   Full Audio Mixer (Pavucontrol)", self.on_pavu_clicked)
        main_box.pack_start(self.btn_pavu, False, False, 0)

        # Audio Sinks
        sinks = get_sinks()
        if len(sinks) > 1:
            sep_label = Gtk.Label(label="─── Audio Outputs ───")
            sep_label.get_style_context().add_class("section-sep")
            main_box.pack_start(sep_label, False, False, 4)

            for sid, name, is_def in sinks:
                tag = " ✓" if is_def else ""
                sink_btn, _ = make_action_btn(f"󰋋   {name}{tag}", lambda b, s=sid: self.on_sink_clicked(s))
                main_box.pack_start(sink_btn, False, False, 0)

        # Keyboard & Destroy events
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def on_slider_changed(self, scale):
        if self.updating_slider:
            return
        vol = int(scale.get_value())
        self.current_vol = vol
        self.badge_vol.set_text(f"{vol}%" if not self.is_muted else "Muted")
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SINK@", f"{vol/100.0:.2f}"])

    def on_mute_clicked(self, btn):
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"])
        vol, muted = get_volume_info()
        self.is_muted = muted
        self.badge_vol.set_text("Muted" if muted else f"{vol}%")
        self.lbl_mute.set_text("󰕾   Unmute Audio" if muted else "󰝟   Mute Audio")

    def on_mic_clicked(self, btn):
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SOURCE@", "toggle"])
        subprocess.run(["notify-send", "-a", "Audio", "Microphone", "Microphone state toggled."])
        self.close_app()

    def on_pavu_clicked(self, btn):
        subprocess.Popen(["pavucontrol"])
        self.close_app()

    def on_sink_clicked(self, sid):
        subprocess.run(["wpctl", "set-default", sid])
        self.close_app()

    def on_key_press(self, widget, event):
        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            self.close_app()
            return True
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
    load_styles()

    app = AudioApplet()
    app.show_all()
    GLib.idle_add(lambda: align_to_top_right(app))
    GLib.timeout_add(50, lambda: align_to_top_right(app))
    GLib.timeout_add(150, lambda: align_to_top_right(app))

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
