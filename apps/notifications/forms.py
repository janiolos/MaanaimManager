from django import forms
from .models import ReminderConfig


class ReminderConfigForm(forms.ModelForm):
    data_hora_envio = forms.DateTimeField(
        label='Quando enviar?',
        required=True,
        input_formats=['%Y-%m-%dT%H:%M'],
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            },
            format='%Y-%m-%dT%H:%M',
        ),
        error_messages={
            'required': 'Por favor, informe data e hora de envio.',
        }
    )

    # Campo de telefone com label melhorado
    telefone = forms.CharField(
        label='Número do WhatsApp',
        required=True,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+55xxxxxxxxxx',
            'pattern': r'\+?55\d{9,}',
            'title': 'Formato: +55xxxxxxxxxx',
        }),
        error_messages={
            'required': 'Por favor, digite o número do WhatsApp.',
            'max_length': 'Número de telefone muito longo.',
        }
    )

    class Meta:
        model = ReminderConfig
        fields = ['data_hora_envio', 'telefone', 'mensagem', 'midia', 'midia_url', 'ativo']
        widgets = {
            'mensagem': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': (
                    "Exemplo:\\n"
                    "🔔 Lembrete do {evento_nome}\\n"
                    "Data: {data_evento}\\n"
                    "Intervalo: {intervalo}"
                ),
            }),
            'midia_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://seu-dominio.com/imagem-ou-figurinha.webp',
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'mensagem': 'Mensagem do WhatsApp',
            'midia': 'Arquivo de mídia (opcional)',
            'midia_url': 'URL de mídia (opcional)',
            'ativo': 'Ativo (O lembrete será enviado automaticamente)',
        }

    def clean_data_hora_envio(self):
        data_hora_envio = self.cleaned_data.get('data_hora_envio')
        if not data_hora_envio:
            raise forms.ValidationError('Informe a data e hora de envio.')
        return data_hora_envio

    def clean_telefone(self):
        """Validar e formatar o número de telefone"""
        telefone = self.cleaned_data.get('telefone', '').strip()

        if not telefone:
            raise forms.ValidationError('O número do WhatsApp é obrigatório.')

        # Remover caracteres especiais
        telefone_limpo = ''.join(filter(str.isdigit, telefone))

        # Validar se tem pelo menos 10 dígitos (sem 55) ou 12 (com 55)
        if len(telefone_limpo) < 10:
            raise forms.ValidationError(
                'Telefone inválido! Deve ter pelo menos 10 dígitos. '
                'Use o formato: +55xxxxxxxxxx ou apenas xxxxxxxxxx'
            )

        if len(telefone_limpo) > 13:
            raise forms.ValidationError(
                'Número de telefone inválido (muito longo).')

        # Adicionar +55 se não tiver
        if not telefone.startswith('+'):
            if telefone.startswith('55') and len(telefone_limpo) == 12:
                telefone = '+' + telefone_limpo
            elif not telefone.startswith('55'):
                # Se começar com 0, remover
                if telefone.startswith('0'):
                    telefone_limpo = telefone_limpo[1:]
                telefone = '+55' + telefone_limpo[-10:]
            else:
                telefone = '+' + telefone_limpo

        return telefone

    def clean_mensagem(self):
        mensagem = self.cleaned_data.get('mensagem', '')
        if mensagem and len(mensagem) > 1500:
            raise forms.ValidationError('Mensagem muito longa. Limite de 1500 caracteres.')
        return mensagem
