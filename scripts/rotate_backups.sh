#!/usr/bin/env bash
set -euo pipefail

# Script de Rotação de Backups
# Remove backups mais antigos que X dias para economizar espaço.

BACKUP_DIR="/opt/cyclohub/backups/global"
KEEP_DAYS=7

echo "🧹 Iniciando limpeza de backups antigos (mantendo os últimos $KEEP_DAYS dias)..."

if [ ! -d "$BACKUP_DIR" ]; then
    echo "⚠️ Diretório de backups não encontrado."
    exit 0
fi

# Procurar e remover arquivos .sql.gz com mais de KEEP_DAYS dias
find "$BACKUP_DIR" -type f -name "*.sql.gz" -mtime +$KEEP_DAYS -exec rm {} \; -print

echo "✅ Limpeza concluída."
