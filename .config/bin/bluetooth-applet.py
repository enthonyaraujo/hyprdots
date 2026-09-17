#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modern GTK3 Bluetooth applet for Hyprland.
Translucent Breeze/Catppuccin styling aligned in top-right corner.
"""
import os
import sys
import json
import signal
import subprocess
import threading
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

PID_FILE = "/tmp/hypr_bluetooth_applet.pid"
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

GLib.set_prgname("bluetooth-applet")
GLib.set_application_name("bluetooth-applet")

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
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(bluetooth-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

def is_powered():
    res = subprocess.run(["bluetoothctl", "show"], text=True, capture_output=True)
    return "Powered: yes" in res.stdout

def toggle_power(enable):
    state = "on" if enable else "off"
    subprocess.run(["bluetoothctl", "power", state])
    subprocess.run(["notify-send", "-a", "Bluetooth", "Bluetooth", f"Bluetooth {'ativado' if enable else 'desativado'}."])

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
        
        icon = "󰂱" if connected else "󰂯"
        info_lower = (info + " " + name).lower()
        if any(w in info_lower for w in ["headset", "audio", "headphones", "pods", "earbuds"]):
            icon = "󰋋"
        elif "keyboard" in info_lower:
            icon = "󰌌"
        elif "mouse" in info_lower:
            icon = "󰍽"
        elif any(w in info_lower for w in ["gaming", "controller", "gamepad"]):
            icon = "󰊴"
        elif "phone" in info_lower:
            icon = "󰄡"

        devices.append({
            "mac": mac,
            "name": name,
            "connected": connected,
            "paired": paired,
            "icon": icon
        })
    return devices

class BluetoothApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("bluetooth-applet")
        self.set_title("Bluetooth")
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

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.main_box.get_style_context().add_class("main-box")
        self.main_box.set_margin_top(14)
        self.main_box.set_margin_bottom(14)
        self.main_box.set_margin_start(14)
        self.main_box.set_margin_end(14)
        self.add(self.main_box)

        self.rebuild_ui()

        # Keyboard and destruction events
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def rebuild_ui(self):
        # Clear previous widgets
        for child in self.main_box.get_children():
            self.main_box.remove(child)

        powered = is_powered()
        devices = get_devices() if powered else []
        connected_count = sum(1 for d in devices if d["connected"])

        # Header
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")

        icon_label = Gtk.Label(label="󰂯  Bluetooth")
        icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(icon_label, False, False, 0)

        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        if not powered:
            badge_text = "Off"
        elif connected_count > 0:
            badge_text = f"{connected_count} connected"
        else:
            badge_text = "On"

        badge = Gtk.Label(label=badge_text)
        badge.get_style_context().add_class("header-badge")
        right_header.pack_start(badge, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_header.pack_start(btn_close, False, False, 0)

        header_box.pack_end(right_header, False, False, 0)
        self.main_box.pack_start(header_box, False, False, 0)

        if not powered:
            btn_turn_on = Gtk.Button()
            btn_turn_on.set_can_focus(False)
            btn_turn_on.get_style_context().add_class("action-btn")
            lbl = Gtk.Label(label="󰂯   Turn on Bluetooth")
            lbl.set_xalign(0.0)
            btn_turn_on.add(lbl)
            btn_turn_on.connect("clicked", self.on_toggle_power)
            self.main_box.pack_start(btn_turn_on, False, False, 4)

            btn_blueman = Gtk.Button()
            btn_blueman.set_can_focus(False)
            btn_blueman.get_style_context().add_class("action-btn")
            lbl_b = Gtk.Label(label="   More Bluetooth Settings")
            lbl_b.set_xalign(0.0)
            btn_blueman.add(lbl_b)
            btn_blueman.connect("clicked", self.on_open_blueman)
            self.main_box.pack_start(btn_blueman, False, False, 0)
            self.show_all()
            return

        # Quick Actions when Powered On
        btn_turn_off = Gtk.Button()
        btn_turn_off.set_can_focus(False)
        btn_turn_off.get_style_context().add_class("action-btn")
        lbl_off = Gtk.Label(label="󰂲   Turn off Bluetooth")
        lbl_off.set_xalign(0.0)
        btn_turn_off.add(lbl_off)
        btn_turn_off.connect("clicked", self.on_toggle_power)
        self.main_box.pack_start(btn_turn_off, False, False, 0)

        btn_scan = Gtk.Button()
        btn_scan.set_can_focus(False)
        btn_scan.get_style_context().add_class("action-btn")
        self.lbl_scan = Gtk.Label(label="󰑓   Scan for new devices")
        self.lbl_scan.set_xalign(0.0)
        btn_scan.add(self.lbl_scan)
        btn_scan.connect("clicked", self.on_scan_clicked)
        self.main_box.pack_start(btn_scan, False, False, 0)

        btn_blueman = Gtk.Button()
        btn_blueman.set_can_focus(False)
        btn_blueman.get_style_context().add_class("action-btn")
        lbl_b = Gtk.Label(label="   More Bluetooth Settings")
        lbl_b.set_xalign(0.0)
        btn_blueman.add(lbl_b)
        btn_blueman.connect("clicked", self.on_open_blueman)
        self.main_box.pack_start(btn_blueman, False, False, 0)

        # Separator and device list
        sep_label = Gtk.Label(label="─── Paired / Nearby Devices ───")
        sep_label.get_style_context().add_class("section-sep")
        self.main_box.pack_start(sep_label, False, False, 2)

        if not devices:
            no_dev_lbl = Gtk.Label(label="No devices found")
            no_dev_lbl.get_style_context().add_class("section-sep")
            self.main_box.pack_start(no_dev_lbl, False, False, 4)
        else:
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_can_focus(False)
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_propagate_natural_height(False)
            scrolled.set_min_content_height(200)
            scrolled.set_max_content_height(240)
            scrolled.set_size_request(-1, 220)

            list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            for dev in devices:
                row_btn = Gtk.Button()
                row_btn.set_can_focus(False)
                row_btn.get_style_context().add_class("action-btn")
                if dev["connected"]:
                    row_btn.get_style_context().add_class("active")

                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                dev_icon = Gtk.Label(label=dev["icon"])
                row_box.pack_start(dev_icon, False, False, 0)

                status_suffix = "  (Connected)" if dev["connected"] else ""
                name_lbl = Gtk.Label(label=f"{dev['name']}{status_suffix}")
                name_lbl.set_xalign(0.0)
                name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                name_lbl.set_max_width_chars(25)
                row_box.pack_start(name_lbl, True, True, 0)

                action_hint = Gtk.Label(label="Disconnect" if dev["connected"] else "Connect")
                action_hint.get_style_context().add_class("section-sep")
                row_box.pack_end(action_hint, False, False, 0)

                row_btn.add(row_box)
                row_btn.connect("clicked", self.make_device_handler(dev))
                list_box.pack_start(row_btn, False, False, 0)

            scrolled.add(list_box)
            self.main_box.pack_start(scrolled, True, True, 0)

        self.show_all()
        GLib.idle_add(align_to_top_right)
        GLib.timeout_add(50, align_to_top_right)

    def on_toggle_power(self, btn):
        currently_powered = is_powered()
        toggle_power(not currently_powered)
        GLib.timeout_add(400, self.rebuild_ui)

    def on_open_blueman(self, btn):
        subprocess.Popen(["blueman-manager"])
        self.close_app()

    def on_scan_clicked(self, btn):
        self.lbl_scan.set_text("󰑓   Scanning... (8s)")
        subprocess.run(["notify-send", "-a", "Bluetooth", "Bluetooth", "Scanning for new devices..."])
        def scan_worker():
            try:
                proc = subprocess.Popen(["bluetoothctl", "scan", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                import time
                time.sleep(8)
                proc.terminate()
                subprocess.run(["bluetoothctl", "scan", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["notify-send", "-a", "Bluetooth", "Bluetooth", "Scan finished."])
            except Exception:
                pass
            GLib.idle_add(self.rebuild_ui)
        threading.Thread(target=scan_worker, daemon=True).start()

    def make_device_handler(self, dev):
        def handler(widget):
            mac = dev["mac"]
            name = dev["name"]
            connected = dev["connected"]
            if connected:
                subprocess.run(["notify-send", "-a", "Bluetooth", "Bluetooth", f"Disconnecting from '{name}'..."])
                subprocess.run(["bluetoothctl", "disconnect", mac])
            else:
                subprocess.run(["notify-send", "-a", "Bluetooth", "Bluetooth", f"Connecting to '{name}'..."])
                subprocess.run(["bluetoothctl", "connect", mac])
            GLib.timeout_add(1000, self.rebuild_ui)
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

    app = BluetoothApplet()
    app.show_all()
    GLib.idle_add(align_to_top_right)
    GLib.timeout_add(50, align_to_top_right)
    GLib.timeout_add(150, align_to_top_right)

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
