# Future Improvements

## Objetivo

Registrar melhorias futuras de forma priorizada, com critério de valor e risco.

## Prioridade P0

Itens que afetam integridade, segurança ou capacidade de operar o sistema com previsibilidade.

- formalizar seed idempotente da stack nova:
  - usuário admin
  - grupos/scopes
  - evento de demonstração
- criar smoke test automatizado pós-deploy
- revisar política de segredos e rotação operacional
- eliminar pendência de permissões herdadas em `data/static`
- documentar e automatizar restore da stack nova

## Prioridade P1

Itens que melhoram robustez operacional dos módulos já ativos.

- POS:
  - cancelamento de venda
  - estorno
  - sangria
  - suprimento
  - fechamento por turno com conferência
- estoque:
  - inventário físico
  - ajustes manuais auditáveis
  - perdas e avarias
- financeiro:
  - fechamento por período
  - integração explícita com caixas operacionais
  - relatórios de divergência
- hospedagem:
  - leitos/camas
  - check-in/check-out
  - bloqueios temporários

## Prioridade P2

Itens que aumentam produtividade e governança.

- dashboard executivo consolidado do retiro;
- auditoria navegável por módulo;
- exportações padronizadas por operação;
- seeds de dados de demonstração;
- documentação de API consumível por terceiros.

## Prioridade P3

Itens estratégicos ou de expansão.

- multiunidade ou multi-fazenda;
- agenda operacional integrada;
- gestão de participantes/inscrições;
- motor de notificações moderno substituindo o legado arquivado;
- relatórios gerenciais comparativos entre eventos.

## Melhorias arquiteturais recomendadas

- consolidar validações compartilhadas entre serviços;
- aumentar cobertura de testes por serviço crítico;
- reduzir dívida de lint e tipagem no backend;
- adicionar CI com etapas mínimas:
  - lint
  - testes backend
  - build frontend
  - validação de migração

## Critérios para aceitar novas melhorias

- preservar compatibilidade com o schema legado ou justificar migração explícita;
- manter separação entre estoque central e estoque local do PDV;
- manter escopo por evento onde o domínio exige;
- preferir mudanças auditáveis e reversíveis;
- toda nova regra de negócio deve nascer acompanhada de spec e teste.
