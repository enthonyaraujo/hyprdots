#!/bin/bash

# adicione os nomes dos processos dos seus gravadores de tela
# exemplos: "wf-recorder", "obs", "Kooha", "simplescreenrecorder"
PROCESSOS_GRAVADOR=("obs")

gravando=false

for processo in "${PROCESSOS_GRAVADOR[@]}"; do

    if pgrep -x "$processo" > /dev/null; then
        gravando=true
        break 
    fi
done

if $gravando; then
    echo '{"text": " ", "class": "recording", "tooltip": "Gravação de tela ativa"}'
else
    echo '{}'
fi