Hyprland Configs :)

Dependencies:

```bash
sudo pacman -S network-manager-applet blueman waybar hyprpaper udiskie
```
Modificar **day** para maisculo em:

```bash
sudo nano /usr/share/i18n/locales/pt_BR 
```
```nano
day     "Domingo";/
        "Segunda";/
        "Terça";/
        "Quarta";/
        "Quinta";/
        "Sexta";/
        "Sábado"
``` 



Install:
```bash
git clone https://github.com/enthonyaraujo/hyprdots.git

```


```bash
cp -r hyprdots/* /$HOME/.config/ && rm -r hyprdots
```


<p align="center">
<img src="preview.png">
</p>

