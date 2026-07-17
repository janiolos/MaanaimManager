# System Overview

## Propósito do produto

MaanaimManager é um sistema de gestão para uma fazenda que realiza retiros espirituais. O domínio principal gira em torno de eventos, que funcionam como unidade de operação para finanças, hospedagem, vendas e parte do estoque.

## Domínio central

Entidades principais:

- evento
- usuário e grupos/permissões
- lançamento financeiro
- produto de estoque central
- local de venda do PDV
- produto disponível em local de venda
- venda e pagamentos
- chalé
- reserva de chalé

## Arquitetura atual

### Backend

- FastAPI exposto em `/api/v1`
- SQLAlchemy 2 async com `asyncpg`
- Alembic para migrações incrementais
- autenticação JWT com refresh por cookie
- escopos derivados da estrutura de grupos herdada do sistema anterior
- geração de PDF via WeasyPrint no backend

### Frontend

- SPA React 19
- React Router para navegação
- Zustand para autenticação e evento atual
- TanStack Query para leitura e mutações
- formulários com `react-hook-form` e `zod`

### Infra

- `db`: PostgreSQL 16
- `backend`: API FastAPI
- `frontend`: build Vite servido por nginx
- `caddy`: reverse proxy da stack

## Contratos estruturais

- o schema legado do PostgreSQL foi preservado;
- nomes de tabelas continuam compatíveis com o sistema antigo;
- o evento ativo é enviado via header `X-Evento-Id`;
- a API base é `/api/v1`;
- o Caddy roteia `/api/*` para o backend e o restante para o frontend.

## Estado atual dos módulos

### Auth

- login
- refresh token
- logout
- leitura do usuário atual

### Core

- CRUD de eventos
- configuração básica
- administração básica
- leitura e aplicação de permissões

### Finance

- lançamentos por evento
- dashboard
- DRE
- fluxo de caixa
- conciliação
- relatório oficial
- exportação PDF/CSV

### Inventory

- produtos
- entradas
- requisições
- cotações
- fornecedores

### Lodging

- cadastro de chalés
- reservas
- ações de chalé
- mapa

### POS

- locais de venda
- famílias de produto por local
- produtos locais
- abertura e fechamento de caixa
- transferência do estoque central para subestoque do local
- vendas com múltiplos pagamentos
- dashboard e histórico

## Decisões de negócio já codificadas

- financeiro, hospedagem e vendas dependem do evento atual;
- o estoque central é perene, mas o PDV usa subestoque por local;
- não há entrada direta válida em estoque de local sem refletir saída do estoque central;
- vendas do PDV precisam respeitar local, evento, caixa aberto, desconto permitido e disponibilidade de estoque;
- a integração financeira do PDV é parte do backend atual.

## Limites conhecidos

- o legado Django foi arquivado, mas parte do modelo mental ainda referencia nomes herdados;
- o repositório possui dívida histórica de lint e organização em alguns pontos;
- ainda faltam specs de processos operacionais como cancelamento de venda, inventário físico e fechamento financeiro mais detalhado.
