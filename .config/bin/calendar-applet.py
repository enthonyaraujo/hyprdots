#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Central de Notificações e Calendário Integrado em GTK3 para Hyprland.
Layout de duas colunas estilo GNOME com histórico do Dunst e calendário Catppuccin/Breeze.
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
        target_y = mon_y + 46
        subprocess.run(
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(calendar-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

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
                appname = parse_val(item.get("appname")) or "Sistema"
                summary = parse_val(item.get("summary")) or ""
                body = parse_val(item.get("body")) or ""
                timestamp = parse_val(item.get("timestamp"))

                time_str = ""
                if timestamp:
                    try:
                        ts = int(timestamp)
                        if ts > 1e11:
                            ts = ts / 1e6
                        dt = datetime.fromtimestamp(ts)
                        time_str = dt.strftime("%H:%M")
                    except Exception:
                        pass

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
        self.set_title("Central de Notificações e Calendário")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(620, -1)
        self.set_size_request(620, -1)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.get_style_context().add_class("calendar-window")

        # Container Principal
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.main_box.set_margin_top(14)
        self.main_box.set_margin_bottom(14)
        self.main_box.set_margin_start(14)
        self.main_box.set_margin_end(14)
        self.add(self.main_box)

        # Cabeçalho Superior Integrado
        top_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_header.get_style_context().add_class("header-box")

        notif_header_title = Gtk.Label(label="󰂚  Central de Notificações")
        notif_header_title.get_style_context().add_class("header-title")
        top_header.pack_start(notif_header_title, False, False, 0)

        right_top_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.btn_clear_all = Gtk.Button(label="󰃢  Limpar")
        self.btn_clear_all.set_can_focus(False)
        self.btn_clear_all.get_style_context().add_class("small-btn")
        self.btn_clear_all.connect("clicked", self.on_clear_all)
        right_top_header.pack_start(self.btn_clear_all, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_top_header.pack_start(btn_close, False, False, 0)

        top_header.pack_end(right_top_header, False, False, 0)
        self.main_box.pack_start(top_header, False, False, 0)

        # Layout de 2 Colunas
        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.main_box.pack_start(columns_box, True, True, 4)

        # -------------------------------------------------------------
        # COLUNA ESQUERDA: NOTIFICAÇÕES
        # -------------------------------------------------------------
        self.notif_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.notif_box.set_size_request(290, 310)
        self.notif_box.set_hexpand(True)
        columns_box.pack_start(self.notif_box, True, True, 0)

        # Divisor Vertical
        v_sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        v_sep.get_style_context().add_class("v-separator")
        columns_box.pack_start(v_sep, False, False, 0)

        # -------------------------------------------------------------
        # COLUNA DIREITA: CALENDÁRIO & DATA
        # -------------------------------------------------------------
        cal_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        cal_col.set_size_request(290, 310)
        cal_col.set_hexpand(True)
        columns_box.pack_start(cal_col, True, True, 0)

        # Data por extenso (estilo do exemplo enviado)
        now = datetime.now()
        dias = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
        weekday_str = dias[now.weekday()].capitalize()
        fulldate_str = f"{meses[now.month - 1]} {now.day} {now.year}"

        date_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        date_box.set_margin_start(4)
        lbl_weekday = Gtk.Label(label=weekday_str)
        lbl_weekday.set_xalign(0.0)
        lbl_weekday.get_style_context().add_class("cal-weekday")
        date_box.pack_start(lbl_weekday, False, False, 0)

        lbl_fulldate = Gtk.Label(label=fulldate_str)
        lbl_fulldate.set_xalign(0.0)
        lbl_fulldate.get_style_context().add_class("cal-fulldate")
        date_box.pack_start(lbl_fulldate, False, False, 0)
        cal_col.pack_start(date_box, False, False, 0)

        # Widget do Calendário GTK
        self.calendar = Gtk.Calendar()
        self.calendar.set_can_focus(False)
        self.calendar.set_property("show-heading", True)
        self.calendar.set_property("show-day-names", True)
        self.calendar.set_property("show-details", False)
        self.calendar.set_property("show-week-numbers", False)
        cal_col.pack_start(self.calendar, True, True, 0)

        # Card Hoje / Resumo
        today_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        today_card.get_style_context().add_class("today-card")
        lbl_today = Gtk.Label(label="󰃭  Hoje")
        lbl_today.set_xalign(0.0)
        lbl_today.get_style_context().add_class("today-title")
        today_card.pack_start(lbl_today, False, False, 0)

        lbl_no_events = Gtk.Label(label="Nenhum evento agendado")
        lbl_no_events.set_xalign(0.0)
        lbl_no_events.get_style_context().add_class("today-desc")
        today_card.pack_start(lbl_no_events, False, False, 0)
        cal_col.pack_start(today_card, False, False, 0)

        # Montar Lista de Notificações
        self.render_notifications()

        # Teclado e destruição
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def render_notifications(self):
        for child in self.notif_box.get_children():
            self.notif_box.remove(child)

        notifs = get_notifications()

        if not notifs:
            self.btn_clear_all.set_visible(False)

            # Estado Vazio com Ícone de Sino (Visual exatamente como na imagem de referência)
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            empty_box.set_valign(Gtk.Align.CENTER)
            empty_box.set_halign(Gtk.Align.CENTER)
            empty_box.set_vexpand(True)

            bell_icon = Gtk.Label(label="󰂚")
            bell_icon.get_style_context().add_class("notif-empty-icon")
            empty_box.pack_start(bell_icon, False, False, 0)

            empty_lbl = Gtk.Label(label="Nenhuma Notificação")
            empty_lbl.get_style_context().add_class("notif-empty-label")
            empty_box.pack_start(empty_lbl, False, False, 0)

            self.notif_box.pack_start(empty_box, True, True, 0)
        else:
            self.btn_clear_all.set_visible(True)

            scrolled = Gtk.ScrolledWindow()
            scrolled.set_can_focus(False)
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_max_content_height(300)
            scrolled.set_propagate_natural_height(False)
            scrolled.set_vexpand(True)

            cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            cards_box.set_margin_end(4)

            for item in notifs:
                card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
                card.get_style_context().add_class("notif-card")

                # Linha do App + Horário + Fechar
                header_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                app_lbl = Gtk.Label(label=f"󰂚 {item['appname']}")
                app_lbl.get_style_context().add_class("notif-appname")
                app_lbl.set_xalign(0.0)
                header_row.pack_start(app_lbl, False, False, 0)

                right_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
                if item["time"]:
                    time_lbl = Gtk.Label(label=item["time"])
                    time_lbl.get_style_context().add_class("notif-time")
                    right_card.pack_start(time_lbl, False, False, 0)

                if item["id"]:
                    btn_rm = Gtk.Button(label="✕")
                    btn_rm.set_can_focus(False)
                    btn_rm.get_style_context().add_class("btn-close-notif")
                    btn_rm.connect("clicked", lambda b, nid=item["id"]: self.on_remove_one(nid))
                    right_card.pack_start(btn_rm, False, False, 0)

                header_row.pack_end(right_card, False, False, 0)
                card.pack_start(header_row, False, False, 0)

                # Título
                if item["summary"]:
                    title_lbl = Gtk.Label(label=item["summary"])
                    title_lbl.set_xalign(0.0)
                    title_lbl.set_line_wrap(True)
                    title_lbl.get_style_context().add_class("notif-title")
                    card.pack_start(title_lbl, False, False, 0)

                # Corpo
                if item["body"]:
                    body_lbl = Gtk.Label(label=item["body"])
                    body_lbl.set_xalign(0.0)
                    body_lbl.set_line_wrap(True)
                    body_lbl.get_style_context().add_class("notif-body")
                    card.pack_start(body_lbl, False, False, 0)

                cards_box.pack_start(card, False, False, 0)

            scrolled.add(cards_box)
            self.notif_box.pack_start(scrolled, True, True, 0)

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
