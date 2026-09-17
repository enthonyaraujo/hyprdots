#!/usr/bin/env bash
set -euo pipefail

# Executa o seletor moderno nativo em Python 3 + GTK 3
exec python3 "$HOME/.config/bin/wallpaper-applet.py" "$@"