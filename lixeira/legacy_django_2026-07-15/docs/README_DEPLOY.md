# Deploy VPS com Docker Compose (Eventa)

Deploy padrao para VPS Linux (Debian/Ubuntu) com:
- `app` (Django + Gunicorn)
- `db` (PostgreSQL 16, sem exposicao publica)
- `caddy` (proxy reverso com HTTPS automatico)

## 1. Pre-requisitos
- VPS Linux com acesso SSH
- DNS do `DOMAIN` apontando para o IP da VPS
- Portas 80 e 443 liberadas

## 2. Instalar e subir stack
```bash
git clone <URL_DO_REPOSITORIO>
cd MaanaimManager
chmod +x scripts/*.sh
./scripts/install.sh
```

## 3. Configurar `.env`
Se ainda nao existir:
```bash
cp .env.example .env
```

Edite obrigatoriamente:
- `DOMAIN`
- `ADMIN_EMAIL`
- `POSTGRES_PASSWORD`
- `APP_SECRET_KEY`
- `APP_ALLOWED_HOSTS`

Aplicar alteracoes:
```bash
docker compose up -d --build
```

## 4. Pos-deploy (Django)
```bash
docker compose exec app python manage.py createsuperuser
# opcional
docker compose exec app python manage.py seed_eventa
```

## 5. Operacao basica
```bash
docker compose ps
docker compose logs -f app
docker compose logs -f caddy
./scripts/healthcheck.sh
```

## 6. Backup
```bash
./scripts/backup.sh
./scripts/rotate_backups.sh
```

Restaurar:
```bash
./scripts/restore.sh ./backups/db/AAAAMMDD_HHMM_eventa.sql.gz
```

## 7. Atualizacao e rollback
Atualizar:
```bash
git pull
docker compose up -d --build
```

Rollback simples:
```bash
git checkout <commit_anterior>
docker compose up -d --build
```

## 8. Teste HTTPS
```bash
curl -I https://SEU_DOMINIO
```
