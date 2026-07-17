# Guia de Lembretes WhatsApp

## Visao geral
O modulo `apps.notifications` permite criar lembretes por evento com envio automatico via Twilio.

## Campos do lembrete
- `data_hora_envio` (obrigatorio): data e hora exatas do envio
- `telefone` (obrigatorio): numero WhatsApp (normalizado para formato internacional)
- `mensagem` (opcional): template com placeholders
- `midia` (opcional): arquivo de imagem
- `midia_url` (opcional): URL publica de midia
- `ativo` (boolean)
- `enviado` (boolean controlado pelo sistema)

## Placeholders de mensagem
- `{evento_nome}`
- `{data_evento}`
- `{intervalo}`

Exemplo:
```text
Lembrete do {evento_nome}
Data: {data_evento}
Agendado para envio em: {intervalo}
```

## Como criar um lembrete
1. Selecionar evento atual
2. Acessar menu `Lembretes`
3. Clicar em `Novo lembrete`
4. Informar data/hora, telefone e (opcionalmente) mensagem/midia
5. Salvar

## Envio
- Job periodico verifica lembretes ativos e pendentes
- Quando chega o horario, envia mensagem (com ou sem midia) e marca `enviado=True`

## Reenvio
- Na listagem, use acao de reset para voltar `enviado=False`

## Variaveis de ambiente necessarias
```env
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_NUMBER=
```

## Boas praticas
- Preferir `midia_url` publica quando possivel
- Usar mensagens curtas e objetivas
- Validar numero de destino com codigo de pais
