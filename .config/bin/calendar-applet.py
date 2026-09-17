#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integrated Notifications and Calendar in GTK3 for Hyprland.
Two-column GNOME style layout with Dunst history and Catppuccin/Breeze calendar.
"""
import os
import sys
import json
import signal
import subprocess
import warnings
from datetime import datetime

warnings.filterwarnings("ignore", category=DeprecationWarning)

PID_FILE = "/tmp/hypr_calendar_applet.pid"
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

GLib.set_prgname("calendar-applet")
GLib.set_application_name("calendar-applet")

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

def align_to_center(cal_w=620):
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
        target_y = mon_y + 32
        subprocess.run(
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(calendar-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

def format_relative_time(timestamp):
    if not timestamp:
        return ""
    try:
        ts = int(timestamp)
        if ts > 1e11:
            ts = ts / 1e6
        dt = datetime.fromtimestamp(ts)
        diff = datetime.now() - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        else:
            days = seconds // 86400
            return f"{days}d ago"
    except Exception:
        return ""

def get_notifications():
    try:
        res = subprocess.run(["dunstctl", "history"], capture_output=True, text=True, timeout=1)
        if res.returncode == 0 and res.stdout.strip():
            data = json.loads(res.stdout)
            raw_list = data.get("data", [[]])[0]
            notifs = []
            for item in raw_list:
                def parse_val(v):
                    if isinstance(v, dict) and "data" in v:
                        return v["data"]
                    return v or ""

                nid = parse_val(item.get("id"))
                appname = parse_val(item.get("appname")) or "System"
                summary = parse_val(item.get("summary")) or ""
                body = parse_val(item.get("body")) or ""
                timestamp = parse_val(item.get("timestamp"))

                time_str = format_relative_time(timestamp)

                if summary or body:
                    notifs.append({
                        "id": nid,
                        "appname": str(appname),
                        "summary": str(summary),
                        "body": str(body),
                        "time": time_str
                    })
            return notifs
    except Exception:
        pass
    return []

class NotificationCalendarApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("calendar-applet")
        self.set_title("Notifications & Calendar")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(660, 440)
        self.set_size_request(660, 440)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.get_style_context().add_class("calendar-window")

        # Main Container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_box.set_margin_top(16)
        self.main_box.set_margin_bottom(16)
        self.main_box.set_margin_start(16)
        self.main_box.set_margin_end(16)
        self.add(self.main_box)

        # Integrated 2-column layout (GNOME / Ubuntu style)
        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.pack_start(columns_box, True, True, 0)

        # -------------------------------------------------------------
        # LEFT COLUMN: NOTIFICATIONS
        # -------------------------------------------------------------
        self.notif_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.notif_box.set_size_request(320, 400)
        self.notif_box.set_hexpand(True)
        columns_box.pack_start(self.notif_box, True, True, 0)

        # Vertical Divider
        v_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        v_sep.set_margin_top(4)
        v_sep.set_margin_bottom(4)
        v_sep.get_style_context().add_class("v-separator")
        columns_box.pack_start(v_sep, False, False, 0)

        # -------------------------------------------------------------
        # RIGHT COLUMN: CALENDAR & DATE
        # -------------------------------------------------------------
        cal_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        cal_col.set_size_request(290, 400)
        cal_col.set_hexpand(True)
        columns_box.pack_start(cal_col, True, True, 0)

        # Date header
        now = datetime.now()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        weekday_str = days[now.weekday()]
        fulldate_str = f"{months[now.month - 1]} {now.day}, {now.year}"

        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        right_header.set_margin_bottom(4)

        date_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        date_box.set_margin_start(8)

        lbl_weekday = Gtk.Label(label=weekday_str)
        lbl_weekday.set_xalign(0.0)
        lbl_weekday.get_style_context().add_class("cal-weekday")
        date_box.pack_start(lbl_weekday, False, False, 0)

        lbl_fulldate = Gtk.Label(label=fulldate_str)
        lbl_fulldate.set_xalign(0.0)
        lbl_fulldate.get_style_context().add_class("cal-fulldate")
        date_box.pack_start(lbl_fulldate, False, False, 0)
        right_header.pack_start(date_box, True, True, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.set_valign(Gtk.Align.START)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_header.pack_end(btn_close, False, False, 0)

        cal_col.pack_start(right_header, False, False, 0)

        # Calendar Widget
        self.calendar = Gtk.Calendar()
        self.calendar.set_can_focus(False)
        self.calendar.set_property("show-heading", True)
        self.calendar.set_property("show-day-names", True)
        self.calendar.set_property("show-details", False)
        self.calendar.set_property("show-week-numbers", False)
        cal_col.pack_start(self.calendar, True, True, 0)

        # Today / Summary Card
        today_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        today_card.get_style_context().add_class("today-card")
        lbl_today = Gtk.Label(label="Today")
        lbl_today.set_xalign(0.0)
        lbl_today.get_style_context().add_class("today-title")
        today_card.pack_start(lbl_today, False, False, 0)

        lbl_no_events = Gtk.Label(label="No events")
        lbl_no_events.set_xalign(0.0)
        lbl_no_events.get_style_context().add_class("today-desc")
        today_card.pack_start(lbl_no_events, False, False, 0)
        cal_col.pack_start(today_card, False, False, 0)

        # Build notifications list
        self.render_notifications()

        # Keyboard and destruction events
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def render_notifications(self):
        for child in self.notif_box.get_children():
            self.notif_box.remove(child)

        notifs = get_notifications()

        if not notifs:
            # Empty state
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            empty_box.set_valign(Gtk.Align.CENTER)
            empty_box.set_halign(Gtk.Align.CENTER)
            empty_box.set_vexpand(True)

            bell_icon = Gtk.Label(label="󰂚")
            bell_icon.get_style_context().add_class("notif-empty-icon")
            empty_box.pack_start(bell_icon, False, False, 0)

            empty_lbl = Gtk.Label(label="No Notifications")
            empty_lbl.get_style_context().add_class("notif-empty-label")
            empty_box.pack_start(empty_lbl, False, False, 0)

            self.notif_box.pack_start(empty_box, True, True, 0)
        else:
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_can_focus(False)
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_propagate_natural_height(False)
            scrolled.set_vexpand(True)

            cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            cards_box.set_margin_end(6)

            for item in notifs:
                card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
                card.get_style_context().add_class("notif-card")

                # App + Time + Close
                header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

                icon_lbl = Gtk.Label(label="󰂚")
                icon_lbl.get_style_context().add_class("notif-icon")
                header_row.pack_start(icon_lbl, False, False, 0)

                app_lbl = Gtk.Label(label=item["appname"])
                app_lbl.get_style_context().add_class("notif-appname")
                app_lbl.set_xalign(0.0)
                header_row.pack_start(app_lbl, False, False, 0)

                if item["time"]:
                    time_lbl = Gtk.Label(label=item["time"])
                    time_lbl.get_style_context().add_class("notif-time")
                    header_row.pack_start(time_lbl, False, False, 0)

                if item["id"]:
                    btn_rm = Gtk.Button(label="✕")
                    btn_rm.set_can_focus(False)
                    btn_rm.get_style_context().add_class("btn-close-notif")
                    btn_rm.connect("clicked", lambda b, nid=item["id"]: self.on_remove_one(nid))
                    header_row.pack_end(btn_rm, False, False, 0)

                card.pack_start(header_row, False, False, 0)

                # Title
                if item["summary"]:
                    title_lbl = Gtk.Label(label=item["summary"])
                    title_lbl.set_xalign(0.0)
                    title_lbl.set_line_wrap(True)
                    title_lbl.get_style_context().add_class("notif-title")
                    card.pack_start(title_lbl, False, False, 0)

                # Body
                if item["body"]:
                    body_lbl = Gtk.Label(label=item["body"])
                    body_lbl.set_xalign(0.0)
                    body_lbl.set_line_wrap(True)
                    body_lbl.get_style_context().add_class("notif-body")
                    card.pack_start(body_lbl, False, False, 0)

                cards_box.pack_start(card, False, False, 0)

            scrolled.add(cards_box)
            self.notif_box.pack_start(scrolled, True, True, 0)

            # Clear button at bottom left (Ubuntu pill style)
            clear_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            clear_box.set_margin_top(10)
            clear_box.set_margin_bottom(2)
            clear_box.set_margin_start(2)
            self.btn_clear_all = Gtk.Button(label="Clear all")
            self.btn_clear_all.set_can_focus(False)
            self.btn_clear_all.get_style_context().add_class("btn-clear-ubuntu")
            self.btn_clear_all.connect("clicked", self.on_clear_all)
            clear_box.pack_start(self.btn_clear_all, False, False, 0)
            self.notif_box.pack_end(clear_box, False, False, 0)

        self.notif_box.show_all()

    def on_clear_all(self, btn):
        subprocess.run(["dunstctl", "history-clear"], stderr=subprocess.DEVNULL)
        subprocess.run(["dunstctl", "close-all"], stderr=subprocess.DEVNULL)
        self.render_notifications()

    def on_remove_one(self, nid):
        subprocess.run(["dunstctl", "history-rm", str(nid)], stderr=subprocess.DEVNULL)
        self.render_notifications()

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

    app = NotificationCalendarApplet()
    app.show_all()
    GLib.idle_add(lambda: align_to_center(620))
    GLib.timeout_add(50, lambda: align_to_center(620))
    GLib.timeout_add(150, lambda: align_to_center(620))

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
