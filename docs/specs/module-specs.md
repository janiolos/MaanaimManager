# Module Specs

## Auth

### Objetivo

Controlar acesso ao sistema e manter contexto do usuário autenticado.

### Regras

- autenticação via JWT;
- refresh feito por cookie HTTP-only;
- frontend mantém access token e dados do usuário;
- permissões são derivadas de grupos legados.

### Fluxos mínimos

- login
- refresh
- logout
- leitura de `me`

## Core

### Objetivo

Manter o contexto administrativo do sistema.

### Entidades

- evento
- usuário
- grupo/permissão
- configuração de sistema
- centro de custo

### Regras

- o evento atual precisa ser escolhido para operar módulos dependentes;
- o header `X-Evento-Id` é obrigatório onde houver escopo por evento.

## Finance

### Objetivo

Registrar e reportar movimentação financeira por evento.

### Capacidades atuais

- cadastro e edição de lançamentos;
- dashboard financeiro;
- relatórios DRE, fluxo de caixa, conciliação e oficial;
- exportações CSV/PDF.

### Regras

- todos os lançamentos devem respeitar o evento ativo;
- relatórios são calculados no backend;
- PDFs são gerados com WeasyPrint.

### Melhorias futuras recomendadas

- fechamento mensal formal;
- contas/caixas mais explícitos por origem operacional;
- trilha de estorno e cancelamento com motivo.

## Inventory

### Objetivo

Manter o estoque central da fazenda.

### Capacidades atuais

- cadastro de produtos;
- entradas;
- requisições;
- cotações;
- fornecedores.

### Regras

- o estoque central é a origem para abastecimento dos locais de venda;
- a movimentação deve manter saldo consistente;
- produtos do PDV devem derivar do estoque central quando forem itens estocáveis.

### Melhorias futuras recomendadas

- inventário físico;
- ajuste por perda, consumo interno e avaria;
- custo médio auditável por movimento.

## Lodging

### Objetivo

Controlar ocupação dos chalés durante os retiros.

### Capacidades atuais

- cadastro de chalés;
- reservas;
- ações;
- mapa de ocupação.

### Regras

- reservas precisam obedecer disponibilidade e capacidade;
- o evento define o contexto operacional da hospedagem;
- estados visuais do mapa dependem do status de ocupação.

### Melhorias futuras recomendadas

- ocupação por cama/leito;
- bloqueios parciais de chalé;
- integração com check-in/check-out operacional.

## POS

### Objetivo

Operar os pontos de venda do retiro.

### Locais de venda

- cantina
- fazendinha
- livraria
- secretaria

### Capacidades atuais

- cadastro de locais;
- abertura e fechamento de caixa por turnos;
- famílias por local;
- produtos locais;
- transferência do estoque central para subestoque do local;
- venda com múltiplos pagamentos;
- conciliação de caixa consolidada por turno;
- impressão de comprovante de venda e relatório oficial de fechamento (PDF via WeasyPrint);
- dashboard e histórico de vendas.

### Regras de integridade atuais

- local deve pertencer ao evento atual;
- local deve estar ativo;
- caixa deve estar aberto (turno de caixa ativo) para realizar vendas;
- vendas são vinculadas a um turno de caixa (`pos_turnocaixa`);
- a criação de venda não gera lançamentos financeiros individuais;
- o fechamento do caixa consolida os valores totais de venda do turno por forma de pagamento, criando os respectivos lançamentos financeiros contendo o PDF do relatório oficial de fechamento como anexo;
- vendas pertencentes a turnos já fechados são bloqueadas contra exclusão ou alteração;
- produtos inativos ou de outro local não podem entrar na venda;
- itens duplicados na mesma venda são rejeitados;
- desconto precisa respeitar permissão e limite configurado;
- pagamentos mistos precisam respeitar permissão do local;
- venda baixa subestoque do local;
- transferência para local gera saída no estoque central e registro próprio no POS;
- entrada direta em estoque local foi descontinuada para preservar integridade.

### Melhorias futuras recomendadas

- cancelamento e estorno de venda;
- sangria e suprimento de caixa;
- catálogo de serviços sem estoque para secretaria;

## Administração

### Objetivo

Permitir governança mínima sem depender de manipulação direta do banco.

### Capacidades atuais

- telas administrativas básicas no frontend;
- gestão de eventos;
- configuração e permissões em nível funcional.

### Melhorias futuras recomendadas

- trilha de auditoria navegável;
- gestão mais clara de grupos e scopes;
- parametrização por unidade/centro de custo.
