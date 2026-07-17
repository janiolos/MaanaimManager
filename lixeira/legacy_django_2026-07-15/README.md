## Lixeira de legado Django

Arquivos movidos em `2026-07-15` durante a limpeza da base após a migração para a stack `backend/` FastAPI + `frontend/` React.

Critérios usados:

- dependência explícita de `manage.py`, `config.settings`, `apps/*` ou `docker-compose.yml` antigo;
- documentação operacional apontando para a stack Django (`app` + Caddy antigo);
- templates e estáticos do Django não consumidos pela aplicação nova.

Objetivo:

- retirar ruído da raiz do projeto;
- preservar histórico local e facilitar rollback manual, sem exclusão definitiva.
