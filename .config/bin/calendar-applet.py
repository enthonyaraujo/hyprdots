#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applet de calendário suspenso em GTK3 para o relógio da Waybar.
Estilo translúcido Catppuccin/Breeze com bordas arredondadas e centralização abaixo do relógio.
"""
import os
import sys
import json
import signal
import subprocess
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Single instance / Toggle behavior
PID_FILE = "/tmp/hypr_calendar_applet.pid"
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

with open(PID_FILE, "w") as f:
    f.write(str(os.getpid()))

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

GLib.set_prgname("calendar-applet")
GLib.set_application_name("calendar-applet")

CSS_DATA = """
window.calendar-window {
    background-color: rgba(35, 38, 41, 0.95);
    border: 2px solid #3daee9;
    border-radius: 12px;
}

box.header-box {
    background-color: #2a2e32;
    border-radius: 8px;
    padding: 8px 12px;
}

label.header-title {
    color: #3daee9;
    font-family: 'FiraCode Nerd Font';
    font-size: 12px;
    font-weight: bold;
}

label.header-date {
    color: #eff0f1;
    font-family: 'FiraCode Nerd Font';
    font-size: 12px;
    font-weight: 600;
}

button.btn-close {
    background-color: transparent;
    color: #7f8c8d;
    border: none;
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 12px;
    font-weight: bold;
}

button.btn-close:hover {
    background-color: #ed1515;
    color: #eff0f1;
}

calendar {
    background-color: transparent;
    color: #eff0f1;
    font-family: 'FiraCode Nerd Font';
    font-size: 12px;
    border: none;
    padding: 4px;
}

calendar:selected {
    background-color: #3daee9;
    color: #141618;
    border-radius: 6px;
    font-weight: bold;
}

calendar.header {
    color: #3daee9;
    font-weight: bold;
    border-bottom: 1px solid #31363b;
}

calendar.button {
    color: #3daee9;
    background-color: transparent;
    border-radius: 4px;
}

calendar.button:hover {
    background-color: #31363b;
    color: #eff0f1;
}

calendar.highlight {
    color: #3daee9;
    font-weight: bold;
}
"""

def align_to_center(cal_w=310):
    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]))
        focused = next((m for m in monitors if m.get("focused")), monitors[0])
        mon_x = focused["x"]
        mon_y = focused["y"]
        mon_w = int(focused["width"] / focused["scale"])

        try:
            clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]))
            for c in clients:
                if c.get("class") == "calendar-applet":
                    cal_w = c["size"][0]
                    break
        except Exception:
            pass

        target_x = mon_x + (mon_w - cal_w) // 2
        target_y = mon_y + 46
        subprocess.run(
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(calendar-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

class CalendarApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("calendar-applet")
        self.set_title("Calendário")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(310, -1)
        self.set_size_request(310, -1)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.get_style_context().add_class("calendar-window")

        # Container principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(14)
        main_box.set_margin_bottom(14)
        main_box.set_margin_start(14)
        main_box.set_margin_end(14)
        self.add(main_box)

        # Cabeçalho no estilo inputbar do Rofi
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")

        icon_label = Gtk.Label(label="󰃭  Calendário")
        icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(icon_label, False, False, 0)

        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        now_str = datetime.now().strftime("%d/%m")
        self.date_label = Gtk.Label(label=now_str)
        self.date_label.get_style_context().add_class("header-date")
        right_header.pack_start(self.date_label, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_header.pack_start(btn_close, False, False, 0)

        header_box.pack_end(right_header, False, False, 0)
        main_box.pack_start(header_box, False, False, 0)

        # Calendário GTK
        self.calendar = Gtk.Calendar()
        self.calendar.set_property("show-heading", True)
        self.calendar.set_property("show-day-names", True)
        self.calendar.set_property("show-details", False)
        self.calendar.set_property("show-week-numbers", False)
        main_box.pack_start(self.calendar, True, True, 0)

        # Teclado e destruição
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

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
    provider = Gtk.CssProvider()
    provider.load_from_data(CSS_DATA.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    app = CalendarApplet()
    app.show_all()
    GLib.idle_add(lambda: align_to_center(310))
    GLib.timeout_add(50, lambda: align_to_center(310))
    GLib.timeout_add(150, lambda: align_to_center(310))

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
