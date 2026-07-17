# Reproducibility

## Objetivo

Qualquer pessoa do time deve conseguir subir o projeto, aplicar migrações e validar o fluxo mínimo sem depender de conhecimento implícito.

## Requisitos do host

- Linux, macOS ou WSL com Docker funcional
- Docker Engine com `docker compose`
- portas `8090`, `8000` e `5432` disponíveis no ambiente local, ou variáveis equivalentes ajustadas

## Arquivos de configuração

### Obrigatórios

- `backend/.env`

### Opcionais

- `.env.v2` para parametrizar variáveis de compose e nomes de serviços

## Stack reprodutível padrão

Arquivo principal:

```bash
docker-compose.v2.yml
```

Serviços:

- `db`
- `backend`
- `frontend`
- `caddy`

## Bootstrap com Docker

### 1. Preparar variáveis

Criar ou revisar:

```bash
backend/.env
```

Opcional:

```bash
cp .env.v2.example .env.v2
export $(cat .env.v2 | xargs)
```

### 2. Subir a stack

```bash
docker compose -f docker-compose.v2.yml up -d --build
```

### 3. Validar saúde mínima

Checklist:

- `docker compose -f docker-compose.v2.yml ps`
- `curl http://localhost:8090`
- `curl http://localhost:8000/api/v1/health`

Resultado esperado no health:

```json
{"status":"ok","project":"<nome>","environment":"<env>"}
```

## Bootstrap sem Docker

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Migrações

As migrações ativas vivem em:

```text
backend/alembic/versions/
```

Head atual esperado:

- `0005_integridade_estoque_pdv.py`

Comando de validação:

```bash
cd backend
alembic current
alembic heads
```

## Fluxo mínimo de verificação funcional

### 1. Autenticação

- acessar a tela de login;
- autenticar com usuário válido;
- confirmar que o frontend recebe usuário e token;
- validar refresh passivo quando aplicável.

### 2. Seleção de evento

- escolher um evento ativo;
- confirmar persistência do `eventoId` no frontend;
- validar envio do header `X-Evento-Id` nas chamadas autenticadas.

### 3. Financeiro

- abrir dashboard;
- criar um lançamento;
- consultar pelo menos um relatório.

### 4. Estoque

- listar produtos;
- criar ou editar produto;
- registrar uma entrada no estoque central.

### 5. Hospedagem

- listar chalés;
- criar ou editar uma reserva.

### 6. POS

- abrir caixa de um local;
- transferir estoque central para o local;
- realizar uma venda válida;
- consultar dashboard ou histórico de vendas.

## Artefatos que não entram na reprodução ativa

Ignorar para bootstrap funcional:

- `lixeira/`
- `docs/design/`
- diretórios herdados de estático do Django

## Riscos conhecidos para reprodução

- `data/static` legado ainda possui ownership de container;
- variáveis ausentes em `backend/.env` quebram inicialização do backend;
- o backend depende de schema compatível com as tabelas esperadas do legado;
- rotinas de seed ainda não estão formalizadas como fluxo único da stack nova.

## Melhorias necessárias para reproduzibilidade

- consolidar um `backend/.env.example` garantidamente atualizado;
- criar seed idempotente para usuário admin, grupos e evento de demonstração;
- adicionar smoke test automatizado pós-subida da stack;
- documentar dataset mínimo para homologação.
