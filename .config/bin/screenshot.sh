#!/usr/bin/env bash
# Script de captura de tela para Hyprland (Wayland)
# Suporta captura de área, tela cheia e modo interativo com anotações

DIR="$HOME/Pictures/Screenshots"
mkdir -p "$DIR"
FILE="$DIR/Screenshot_$(date +%Y-%m-%d_%H-%M-%S).png"

mode="${1:-area}"

# Verifica se os utilitários essenciais estão instalados
if ! command -v grim &>/dev/null || ! command -v slurp &>/dev/null || ! command -v wl-copy &>/dev/null; then
    notify-send -u critical -a "Captura de Tela" "Ferramentas ausentes" "Por favor, instale: sudo apt install grim slurp wl-clipboard swappy"
    exit 1
fi

case "$mode" in
    area|region)
        # Seleciona uma área com o mouse, salva e copia para a área de transferência
        geom=$(slurp)
        if [ -n "$geom" ]; then
            grim -g "$geom" "$FILE"
            wl-copy --type image/png < "$FILE"
            notify-send -a "Captura de Tela" -i "$FILE" "Captura salva e copiada!" "Arquivo: $(basename "$FILE")"
        fi
        ;;
    edit|swappy)
        # Seleciona uma área e abre o Swappy para anotações/edição (estilo GNOME/Flameshot)
        geom=$(slurp)
        if [ -n "$geom" ]; then
            if command -v swappy &>/dev/null; then
                grim -g "$geom" - | swappy -f -
            else
                grim -g "$geom" "$FILE"
                wl-copy --type image/png < "$FILE"
                notify-send -a "Captura de Tela" -i "$FILE" "Captura salva e copiada!" "Arquivo: $(basename "$FILE")\n(Instale swappy para editor gráfico)"
            fi
        fi
        ;;
    full|screen)
        # Captura tela inteira
        grim "$FILE"
        wl-copy --type image/png < "$FILE"
        notify-send -a "Captura de Tela" -i "$FILE" "Tela cheia capturada!" "Arquivo: $(basename "$FILE")"
        ;;
    *)
        echo "Uso: $0 {area|edit|full}"
        exit 1
        ;;
esac
