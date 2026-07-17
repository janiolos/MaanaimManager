# Specs

Esta pasta concentra a especificação viva do MaanaimManager.

Objetivos:

- tornar o projeto reproduzível em outro ambiente;
- registrar contratos funcionais e técnicos da stack atual;
- explicitar melhorias futuras sem depender de memória oral;
- reduzir ambiguidade em novas implementações.

## Documentos

- [system-overview.md](./system-overview.md): visão funcional e técnica do sistema atual
- [reproducibility.md](./reproducibility.md): requisitos, setup, bootstrap e verificações mínimas
- [module-specs.md](./module-specs.md): regras e fluxos por módulo
- [future-improvements.md](./future-improvements.md): backlog priorizado de evolução

## Escopo

Estas specs descrevem a árvore ativa do projeto:

- `backend/` FastAPI
- `frontend/` React
- `docker-compose.v2.yml`
- `caddy/Caddyfile.v2`

O conteúdo arquivado em `lixeira/` e em `docs/design/` é referência histórica, não contrato ativo do sistema.
