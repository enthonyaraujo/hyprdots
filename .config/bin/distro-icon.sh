#!/bin/sh
# Identify Linux distribution and return the corresponding Nerd Font icon for Waybar

if [ -f /etc/os-release ]; then
    . /etc/os-release
fi

distro_id="${ID:-linux}"

case "$distro_id" in
    ubuntu)           icon="󰕈" ;;
    arch)             icon="󰣇" ;;
    fedora)           icon="󰣛" ;;
    debian)           icon="󰣚" ;;
    opensuse*|suse)   icon="" ;;
    manjaro)          icon="" ;;
    pop)              icon="" ;;
    nixos)            icon="" ;;
    void)             icon="" ;;
    gentoo)           icon="" ;;
    alpine)           icon="" ;;
    linuxmint|mint)   icon="󰣭" ;;
    rhel|redhat)      icon="󱄛" ;;
    kali)             icon="" ;;
    endeavouros)      icon="" ;;
    *)                icon="" ;;
esac

name="${PRETTY_NAME:-$NAME}"
[ -z "$name" ] && name="Linux"

printf '{"text":"%s","tooltip":"%s"}\n' "$icon" "$name"
