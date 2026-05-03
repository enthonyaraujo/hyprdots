#!/bin/bash

# Extrai apenas o número do uso da GPU da NVIDIA
usage=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits)

# Se o nvidia-smi falhar ou retornar vazio, define como 0
if [ -z "$usage" ]; then
  usage="0"
fi

# Formata a saída em JSON para o Waybar
echo "{\"text\": \"$usage%\", \"tooltip\": \"Uso da GPU: $usage%\", \"class\": \"gpu\"}"
