Hyprland Configs :)

Instalar apenas as configurações do **waybar**, **wofi** e **hyprland**:
```bash
sudo mv pt_BR /usr/share/i18n/locales/pt_BR 
sudo locale-gen
sudo pacman -S --noconfirm --needed network-manager-applet blueman wofi waybar hyprpaper hyprlock hypridle udiskie ttf-firacode-nerd nautilus btop adw-gtk-theme polkit
cp -r /$HOME/hyprdots/waybar/ /$HOME/hyprdots/wofi/ /$HOME/hyprdots/hypr/ /$HOME/hyprdots/kitty/ /$HOME/.config/
```

Instalar SETUP Completo:
```bash
git clone https://github.com/enthonyaraujo/hyprdots.git
./install.sh

```
<p align="center">
<img src="preview.png">
</p>

