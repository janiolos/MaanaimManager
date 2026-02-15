from django import forms
from django.db.models import Q

from apps.finance.models import ContaCaixa
from .models import AcaoChale, Chale, ReservaChale


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
    possui_necessidade_especial = forms.TypedChoiceField(
        choices=(("0", "Nao"), ("1", "Sim")),
        coerce=lambda value: value == "1",
        empty_value=False,
    )

    class Meta:
        model = ReservaChale
        fields = [
            "chale",
            "data_entrada",
            "data_saida",
            "responsavel_nome",
            "qtd_pessoas",
            "qtd_criancas",
            "idades_criancas",
            "possui_necessidade_especial",
            "detalhes_necessidade_especial",
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
        if "possui_necessidade_especial" in self.fields:
            self.initial["possui_necessidade_especial"] = (
                "1" if self.instance and self.instance.possui_necessidade_especial else "0"
            )
        for name, field in self.fields.items():
            if name in {"chale", "status", "possui_necessidade_especial"}:
                field.widget.attrs["class"] = "form-select"
            elif name in {"forma_pagamento", "conta"}:
                field.widget.attrs["class"] = "form-select"
            elif name == "pago":
                field.widget = forms.CheckboxInput()
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"
        if "data_entrada" in self.fields:
            self.fields["data_entrada"].widget = forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            )
            self.fields["data_entrada"].required = True
        if "data_saida" in self.fields:
            self.fields["data_saida"].widget = forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            )
            self.fields["data_saida"].required = True
        self.fields["valor_adicional"].widget.attrs["step"] = "0.01"
        if "conta" in self.fields:
            self.fields["conta"].queryset = ContaCaixa.objects.filter(ativo=True)
        if evento and "chale" in self.fields:
            entrada_inicial = self.initial.get("data_entrada") or getattr(self.instance, "data_entrada", None)
            saida_inicial = self.initial.get("data_saida") or getattr(self.instance, "data_saida", None)

            qs_chales = Chale.objects.filter(status=Chale.ATIVO)
            if entrada_inicial and saida_inicial:
                conflitos_reserva = ReservaChale.objects.filter(
                    evento=evento,
                    status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
                    data_entrada__lt=saida_inicial,
                    data_saida__gt=entrada_inicial,
                ).exclude(pk=self.instance.pk)

                conflitos_acao = AcaoChale.objects.filter(
                    evento=evento,
                    ativo=True,
                    data_inicio__lt=saida_inicial,
                    data_fim__gt=entrada_inicial,
                )

                qs_chales = qs_chales.exclude(
                    id__in=conflitos_reserva.values_list("chale_id", flat=True)
                ).exclude(
                    id__in=conflitos_acao.values_list("chale_id", flat=True)
                )

            if self.instance.pk and self.instance.chale_id:
                qs_chales = Chale.objects.filter(
                    Q(id=self.instance.chale_id) | Q(id__in=qs_chales.values_list("id", flat=True))
                )

            self.fields["chale"].queryset = qs_chales

    def clean(self):
        cleaned_data = super().clean()
        chale = cleaned_data.get("chale")
        evento = getattr(self.instance, "evento", None)
        data_entrada = cleaned_data.get("data_entrada")
        data_saida = cleaned_data.get("data_saida")

        if data_entrada and data_saida and data_saida <= data_entrada:
            self.add_error("data_saida", "A data de saida deve ser maior que a data de entrada.")

        if chale and evento and data_entrada and data_saida:
            exists = (
                ReservaChale.objects.filter(
                    evento=evento,
                    chale=chale,
                    status__in=[ReservaChale.PRE_RESERVA, ReservaChale.CONFIRMADA],
                    data_entrada__lt=data_saida,
                    data_saida__gt=data_entrada,
                )
                .exclude(pk=self.instance.pk)
                .exists()
            )
            if exists:
                self.add_error("chale", "Este chale nao esta disponivel para reserva.")
            if chale.status != Chale.ATIVO:
                self.add_error("chale", "Somente chales disponiveis podem receber reserva.")

            if AcaoChale.objects.filter(
                evento=evento,
                chale=chale,
                ativo=True,
                data_inicio__lt=data_saida,
                data_fim__gt=data_entrada,
            ).exists():
                self.add_error("chale", "Existe bloqueio/manutencao para o periodo informado.")

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

        possui_necessidade_especial = cleaned_data.get("possui_necessidade_especial")
        detalhes_necessidade = (cleaned_data.get("detalhes_necessidade_especial") or "").strip()
        if possui_necessidade_especial and not detalhes_necessidade:
            self.add_error(
                "detalhes_necessidade_especial",
                "Descreva a necessidade especial para suporte da equipe.",
            )

        if cleaned_data.get("pago"):
            if not cleaned_data.get("forma_pagamento"):
                self.add_error("forma_pagamento", "Informe a forma de pagamento.")
            if not cleaned_data.get("conta"):
                self.add_error("conta", "Informe a conta.")
        return cleaned_data


class AcaoChaleForm(forms.ModelForm):
    class Meta:
        model = AcaoChale
        fields = ["chale", "tipo", "titulo", "data_inicio", "data_fim", "descricao", "ativo"]
        widgets = {
            "data_inicio": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "data_fim": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "descricao": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"chale", "tipo"}:
                field.widget.attrs["class"] = "form-select"
            elif name not in {"data_inicio", "data_fim", "descricao", "ativo"}:
                field.widget.attrs["class"] = "form-control"
