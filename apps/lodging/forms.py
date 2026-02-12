from django import forms

from apps.finance.models import ContaCaixa
from .models import Chale, ReservaChale


class ChaleForm(forms.ModelForm):
    acessivel_cadeirante = forms.TypedChoiceField(
        choices=(("1", "Sim"), ("0", "Nao")),
        coerce=lambda value: value == "1",
        empty_value=False,
    )

    class Meta:
        model = Chale
        fields = ["codigo", "capacidade", "status", "acessivel_cadeirante", "observacoes"]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.initial["acessivel_cadeirante"] = "1" if self.instance.acessivel_cadeirante else "0"
        for name, field in self.fields.items():
            if name in {"status", "acessivel_cadeirante"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class ReservaChaleForm(forms.ModelForm):
    class Meta:
        model = ReservaChale
        fields = [
            "chale",
            "responsavel_nome",
            "qtd_pessoas",
            "qtd_criancas",
            "idades_criancas",
            "valor_adicional",
            "status",
            "pago",
            "forma_pagamento",
            "conta",
            "observacoes",
        ]
        widgets = {"observacoes": forms.Textarea(attrs={"rows": 3})}

    def __init__(self, *args, **kwargs):
        evento = kwargs.pop("evento", None)
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"chale", "status"}:
                field.widget.attrs["class"] = "form-select"
            elif name in {"forma_pagamento", "conta"}:
                field.widget.attrs["class"] = "form-select"
            elif name == "pago":
                field.widget = forms.CheckboxInput()
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"
        self.fields["valor_adicional"].widget.attrs["step"] = "0.01"
        if "conta" in self.fields:
            self.fields["conta"].queryset = ContaCaixa.objects.filter(ativo=True)
        if evento and "chale" in self.fields:
            bloqueados = ReservaChale.objects.filter(
                evento=evento,
                status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
            ).exclude(pk=self.instance.pk)
            self.fields["chale"].queryset = Chale.objects.filter(status=Chale.ATIVO).exclude(
                id__in=bloqueados.values_list("chale_id", flat=True)
            )

    def clean(self):
        cleaned_data = super().clean()
        chale = cleaned_data.get("chale")
        evento = getattr(self.instance, "evento", None)
        if chale and evento:
            exists = (
                ReservaChale.objects.filter(
                    evento=evento,
                    chale=chale,
                    status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
                )
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if exists:
                self.add_error("chale", "Este chale nao esta disponivel para reserva.")
            if chale.status != Chale.ATIVO:
                self.add_error("chale", "Somente chales disponiveis podem receber reserva.")

        qtd_pessoas = cleaned_data.get("qtd_pessoas") or 0
        qtd_criancas = cleaned_data.get("qtd_criancas") or 0
        idades_criancas = (cleaned_data.get("idades_criancas") or "").strip()
        total_hospedes = qtd_pessoas + qtd_criancas

        if chale and total_hospedes > chale.capacidade:
            self.add_error("qtd_pessoas", "Total de hospedes excede a capacidade do chale.")

        if qtd_criancas > 0 and not idades_criancas:
            self.add_error("idades_criancas", "Informe as idades das criancas.")
        if qtd_criancas == 0 and idades_criancas:
            self.add_error("qtd_criancas", "Informe quantidade de criancas maior que zero.")

        if idades_criancas:
            partes = [p.strip() for p in idades_criancas.split(",") if p.strip()]
            if any(not p.isdigit() for p in partes):
                self.add_error("idades_criancas", "Use apenas numeros separados por virgula. Ex: 5, 8")
            elif qtd_criancas > 0 and len(partes) != qtd_criancas:
                self.add_error("idades_criancas", "Quantidade de idades deve ser igual ao numero de criancas.")

        if cleaned_data.get("pago"):
            if not cleaned_data.get("forma_pagamento"):
                self.add_error("forma_pagamento", "Informe a forma de pagamento.")
            if not cleaned_data.get("conta"):
                self.add_error("conta", "Informe a conta.")
        return cleaned_data
