from django import forms

from .models import EntradaEstoque, MovimentoEstoque, Produto


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            "nome",
            "sku",
            "unidade",
            "estoque_minimo",
            "estoque_maximo",
            "ativo",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "ativo":
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class EntradaEstoqueForm(forms.ModelForm):
    class Meta:
        model = EntradaEstoque
        fields = ["produto", "data", "quantidade", "custo_unitario", "documento", "observacao"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name == "produto":
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"


class MovimentoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentoEstoque
        fields = ["tipo", "produto", "data", "quantidade", "observacao"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in {"tipo", "produto"}:
                field.widget.attrs["class"] = "form-select"
            else:
                field.widget.attrs["class"] = "form-control"
