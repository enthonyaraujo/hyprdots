#!/bin/bash

rsync -av dunst $HOME/.config/
rsync -av gtk-3.0 $HOME/.config/
rsync -av gtk-4.0 $HOME/.config/
rsync -av kitty $HOME/.config/
rsync -av rofi $HOME/.config/
rsync -av waybar $HOME/.config/
rsync -av .gtkrc-2.0 $HOME/

gsettings set org.gnome.desktop.interface gtk-theme 'catppuccin-latte-blue-standard+default'

gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Light'

echo '$wallpaper_hyprland = $HOME/.config/themes/light/Clearday.jpg' > $HOME/.config/hypr/wallpaper.conf

sed -i '2s/.*/   "workbench.colorTheme": "Catppuccin Latte",/' $HOME/.config/Code/User/settings.json

killall waybar && waybar -l trace
killall hyprpaper && hyprpaper &