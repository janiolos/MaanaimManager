# Documentacao Completa - Eventa

## 1. Visao geral
Eventa e um sistema web modular para gestao administrativa orientada a ciclos operacionais, usando `Evento` como entidade tecnica central.

## 2. Arquitetura

### Stack
- Python 3.13 + Django 6
- PostgreSQL 16
- APScheduler (tarefas recorrentes)
- Twilio WhatsApp API
- Docker Compose + Caddy (deploy)

### Estrutura principal
```
apps/
  core/           # autenticacao, permissoes, evento/ciclo, dashboard
  finance/        # receitas, despesas, relatorios
  inventory/      # produtos e movimentos de estoque
  lodging/        # chales e reservas
  notifications/  # lembretes WhatsApp
config/
static/
templates/
docs/
```

## 3. Modulos

### 3.1 Core
- Selecao de evento atual por sessao
- Perfis: `ADMINISTRADOR`, `FINANCEIRO`, `ESTOQUE`, `COORDENADOR`, `VISUALIZACAO`
- Rotulo configuravel para exibicao de "Evento" na interface
- Dashboard com KPIs e graficos

### 3.2 Financeiro
- Lancamentos de receita/despesa
- Categorias e contas
- Relatorios: conciliacao, fluxo de caixa, detalhado e PDF

### 3.3 Estoque
- Cadastro de produtos
- Entradas e saidas vinculadas ao evento
- Alertas visuais de estoque minimo/maximo

### 3.4 Hospedagem
- Cadastro de chales com capacidade, status e acessibilidade
- Estados visuais na listagem:
  - Disponivel (verde)
  - Reservado (amarelo)
  - Ocupado (vermelho)
  - Indisponivel (cinza)
- Regras de negocio:
  - reserva apenas para chale `ATIVO` e nao bloqueado no evento
  - total de hospedes (`qtd_pessoas + qtd_criancas`) nao pode exceder capacidade
  - idades de criancas obrigatorias quando `qtd_criancas > 0`

### 3.5 Lembretes WhatsApp
- Agendamento por `data_hora_envio`
- Telefone validado e normalizado
- Mensagem personalizada com placeholders:
  - `{evento_nome}`
  - `{data_evento}`
  - `{intervalo}`
- Midia opcional:
  - upload (`midia`)
  - URL publica (`midia_url`)
- Envio automatico por job periodico

## 4. Dashboard
- Cards financeiros: receitas, despesas, saldo, quantidade de lancamentos
- KPIs modulares por disponibilidade:
  - estoque
  - hospedagem
  - lembretes
- Grafico principal com alternancia:
  - barras (padrao)
  - linha
- Grafico de saldo acumulado por dia

## 5. API
- `GET /api/v1/health/` (protegido por autenticacao)
- `GET /api/v1/dashboard/` (resumo do evento atual)

## 6. Instalacao local
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_eventa
python manage.py runserver
```

## 7. Deploy em VPS
Usar documentacao operacional:
- `docs/README_DEPLOY.md`
- `docs/RUNBOOK.md`

## 8. Troubleshooting rapido

### Reservas nao aparecem / evento errado
- Selecione o evento em `/core/evento/`

### Lembrete nao envia
- Validar credenciais Twilio no `.env`
- Verificar se `ativo=True` e `enviado=False`
- Conferir `data_hora_envio`

### Falha de acesso ao banco
- Conferir `POSTGRES_*` e mapeamento para `DB_*` no app

### Estilo nao atualiza
- Fazer hard refresh (`Ctrl+Shift+R`) e limpar cache

## 9. Versao
- Versao funcional consolidada: Fevereiro/2026
- Documento atualizado em: 10/02/2026
