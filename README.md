# MaanaimManager

Sistema de gestão para retiros espirituais em fazenda, reescrito em FastAPI + React sobre o schema PostgreSQL herdado do projeto Django anterior.

## Escopo atual

O projeto cobre os módulos operacionais centrais:

- autenticação e seleção de evento;
- administração básica de eventos, usuários, permissões e configuração;
- financeiro por evento, com relatórios e exportações;
- estoque central;
- hospedagem em chalés;
- PDV com subestoque por local de venda;
- integração financeira das vendas do PDV.

Locais de venda atualmente tratados no domínio do PDV:

- cantina;
- fazendinha;
- livraria;
- secretaria.

## Stack

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2 async, Alembic, Pydantic v2 |
| Frontend | React 19, TypeScript, Vite, TailwindCSS, shadcn/ui, Zustand, TanStack Query |
| Banco | PostgreSQL 16 |
| Autenticação | JWT com refresh cookie e escopos derivados dos grupos legados |
| PDF | WeasyPrint |
| Infra local | Docker Compose + Caddy |

## Estrutura

```text
MaanaimManager/
├── backend/                 # API FastAPI
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
├── frontend/                # SPA React
│   └── src/
│       ├── components/
│       ├── lib/
│       ├── routes/
│       └── stores/
├── caddy/
├── docs/design/             # artefatos visuais arquivados
├── scripts/backup.sh        # backup do banco
├── docker-compose.v2.yml    # stack ativa
└── lixeira/                 # legado movido da árvore principal
```

## Status dos módulos

| Módulo | Backend | Frontend | Observações |
|---|---|---|---|
| Auth | OK | OK | login, refresh, logout, usuário atual |
| Core | OK | OK | eventos, admin, configuração e permissões |
| Finance | OK | OK | lançamentos, dashboard, DRE, fluxo, conciliação, oficial, PDF/CSV |
| Inventory | OK | OK | produtos, entradas, requisições, cotações e fornecedores |
| Lodging | OK | OK | chalés, reservas, ações e mapa |
| POS | OK | OK | locais, famílias, subestoque, transferências, vendas e caixa |

## Regras importantes já implementadas

- o backend preserva nomes de tabelas do schema legado Django;
- o evento ativo é informado pelo header `X-Evento-Id`;
- o PDV opera com subestoque por local, sem entrada direta fora da transferência do estoque central;
- vendas do PDV validam caixa aberto, local do evento, permissões de desconto e estoque disponível;
- relatórios financeiros continuam sendo gerados no backend, incluindo PDF.

## Subir o projeto com Docker

Pré-requisitos:

- Docker com `docker compose`;
- arquivo `backend/.env` configurado;
- opcionalmente `.env.v2` ou variáveis exportadas no shell para customizar nomes/portas.

Comando:

```bash
docker compose -f docker-compose.v2.yml up -d --build
```

Acessos padrão:

- aplicação: `http://localhost:8090`
- API interna: `http://localhost:8000/api/v1`
- Swagger: `http://localhost:8000/docs` quando `ENVIRONMENT` estiver em modo de desenvolvimento

## Desenvolvimento local

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

Em desenvolvimento, o frontend usa a configuração de `VITE_API_BASE_URL` para acessar a API.

## Operação

Backup manual do banco:

```bash
./scripts/backup.sh
```

Os arquivos são gravados em `backups/db/`. Se `BACKUP_S3_BUCKET` estiver configurado, o script também envia o dump para S3.

## Documentação interna

- [backend/README.md](./backend/README.md)
- [frontend/README.md](./frontend/README.md)
- [docs/specs/README.md](./docs/specs/README.md)
- [SECURITY.md](./SECURITY.md)
- [AGENTS.md](./AGENTS.md)

## Observações

- a árvore Django anterior foi removida da raiz e preservada em `lixeira/legacy_django_2026-07-15`;
- ainda existe uma pendência operacional para `data/static`, mantida fora da lixeira por permissão de filesystem;
- há dívida técnica pré-existente de lint no backend, fora do escopo da limpeza documental.
