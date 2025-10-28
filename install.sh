#!/bin/bash

echo "Hyprdots..."

echo "Modificando pacote de linguagem..."

sudo mv pt_BR /usr/share/i18n/locales/pt_BR 
sudo locale-gen

echo "Instalando dependências via pacman..."

sudo pacman -S --noconfirm --needed network-manager-applet blueman wofi waybar hyprpaper hyprlock hypridle udiskie ttf-fira-code nautilus btop kitty adw-gtk-theme polkit

mkdir aur
cd aur/
echo "Instalando dependências via aur..."

git clone https://aur.archlinux.org/networkmanager-dmenu-git.git
(
	cd networkmanager-dmenu-git
	makepkg -si --noconfirm
)

git clone https://aur.archlinux.org/nautilus-open-any-terminal.git
(
	cd nautilus-open-any-terminal
	makepkg -si --noconfirm
)

echo "Copiando arquivos para .config..."

cp -r waybar/ wofi/ hypr/ kitty/ /$HOME/.config/

echo "Terminado!"
