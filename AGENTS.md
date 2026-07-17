# AGENTS.md — MaanaimManager

## Project Overview

MaanaimManager is the active FastAPI + React rewrite of a retreat-center management system. The legacy Django tree is no longer part of the active application flow and was moved to `lixeira/legacy_django_2026-07-15`.

The current product scope centers on event-based operations for a spiritual retreat farm:

- event management;
- finance per event;
- central inventory plus local subinventory for POS;
- lodging in chalets;
- POS operation for cantina, fazendinha, livraria and secretaria;
- administrative screens and permissions.

## Agent Guidelines & Optimization

To maximize efficiency, reduce token usage, and save processing time, the agent MUST adhere to the following rules:

- **Concise Communication**: Write extremely short, objective, and only necessary responses. Avoid long introductions, explanations, or summaries unless explicitly requested.
- **Token & Processing Economy**:
  - Do not read entire large files; use specific line ranges when possible.
  - Apply minimal targeted code changes rather than rewriting large blocks or whole files.
  - Do not run commands that generate large volumes of output unless required.
- **Excluded Directories** (do not search, index, or read files from these directories):
  - `backups/` - Contains database dumps and backups.
  - `lixeira/` - Contains the legacy Django system and deprecated files.
  - `data/` - Docker data volumes and runtime state.
  - `media/` - Uploaded media files.
  - `staticfiles/` - Compiled static assets.
  - `.venv/` - Python virtual environment.
  - `.git/` - Git internal repository files.

## Tech Stack

| Layer | Stack |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0 async, Alembic, Pydantic v2 |
| Frontend | React 19, TypeScript, Vite, TailwindCSS, shadcn/ui, Zustand, TanStack Query, react-hook-form, zod |
| Database | PostgreSQL 16 |
| Auth | JWT + refresh cookie, scopes derived from legacy groups |
| Reports | PDF via WeasyPrint, CSV export |
| Infra | Docker Compose v2 + Caddy |

## Directory Structure

```text
MaanaimManager/
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── finance/
│   │   ├── inventory/
│   │   ├── lodging/
│   │   ├── pos/
│   │   ├── db/
│   │   └── middleware/
│   ├── alembic/
│   └── scripts/
├── frontend/
│   └── src/
│       ├── components/
│       ├── lib/
│       ├── routes/
│       └── stores/
├── caddy/
├── scripts/
├── docs/design/
├── docker-compose.v2.yml
└── lixeira/
```

## Code Conventions

### Backend

- Use SQLAlchemy 2 declarative models with `Mapped[]` and `mapped_column`.
- Preserve Django table names and field semantics where the existing schema requires it.
- Prefer `lazy="selectin"` on relationships.
- Keep business logic inside `*Service` classes.
- Keep routers mounted under `/api/v1`.
- Use `CurrentUser` and `EventoAtualId` dependencies consistently.
- Avoid patterns that trigger async lazy-load after `flush()`.

### Frontend

- Keep one folder per module under `src/routes/<module>/`.
- Use `hooks.ts` and `types.ts` inside each route module.
- Keep auth and event selection in Zustand stores.
- Route API calls through `src/lib/api.ts`.
- Preserve the current visual language already established in the app.

## Current Module Status

| Module | Backend | Frontend | Notes |
|---|---|---|---|
| Auth | OK | OK | login, refresh, logout, me |
| Core | OK | OK | events, admin, config, permissions |
| Finance | OK | OK | CRUD, reports, DRE, fluxo, conciliação, official report |
| Inventory | OK | OK | products, stock flows, requests, quotes, suppliers |
| Lodging | OK | OK | chalets, reservations, actions, map |
| POS | OK | OK | locals, families, local products, transfers, sales, cash shift |

## Key Decisions

- The legacy PostgreSQL schema remains the source of truth for table names.
- The active event is selected by `X-Evento-Id`.
- POS local stock must be fed from central inventory through transfers.
- Financial reporting stays on the backend.
- Legacy Django assets are archival only unless explicitly restored.

## Running the Project

```bash
docker compose -f docker-compose.v2.yml up -d --build
```

Default access:

- frontend: `http://localhost:8090`
- backend API: `http://localhost:8000/api/v1`
- docs: `http://localhost:8000/docs` in development mode

# Clean Code para Agentes de IA

Este guia estabelece os princípios de desenvolvimento de código otimizados para leitura, edição e manutenção por agentes de inteligência artificial (LLMs), baseados nas restrições técnicas de contexto, atenção e execução de ferramentas.

---

## Princípios de Desenvolvimento

### 1. Funções e Arquivos Pequenos

- **Regra:** Mantenha arquivos curtos (idealmente 200–300 linhas, máximo 500) e funções focadas (4 a 20 linhas).

- **Porquê:** Evita o truncamento de contexto nas chamadas de ferramentas (*tool calls*), permitindo que o agente processe toda a unidade lógica de uma vez com atenção máxima.

### 2. Responsabilidade Única (SRP)

- **Regra:** Cada arquivo ou classe deve ter uma única responsabilidade clara.

- **Porquê:** Facilita o isolamento de lógica, permitindo que o agente altere uma funcionalidade sem medo de efeitos colaterais e sem a necessidade de ler grandes partes do ecossistema.

### 3. Nomes Significativos e Únicos (Grepáveis)

- **Regra:** Use nomes altamente descritivos e evite termos genéricos (ex: prefira `InvoiceLineItemTotal` a `ItemTotal` ou `data`).

- **Porquê:** Agentes navegam pelo repositório utilizando buscas léxicas rápidas (como `grep` ou `ripgrep`). Nomes únicos reduzem resultados falsos positivos e otimizam o uso de tokens.

### 4. Comentários de Contexto e Proveniência (O "Porquê")

- **Regra:** Adicione comentários que expliquem a motivação de decisões não óbvias (ex: contornos de bugs externos, regras de negócio complexas, histórico de decisão). Escreva docstrings estruturadas com exemplos de uso.

- **Porquê:** Agentes leem e usam comentários como contexto de primeira classe. Ao contrário dos humanos, eles se beneficiam imensamente de explicações contextuais de alto nível sobre *por que* algo foi feito de determinada maneira.

### 5. Tipagem Explícita

- **Regra:** Sempre declare tipos explicitamente (Type Hints em Python, TypeScript em vez de JS, etc.).

- **Porquê:** Reduz a necessidade de inferência cognitiva por parte do LLM, evitando erros de interpretação sobre os contratos de entrada/saída das funções.

### 6. DRY (Don't Repeat Yourself) estrito

- **Regra:** Elimine duplicações de código de forma agressiva.

- **Porquê:** O agente pode falhar em identificar todas as cópias duplicadas espalhadas pelo repositório ao realizar uma refatoração, gerando inconsistências silenciosas.

### 7. Testabilidade Automatizada e Headless

- **Regra:** Os testes devem ser facilmente executáveis pelo agente sem intervenção manual (comandos documentados no `README.md` ou `CLAUDE.md`, execução rápida, sem dependência de credenciais locais não versionadas).

- **Porquê:** O agente trabalha em ciclos de *tentativa-erro-ajuste*. Se ele não puder rodar a suíte de testes de forma autônoma para validar as alterações, o risco de introduzir regressões invisíveis é alto.
