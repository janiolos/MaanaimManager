from django import forms
from django.forms import inlineformset_factory

from .models import (
    CotacaoCompra,
    CotacaoCompraItem,
    EntradaEstoque,
    Fornecedor,
    Produto,
    RequisicaoSaida,
    RequisicaoSaidaItem,
)
from apps.finance.models import CategoriaFinanceira, ContaCaixa, LancamentoFinanceiro


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "nome",
            "sku",
            "categoria",
            "unidade",
            "estoque_minimo",
            "estoque_reabastecimento",
            "estoque_maximo",
            "ativo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "ativo":
                field.widget.attrs["class"] = "form-check-input"
            elif name == "categoria":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class EntradaEstoqueForm(forms.ModelForm):
    class Meta:
        model = EntradaEstoque
        fields = ["produto", "data", "quantidade", "custo_unitario", "documento", "observacao"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produto"].queryset = Produto.objects.filter(ativo=True).order_by("nome")
        for name, field in self.fields.items():
            if name == "produto":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class RequisicaoSaidaForm(forms.ModelForm):
    class Meta:
        model = RequisicaoSaida
        fields = ["area", "observacao"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["area"].widget.attrs["class"] = "form-select"
        self.fields["observacao"].widget.attrs["class"] = "form-control"


class RequisicaoSaidaItemForm(forms.ModelForm):
    class Meta:
        model = RequisicaoSaidaItem
        fields = ["produto", "quantidade"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produto"].queryset = Produto.objects.filter(ativo=True).order_by("nome")
        self.fields["produto"].widget.attrs["class"] = "form-select"
        self.fields["quantidade"].widget.attrs["class"] = "form-control"


RequisicaoSaidaItemFormSet = inlineformset_factory(
    RequisicaoSaida,
    RequisicaoSaidaItem,
    form=RequisicaoSaidaItemForm,
    extra=5,
    can_delete=True,
)


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ["nome", "documento", "contato", "telefone", "email", "ativo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "ativo":
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class CotacaoCompraForm(forms.ModelForm):
    class Meta:
        model = CotacaoCompra
        fields = ["observacao"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["observacao"].widget.attrs["class"] = "form-control"


class CotacaoCompraItemForm(forms.ModelForm):
    class Meta:
        model = CotacaoCompraItem
        fields = ["produto", "quantidade"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["produto"].queryset = Produto.objects.filter(ativo=True).order_by("nome")
        self.fields["produto"].widget.attrs["class"] = "form-select"
        self.fields["quantidade"].widget.attrs["class"] = "form-control"


CotacaoCompraItemFormSet = inlineformset_factory(
    CotacaoCompra,
    CotacaoCompraItem,
    form=CotacaoCompraItemForm,
    extra=5,
    can_delete=True,
)


class CotacaoAprovacaoForm(forms.Form):
    fornecedor = forms.ModelChoiceField(queryset=Fornecedor.objects.none())
    categoria_despesa = forms.ModelChoiceField(queryset=CategoriaFinanceira.objects.none())
    conta = forms.ModelChoiceField(queryset=ContaCaixa.objects.none())
    forma_pagamento = forms.ChoiceField(choices=LancamentoFinanceiro.FORMAS_PAGAMENTO)
    data = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, **kwargs):
        fornecedores = kwargs.pop("fornecedores")
        super().__init__(*args, **kwargs)
        self.fields["fornecedor"].queryset = fornecedores
        self.fields["categoria_despesa"].queryset = CategoriaFinanceira.objects.filter(
            tipo=LancamentoFinanceiro.DESPESA
        ).order_by("nome")
        self.fields["conta"].queryset = ContaCaixa.objects.filter(ativo=True).order_by("nome")

        self.fields["fornecedor"].widget.attrs["class"] = "form-select"
        self.fields["categoria_despesa"].widget.attrs["class"] = "form-select"
        self.fields["conta"].widget.attrs["class"] = "form-select"
        self.fields["forma_pagamento"].widget.attrs["class"] = "form-select"
        self.fields["data"].widget.attrs["class"] = "form-control"
