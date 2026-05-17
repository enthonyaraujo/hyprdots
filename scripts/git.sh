#!/usr/bin/env bash
set -euo pipefail

echo "===== Configurando Git ====="

read -rp "Digite seu nome para o Git: " GIT_NAME
while [[ -z "$GIT_NAME" ]]; do
    read -rp "Nome não pode ser vazio. Digite novamente: " GIT_NAME
done

read -rp "Digite seu email para o Git/GitHub: " GIT_EMAIL
while [[ -z "$GIT_EMAIL" ]]; do
    read -rp "Email não pode ser vazio. Digite novamente: " GIT_EMAIL
done

git config --global user.name "$GIT_NAME"
git config --global user.email "$GIT_EMAIL"
git config --global init.defaultBranch main

echo
echo "Git configurado:"
git config --global --list | grep -E "user.name|user.email|init.defaultBranch"

echo
echo "===== Configurando SSH ====="

mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

KEY_PATH="$HOME/.ssh/id_ed25519"

if [[ ! -f "$KEY_PATH" ]]; then
    echo "Gerando chave SSH..."
    ssh-keygen -t ed25519 -C "$GIT_EMAIL" -f "$KEY_PATH"
else
    echo "Chave SSH já existe em: $KEY_PATH"
fi

echo
echo "Iniciando ssh-agent..."
eval "$(ssh-agent -s)"

echo "Adicionando chave SSH ao agente..."
ssh-add "$KEY_PATH"

echo
echo "COPIE A CHAVE ABAIXO E ADICIONE NO GITHUB:"
echo "GitHub > Settings > SSH and GPG keys > New SSH key"
echo "----------------------------------------"
cat "$KEY_PATH.pub"
echo "----------------------------------------"
echo

read -rp "Digite 'y' após adicionar a chave no GitHub: " OK
[[ "${OK,,}" == "y" ]] || exit 1

echo
echo "Testando conexão com o GitHub..."
ssh -T git@github.com || true

echo
echo "Configuração finalizada."
