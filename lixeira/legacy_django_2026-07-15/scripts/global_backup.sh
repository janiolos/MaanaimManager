#!/usr/bin/env bash
set -euo pipefail

# Script de Backup Global do CycloHub SaaS
# Este script percorre todos os clientes em /opt/eventa/clients/ e executa o backup de cada um.

CLIENTS_DIR="/opt/cyclohub/clients"
GLOBAL_BACKUP_DIR="/opt/cyclohub/backups/global"
TIMESTAMP="$(date +%Y%m%d_%H%M)"

mkdir -p "$GLOBAL_BACKUP_DIR"

echo "📂 Iniciando Backup Global: $TIMESTAMP"

if [ ! -d "$CLIENTS_DIR" ]; then
    echo "⚠️ Diretório de clientes não encontrado: $CLIENTS_DIR"
    exit 0
fi

for client_path in "$CLIENTS_DIR"/*; do
    if [ -d "$client_path" ] && [ -f "$client_path/docker-compose.yml" ]; then
        client_name=$(basename "$client_path")
        echo "💾 Fazendo backup do cliente: $client_name"
        
        # Criar pasta de backup para o cliente se não existir
        mkdir -p "$GLOBAL_BACKUP_DIR/$client_name"
        
        # Executar backup usando o script interno do cliente ou via docker diretamente
        cd "$client_path"
        
        # Carregar variáveis do .env do cliente
        set -a
        source .env
        set +a
        
        OUT_FILE="$GLOBAL_BACKUP_DIR/$client_name/${TIMESTAMP}_${client_name}.sql.gz"
        
        # Dump do banco direto para a pasta global
        docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip -c > "$OUT_FILE"
        
        if [[ -s "$OUT_FILE" ]]; then
            echo "✅ Backup concluído para $client_name: $(basename "$OUT_FILE")"
        else
            echo "❌ Erro ao gerar backup para $client_name"
            rm -f "$OUT_FILE"
        fi
    fi
done

echo "🏁 Backup Global Finalizado."
