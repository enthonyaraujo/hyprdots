-- ██▄  ▄██ ██  ██   █████▄ █████▄  ▄████▄  ▄████  █████▄  ▄████▄ ██▄  ▄██ ▄█████ 
-- ██ ▀▀ ██  ▀██▀    ██▄▄█▀ ██▄▄██▄ ██  ██ ██  ▄▄▄ ██▄▄██▄ ██▄▄██ ██ ▀▀ ██ ▀▀▀▄▄▄ 
-- ██    ██   ██     ██     ██   ██ ▀████▀  ▀███▀  ██   ██ ██  ██ ██    ██ █████▀ 

hl.config({
    xwayland = {
        enabled = true,
        force_zero_scaling = true,
    },
})
-- Default applications
terminal = "kitty"
fileManager = "nautilus"
menu = "rofi -show drun -theme-str 'window { width: 500px; height: 600px; }'"
editor = "nano"
-- Autostart programs on hyprland.start event
hl.on("hyprland.start", function()
    -- Sync environment with systemd and D-Bus (required for portals & screen sharing)
    hl.exec_cmd("dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")
    hl.exec_cmd("systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP")

    -- Core daemons and bars
    hl.exec_cmd("waybar")
    hl.exec_cmd("hyprpaper")
    hl.exec_cmd("hypridle")
    hl.exec_cmd("dunst")

    -- Polkit agent and automount (if available)
    hl.exec_cmd("command -v hyprpolkitagent >/dev/null 2>&1 && hyprpolkitagent")
    hl.exec_cmd("command -v udiskie >/dev/null 2>&1 && udiskie -A")
end)

return {
    terminal = terminal,
    fileManager = fileManager,
    menu = menu,
    editor = editor,
}
