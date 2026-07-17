from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import Evento


class LoginForm(AuthenticationForm):
    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request=request, *args, **kwargs)
        self.fields["username"].widget.attrs["class"] = "form-control"
        self.fields["password"].widget.attrs["class"] = "form-control"


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = [
            "nome",
            "data_inicio",
            "data_fim",
            "status",
            "ativo",
            "fechado",
            "centro_custo",
            "taxa_base",
            "taxa_trabalhador",
            "adicional_chale",
            "prev_participantes",
            "prev_trabalhadores",
            "responsavel_geral",
            "observacoes",
        ]
        widgets = {
            "data_inicio": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "data_fim": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"ativo", "fechado"}:
                field.widget = forms.CheckboxInput()
                field.widget.attrs["class"] = "form-check-input"
            elif name in {"status", "responsavel_geral", "centro_custo"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"
