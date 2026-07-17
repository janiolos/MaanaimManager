# Frontend MaanaimManager

SPA React responsável pela operação diária do sistema MaanaimManager.

## Stack

- React 19
- TypeScript
- Vite
- React Router
- Zustand
- TanStack Query
- react-hook-form + zod
- TailwindCSS
- shadcn/ui
- Sonner

## Estrutura

```text
frontend/
├── src/
│   ├── components/   # shell, guards e componentes UI
│   ├── lib/          # api client e utilitários
│   ├── routes/       # telas por módulo
│   ├── stores/       # auth e evento atual
│   ├── App.tsx
│   └── main.tsx
├── public/
└── package.json
```

## Rotas principais

- autenticação: login e seleção de evento;
- core: eventos, administração, permissões e configuração;
- financeiro: dashboard, listagem, formulário e relatórios;
- estoque: produtos, requisições, cotações, fornecedores e entradas;
- hospedagem: chalés, reservas, ações e mapa;
- PDV: dashboard, operação de venda, locais, famílias, produtos locais e transferências.

## Padrões de implementação

- cada módulo em `src/routes/<modulo>/`;
- `hooks.ts` para queries e mutations;
- `types.ts` para contratos do módulo;
- `src/lib/api.ts` injeta JWT e `X-Evento-Id`;
- `useAuthStore` e `useEventoStore` concentram estado global mínimo.

## Rodar localmente

```bash
npm install
npm run dev
```

Scripts disponíveis:

```bash
npm run build
npm run lint
npm run typecheck
npm run preview
```

## Integração com a API

O frontend espera a API sob a base configurada em `VITE_API_BASE_URL`. Em produção, o Caddy encaminha `/api/*` para o backend e o restante para o frontend.

## Observações

- o `README` padrão do template Vite foi substituído por documentação do projeto real;
- a interface segue a organização funcional do sistema, não um design system genérico separado;
- o módulo de notificações do legado não existe mais na árvore ativa do frontend.
