#!/bin/bash

echo "Iniciando desinstalação..."

read -p "Deseja continuar com a desinstalação? (s/N) " confirm
if [[ "$confirm" != "s" && "$confirm" != "S" ]]; then
    echo "Desinstalação cancelada."
    exit 0
fi

# Remover os pacotes 
echo
echo "O script de instalação instalou os seguintes pacotes:"
echo "obsidian firefox spotify-launcher discord xournalpp flatpak gnome-boxes gnome-software showtime papers gnome-text-editor network-manager-applet python-pip blueman wofi waybar hyprpaper hyprlock hypridle udiskie ttf-firacode-nerd nautilus btop kitty adw-gtk-theme polkit networkmanager-dmenu-git visual-studio-code-bin logisim-evolution"
echo
echo "Muitos deles (como firefox, nautilus, polkit) podem ser usados por outros ambientes."

read -p "Deseja remover TODOS os pacotes listados acima? (s/N) " remove_all_pkgs

if [[ "$remove_all_pkgs" == "s" || "$remove_all_pkgs" == "S" ]]; then
    echo "Removendo todos os pacotes do pacman e AUR..."
    sudo pacman -Rns --noconfirm obsidian firefox spotify-launcher discord xournalpp flatpak gnome-boxes gnome-software showtime papers gnome-text-editor network-manager-applet python-pip blueman wofi waybar hyprpaper hyprlock hypridle udiskie ttf-firacode-nerd nautilus btop kitty adw-gtk-theme polkit networkmanager-dmenu-git 
    flatpak uninstall flathub com.github.reds.LogisimEvolution 
    flatpak uninstall flathub com.rtosta.zapzap
    flatpak uninstall flathub org.gnome.Snapshot
    flatpak uninstall flathub com.visualstudio.code
    flatpak uninstall flathub org.libreoffice.LibreOffice
else
    echo "Pulando remoção de pacotes."
    echo "Se desejar, você pode remover manualmente apenas os pacotes específicos do Hyprdots:"
    echo "sudo pacman -Rns wofi waybar hyprpaper hyprlock hypridle networkmanager-dmenu-git"
fi

# Remover pacote pip
echo
read -p "Deseja remover o pacote pip 'nautilus-open-any-terminal'? (s/N) " remove_pip
if [[ "$remove_pip" == "s" || "$remove_pip" == "S" ]]; then
    echo "Removendo pacote pip..."
    sudo pip uninstall -y nautilus-open-any-terminal
else
    echo "Pulando remoção de pacote pip."
fi

# Remover arquivos de configuração 
echo
echo "O script de instalação copiou arquivos para:"
echo "$HOME/.config/waybar"
echo "$HOME/.config/wofi"
echo "$HOME/.config/hypr"
echo "$HOME/.config/kitty"
echo
read -p "Deseja remover esses diretórios de configuração (isso removerá quaisquer customizações que você fez)? (s/N) " remove_configs
if [[ "$remove_configs" == "s" || "$remove_configs" == "S" ]]; then
    echo "Removendo arquivos de configuração..."
    rm -rfv "$HOME/.config/waybar"
    rm -rfv "$HOME/.config/wofi"
    rm -rfv "$HOME/.config/hypr"
    rm -rfv "$HOME/.config/kitty"
else
    echo "Pulando remoção de arquivos de configuração."
fi

# Remover diretório aur
echo
if [ -d "aur" ]; then
    read -p "Deseja remover o diretório 'aur' (usado para compilar pacotes)? (s/N) " remove_aur_dir
    if [[ "$remove_aur_dir" == "s" || "$remove_aur_dir" == "S" ]]; then
        echo "Removendo diretório 'aur'..."
        rm -rfv aur
    else
        echo "Pulando remoção do diretório 'aur'."
    fi
fi

# Reverter Locale 
echo
echo "O script de instalação moveu um arquivo para '/usr/share/i18n/locales/pt_BR'."
read -p "Deseja remover este arquivo de locale (pode afetar o suporte a pt_BR)? (s/N) " remove_locale
if [[ "$remove_locale" == "s" || "$remove_locale" == "S" ]]; then
    if [ -f "/usr/share/i18n/locales/pt_BR" ]; then
        echo "Removendo /usr/share/i18n/locales/pt_BR..."
        sudo rm /usr/share/i18n/locales/pt_BR
        echo "Regenerando locales..."
        sudo locale-gen
    else
        echo "Arquivo de locale /usr/share/i18n/locales/pt_BR não encontrado."
    fi
else
    echo "Pulando remoção de locale."
fi

echo
echo "Desinstalação terminada!"
read -p "É recomendado reiniciar. Deseja reiniciar agora? (s/N) " reboot_now
if [[ "$reboot_now" == "s" || "$reboot_now" == "S" ]]; then
    echo "Reiniciando..."
    sudo reboot
fi