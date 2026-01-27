#!/bin/bash

rsync -av dunst $HOME/.config/
rsync -av gtk-3.0 $HOME/.config/
rsync -av gtk-4.0 $HOME/.config/
rsync -av kitty $HOME/.config/
rsync -av rofi $HOME/.config/
rsync -av waybar $HOME/.config/
rsync -av .gtkrc-2.0 $HOME/


gsettings set org.gnome.desktop.interface gtk-theme 'catppuccin-mocha-blue-standard+default'

gsettings set org.gnome.desktop.interface icon-theme 'Papirus-Dark'

echo '$wallpaper_hyprland = $HOME/.config/themes/dark/evening-sky.png' > $HOME/.config/hypr/wallpaper.conf

sed -i '2s/.*/   "workbench.colorTheme": "Catppuccin Mocha",/' $HOME/.config/Code/User/settings.json


killall hyprpaper && hyprpaper &

killall waybar && waybar -l trace
