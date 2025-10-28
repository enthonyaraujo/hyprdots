#!/bin/bash

echo "Hyprdots..."

echo "Modificando pacote de linguagem..."

sudo mv pt_BR /usr/share/i18n/locales/pt_BR 
sudo locale-gen

echo "Instalando dependências via pacman..."

sudo pacman -S --noconfirm --needed obsidian firefox spotify-launcher discord xournalpp flatpak gnome-boxes gnome-software showtime papers gnome-text-editor network-manager-applet python-pip blueman wofi waybar hyprpaper hyprlock hypridle udiskie ttf-firacode-nerd nautilus btop kitty adw-gtk-theme polkit

mkdir aur
cd aur/
echo "Instalando dependências via aur..."

git clone https://aur.archlinux.org/networkmanager-dmenu-git.git
(
	cd networkmanager-dmenu-git
	makepkg -si --noconfirm
)
git clone https://aur.archlinux.org/visual-studio-code-bin.git
(
	cd visual-studio-code-bin
	makepkg -si --noconfirm
)
git clone https://aur.archlinux.org/logisim-evolution.git
(
	cd logisim-evolution 
	makepkg -si --noconfirm
)
cd ..

pip install nautilus-open-any-terminal --break-system-packages

echo "Copiando arquivos para .config..."

cp -r /$HOME/hyprdots/waybar/ /$HOME/hyprdots/wofi/ /$HOME/hyprdots/hypr/ /$HOME/hyprdots/kitty/ /$HOME/.config/

echo "Terminado!"
