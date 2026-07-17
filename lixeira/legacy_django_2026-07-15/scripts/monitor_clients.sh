#!/usr/bin/env bash
set -euo pipefail

# Script de Monitoramento Global (Health Check) do CycloHub SaaS
# Verifica se todos os containers de todos os clientes estão rodando.

CLIENTS_DIR="/opt/cyclohub/clients"

echo "📊 Status Global do CycloHub SaaS - $(date)"
echo "------------------------------------------------"

if [ ! -d "$CLIENTS_DIR" ]; then
    echo "⚠️ Nenhum cliente encontrado."
    exit 0
fi

printf "%-20s | %-15s | %-10s\n" "CLIENTE" "CONTAINER" "STATUS"
echo "------------------------------------------------"

for client_path in "$CLIENTS_DIR"/*; do
    if [ -d "$client_path" ] && [ -f "$client_path/docker-compose.yml" ]; then
        client_name=$(basename "$client_path")
        
        # Coletar status dos containers do cliente
        docker compose -f "$client_path/docker-compose.yml" ps --format "{{.Name}} | {{.Status}}" | while read -r line; do
            container=$(echo "$line" | cut -d'|' -f1)
            status=$(echo "$line" | cut -d'|' -f2)
            printf "%-20s | %-15s | %-10s\n" "$client_name" "$container" "$status"
        done
    fi
done

echo "------------------------------------------------"
