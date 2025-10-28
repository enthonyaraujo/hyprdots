#!/bin/bash

echo "Hyprdots..."

echo "Modificando pacote de linguagem..."

sudo mv pt_BR /usr/share/i18n/locales/pt_BR 
sudo locale-gen

echo "Verificando se o repositório multilib já está habilitado..."
if grep -q "^\[multilib\]" /etc/pacman.conf; then
    echo "O repositório multilib já está habilitado ✅"
    exit 0
fi

echo "Habilitando o repositório multilib..."
sudo sed -i '/#\[multilib\]/,/#Include = \/etc\/pacman.d\/mirrorlist/ s/^#//' /etc/pacman.conf

echo "Atualizando a base de pacotes..."
sudo pacman -Sy

echo "Instalando dependências via pacman..."

sudo pacman -S --noconfirm --needed linux-headers base-devel nvidia nvidia-utils nvidia-settings lib32-nvidia-utils steam fastfetch obsidian gcc cmake firefox spotify-launcher discord xournalpp flatpak gnome-boxes gnome-software showtime papers gnome-text-editor network-manager-applet python-pip blueman wofi waybar hyprpaper hyprlock hypridle udiskie ttf-firacode-nerd nautilus btop kitty adw-gtk-theme polkit

mkdir aur
cd aur/
echo "Instalando dependências via aur..."

git clone https://aur.archlinux.org/networkmanager-dmenu-git.git
(
	cd networkmanager-dmenu-git/
	makepkg -si --noconfirm
)
git clone https://aur.archlinux.org/visual-studio-code-bin.git
(
	cd visual-studio-code-bin/
	makepkg -si --noconfirm
)
git clone https://aur.archlinux.org/logisim-evolution.git
(
	cd logisim-evolution/
	makepkg -si --noconfirm
)
git clone https://aur.archlinux.org/zapzap.git
(
	cd zapzap/
	makepkg -si --noconfirm
)
cd ..

pip install nautilus-open-any-terminal --break-system-packages

echo "Copiando arquivos para .config..."

cp -r /$HOME/hyprdots/waybar/ /$HOME/hyprdots/wofi/ /$HOME/hyprdots/hypr/ /$HOME/hyprdots/kitty/ /$HOME/.config/

echo "Terminado!"

sudo reboot
