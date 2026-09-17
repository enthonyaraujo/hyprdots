#!/usr/bin/env bash
set -euo pipefail

# Discover script directory and repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

AUR_LIST="aur.txt" 
AUR_DIR="$HOME/aur"
PACMAN_LIST="pacotes_hyprland.txt"
WM_NAME="hyprland"

echo "===== Starting Setup: $WM_NAME ====="
echo

echo "===== Enabling multilib in /etc/pacman.conf ====="
echo

sudo bash -c 'cat <<EOF >> /etc/pacman.conf

[multilib]
Include = /etc/pacman.d/mirrorlist
EOF'

echo "===== Checking package list... ====="
echo

if [[ ! -f "$PACMAN_LIST" ]]; then
    echo "Error: File $PACMAN_LIST not found."
    exit 1
fi

echo "===== Updating system ====="
sudo pacman -Syu --noconfirm

echo "===== Installing pacman packages ($WM_NAME) ====="
while read -r pacote; do
    [[ -z "$pacote" || "$pacote" =~ ^# ]] && continue
    sudo pacman -S --needed --noconfirm "$pacote"
done < "$PACMAN_LIST"

echo "===== Installing yay (AUR Helper) ====="
if ! command -v yay >/dev/null; then
    sudo pacman -S --needed --noconfirm base-devel git
    mkdir -p "$AUR_DIR"
    git clone https://aur.archlinux.org/yay.git "$AUR_DIR/yay"
    cd "$AUR_DIR/yay"
    makepkg -si --noconfirm
    cd "$HOME"
fi

echo "===== Installing AUR packages ====="
if [[ -f "$AUR_LIST" ]]; then
    while read -r pacote; do
        [[ -z "$pacote" || "$pacote" =~ ^# ]] && continue
        yay -S --needed --noconfirm "$pacote"
    done < "$AUR_LIST"
fi

echo "===== Installing nwg-dock (Dock) ====="
if ! command -v nwg-dock >/dev/null; then
    # Install Rust if not present
    if ! command -v cargo >/dev/null; then
        echo "Installing Rust toolchain..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source "$HOME/.cargo/env"
    fi
    # Install GTK4 layer-shell dev dependencies
    if command -v pacman >/dev/null; then
        sudo pacman -S --needed --noconfirm gtk4 gtk4-layer-shell
    elif command -v apt >/dev/null; then
        sudo apt install -y libgtk-4-dev libgtk4-layer-shell-dev
    fi
    echo "Building nwg-dock from source (this may take a few minutes)..."
    cargo install nwg-dock
    echo "nwg-dock installed successfully."
else
    echo "nwg-dock is already installed."
fi

echo "===== Do you want to install Nvidia drivers? ====="
echo "1) Yes"
echo "2) No"
read -rp "Choose an option (1 or 2) [Default: 1]: " NVIDIA
case "$NVIDIA" in
    2)
        echo " "
        ;;
    *)
        echo "Installing Nvidia drivers..."
        sudo pacman -S --needed --noconfirm linux-headers nvidia-open-dkms libva-nvidia-driver nvidia-settings nvidia-utils egl-wayland lib32-nvidia-utils
        ;;
esac

echo "===== Applying Local Dotfiles ====="
mkdir -p "$HOME/.config"

echo "Synchronizing .config folder..."
# Copy contents of repo's .config folder to ~/.config
rsync -av "$REPO_DIR/.config/" "$HOME/.config/"

# Copy .zshrc from repo root
if [[ -f "$REPO_DIR/.zshrc" ]]; then
    echo "Synchronizing .zshrc file..."
    cp "$REPO_DIR/.zshrc" "$HOME/.zshrc"
fi

echo "===== Configuring Shell ====="
echo "Which shell do you want to set as default?"
echo "1) ZSH"
echo "2) Fish"
read -rp "Choose an option (1 or 2) [Default: 1]: " SHELL_CHOICE

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
        echo "Changing default shell to $SHELL_NAME..."
        chsh -s "$CHOSEN_SHELL"
    else
        echo "Warning: Shell $SHELL_NAME ($CHOSEN_SHELL) was not found."
        echo "Make sure it was installed through your package list."
    fi
else
    echo "$SHELL_NAME is already your default shell."
fi

echo
echo "===== Setup completed ====="
echo "Environment: $WM_NAME"
echo "Configurations were applied successfully!"
echo "Log out or reboot to apply all changes."
