#!/usr/bin/env bash
set -euo pipefail

AUR_LIST="aur.txt"
AUR_DIR="$HOME/aur"
PACMAN_LIST="pacotes_hyprland.txt"
WM_NAME="hyprland"

echo "===== Iniciando Setup: $WM_NAME ====="
echo

# Verificação de arquivos de lista
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

# Clona o repositório em uma pasta temporária
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

# Garante que a pasta ~/.config existe no seu sistema
mkdir -p "$HOME/.config"

# Copia o conteúdo da pasta .config do repositório para a sua ~/.config
echo "Aplicando arquivos em $HOME/.config..."
rsync -av "$HOME/dotfiles_temp/.config/" "$HOME/.config/"

# Remove a pasta temporária após a cópia
rm -rf "$HOME/dotfiles_temp"

echo "===== Configurando Shell ====="
if [[ "$SHELL" != "/usr/bin/zsh" ]]; then
    echo "Mudando shell padrão para ZSH..."
    chsh -s /usr/bin/zsh
fi

echo
echo "===== Setup finalizado ====="
echo "Ambiente: $WM_NAME"
echo "As configurações foram aplicadas corretamente!"
echo "Faça logout ou reinicie para efetivar as mudanças."
