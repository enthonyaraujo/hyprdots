#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applet moderno de Sessão e Energia em GTK3 para Hyprland.
Estilo translúcido Breeze/Catppuccin alinhado no canto superior direito.
"""
import os
import sys
import json
import signal
import subprocess
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

PID_FILE = "/tmp/hypr_session_applet.pid"
ALL_PID_FILES = [
    "/tmp/hypr_audio_applet.pid",
    "/tmp/hypr_calendar_applet.pid",
    "/tmp/hypr_wifi_applet.pid",
    "/tmp/hypr_bluetooth_applet.pid",
    "/tmp/hypr_power_applet.pid",
    "/tmp/hypr_session_applet.pid",
]

# Toggle behavior & fechar outros applets concorrentes
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

GLib.set_prgname("session-applet")
GLib.set_application_name("session-applet")

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
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(session-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

def get_uptime_short():
    try:
        out = subprocess.check_output(["uptime", "-p"], text=True).strip()
        # ex: 'up 2 hours, 15 minutes' -> '2h 15m'
        out = out.replace("up ", "")
        out = out.replace(" hours", "h").replace(" hour", "h")
        out = out.replace(" minutes", "m").replace(" minute", "m")
        out = out.replace(", ", " ")
        return out
    except Exception:
        return ""

class SessionApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("session-applet")
        self.set_title("Menu de Sessão")
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

        # Layout principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.get_style_context().add_class("main-box")
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(14)
        main_box.set_margin_start(14)
        main_box.set_margin_end(14)
        self.add(main_box)

        # Cabeçalho no estilo inputbar do Rofi
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")

        icon_label = Gtk.Label(label="⏻  Menu de Energia")
        icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(icon_label, False, False, 0)

        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        uptime_str = get_uptime_short()
        if uptime_str:
            badge_up = Gtk.Label(label=f"Ativo: {uptime_str}")
            badge_up.get_style_context().add_class("header-badge")
            right_header.pack_start(badge_up, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_header.pack_start(btn_close, False, False, 0)

        header_box.pack_end(right_header, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        # Opções do menu de sessão
        actions = [
            ("󰌾   Bloquear Tela", "hyprlock", False),
            ("󰤄   Suspender Sistema", "systemctl suspend", False),
            ("󰍃   Encerrar Sessão (Logout)", "hyprctl dispatch exit", False),
            ("󰜉   Reiniciar Computador", "systemctl reboot", False),
            ("   Reiniciar no Firmware UEFI", "systemctl reboot --firmware-setup", False),
            ("󰐥   Desligar Computador", "systemctl poweroff", True),
        ]

        for label_text, cmd, is_danger in actions:
            btn = Gtk.Button()
            btn.set_can_focus(False)
            btn.get_style_context().add_class("action-btn")
            if is_danger:
                btn.get_style_context().add_class("danger")
            btn.set_halign(Gtk.Align.FILL)

            lbl = Gtk.Label(label=label_text)
            lbl.set_xalign(0.0)
            lbl.set_hexpand(True)
            btn.add(lbl)

            btn.connect("clicked", self.make_action_handler(cmd))
            main_box.pack_start(btn, False, False, 0)

        # Eventos de teclado e destruição
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def make_action_handler(self, cmd):
        def handler(widget):
            self.close_app()
            if cmd.startswith("hyprctl"):
                subprocess.run(cmd.split())
            else:
                subprocess.run(cmd, shell=True)
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

    app = SessionApplet()
    app.show_all()
    GLib.idle_add(align_to_top_right)
    GLib.timeout_add(50, align_to_top_right)
    GLib.timeout_add(150, align_to_top_right)

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
