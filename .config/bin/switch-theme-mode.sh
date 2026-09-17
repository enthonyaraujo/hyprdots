#!/usr/bin/env bash
# ==============================================================================
# switch-theme-mode.sh
# Unified theme switcher between White (Light) and Dark modes.
# Synchronously updates:
# - Waybar (top panel)
# - All GTK 3 applets (Calendar, Wifi, Bluetooth, Volume, Wallpaper, etc.)
# - GTK 3 / GTK 4 settings (settings.ini and gsettings)
# - Rofi (all menus and dialogs)
# - Kitty Terminal
# - Dunst Notifications
# - Hyprland Window Borders
# - Btop System Monitor
# ==============================================================================
set -euo pipefail

THEME_MODE_FILE="$HOME/.config/theme.mode"
CURRENT_MODE="dark"
if [[ -f "$THEME_MODE_FILE" ]]; then
    CURRENT_MODE="$(cat "$THEME_MODE_FILE" | tr -d '[:space:]')"
fi

TARGET="${1:-toggle}"

case "$TARGET" in
    toggle)
        if [[ "$CURRENT_MODE" == "white" || "$CURRENT_MODE" == "light" ]]; then
            NEW_MODE="dark"
        else
            NEW_MODE="white"
        fi
        ;;
    white|light)
        NEW_MODE="white"
        ;;
    dark)
        NEW_MODE="dark"
        ;;
    *)
        echo "Usage: $0 [white|dark|toggle]"
        exit 1
        ;;
esac

echo "$NEW_MODE" > "$THEME_MODE_FILE"

if [[ "$NEW_MODE" == "white" ]]; then
    # --------------------------------------------------------------------------
    # 1. WAYBAR & APPLETS GTK 3
    # --------------------------------------------------------------------------
    ln -sf light.css "$HOME/.config/waybar/current-theme.css"
    killall -SIGUSR2 waybar 2>/dev/null || true

    # --------------------------------------------------------------------------
    # 2. ROFI
    # --------------------------------------------------------------------------
    ln -sf theme-light.rasi "$HOME/.config/rofi/themes/theme.rasi"

    # --------------------------------------------------------------------------
    # 3. KITTY TERMINAL
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/kitty/themes/light.conf" ]]; then
        cp "$HOME/.config/kitty/themes/light.conf" "$HOME/.config/kitty/current-theme.conf"
        killall -SIGUSR1 kitty 2>/dev/null || true
    fi

    # --------------------------------------------------------------------------
    # 4. DUNST NOTIFICATIONS
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/dunst/themes/dunstrc.light" ]]; then
        cp "$HOME/.config/dunst/themes/dunstrc.light" "$HOME/.config/dunst/dunstrc"
        dunstctl reload 2>/dev/null || true
    fi

    # --------------------------------------------------------------------------
    # 5. GTK 3 & GTK 4 SETTINGS
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/gtk-3.0/settings.ini" ]]; then
        sed -i 's/^gtk-theme-name=.*/gtk-theme-name=adw-gtk3/' "$HOME/.config/gtk-3.0/settings.ini"
        sed -i 's/^gtk-icon-theme-name=.*/gtk-icon-theme-name=kora/' "$HOME/.config/gtk-3.0/settings.ini"
        sed -i 's/^gtk-application-prefer-dark-theme=.*/gtk-application-prefer-dark-theme=0/' "$HOME/.config/gtk-3.0/settings.ini"
    fi

    if [[ -f "$HOME/.config/gtk-4.0/settings.ini" ]]; then
        sed -i 's/^gtk-theme-name=.*/gtk-theme-name=adw-gtk3/' "$HOME/.config/gtk-4.0/settings.ini"
        sed -i 's/^gtk-icon-theme-name=.*/gtk-icon-theme-name=kora/' "$HOME/.config/gtk-4.0/settings.ini"
        sed -i 's/^gtk-application-prefer-dark-theme=.*/gtk-application-prefer-dark-theme=0/' "$HOME/.config/gtk-4.0/settings.ini"
    fi

    gsettings set org.gnome.desktop.interface color-scheme 'prefer-light' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme 'adw-gtk3' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface icon-theme 'kora' 2>/dev/null || true

    # --------------------------------------------------------------------------
    # 6. HYPRLAND BORDERS
    # --------------------------------------------------------------------------
    cat <<'EOF' > "$HOME/.config/hypr/.theme-colors.conf.tmp"
