from django import forms

from .models import LancamentoFinanceiro, AnexoLancamento, CategoriaFinanceira


class LancamentoFinanceiroForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"tipo", "categoria", "conta", "forma_pagamento"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"

        tipo = None
        if self.data.get("tipo"):
            tipo = self.data.get("tipo")
        elif self.initial.get("tipo"):
            tipo = self.initial.get("tipo")
        elif self.instance and self.instance.pk:
            tipo = self.instance.tipo

        if tipo in {LancamentoFinanceiro.RECEITA, LancamentoFinanceiro.DESPESA}:
            self.fields["categoria"].queryset = CategoriaFinanceira.objects.filter(tipo=tipo)

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        categoria = cleaned_data.get("categoria")
        if tipo and categoria and categoria.tipo != tipo:
            raise forms.ValidationError(
                "A categoria selecionada nao corresponde ao tipo informado."
            )
        return cleaned_data

    class Meta:
        model = LancamentoFinanceiro
        fields = [
            "tipo",
            "categoria",
            "conta",
            "data",
            "descricao",
            "valor",
            "forma_pagamento",
        ]
        widgets = {
            "data": forms.DateInput(attrs={"type": "date"}),
            "descricao": forms.TextInput(attrs={"placeholder": "Descricao"}),
            "valor": forms.NumberInput(attrs={"step": "0.01"}),
        }


class AnexoLancamentoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["arquivo"].widget.attrs["class"] = "form-control"
        self.fields["descricao"].widget.attrs["class"] = "form-control"

    class Meta:
        model = AnexoLancamento
        fields = ["arquivo", "descricao"]
