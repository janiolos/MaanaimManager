# Eventa (MaanaimManager)

Sistema web modular para gestao operacional por ciclos (entidade tecnica: `Evento`).

## Visao geral
- Backend: Django 6 + PostgreSQL
- Frontend: Tabler + CSS customizado
- Modulos:
  - Nucleo (`apps.core`)
  - Financeiro (`apps.finance`)
  - Estoque (`apps.inventory`)
  - Hospedagem (`apps.lodging`)
  - Lembretes WhatsApp (`apps.notifications`)
- Deploy padrao: Docker Compose + Caddy + HTTPS automatico

## Funcionalidades principais
- Controle de perfis e permissoes por modulo
- Ciclo operacional com selecao de evento ativo por sessao
- Lancamentos financeiros, relatorios e dashboard
- Estoque com entradas/saidas e alertas de minimo/maximo
- Hospedagem com status visual de chale e regras de reserva
- Lembretes WhatsApp com agendamento por data/hora, mensagem personalizada e midia opcional

## Requisitos (desenvolvimento local)
- Python 3.11+
- PostgreSQL 16 (ou container)
- Dependencias de `requirements.txt`

## Rodar localmente
1. Criar ambiente virtual e instalar dependencias:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Criar `.env` (baseado em `.env.example`) e ajustar credenciais.

3. Rodar migracoes e seed opcional:
```bash
python manage.py migrate
python manage.py seed_eventa
python manage.py createsuperuser
```

4. Subir servidor:
```bash
python manage.py runserver
```

## Rodar com Docker (stack completa)
```bash
chmod +x scripts/*.sh
./scripts/install.sh
```

Comandos uteis:
```bash
docker compose ps
docker compose logs -f app
./scripts/healthcheck.sh
```

## Rotas principais
- `/login/` e `/logout/`
- `/dashboard/`
- `/core/evento/` (selecao de ciclo atual)
- `/finance/lancamentos/`
- `/inventory/produtos/`
- `/lodging/chales/`
- `/notifications/`

## Documentacao
- Arquitetura e uso completo: `DOCUMENTACAO_COMPLETA.md`
- MVP e escopo: `EVENTA_MVP.md`
- Deploy VPS: `docs/README_DEPLOY.md`
- Operacao diaria: `docs/RUNBOOK.md`
