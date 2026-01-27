#!/usr/bin/env bash
set -euo pipefail

THEMES="$HOME/.config/themes"

choice=$(find "$THEMES" -maxdepth 1 -mindepth 1 -type d | sort | while read -r dir; do
  name=$(basename "$dir")
  icon="$dir/preview.png"
  echo -e "$name\x00icon\x1f$icon"
done | rofi \
  -dmenu \
  -show-icons \
  -theme ~/.config/bin/theme-picker.rasi \
  -p "Temas")

[[ -z "$choice" ]] && exit 0

INSTALL_SCRIPT="$THEMES/$choice/install.sh"

if [[ -f "$INSTALL_SCRIPT" ]]; then

    cd "$THEMES/$choice"
    
    # Executa o script
    bash "install.sh"
    
    notify-send "Tema Aplicado" "O tema $choice foi instalado com sucesso!"
else
    notify-send "Erro" "Script de instalação não encontrado em: $INSTALL_SCRIPT"
fi