from decimal import Decimal
from django import template

register = template.Library()


@register.filter
def brl(value):
    if value is None:
        return "R$ 0,00"
    try:
        quantized = Decimal(value).quantize(Decimal("0.01"))
    except Exception:
        return value
    parts = f"{quantized:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {parts}"
