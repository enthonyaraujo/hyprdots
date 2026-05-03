#!/usr/bin/env bash

touch ~/.zshrc

cat << 'EOF' >> ~/.zshrc
#plugins

source /usr/share/zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source /usr/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

source <(fzf --zsh)

#starship prompt
eval "$(starship init zsh)"

source <(fzf --zsh)
EOF
