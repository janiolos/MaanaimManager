# Resumo de Implementacao (Estado Atual)

## Status
Implementacao MVP funcional, com modulos integrados e deploy padrao por Docker Compose.

## Modulos
- `core`: perfis, permissoes, evento/ciclo e dashboard
- `finance`: lancamentos e relatorios
- `inventory`: produtos, entradas e saidas
- `lodging`: chales e reservas com regras de capacidade/disponibilidade
- `notifications`: lembretes WhatsApp com agendamento por data/hora

## Pontos tecnicos relevantes
- Dashboard com grafico principal em barras (padrao) e alternancia para linha
- Hospedagem com status visuais de chales na listagem
- Reserva de chale limitada por disponibilidade e capacidade
- Campo de acessibilidade de chale com selecao explicita (sim/nao)
- Lembretes com mensagem customizavel, placeholders e midia opcional

## Deploy operacional
- `docker-compose.yml` com servicos `db`, `app` e `caddy`
- Scripts operacionais:
  - `scripts/install.sh`
  - `scripts/backup.sh`
  - `scripts/restore.sh`
  - `scripts/rotate_backups.sh`
  - `scripts/healthcheck.sh`

## Documentos de operacao
- `docs/README_DEPLOY.md`
- `docs/RUNBOOK.md`

## Data de consolidacao
10/02/2026
