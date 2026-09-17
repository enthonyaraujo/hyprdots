#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Seletor moderno de papéis de parede nativo em Python 3 + GTK 3 para Hyprland.
Substitui o Rofi com miniaturas 16:9 widescreen, realce Catppuccin/Breeze e integração ao hyprpaper.
"""
import os
import sys
import re
import json
import signal
import subprocess
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=DeprecationWarning)

PID_FILE = "/tmp/hypr_wallpaper_applet.pid"
ALL_PID_FILES = [
    "/tmp/hypr_audio_applet.pid",
    "/tmp/hypr_calendar_applet.pid",
    "/tmp/hypr_wifi_applet.pid",
    "/tmp/hypr_bluetooth_applet.pid",
    "/tmp/hypr_power_applet.pid",
    "/tmp/hypr_session_applet.pid",
    "/tmp/hypr_wallpaper_applet.pid",
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
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf

GLib.set_prgname("wallpaper-applet")
GLib.set_application_name("wallpaper-applet")

CSS_FILE = os.path.expanduser("~/.config/gtk-3.0/applets.css")
WALLPAPER_DIR = os.path.expanduser("~/.config/wallpapers")
CONFIG_FILE = os.path.expanduser("~/.config/hypr/wallpaper.conf")
CACHE_DIR = os.path.expanduser("~/.cache/wallpaper-thumbnails")

def load_styles():
    provider = Gtk.CssProvider()
    if os.path.exists(CSS_FILE):
        provider.load_from_path(CSS_FILE)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

def format_name(filename):
    base = os.path.splitext(filename)[0]
    words = base.replace("_", " ").replace("-", " ").split()
    return " ".join(w.capitalize() for w in words)

def get_current_wallpaper():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("$wallpaper_hyprland"):
                        parts = line.split("=", 1)
                        if len(parts) == 2:
                            return parts[1].strip()
        except Exception:
            pass
    return ""

def align_to_center(win_w=850, win_h=260):
    try:
        monitors = json.loads(subprocess.check_output(["hyprctl", "monitors", "-j"]))
        focused = next((m for m in monitors if m.get("focused")), monitors[0])
        mon_x = focused["x"]
        mon_y = focused["y"]
        mon_w = int(focused["width"] / focused["scale"])
        mon_h = int(focused["height"] / focused["scale"])

        try:
            clients = json.loads(subprocess.check_output(["hyprctl", "clients", "-j"]))
            for c in clients:
                if c.get("class") == "wallpaper-applet":
                    win_w = c["size"][0]
                    win_h = c["size"][1]
                    break
        except Exception:
            pass

        target_x = mon_x + (mon_w - win_w) // 2
        target_y = mon_y + (mon_h - win_h) // 2
        subprocess.run(
            ["hyprctl", "dispatch", "movewindowpixel", f"exact {target_x} {target_y}", ",class:^(wallpaper-applet)$"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass
    return False

class WallpaperApplet(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_role("wallpaper-applet")
        self.set_title("Escolher Papel de Parede")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)

        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.get_style_context().add_class("wallpaper-window")

        self.current_wallpaper = get_current_wallpaper()
        self.wallpapers = self.load_wallpaper_list()
        self.selected_index = 0
        self.cards = []

        # Find initial selected index matching current wallpaper
        for i, wp in enumerate(self.wallpapers):
            if wp == self.current_wallpaper:
                self.selected_index = i
                break

        # Container Principal
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        self.main_box.set_margin_top(16)
        self.main_box.set_margin_bottom(16)
        self.main_box.set_margin_start(16)
        self.main_box.set_margin_end(16)
        self.add(self.main_box)

        # Header Box
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon_lbl = Gtk.Label(label="󰸉")
        icon_lbl.get_style_context().add_class("header-icon")
        title_box.pack_start(icon_lbl, False, False, 0)

        title_lbl = Gtk.Label(label="Papéis de Parede")
        title_lbl.get_style_context().add_class("header-title")
        title_box.pack_start(title_lbl, False, False, 0)

        count_str = f"{len(self.wallpapers)} disponíveis"
        badge_lbl = Gtk.Label(label=count_str)
        badge_lbl.get_style_context().add_class("badge-active")
        title_box.pack_start(badge_lbl, False, False, 0)

        header_box.pack_start(title_box, False, False, 0)

        btn_close = Gtk.Button(label="✕")
        btn_close.set_can_focus(False)
        btn_close.get_style_context().add_class("btn-close")
        btn_close.connect("clicked", lambda b: self.close_app())
        header_box.pack_end(btn_close, False, False, 0)

        self.main_box.pack_start(header_box, False, False, 0)

        # Cards Container
        os.makedirs(CACHE_DIR, exist_ok=True)
        cards_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        cards_box.set_halign(Gtk.Align.CENTER)
        self.main_box.pack_start(cards_box, True, True, 0)

        for i, full_path in enumerate(self.wallpapers):
            wp_file = os.path.basename(full_path)
            is_active = (full_path == self.current_wallpaper)

            event_box = Gtk.EventBox()
            event_box.set_can_focus(False)
            event_box.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.ENTER_NOTIFY_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)

            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            card.get_style_context().add_class("wallpaper-card")
            if is_active:
                card.get_style_context().add_class("wallpaper-card-active")

            # Thumbnail (16:9 widescreen ratio)
            pixbuf = self.get_thumbnail(full_path)
            if pixbuf:
                img = Gtk.Image.new_from_pixbuf(pixbuf)
                img.get_style_context().add_class("wallpaper-thumb")
                card.pack_start(img, False, False, 0)

            # Info Row
            info_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            name_lbl = Gtk.Label(label=format_name(wp_file))
            name_lbl.get_style_context().add_class("wallpaper-title")
            name_lbl.set_xalign(0.0)
            info_row.pack_start(name_lbl, True, True, 0)

            if is_active:
                badge = Gtk.Label(label="󰄬 Atual")
                badge.get_style_context().add_class("wallpaper-badge-current")
                info_row.pack_end(badge, False, False, 0)
            else:
                hint = Gtk.Label(label="Aplicar")
                hint.get_style_context().add_class("wallpaper-hint")
                info_row.pack_end(hint, False, False, 0)

            card.pack_start(info_row, False, False, 0)
            event_box.add(card)

            # Event callbacks
            event_box.connect("button-press-event", lambda w, e, p=full_path: self.on_card_clicked(p))
            event_box.connect("enter-notify-event", lambda w, e, idx=i: self.on_card_hover(idx))

            cards_box.pack_start(event_box, False, False, 0)
            self.cards.append((event_box, card, full_path))

        self.update_keyboard_highlight()

        # Keyboard & Destroy
        self.connect("key-press-event", self.on_key_press)
        self.connect("destroy", self.cleanup)

    def load_wallpaper_list(self):
        if not os.path.exists(WALLPAPER_DIR):
            return []
        valid_exts = {".jpg", ".jpeg", ".png", ".webp"}
        files = []
        for f in os.listdir(WALLPAPER_DIR):
            ext = os.path.splitext(f)[1].lower()
            if ext in valid_exts:
                files.append(os.path.join(WALLPAPER_DIR, f))
        return sorted(files)

    def get_thumbnail(self, path, width=240, height=135):
        cache_name = re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.basename(path)) + f"_{width}x{height}.png"
        cache_file = os.path.join(CACHE_DIR, cache_name)

        try:
            file_mtime = os.path.getmtime(path)
            if os.path.exists(cache_file):
                cache_mtime = os.path.getmtime(cache_file)
                if cache_mtime >= file_mtime:
                    return GdkPixbuf.Pixbuf.new_from_file(cache_file)
        except Exception:
            pass

        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, width, height, False)
            pixbuf.savev(cache_file, "png", [], [])
            return pixbuf
        except Exception:
            return None

    def on_card_hover(self, index):
        self.selected_index = index
        self.update_keyboard_highlight()

    def update_keyboard_highlight(self):
        for i, (eb, card, path) in enumerate(self.cards):
            ctx = card.get_style_context()
            is_active = (path == self.current_wallpaper)
            if i == self.selected_index:
                ctx.add_class("wallpaper-card-active")
            elif not is_active:
                ctx.remove_class("wallpaper-card-active")

    def on_key_press(self, widget, event):
        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            self.close_app()
            return True
        elif event.keyval in (Gdk.KEY_Left, Gdk.KEY_h):
            if self.cards:
                self.selected_index = (self.selected_index - 1) % len(self.cards)
                self.update_keyboard_highlight()
            return True
        elif event.keyval in (Gdk.KEY_Right, Gdk.KEY_l):
            if self.cards:
                self.selected_index = (self.selected_index + 1) % len(self.cards)
                self.update_keyboard_highlight()
            return True
        elif event.keyval in (Gdk.KEY_Return, Gdk.KEY_space, Gdk.KEY_KP_Enter):
            if self.cards and 0 <= self.selected_index < len(self.cards):
                _, _, selected_path = self.cards[self.selected_index]
                self.apply_wallpaper(selected_path)
            return True
        return False

    def on_card_clicked(self, path):
        self.apply_wallpaper(path)

    def apply_wallpaper(self, path):
        # 1. Atualizar arquivo wallpaper.conf do Hyprland
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    content = f.read()
                new_content = re.sub(r"^(\$wallpaper_hyprland\s*=).*", f"\1 {path}", content, flags=re.MULTILINE)
                with open(CONFIG_FILE, "w") as f:
                    f.write(new_content)
        except Exception as e:
            print("Erro ao atualizar config:", e)

        # 2. Atualizar hyprpaper live
        try:
            subprocess.run(["hyprctl", "hyprpaper", "preload", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(["hyprctl", "hyprpaper", "wallpaper", f",{path}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        # Forçar reinício silencioso do hyprpaper para garantir recarregamento de todos os monitores
        subprocess.run(["killall", "hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.Popen(["hyprpaper"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Notificação
        name = format_name(os.path.basename(path))
        subprocess.run(["notify-send", "-i", path, "Papel de Parede", f"Alterado para {name}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 4. Fechar applet
        self.close_app()

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

    app = WallpaperApplet()
    app.show_all()

    # Centralizar suavemente
    GLib.idle_add(lambda: align_to_center())
    GLib.timeout_add(50, lambda: align_to_center())
    GLib.timeout_add(150, lambda: align_to_center())

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (app.cleanup(), Gtk.main_quit()))
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, lambda: (app.cleanup(), Gtk.main_quit()))
    Gtk.main()

if __name__ == "__main__":
    main()
