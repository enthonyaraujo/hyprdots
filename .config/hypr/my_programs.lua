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
fileManager = "dolphin"
menu = "rofi -show drun -theme-str 'window { width: 500px; height: 600px; }'"
editor = "nano"

-- Autostart programs on hyprland.start event
hl.on("hyprland.start", function()
    hl.exec("udiskie -A")
    hl.exec("/usr/lib/xdg-desktop-portal-hyprland")
    hl.exec("/usr/lib/xdg-desktop-portal-gtk")
    hl.exec("/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &")
    hl.exec("hyprpaper & waybar")
    hl.exec("hypridle & dunst")
end)

return {
    terminal = terminal,
    fileManager = fileManager,
    menu = menu,
    editor = editor,
}
