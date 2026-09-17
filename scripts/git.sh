#!/usr/bin/env bash
set -euo pipefail

echo "===== Configuring Git ====="

read -rp "Enter your name for Git: " GIT_NAME
while [[ -z "$GIT_NAME" ]]; do
    read -rp "Name cannot be empty. Please enter again: " GIT_NAME
done

read -rp "Enter your email for Git/GitHub: " GIT_EMAIL
while [[ -z "$GIT_EMAIL" ]]; do
    read -rp "Email cannot be empty. Please enter again: " GIT_EMAIL
done

git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"
git config --global init.defaultBranch main

echo
echo "Git configured:"
git config --global --list | grep -E "user.name|user.email|init.defaultBranch"

echo
echo "===== Configuring SSH ====="

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

KEY_PATH="$HOME/.ssh/id_ed25519"

if [[ ! -f "$KEY_PATH" ]]; then
    echo "Generating SSH key..."
    ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$KEY_PATH"
else
    echo "SSH key already exists at: $KEY_PATH"
fi

echo
echo "Starting ssh-agent..."
eval "$(ssh-agent -s)"

echo "Adding SSH key to agent..."
ssh-add "$KEY_PATH"

echo
echo "COPY THE KEY BELOW AND ADD TO GITHUB:"
echo "GitHub > Settings > SSH and GPG keys > New SSH key"
echo "----------------------------------------"
cat "$KEY_PATH.pub"
echo "----------------------------------------"
echo

read -rp "Enter 'y' after adding the key to GitHub: " OK
[[ "${OK,,}" == "y" ]] || exit 1

echo
echo "Testing connection to GitHub..."
ssh -T git@github.com || true

echo
echo "Configuration complete."
