#!/usr/bin/env bash
# Screenshot script for Hyprland (Wayland)
# Supports region selection, fullscreen, and interactive edit mode

DIR="$HOME/Pictures/Screenshots"
mkdir -p "$DIR"
FILE="$DIR/Screenshot_$(date +%Y-%m-%d_%H-%M-%S).png"

mode="${1:-area}"

# Verify required utilities are installed
if ! command -v grim &>/dev/null || ! command -v slurp &>/dev/null || ! command -v wl-copy &>/dev/null; then
    notify-send -u critical -a "Screenshot" "Missing Tools" "Please install: sudo apt install grim slurp wl-clipboard swappy"
    exit 1
fi

case "$mode" in
    area|region)
        # Select region with mouse, save and copy to clipboard
        geom=$(slurp)
        if [ -n "$geom" ]; then
            grim -g "$geom" "$FILE"
            wl-copy --type image/png < "$FILE"
            notify-send -a "Screenshot" -i "$FILE" "Screenshot saved and copied!" "File: $(basename "$FILE")"
        fi
        ;;
    edit|swappy)
        # Select region and open Swappy for annotations/editing
        geom=$(slurp)
        if [ -n "$geom" ]; then
            if command -v swappy &>/dev/null; then
                grim -g "$geom" - | swappy -f -
            else
                grim -g "$geom" "$FILE"
                wl-copy --type image/png < "$FILE"
                notify-send -a "Screenshot" -i "$FILE" "Screenshot saved and copied!" "File: $(basename "$FILE")\n(Install swappy for graphic editor)"
            fi
        fi
        ;;
    full|screen)
        # Capture full screen
        grim "$FILE"
        wl-copy --type image/png < "$FILE"
        notify-send -a "Screenshot" -i "$FILE" "Full screen captured!" "File: $(basename "$FILE")"
        ;;
    *)
        echo "Usage: $0 {area|edit|full}"
        exit 1
        ;;
esac
