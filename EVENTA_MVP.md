# Eventa MVP - Escopo Implementado

## Objetivo
Entregar um prototipo funcional, modular e navegavel para gestao operacional por ciclos (`Evento`).

## Entregas do MVP
- Nucleo com autenticacao, permissoes e selecao de ciclo atual
- Dashboard com KPIs e graficos
- Modulo Financeiro funcional
- Modulo Estoque funcional
- Modulo Hospedagem funcional
- Modulo de Lembretes WhatsApp funcional
- Seed de dados com usuarios/perfis e dados iniciais

## Semantica configuravel
- Nome tecnico no codigo/banco: `Evento`
- Rotulo exibido na interface: configuravel via `ConfiguracaoSistema`

## Perfis
- `ADMINISTRADOR`
- `FINANCEIRO`
- `ESTOQUE`
- `COORDENADOR`
- `VISUALIZACAO`

## Fluxos principais prontos
1. Selecionar ciclo atual
2. Lancar receitas/despesas e consultar relatorios
3. Cadastrar produtos e movimentar estoque
4. Gerenciar chales/reservas com validacoes
5. Criar lembretes com data/hora e mensagem personalizada

## Comandos rapidos
```bash
python manage.py migrate
python manage.py seed_eventa
python manage.py runserver
```

## Usuarios seed
- `eventa_admin` / `eventa123`
- `eventa_financeiro` / `eventa123`
