#!/usr/bin/env bash
set -euo pipefail

AUR_LIST="aur.txt"
AUR_DIR="$HOME/aur"
PACMAN_LIST="pacotes_hyprland.txt"
WM_NAME="hyprland"

echo "===== Iniciando Setup: $WM_NAME ====="
echo

if [[ ! -f "$PACMAN_LIST" ]]; then
    echo "Erro: Arquivo $PACMAN_LIST não encontrado."
    exit 1
fi

echo "===== Atualizando sistema ====="
sudo pacman -Syu --noconfirm

echo "===== Instalando pacotes do pacman ($WM_NAME) ====="
while read -r pacote; do
    [[ -z "$pacote" || "$pacote" =~ ^# ]] && continue
    sudo pacman -S --needed --noconfirm "$pacote"
done < "$PACMAN_LIST"

echo "===== Instalando yay (AUR Helper) ====="
if ! command -v yay >/dev/null; then
    sudo pacman -S --needed --noconfirm base-devel git
    mkdir -p "$AUR_DIR"
    git clone https://aur.archlinux.org/yay.git "$AUR_DIR/yay"
    cd "$AUR_DIR/yay"
    makepkg -si --noconfirm
    cd "$HOME"
fi

echo "===== Instalando pacotes AUR ====="
if [[ -f "$AUR_LIST" ]]; then
    while read -r pacote; do
        [[ -z "$pacote" || "$pacote" =~ ^# ]] && continue
        yay -S --needed --noconfirm "$pacote"
    done < "$AUR_LIST"
fi

echo "===== Clonando e Aplicando Dotfiles ====="
read -rp "Git/GitHub está configurado com chave SSH? [Y/n]: " RESPOSTA

case "${RESPOSTA,,}" in
    y|"")
        echo "Clonando via SSH..."
        git clone git@github.com:enthonyaraujo/dotfiles.git "$HOME/dotfiles_temp"
        ;;
    *)
        echo "Clonando via HTTPS..."
        git clone https://github.com/enthonyaraujo/dotfiles.git "$HOME/dotfiles_temp"
        ;;
esac

mkdir -p "$HOME/.config"

echo "Aplicando arquivos em $HOME/.config..."
rsync -av "$HOME/dotfiles_temp/.config/" "$HOME/.config/"

rm -rf "$HOME/dotfiles_temp"

echo "===== Configurando Shell ====="
echo "Qual shell você deseja definir como padrão?"
echo "1) ZSH"
echo "2) Fish"
read -rp "Escolha uma opção (1 ou 2) [Padrão: 1]: " SHELL_CHOICE

case "$SHELL_CHOICE" in
    2)
        CHOSEN_SHELL="/usr/bin/fish"
        SHELL_NAME="Fish"
        ;;
    *)
        CHOSEN_SHELL="/usr/bin/zsh"
        SHELL_NAME="ZSH"
        ;;
esac

if [[ "$SHELL" != "$CHOSEN_SHELL" ]]; then
    if command -v "$CHOSEN_SHELL" >/dev/null; then
        echo "Mudando shell padrão para $SHELL_NAME..."
        chsh -s "$CHOSEN_SHELL"
    else
        echo "Aviso: O shell $SHELL_NAME ($CHOSEN_SHELL) não foi encontrado."
        echo "Certifique-se de que ele foi instalado através da sua lista de pacotes."
    fi
else
    echo "O $SHELL_NAME já é o seu shell padrão."
fi

echo
echo "===== Setup finalizado ====="
echo "Ambiente: $WM_NAME"
echo "As configurações foram aplicadas corretamente!"
echo "Faça logout ou reinicie para efetivar as mudanças."
