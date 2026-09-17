#!/usr/bin/env bash
set -euo pipefail

# Launch modern native wallpaper chooser in Python 3 + GTK 3
exec python3 "$HOME/.config/bin/wallpaper-applet.py" "$@"