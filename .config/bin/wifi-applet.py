#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Applet moderno de Wi-Fi em GTK3 para Hyprland.
Estilo translúcido Breeze/Catppuccin alinhado no canto superior direito.
"""
import os
import sys
import json
import signal
import subprocess
import threading
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

PID_FILE = "/tmp/hypr_wifi_applet.pid"
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

GLib.set_prgname("wifi-applet")
GLib.set_application_name("wifi-applet")

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
        target_y = mon_y + 46
        subprocess.run(
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(wifi-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

def get_wifi_status():
    res = subprocess.run(
        ["nmcli", "-t", "-f", "WIFI", "general", "status"],
        text=True,
        stdout=subprocess.PIPE
    )
    return "enabled" in res.stdout.lower()

def toggle_wifi(enable):
    state = "on" if enable else "off"
    subprocess.run(["nmcli", "radio", "wifi", state])
    subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Wi-Fi {'ativado' if enable else 'desativado'}."])

def get_saved_connections():
    res = subprocess.run(
        ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
        text=True,
        stdout=subprocess.PIPE
    )
    saved = set()
    for line in res.stdout.strip().split("\n"):
        if ":802-11-wireless" in line:
            name = line.split(":802-11-wireless")[0]
            saved.add(name)
    return saved

def get_signal_icon(bars):
    if "█" in bars:
        return "󰤨"
    elif "▆" in bars:
        return "󰤥"
    elif "▄" in bars:
        return "󰤢"
    else:
        return "󰤟"

def scan_networks():
    scan_res = subprocess.run(
        ["nmcli", "-t", "-f", "IN-USE,SSID,BARS,SECURITY", "device", "wifi", "list"],
        text=True,
        stdout=subprocess.PIPE
    )

    current_ssid = None
    networks = []
    seen_ssids = set()

    for line in scan_res.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split(":")
        if len(parts) < 4:
            continue
        in_use = parts[0].strip() == "*"
        ssid = parts[1].strip()
        bars = parts[2].strip()
        security = parts[3].strip()

        if not ssid or ssid in seen_ssids:
            continue
        seen_ssids.add(ssid)

        if in_use:
            current_ssid = ssid

        icon = get_signal_icon(bars)
        is_secured = bool(security and security != "--")
        networks.append({
            "ssid": ssid,
            "in_use": in_use,
            "icon": icon,
            "secured": is_secured,
            "security": security
        })

    # Rede conectada sempre em primeiro lugar
    networks.sort(key=lambda x: (not x["in_use"]))
    return current_ssid, networks

class WifiApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("wifi-applet")
        self.set_title("Wi-Fi")
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

        # Container principal
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.main_box.get_style_context().add_class("main-box")
        self.main_box.set_margin_top(14)
        self.main_box.set_margin_bottom(14)
        self.main_box.set_margin_start(14)
        self.main_box.set_margin_end(14)
        self.add(self.main_box)

        self.password_mode = False
        self.rebuild_ui()

        # Teclado e destruição
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def rebuild_ui(self):
        for child in self.main_box.get_children():
            self.main_box.remove(child)

        self.password_mode = False
        wifi_enabled = get_wifi_status()
        current_ssid, networks = scan_networks() if wifi_enabled else (None, [])
        saved_conns = get_saved_connections() if wifi_enabled else set()

        # Cabeçalho
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")

        icon_label = Gtk.Label(label="󰤨  Wi-Fi")
        icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(icon_label, False, False, 0)

        right_header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        if not wifi_enabled:
            badge_text = "Desativado"
        elif current_ssid:
            badge_text = current_ssid
        else:
            badge_text = "Desconectado"

        badge = Gtk.Label(label=badge_text)
        badge.set_ellipsize(Pango.EllipsizeMode.END)
        badge.set_max_width_chars(16)
        badge.get_style_context().add_class("header-badge")
        right_header.pack_start(badge, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        right_header.pack_start(btn_close, False, False, 0)

        header_box.pack_end(right_header, False, False, 0)
        self.main_box.pack_start(header_box, False, False, 0)

        if not wifi_enabled:
            btn_on = Gtk.Button()
            btn_on.set_can_focus(False)
            btn_on.get_style_context().add_class("action-btn")
            lbl_on = Gtk.Label(label="󰤨   Ativar Wi-Fi")
            lbl_on.set_xalign(0.0)
            btn_on.add(lbl_on)
            btn_on.connect("clicked", self.on_toggle_wifi)
            self.main_box.pack_start(btn_on, False, False, 4)

            btn_settings = Gtk.Button()
            btn_settings.set_can_focus(False)
            btn_settings.get_style_context().add_class("action-btn")
            lbl_s = Gtk.Label(label="   Configurações de Rede")
            lbl_s.set_xalign(0.0)
            btn_settings.add(lbl_s)
            btn_settings.connect("clicked", self.on_open_settings)
            self.main_box.pack_start(btn_settings, False, False, 0)
            self.show_all()
            return

        # Ações do Wi-Fi Ligado
        if current_ssid:
            btn_disc = Gtk.Button()
            btn_disc.set_can_focus(False)
            btn_disc.get_style_context().add_class("action-btn")
            lbl_d = Gtk.Label(label=f"󰖪   Desconectar de '{current_ssid}'")
            lbl_d.set_xalign(0.0)
            lbl_d.set_ellipsize(Pango.EllipsizeMode.END)
            lbl_d.set_max_width_chars(28)
            btn_disc.add(lbl_d)
            btn_disc.connect("clicked", lambda b, s=current_ssid: self.on_disconnect(s))
            self.main_box.pack_start(btn_disc, False, False, 0)

        btn_off = Gtk.Button()
        btn_off.set_can_focus(False)
        btn_off.get_style_context().add_class("action-btn")
        lbl_off = Gtk.Label(label="󰤮   Desativar Wi-Fi")
        lbl_off.set_xalign(0.0)
        btn_off.add(lbl_off)
        btn_off.connect("clicked", self.on_toggle_wifi)
        self.main_box.pack_start(btn_off, False, False, 0)

        btn_rescan = Gtk.Button()
        btn_rescan.set_can_focus(False)
        btn_rescan.get_style_context().add_class("action-btn")
        self.lbl_rescan = Gtk.Label(label="󰑓   Escanear novamente")
        self.lbl_rescan.set_xalign(0.0)
        btn_rescan.add(self.lbl_rescan)
        btn_rescan.connect("clicked", self.on_rescan_clicked)
        self.main_box.pack_start(btn_rescan, False, False, 0)

        btn_settings = Gtk.Button()
        btn_settings.set_can_focus(False)
        btn_settings.get_style_context().add_class("action-btn")
        lbl_s = Gtk.Label(label="   Configurações de Rede")
        lbl_s.set_xalign(0.0)
        btn_settings.add(lbl_s)
        btn_settings.connect("clicked", self.on_open_settings)
        self.main_box.pack_start(btn_settings, False, False, 0)

        sep_label = Gtk.Label(label="─── Redes Disponíveis ───")
        sep_label.get_style_context().add_class("section-sep")
        self.main_box.pack_start(sep_label, False, False, 2)

        if not networks:
            no_net_lbl = Gtk.Label(label="Nenhuma rede encontrada")
            no_net_lbl.get_style_context().add_class("section-sep")
            self.main_box.pack_start(no_net_lbl, False, False, 4)
        else:
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_can_focus(False)
            scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_max_content_height(260)
            scrolled.set_propagate_natural_height(True)

            list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            for net in networks:
                btn_net = Gtk.Button()
                btn_net.set_can_focus(False)
                btn_net.get_style_context().add_class("action-btn")
                if net["in_use"]:
                    btn_net.get_style_context().add_class("active")

                row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                sig_icon = Gtk.Label(label=net["icon"])
                row_box.pack_start(sig_icon, False, False, 0)

                lock_tag = " " if net["secured"] else ""
                name_lbl = Gtk.Label(label=f"{net['ssid']}{lock_tag}")
                name_lbl.set_xalign(0.0)
                name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                name_lbl.set_max_width_chars(24)
                row_box.pack_start(name_lbl, True, True, 0)

                if net["in_use"]:
                    status_lbl = Gtk.Label(label="Conectado ✓")
                    status_lbl.get_style_context().add_class("section-sep")
                    row_box.pack_end(status_lbl, False, False, 0)
                elif net["ssid"] in saved_conns:
                    status_lbl = Gtk.Label(label="Salva")
                    status_lbl.get_style_context().add_class("section-sep")
                    row_box.pack_end(status_lbl, False, False, 0)

                btn_net.add(row_box)
                btn_net.connect("clicked", self.make_network_handler(net, saved_conns))
                list_box.pack_start(btn_net, False, False, 0)

            scrolled.add(list_box)
            self.main_box.pack_start(scrolled, True, True, 0)

        self.show_all()

    def show_password_prompt(self, net):
        self.password_mode = True
        for child in self.main_box.get_children():
            self.main_box.remove(child)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")

        icon_label = Gtk.Label(label="  Conectar ao Wi-Fi")
        icon_label.get_style_context().add_class("header-title")
        header_box.pack_start(icon_label, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.rebuild_ui())
        header_box.pack_end(btn_close, False, False, 0)
        self.main_box.pack_start(header_box, False, False, 4)

        ssid_lbl = Gtk.Label(label=f"Rede: {net['ssid']}")
        ssid_lbl.set_xalign(0.0)
        ssid_lbl.get_style_context().add_class("section-sep")
        self.main_box.pack_start(ssid_lbl, False, False, 2)

        entry = Gtk.Entry()
        entry.set_visibility(False)
        entry.set_placeholder_text("Digite a senha da rede...")
        entry.get_style_context().add_class("applet-entry")
        self.main_box.pack_start(entry, False, False, 4)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn_box.set_halign(Gtk.Align.FILL)

        btn_cancel = Gtk.Button(label="Cancelar")
        btn_cancel.set_can_focus(False)
        btn_cancel.get_style_context().add_class("action-btn")
        btn_cancel.connect("clicked", lambda b: self.rebuild_ui())
        btn_box.pack_start(btn_cancel, True, True, 0)

        btn_connect = Gtk.Button(label="Conectar")
        btn_connect.set_can_focus(False)
        btn_connect.get_style_context().add_class("action-btn")
        btn_connect.get_style_context().add_class("active")

        def on_submit(b=None):
            pwd = entry.get_text().strip()
            if not pwd:
                return
            subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Conectando a '{net['ssid']}'..."])
            def connect_worker():
                res = subprocess.run(
                    ["nmcli", "device", "wifi", "connect", net["ssid"], "password", pwd],
                    capture_output=True,
                    text=True
                )
                if res.returncode == 0:
                    subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Conectado com sucesso a '{net['ssid']}'."])
                else:
                    subprocess.run(["notify-send", "-u", "critical", "-a", "Wi-Fi", "Wi-Fi", f"Falha ao conectar: {res.stderr.strip()}"])
                GLib.idle_add(self.rebuild_ui)
            threading.Thread(target=connect_worker, daemon=True).start()

        btn_connect.connect("clicked", on_submit)
        entry.connect("activate", on_submit)
        btn_box.pack_start(btn_connect, True, True, 0)

        self.main_box.pack_start(btn_box, False, False, 4)
        self.show_all()
        entry.grab_focus()

    def make_network_handler(self, net, saved_conns):
        def handler(widget):
            if net["in_use"]:
                return
            ssid = net["ssid"]
            if ssid in saved_conns:
                subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Conectando a '{ssid}'..."])
                def connect_saved():
                    res = subprocess.run(["nmcli", "connection", "up", "id", ssid], capture_output=True, text=True)
                    if res.returncode == 0:
                        subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Conectado com sucesso a '{ssid}'."])
                    else:
                        subprocess.run(["notify-send", "-u", "critical", "-a", "Wi-Fi", "Wi-Fi", f"Erro ao conectar: {res.stderr.strip()}"])
                    GLib.idle_add(self.rebuild_ui)
                threading.Thread(target=connect_saved, daemon=True).start()
            elif net["secured"]:
                self.show_password_prompt(net)
            else:
                subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Conectando à rede aberta '{ssid}'..."])
                def connect_open():
                    res = subprocess.run(["nmcli", "device", "wifi", "connect", ssid], capture_output=True, text=True)
                    if res.returncode == 0:
                        subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Conectado com sucesso a '{ssid}'."])
                    else:
                        subprocess.run(["notify-send", "-u", "critical", "-a", "Wi-Fi", "Wi-Fi", f"Erro: {res.stderr.strip()}"])
                    GLib.idle_add(self.rebuild_ui)
                threading.Thread(target=connect_open, daemon=True).start()
        return handler

    def on_disconnect(self, ssid):
        subprocess.run(["nmcli", "connection", "down", "id", ssid], stderr=subprocess.DEVNULL)
        subprocess.run(["nmcli", "device", "disconnect", "wlan0"], stderr=subprocess.DEVNULL)
        subprocess.run(["notify-send", "-a", "Wi-Fi", "Wi-Fi", f"Desconectado de '{ssid}'."])
        GLib.timeout_add(500, self.rebuild_ui)

    def on_toggle_wifi(self, btn):
        status = get_wifi_status()
        toggle_wifi(not status)
        GLib.timeout_add(500, self.rebuild_ui)

    def on_rescan_clicked(self, btn):
        self.lbl_rescan.set_text("󰑓   Escaneando...")
        def rescan_worker():
            subprocess.run(["nmcli", "device", "wifi", "rescan"], stderr=subprocess.DEVNULL)
            import time
            time.sleep(2)
            GLib.idle_add(self.rebuild_ui)
        threading.Thread(target=rescan_worker, daemon=True).start()

    def on_open_settings(self, btn):
        subprocess.Popen(["nm-connection-editor"])
        self.close_app()

    def on_key_press(self, widget, event):
        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            if self.password_mode:
                self.rebuild_ui()
                return True
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

    app = WifiApplet()
    app.show_all()
    GLib.idle_add(align_to_top_right)
    GLib.timeout_add(50, align_to_top_right)
    GLib.timeout_add(150, align_to_top_right)

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
