#!/usr/bin/env bash
set -euo pipefail

# 1. Defina as pastas e arquivos
WALLPAPER_DIR="$HOME/.config/wallpapers"
CONFIG_FILE="$HOME/.config/hypr/wallpaper.conf"

# 2. Lista as imagens e usa a própria imagem como ícone
choice=$(find "$WALLPAPER_DIR" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" \) | sort | while read -r img; do
  name=$(basename "$img")
  echo -en "$name\x00icon\x1f$img\n"
done | rofi \
  -dmenu \
  -show-icons \
  -theme ~/.config/bin/theme-picker.rasi \
  -theme-str '
    window { 
        width: 80%; 
    }
    listview {
        columns: 4;
        lines: 1;
        fixed-height: true;
        dynamic: true;
        scrollbar: false;
        spacing: 25px;
        padding: 20px;
    }
    element {
        orientation: vertical;
        padding: 15px;
    }
    element-icon {
        size: 180px;
    }
    element-text {
        horizontal-align: 0.5;
    }
  ' \
  -p "Wallpaper")

[[ -z "$choice" ]] && exit 0

SELECTED_WALLPAPER="$WALLPAPER_DIR/$choice"

# 3. Salva a escolha no arquivo de configuração do Hyprland
sed -i "s|^\(\$wallpaper_hyprland = \).*|\1$SELECTED_WALLPAPER|" "$CONFIG_FILE"

# 4. Força o encerramento do hyprpaper e inicia novamente
killall hyprpaper || true  # "|| true" evita que o script quebre se o hyprpaper já estiver fechado
sleep 0.5                  # Tempo para o sistema limpar o processo
hyprpaper > /dev/null 2>&1 & # Inicia o hyprpaper em segundo plano de forma silenciosa