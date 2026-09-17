#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern GTK3 Battery and Power Profiles applet for Hyprland.
Translucent Breeze/Catppuccin styling aligned in top-right corner.
"""
import os
import sys
import re
import json
import signal
import subprocess
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

PID_FILE = "/tmp/hypr_power_applet.pid"
ALL_PID_FILES = [
    "/tmp/hypr_audio_applet.pid",
    "/tmp/hypr_calendar_applet.pid",
    "/tmp/hypr_wifi_applet.pid",
    "/tmp/hypr_bluetooth_applet.pid",
    "/tmp/hypr_power_applet.pid",
    "/tmp/hypr_session_applet.pid",
]

# Toggle behavior & close competing applets
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

GLib.set_prgname("power-applet")
GLib.set_application_name("power-applet")

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

def align_to_top_right():
    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]))
        focused = next((m for m in monitors if m.get("focused")), monitors[0])
        mon_x = focused["x"]
        mon_y = focused["y"]
        mon_w = int(focused["width"] / focused["scale"])

        win_w = 380
        margin_right = 12
        target_x = mon_x + mon_w - win_w - margin_right
        target_y = mon_y + 32
        subprocess.run(
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(power-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

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
    icon = "󰁹"
    
    if bat_path:
        out = subprocess.run(["upower", "-i", bat_path], capture_output=True, text=True).stdout
        m_pct = re.search(r"percentage:\s*(\d+)%", out)
        if m_pct:
            pct = m_pct.group(1)
            pct_int = int(pct)
            if pct_int <= 10:
                icon = "󰁺"
            elif pct_int <= 20:
                icon = "󰁻"
            elif pct_int <= 30:
                icon = "󰁼"
            elif pct_int <= 40:
                icon = "󰁽"
            elif pct_int <= 50:
                icon = "󰁾"
            elif pct_int <= 60:
                icon = "󰁿"
            elif pct_int <= 70:
                icon = "󰂀"
            elif pct_int <= 80:
                icon = "󰂁"
            elif pct_int <= 90:
                icon = "󰂂"
            else:
                icon = "󰁹"
        
        m_state = re.search(r"state:\s*(\S+)", out)
        if m_state:
            raw_state = m_state.group(1).lower()
            if "charging" in raw_state and "dis" not in raw_state:
                state = "Charging"
                icon = "󰂄"
            elif "discharging" in raw_state:
                state = "Discharging"
            elif "fully" in raw_state:
                state = "Full"
            else:
                state = raw_state

        m_cap = re.search(r"capacity:\s*([\d,\.]+)%", out)
        if m_cap:
            health = f"Health: {m_cap.group(1)}%"

    return pct, state, health, icon

def get_current_profile():
    res = subprocess.run(["powerprofilesctl", "get"], capture_output=True, text=True)
    return res.stdout.strip()

class PowerApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("power-applet")
        self.set_title("Power Management")
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
        self.get_style_context().add_class("applet-window")

        pct, state, health, icon = get_battery_info()
        self.cur_profile = get_current_profile()

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

        self.icon_label = Gtk.Label(label=f"{icon}  Battery")
        self.icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(self.icon_label, False, False, 0)

        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.badge_bat = Gtk.Label(label=f"{pct}% [{state}]")
        self.badge_bat.get_style_context().add_class("header-badge")
        right_header.pack_start(self.badge_bat, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_header.pack_start(btn_close, False, False, 0)

        header_box.pack_end(right_header, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        # Health info
        if health:
            health_lbl = Gtk.Label(label=f"󰋊  Maximum battery capacity: {health}")
            health_lbl.set_xalign(0.0)
            health_lbl.get_style_context().add_class("section-sep")
            health_lbl.set_margin_start(4)
            main_box.pack_start(health_lbl, False, False, 2)

        sep_label = Gtk.Label(label="─── Power Profiles ───")
        sep_label.get_style_context().add_class("section-sep")
        main_box.pack_start(sep_label, False, False, 2)

        # Power profiles
        self.profile_buttons = {}
        profiles = [
            ("performance", "⚡   Profile: Performance"),
            ("balanced", "🔋   Profile: Balanced"),
            ("power-saver", "🌱   Profile: Power Saver"),
        ]

        for p_code, p_title in profiles:
            btn = Gtk.Button()
            btn.set_can_focus(False)
            btn.get_style_context().add_class("action-btn")
            btn.set_halign(Gtk.Align.FILL)

            is_active = (p_code == self.cur_profile)
            if is_active:
                btn.get_style_context().add_class("active")

            tag = "  ✓" if is_active else ""
            lbl = Gtk.Label(label=f"{p_title}{tag}")
            lbl.set_xalign(0.0)
            lbl.set_hexpand(True)
            btn.add(lbl)

            btn.connect("clicked", self.make_profile_handler(p_code, p_title))
            main_box.pack_start(btn, False, False, 0)
            self.profile_buttons[p_code] = (btn, lbl, p_title)

        # Keyboard & Destroy events
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def make_profile_handler(self, p_code, p_title):
        def handler(widget):
            subprocess.run(["powerprofilesctl", "set", p_code])
            subprocess.run(["notify-send", "-a", "Power", "Power Profile", f"Mode '{p_code.capitalize()}' activated."])
            self.cur_profile = p_code
            for code, (btn, lbl, title) in self.profile_buttons.items():
                if code == p_code:
                    btn.get_style_context().add_class("active")
                    lbl.set_text(f"{title}  ✓")
                else:
                    btn.get_style_context().remove_class("active")
                    lbl.set_text(title)
            self.close_app()
        return handler

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

    app = PowerApplet()
    app.show_all()
    GLib.idle_add(align_to_top_right)
    GLib.timeout_add(50, align_to_top_right)
    GLib.timeout_add(150, align_to_top_right)

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
