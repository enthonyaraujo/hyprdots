#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
Hyprland Dash to Dock — Native GTK4 Layer Shell Dock
=============================================================================
Features:
- Native Wayland Layer Shell (anchored to bottom, floating island pill)
- GNOME Dash to Dock visual style with Kora icon integration
- Smooth animated Intellihide / Auto-hide:
  * Stays visible when active workspace has NO open windows
  * Hides automatically when windows are present on the workspace
  * Instant reveal when mouse cursor touches the bottom screen edge
- Running indicators (accent dots) & active window highlighting
- Easy app pinning:
  * Right-click any running app -> "Pin to Dock"
  * Right-click any pinned app -> "Unpin from Dock"
  * Or edit ~/.config/dock/dock.json directly (auto-reloads on save)
- 9-dots application grid launcher (opens Rofi menu)
- Dynamic dark & light theme synchronization
=============================================================================
"""

import os
import sys

# Auto-preload GTK4 Layer Shell if not already in LD_PRELOAD
if "libgtk4-layer-shell" not in os.environ.get("LD_PRELOAD", ""):
    env = os.environ.copy()
    env["LD_PRELOAD"] = "/usr/lib/x86_64-linux-gnu/libgtk4-layer-shell.so.0"
    env.setdefault("GTK_THEME", "Default")
    os.execve(sys.executable, [sys.executable, __file__] + sys.argv[1:], env)

import json
import signal
import socket
import subprocess
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, GLib, Gtk4LayerShell

CONFIG_DIR = Path(os.path.expanduser("~/.config/dock"))
CONFIG_FILE = CONFIG_DIR / "dock.json"
CSS_FILE = CONFIG_DIR / "style.css"
PID_FILE = "/tmp/hypr_dock.pid"

DEFAULT_CONFIG = {
    "pinned": [
        "firefox",
        "org.gnome.Nautilus",
        "kitty",
        "code",
        "obsidian"
    ],
    "icon_size": 44,
    "autohide": True,
    "show_running": True,
    "show_launcher": True
}


def ensure_single_instance():
    """Kill any previous running dock process to ensure a single instance."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, "r") as f:
                old_pid = int(f.read().strip())
            if old_pid != os.getpid():
                os.kill(old_pid, signal.SIGTERM)
        except Exception:
            pass
        try:
            os.remove(PID_FILE)
        except Exception:
            pass

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def load_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                return {**DEFAULT_CONFIG, **data}
        except Exception as e:
            print(f"[Dock] Error reading config: {e}")
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = CONFIG_FILE.with_suffix(".tmp")
    try:
        with open(tmp_file, "w") as f:
            json.dump(cfg, f, indent=2)
        tmp_file.replace(CONFIG_FILE)
    except Exception as e:
        print(f"[Dock] Error saving config: {e}")


class DesktopAppsIndex:
    """Indexes and looks up .desktop applications on the system."""
    def __init__(self):
        self.apps = []
        self.by_id = {}
        self.by_name = {}
        self.by_wmclass = {}
        self.refresh()

    def refresh(self):
        self.apps = Gio.DesktopAppInfo.get_all()
        self.by_id.clear()
        self.by_name.clear()
        self.by_wmclass.clear()

        for app in self.apps:
            aid = app.get_id() or ""
            aname = (app.get_name() or "").lower()
            base_id = aid.replace(".desktop", "").lower()
            wmclass = (app.get_startup_wm_class() or "").lower()

            self.by_id[aid.lower()] = app
            self.by_id[base_id] = app
            self.by_name[aname] = app
            if wmclass:
                self.by_wmclass[wmclass] = app

    def find(self, identifier):
        if not identifier:
            return None
        low = identifier.lower().strip()
        low_nobase = low.replace(".desktop", "")

        # 1. Direct ID match
        if low in self.by_id:
            return self.by_id[low]
        if low_nobase in self.by_id:
            return self.by_id[low_nobase]

        # 2. StartupWMClass match
        if low in self.by_wmclass:
            return self.by_wmclass[low]
        if low_nobase in self.by_wmclass:
            return self.by_wmclass[low_nobase]

        # 3. Localized Name match
        if low in self.by_name:
            return self.by_name[low]

        # 4. Fuzzy / substring match
        for k, app in self.by_id.items():
            if low_nobase == k or low_nobase in k or k in low_nobase:
                return app
        for k, app in self.by_name.items():
            if low_nobase in k:
                return app

        return None


