# Segurança

Este arquivo registra os pontos de atenção conhecidos no repositório e no fluxo operacional atual.

## 1. Segredos expostos no histórico Git

Existe evidência de que um arquivo `.env` foi commitado no passado e depois removido da árvore ativa. O problema não está na árvore atual, mas no histórico do repositório.

Impacto:

- credenciais antigas podem continuar acessíveis em clones antigos, forks e commits históricos;
- qualquer segredo ainda reutilizado em ambientes atuais deve ser tratado como comprometido.

Ação recomendada:

1. rotacionar todas as credenciais históricas potencialmente expostas;
2. revisar segredos de banco, JWT e integrações externas;
3. reescrever histórico com `git filter-repo` ou ferramenta equivalente, se o time aceitar o custo operacional;
4. forçar re-clone do repositório após a limpeza do histórico.

## 2. Situação atual da árvore

- `.env` local existe em disco, mas não deve ser versionado;
- a stack ativa usa `backend/.env` para o container do backend;
- o arquivo `.env.v2.example` serve apenas como referência para variáveis de compose e ambiente.

## 3. Stack atual e impacto de credenciais

Na stack FastAPI + React, os itens mais sensíveis são:

- `POSTGRES_PASSWORD`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- buckets e credenciais de backup S3, quando configurados

Como o Django legado saiu da árvore ativa, segredos específicos de sessão Django deixaram de ser relevantes para execução atual, mas continuam relevantes se ainda existirem ambientes antigos rodando aquele código.

## 4. Boas práticas mínimas para este projeto

- não versionar `.env`, dumps, chaves ou arquivos exportados de produção;
- manter `ENVIRONMENT=prod` fora de ambientes locais quando não houver necessidade;
- não expor `docs`, `openapi.json` e `redoc` em produção sem intenção explícita;
- revisar permissões de diretórios montados por container, especialmente em `data/` e `media/`;
- manter backups fora da máquina principal quando o script `scripts/backup.sh` for usado em produção.

## 5. Pendências operacionais conhecidas

- existe diretório legado com ownership de container em `data/static`, o que já indica necessidade de revisão de permissões do host;
- o repositório ainda precisa de uma política clara para rotação de segredos e restauração validada de backup na stack nova.
