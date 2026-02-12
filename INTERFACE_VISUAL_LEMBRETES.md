# Interface Visual de Lembretes

## Tela de listagem (`templates/notifications/lembretes_lista.html`)
- Cards de resumo:
  - total de lembretes
  - ativos
  - enviados
- Tabela com:
  - evento
  - data/hora de envio
  - telefone
  - status
  - acoes (editar, resetar, excluir)

## Tela de formulario (`templates/notifications/lembrete_form.html`)
- Campo `Quando enviar?` com seletor de data/hora (`datetime-local`)
- Campo de telefone com validacao
- Textarea de mensagem personalizada
- Upload de midia e campo URL de midia
- Checkbox de ativo

## Regras de UX aplicadas
- Formularios com mensagens de erro por campo
- Labels explicitos
- Botoes de acao padronizados
- Fluxo simples: lista -> criar/editar -> voltar para lista

## Acessos
- Leitura: usuarios com permissao de leitura de notificacoes
- Escrita: usuarios com permissao de escrita de notificacoes