class HyprlandState:
    """Manages active workspace and client tracking via Hyprland IPC."""
    @staticmethod
    def get_clients():
        try:
            out = subprocess.check_output(["hyprctl", "clients", "-j"], stderr=subprocess.DEVNULL)
            return json.loads(out)
        except Exception:
            return []

    @staticmethod
    def get_active_workspace():
        try:
            out = subprocess.check_output(["hyprctl", "activeworkspace", "-j"], stderr=subprocess.DEVNULL)
            return json.loads(out)
        except Exception:
            return {"id": 1, "windows": 0}

    @staticmethod
    def focus_window(address):
        subprocess.run(["hyprctl", "dispatch", "focuswindow", f"address:{address}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @staticmethod
    def close_window(address):
        subprocess.run(["hyprctl", "dispatch", "closewindow", f"address:{address}"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class CustomDock(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.app = app
        self.config = load_config()
        self.app_index = DesktopAppsIndex()

        self.mouse_over = False
        self.visible_margin = 10.0
        self.current_margin = 10.0
        self.target_margin = 10.0
        self.anim_id = None
        self.collapse_timer_id = None
        self.update_timer_id = None
        self.last_state_signature = None

        # Style provider
        self.css_provider = Gtk.CssProvider()
        self.load_styles()

        # Watch style.css and dock.json for dynamic live updates
        self.setup_file_monitors()

        # Layer Shell Setup
        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.BOTTOM, True)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.BOTTOM, int(self.visible_margin))
        Gtk4LayerShell.set_exclusive_zone(self, 0)
        Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.NONE)

        # Dock pill container — shrink-wrapped tightly to icons, zero inactive space
        self.dock_pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.dock_pill.add_css_class("dock-pill")
        self.dock_pill.set_halign(Gtk.Align.CENTER)
        self.dock_pill.set_valign(Gtk.Align.END)
        self.dock_pill.set_hexpand(False)
        self.dock_pill.set_vexpand(False)

        self.set_child(self.dock_pill)

        # Hover motion detection across the dock window
        motion_ctrl = Gtk.EventControllerMotion.new()
        motion_ctrl.connect("enter", self.on_mouse_enter)
        motion_ctrl.connect("leave", self.on_mouse_leave)
        self.add_controller(motion_ctrl)

        # Build initial items
        self.rebuild_dock()

        # Connect Hyprland Socket2 for real-time events
        self.setup_hyprland_socket()

        # Initial check for autohide
        GLib.timeout_add(200, self.check_autohide_state)

        # Periodic refresh (every 500ms) to ensure state stays in sync
        GLib.timeout_add(500, self.on_periodic_sync)

    def load_styles(self):
        if CSS_FILE.exists():
            try:
                self.css_provider.load_from_path(str(CSS_FILE))
            except Exception as e:
                print(f"[Dock] Error loading CSS: {e}")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def setup_file_monitors(self):
        try:
            cfg_file_obj = Gio.File.new_for_path(str(CONFIG_FILE))
            self.cfg_monitor = cfg_file_obj.monitor_file(Gio.FileMonitorFlags.NONE, None)
            self.cfg_monitor.connect("changed", self.on_config_file_changed)

            css_file_obj = Gio.File.new_for_path(str(CSS_FILE))
            self.css_monitor = css_file_obj.monitor_file(Gio.FileMonitorFlags.NONE, None)
            self.css_monitor.connect("changed", lambda *_: self.load_styles())
        except Exception as e:
            print(f"[Dock] File monitor error: {e}")

    def on_config_file_changed(self, monitor, file, other_file, event_type):
        if event_type in (Gio.FileMonitorEvent.CHANGES_DONE_HINT, Gio.FileMonitorEvent.CREATED):
            self.config = load_config()
            self.last_state_signature = None
            self.schedule_rebuild()

    def setup_hyprland_socket(self):
        sig = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
        xdg = os.environ.get("XDG_RUNTIME_DIR", "")
        sock_path = f"{xdg}/hypr/{sig}/.socket2.sock"

        if not os.path.exists(sock_path):
            return

        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(sock_path)
            self.sock.setblocking(False)

            channel = GLib.IOChannel.unix_new(self.sock.fileno())
            channel.add_watch(GLib.IO_IN | GLib.IO_HUP, self.on_socket_event)
        except Exception as e:
            print(f"[Dock] Socket2 connection error: {e}")

    def on_socket_event(self, source, condition):
        if condition & GLib.IO_HUP:
            return False
        try:
            data = self.sock.recv(4096).decode("utf-8", errors="ignore")
            for line in data.splitlines():
                if any(line.startswith(ev) for ev in ("openwindow", "closewindow", "workspace", "activewindow", "movewindow", "focusedmon")):
                    self.schedule_update()
        except Exception:
            pass
        return True

    def schedule_update(self):
        if self.update_timer_id is not None:
            return
        self.update_timer_id = GLib.timeout_add(50, self._do_update)

    def _do_update(self):
        self.update_timer_id = None
        self.rebuild_dock()
        self.check_autohide_state()
        return False

    def schedule_rebuild(self):
        GLib.idle_add(self.rebuild_dock)

    def on_periodic_sync(self):
        self.rebuild_dock()
        self.check_autohide_state()
        return True

    def animate_margin(self, target):
        self.target_margin = float(target)
        if self.anim_id is None:
            self.anim_id = GLib.timeout_add(16, self._step_anim)

    def _step_anim(self):
        diff = self.target_margin - self.current_margin
        if abs(diff) <= 1.5:
            self.current_margin = self.target_margin
            Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.BOTTOM, int(self.current_margin))
            self.anim_id = None
            return False
        # Smooth ease-out interpolation
        self.current_margin += diff * 0.35
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.BOTTOM, int(self.current_margin))
        return True

    def get_hidden_margin(self):
        h = self.get_height()
        if h < 40:
            h = 80
        # Leave 4px on screen at the bottom edge for mouse hover detection
        return -(h - 4)

    def check_autohide_state(self):
        if not self.config.get("autohide", True):
            self.animate_margin(self.visible_margin)
            return True

        # Count open windows on current active workspace
        clients = HyprlandState.get_clients()
        active_ws = HyprlandState.get_active_workspace()
        current_ws_id = active_ws.get("id", 1)
        ws_clients = [c for c in clients if c.get("workspace", {}).get("id") == current_ws_id and not c.get("hidden", False)]
        num_windows = len(ws_clients)

        if self.mouse_over:
            # Mouse hovering -> keep visible
            self.animate_margin(self.visible_margin)
        else:
            # No windows on current workspace -> stay visible
            if num_windows == 0:
                self.animate_margin(self.visible_margin)
            else:
                # Windows exist -> slide down to hidden margin
                self.animate_margin(self.get_hidden_margin())
        return True

    def on_mouse_enter(self, controller, x, y):
        self.mouse_over = True
        if self.collapse_timer_id:
            GLib.source_remove(self.collapse_timer_id)
            self.collapse_timer_id = None
        self.animate_margin(self.visible_margin)

    def on_mouse_leave(self, controller):
        self.mouse_over = False
        if not self.config.get("autohide", True):
            return

        if self.collapse_timer_id:
            GLib.source_remove(self.collapse_timer_id)

        # Debounce collapse by 280ms to prevent accidental flickers
        def delayed_collapse():
            self.collapse_timer_id = None
            if not self.mouse_over:
                self.check_autohide_state()
            return False

        self.collapse_timer_id = GLib.timeout_add(280, delayed_collapse)

    def get_app_icon_widget(self, app_info, fallback_name, icon_size=44):
        theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
        
        # 1. Try GIcon from DesktopAppInfo
        if app_info and app_info.get_icon():
            gicon = app_info.get_icon()
            img = Gtk.Image.new_from_gicon(gicon)
            img.set_pixel_size(icon_size)
            return img

        # 2. Try icon name resolution
        for candidate in [fallback_name, fallback_name.lower(), f"{fallback_name.lower()}-symbolic", "application-x-executable"]:
            if theme.has_icon(candidate):
                img = Gtk.Image.new_from_icon_name(candidate)
                img.set_pixel_size(icon_size)
                return img

        # 3. Generic fallback
        img = Gtk.Image.new_from_icon_name("application-x-executable")
        img.set_pixel_size(icon_size)
        return img

    def rebuild_dock(self):
        clients = HyprlandState.get_clients()
        active_ws = HyprlandState.get_active_workspace()
        active_client_addr = active_ws.get("lastwindow", "")

        # Group clients by app identifier
        client_map = {}
        for c in clients:
            cls = c.get("class", "")
            init_cls = c.get("initialClass", "")
            app = self.app_index.find(cls) or self.app_index.find(init_cls)
            key = app.get_id() if app else cls
            if key not in client_map:
                client_map[key] = []
            client_map[key].append(c)

        icon_size = self.config.get("icon_size", 44)
        pinned = self.config.get("pinned", [])

        # Signature to avoid re-rendering DOM if state hasn't changed
        current_sig = (
            tuple(pinned),
            tuple(sorted(client_map.keys())),
            tuple(sorted((k, len(v), any(c.get("address") == active_client_addr for c in v)) for k, v in client_map.items())),
            icon_size,
            self.config.get("show_launcher", True),
            self.config.get("show_running", True)
        )

        if current_sig == self.last_state_signature:
            return
        self.last_state_signature = current_sig

        # Clear existing children cleanly
        while child := self.dock_pill.get_first_child():
            self.dock_pill.remove(child)

        # Track which apps are displayed
        rendered_keys = set()

        # 1. Render Pinned Apps
        for item in pinned:
            app_info = self.app_index.find(item)
            key = app_info.get_id() if app_info else item
            rendered_keys.add(key)
            app_clients = client_map.get(key, [])

            btn = self.create_app_button(item, app_info, app_clients, active_client_addr, is_pinned=True, icon_size=icon_size)
            self.dock_pill.append(btn)

        # 2. Render Unpinned Running Apps (if show_running enabled)
        if self.config.get("show_running", True):
            unpinned_clients = [k for k in client_map.keys() if k not in rendered_keys]
            if unpinned_clients:
                sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
                sep.add_css_class("dock-sep")
                self.dock_pill.append(sep)

                for key in unpinned_clients:
                    app_clients = client_map[key]
                    app_info = self.app_index.find(key)
                    btn = self.create_app_button(key, app_info, app_clients, active_client_addr, is_pinned=False, icon_size=icon_size)
                    self.dock_pill.append(btn)

        # 3. 9-Dots Application Grid Launcher
        if self.config.get("show_launcher", True):
            launcher_btn = Gtk.Button()
            launcher_btn.add_css_class("launcher-btn")
            launcher_btn.set_tooltip_text("Applications")
            l_img = Gtk.Image.new_from_icon_name("view-app-grid-symbolic")
            l_img.set_pixel_size(int(icon_size * 0.72))
            launcher_btn.set_child(l_img)
            launcher_btn.connect("clicked", self.on_launcher_clicked)
            self.dock_pill.append(launcher_btn)

    def create_app_button(self, identifier, app_info, clients, active_addr, is_pinned, icon_size=44):
        btn = Gtk.Button()
        btn.add_css_class("app-btn")

        app_name = app_info.get_name() if app_info else identifier.capitalize()
        btn.set_tooltip_text(app_name)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        icon_widget = self.get_app_icon_widget(app_info, identifier, icon_size=icon_size)
        box.append(icon_widget)

        # Running indicator dot
        dot = Gtk.Box()
        has_focused = any(c.get("address") == active_addr for c in clients)
        if has_focused:
            dot.add_css_class("dot-focused")
        elif clients:
            dot.add_css_class("dot-indicator")
        else:
            dot.add_css_class("dot-empty")
        box.append(dot)

        btn.set_child(box)

        # Left click action
        btn.connect("clicked", lambda _, ai=app_info, cl=clients: self.on_app_clicked(ai, cl, identifier))

        # Right click context menu (on-demand popover)
        gesture = Gtk.GestureClick.new()
        gesture.set_button(3)
        gesture.connect("pressed", lambda g, np, x, y, b=btn, idn=identifier, ai=app_info, cl=clients, ip=is_pinned: self.show_context_menu(b, idn, ai, cl, ip))
        btn.add_controller(gesture)

        return btn

    def show_context_menu(self, btn, identifier, app_info, clients, is_pinned):
        popover = Gtk.Popover()
        popover.add_css_class("dock-menu")
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        # Pin / Unpin Action
        pin_btn = Gtk.Button()
        pin_btn.add_css_class("menu-btn")
        if is_pinned:
            pin_btn.set_label("🚫 Unpin from Dock")
            pin_btn.connect("clicked", lambda *_: (popover.popdown(), self.unpin_app(identifier)))
        else:
            pin_btn.set_label("📌 Pin to Dock")
            pin_btn.connect("clicked", lambda *_: (popover.popdown(), self.pin_app(identifier)))
        menu_box.append(pin_btn)

        # New Window
        new_win_btn = Gtk.Button(label="✨ New Window")
        new_win_btn.add_css_class("menu-btn")
        new_win_btn.connect("clicked", lambda *_: (popover.popdown(), self.launch_new_window(app_info, identifier)))
        menu_box.append(new_win_btn)

        # Close Windows (if running)
        if clients:
            close_btn = Gtk.Button(label="❌ Close")
            close_btn.add_css_class("menu-btn")
            close_btn.add_css_class("destructive")
            close_btn.connect("clicked", lambda *_: (popover.popdown(), self.close_app_windows(clients)))
            menu_box.append(close_btn)

        popover.set_child(menu_box)
        popover.set_parent(btn)
        popover.connect("closed", lambda p: p.unparent())
        popover.popup()

    def on_app_clicked(self, app_info, clients, fallback_id):
        if not clients:
            self.launch_new_window(app_info, fallback_id)
        elif len(clients) == 1:
            addr = clients[0].get("address")
            HyprlandState.focus_window(addr)
        else:
            # Multiple windows: cycle through
            active_ws = HyprlandState.get_active_workspace()
            current_focus = active_ws.get("lastwindow")
            addrs = [c.get("address") for c in clients]
            if current_focus in addrs:
                idx = (addrs.index(current_focus) + 1) % len(addrs)
                HyprlandState.focus_window(addrs[idx])
            else:
                HyprlandState.focus_window(addrs[0])

    def launch_new_window(self, app_info, identifier):
        if app_info:
            try:
                app_info.launch([], None)
                return
            except Exception:
                pass
        cmd = identifier.replace(".desktop", "")
        subprocess.Popen([cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def close_app_windows(self, clients):
        for c in clients:
            addr = c.get("address")
            if addr:
                HyprlandState.close_window(addr)

    def pin_app(self, identifier):
        pinned = self.config.get("pinned", [])
        clean_id = identifier.replace(".desktop", "")
        if clean_id not in pinned:
            pinned.append(clean_id)
            self.config["pinned"] = pinned
            save_config(self.config)
            self.last_state_signature = None
            self.rebuild_dock()

    def unpin_app(self, identifier):
        pinned = self.config.get("pinned", [])
        clean_id = identifier.replace(".desktop", "")
        if clean_id in pinned:
            pinned.remove(clean_id)
            self.config["pinned"] = pinned
            save_config(self.config)
            self.last_state_signature = None
            self.rebuild_dock()

    def on_launcher_clicked(self, btn):
        menu_cmd = "rofi -show drun -theme-str 'window { width: 500px; height: 600px; }'"
        subprocess.Popen(menu_cmd, shell=True)


class DockApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.hyprland.dashdock",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        self.win = CustomDock(self)
        self.win.present()


def main():
    ensure_single_instance()

    app = DockApplication()

    # Graceful shutdown signals
    def shutdown(*_):
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
        app.quit()

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, shutdown)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, shutdown)

    # SIGUSR2: reload styles immediately
    def on_sigusr2(sig, frame):
        if hasattr(app, "win"):
            GLib.idle_add(lambda: (app.win.load_styles(), app.win.schedule_rebuild()))

    signal.signal(signal.SIGUSR2, on_sigusr2)

    app.run(sys.argv)


if __name__ == "__main__":
    main()