$col_active_border = rgba(0284c7ee) rgba(3daee9ee) 45deg
$col_inactive_border = rgba(c4c8cbcc)
EOF
    mv -f "$HOME/.config/hypr/.theme-colors.conf.tmp" "$HOME/.config/hypr/theme-colors.conf"
    hyprctl keyword general:col.inactive_border "rgba(c4c8cbcc)" 2>/dev/null || true
    hyprctl keyword general:col.active_border "rgba(0284c7ee) rgba(3daee9ee) 45deg" 2>/dev/null || true

    # --------------------------------------------------------------------------
    # 7. BTOP SYSTEM MONITOR
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/btop/btop.conf" ]]; then
        sed -i 's/^color_theme = .*/color_theme = "whiteout"/' "$HOME/.config/btop/btop.conf"
    fi

    # --------------------------------------------------------------------------
    # 8. DASH TO DOCK
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/dock/style-light.css" ]]; then
        cp "$HOME/.config/dock/style-light.css" "$HOME/.config/dock/style.css"
        if [[ -f /tmp/hypr_dock.pid ]]; then
            kill -SIGUSR2 "$(cat /tmp/hypr_dock.pid)" 2>/dev/null || true
        fi
    fi

    notify-send -a "Theme Switcher" -i "weather-clear" "White Theme Activated" "The system has been configured to light mode." 2>/dev/null || true

else
    # --------------------------------------------------------------------------
    # 1. WAYBAR & APPLETS GTK 3
    # --------------------------------------------------------------------------
    ln -sf dark.css "$HOME/.config/waybar/current-theme.css"
    killall -SIGUSR2 waybar 2>/dev/null || true

    # --------------------------------------------------------------------------
    # 2. ROFI
    # --------------------------------------------------------------------------
    ln -sf theme-dark.rasi "$HOME/.config/rofi/themes/theme.rasi"

    # --------------------------------------------------------------------------
    # 3. KITTY TERMINAL
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/kitty/themes/dark.conf" ]]; then
        cp "$HOME/.config/kitty/themes/dark.conf" "$HOME/.config/kitty/current-theme.conf"
        killall -SIGUSR1 kitty 2>/dev/null || true
    fi

    # --------------------------------------------------------------------------
    # 4. DUNST NOTIFICATIONS
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/dunst/themes/dunstrc.dark" ]]; then
        cp "$HOME/.config/dunst/themes/dunstrc.dark" "$HOME/.config/dunst/dunstrc"
        dunstctl reload 2>/dev/null || true
    fi

    # --------------------------------------------------------------------------
    # 5. GTK 3 & GTK 4 SETTINGS
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/gtk-3.0/settings.ini" ]]; then
        sed -i 's/^gtk-theme-name=.*/gtk-theme-name=adw-gtk3-dark/' "$HOME/.config/gtk-3.0/settings.ini"
        sed -i 's/^gtk-icon-theme-name=.*/gtk-icon-theme-name=kora/' "$HOME/.config/gtk-3.0/settings.ini"
        sed -i 's/^gtk-application-prefer-dark-theme=.*/gtk-application-prefer-dark-theme=1/' "$HOME/.config/gtk-3.0/settings.ini"
    fi

    if [[ -f "$HOME/.config/gtk-4.0/settings.ini" ]]; then
        sed -i 's/^gtk-theme-name=.*/gtk-theme-name=adw-gtk3-dark/' "$HOME/.config/gtk-4.0/settings.ini"
        sed -i 's/^gtk-icon-theme-name=.*/gtk-icon-theme-name=kora/' "$HOME/.config/gtk-4.0/settings.ini"
        sed -i 's/^gtk-application-prefer-dark-theme=.*/gtk-application-prefer-dark-theme=1/' "$HOME/.config/gtk-4.0/settings.ini"
    fi

    gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface gtk-theme 'adw-gtk3-dark' 2>/dev/null || true
    gsettings set org.gnome.desktop.interface icon-theme 'kora' 2>/dev/null || true

    # --------------------------------------------------------------------------
    # 6. HYPRLAND BORDERS
    # --------------------------------------------------------------------------
    cat <<'EOF' > "$HOME/.config/hypr/.theme-colors.conf.tmp"
$col_active_border = rgba(3daee9ee) rgba(1d99f3ee) 45deg
$col_inactive_border = rgba(31363bcc)
EOF
    mv -f "$HOME/.config/hypr/.theme-colors.conf.tmp" "$HOME/.config/hypr/theme-colors.conf"
    hyprctl keyword general:col.inactive_border "rgba(31363bcc)" 2>/dev/null || true
    hyprctl keyword general:col.active_border "rgba(3daee9ee) rgba(1d99f3ee) 45deg" 2>/dev/null || true

    # --------------------------------------------------------------------------
    # 7. BTOP SYSTEM MONITOR
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/btop/btop.conf" ]]; then
        sed -i 's/^color_theme = .*/color_theme = "Default"/' "$HOME/.config/btop/btop.conf"
    fi

    # --------------------------------------------------------------------------
    # 8. DASH TO DOCK
    # --------------------------------------------------------------------------
    if [[ -f "$HOME/.config/dock/style-dark.css" ]]; then
        cp "$HOME/.config/dock/style-dark.css" "$HOME/.config/dock/style.css"
        if [[ -f /tmp/hypr_dock.pid ]]; then
            kill -SIGUSR2 "$(cat /tmp/hypr_dock.pid)" 2>/dev/null || true
        fi
    fi

    notify-send -a "Theme Switcher" -i "weather-clear-night" "Dark Theme Activated" "The system has been configured to dark mode." 2>/dev/null || true

fi

exit 0
