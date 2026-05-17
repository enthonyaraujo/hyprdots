#!/usr/bin/env bash
set -euo pipefail

# Descobre o diretório do script e a raiz do repositório
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

AUR_LIST="aur.txt" # Certifique-se de que esses arquivos estão no mesmo diretório em que o script é executado
AUR_DIR="$HOME/aur"
PACMAN_LIST="pacotes_hyprland.txt"
WM_NAME="hyprland"

echo "===== Iniciando Setup: $WM_NAME ====="
echo

echo "===== Ativando multilib em /etc/pacman.conf ====="
echo

sudo bash -c 'cat <<EOF >> /etc/pacman.conf

[multilib]
Include = /etc/pacman.d/mirrorlist
EOF'

echo "===== Verificando lista de pacotes... ====="
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

echo "===== Deseja instalar os drivers da Nvidia? ====="
echo "1) Sim"
echo "2) Não"
read -rp "Escolha uma opção (1 ou 2) [Padrão: 1]: " NVIDIA
case "$NVIDIA" in
    2)
        echo " "
        ;;
    *)
        echo "Instalando drivers Nvidia..."
        sudo pacman -S --needed --noconfirm linux-headers nvidia-open-dkms libva-nvidia-driver nvidia-settings nvidia-utils egl-wayland lib32-nvidia-utils
        ;;
esac

echo "===== Aplicando Dotfiles Locais ====="
mkdir -p "$HOME/.config"

echo "Sincronizando a pasta .config..."
# Copia o conteúdo da pasta .config do repositório para ~/.config
rsync -av "$REPO_DIR/.config/" "$HOME/.config/"

# Copia o .zshrc que está na raiz do repositório (conforme a imagem)
if [[ -f "$REPO_DIR/.zshrc" ]]; then
    echo "Sincronizando o arquivo .zshrc..."
    cp "$REPO_DIR/.zshrc" "$HOME/.zshrc"
fi

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



