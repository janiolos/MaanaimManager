# Runbook Operacional (Eventa)

## 1. App fora do ar
Diagnostico inicial:
```bash
docker compose ps
docker compose logs --tail=200 app
docker compose logs --tail=200 caddy
./scripts/healthcheck.sh
```

Recuperacao:
```bash
docker compose restart app caddy
docker compose up -d --build
```

## 2. Banco cheio
```bash
df -h
du -sh ./data/postgres ./backups ./media
./scripts/rotate_backups.sh
```

Maiores tabelas:
```bash
docker compose exec db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT relname AS tabela, pg_size_pretty(pg_total_relation_size(relid)) AS tamanho FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC LIMIT 20;"
```

## 3. Restaurar backup
```bash
./scripts/restore.sh ./backups/db/AAAAMMDD_HHMM_eventa.sql.gz
./scripts/healthcheck.sh
```

## 4. HTTPS e certificado
```bash
docker compose logs --tail=200 caddy
curl -I https://SEU_DOMINIO
```

Causas comuns:
- DNS incorreto
- porta 80/443 bloqueada
- `DOMAIN` errado no `.env`

## 5. Checklist mensal
1. Executar backup manual e validar tamanho do arquivo.
2. Testar restauracao em ambiente de homologacao.
3. Revisar espaco em disco.
4. Revisar logs de erro do app e caddy.
5. Atualizar sistema operacional da VPS.
