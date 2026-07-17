# Backend MaanaimManager

API FastAPI responsável pelos módulos de autenticação, eventos, financeiro, estoque, hospedagem e PDV.

## Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2 async
- asyncpg
- Alembic
- Pydantic v2
- python-jose
- WeasyPrint
- pytest / Ruff / mypy no ambiente de desenvolvimento

## Estrutura

```text
backend/
├── app/
│   ├── auth/         # JWT, scopes, dependências e rotas
│   ├── core/         # eventos, usuários, grupos, configuração
│   ├── finance/      # lançamentos, relatórios e exportações
│   ├── inventory/    # produtos, estoque, cotações e requisições
│   ├── lodging/      # chalés, reservas, ações e mapa
│   ├── pos/          # PDV, subestoque, caixa e vendas
│   ├── db/           # sessão, base e infraestrutura ORM
│   ├── middleware/   # auditoria e inatividade
│   ├── config.py
│   └── main.py
├── alembic/
├── scripts/
├── tests/
└── pyproject.toml
```

## Convenções relevantes

- nomes de tabela seguem o schema Django legado;
- services ficam em classes `*Service` com métodos estáticos;
- routers são montados sob `/api/v1`;
- relacionamentos ORM usam `lazy="selectin"` para evitar N+1;
- `CurrentUser` e `EventoAtualId` são as dependências padrão de autenticação e escopo de evento;
- o header `X-Evento-Id` define o evento operacional corrente.

## Módulos expostos

- `auth`
- `core`
- `finance`
- `inventory`
- `lodging`
- `pos`

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Swagger fica disponível em `http://localhost:8000/docs` quando `ENVIRONMENT` estiver em modo de desenvolvimento.

## Testes e checagens

```bash
pytest
ruff check .
mypy app
```

Observação: o repositório ainda carrega problemas históricos de lint em arquivos antigos do backend. Nem todo `ruff check .` está limpo hoje.

## Pontos funcionais importantes

- autenticação é compatível com o hash PBKDF2 do legado;
- relatórios financeiros em PDF continuam no backend com WeasyPrint;
- o PDV possui integridade reforçada para caixa, evento, local, desconto e subestoque;
- transferências para estoque de local de venda passam pelo estoque central e geram rastreabilidade própria.
