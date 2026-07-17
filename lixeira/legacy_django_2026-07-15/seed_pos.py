from django.contrib.auth.models import User
from apps.inventory.models import Produto
from decimal import Decimal

# Helper to load standard categories/units
produtos_iniciais = [
    {"nome": "Coletânea Comum", "sku": "COL-COM-01", "preco": 20.00, "estoque": 176},
    {"nome": "Coletânea CIA's", "sku": "COL-CIA-01", "preco": 10.00, "estoque": 16},
    {"nome": "Coletânea Nível II", "sku": "COL-NV2-01", "preco": 30.00, "estoque": 37},
    {"nome": "Coletânea Louvores Avulsos", "sku": "COL-LVA-01", "preco": 75.00, "estoque": 10},
    {"nome": "Coletânea Nível I", "sku": "COL-NV1-01", "preco": 30.00, "estoque": 0},
    {"nome": "Inscrição Seminarista", "sku": "INS-SEM-01", "preco": 75.00, "estoque": 10},
    {"nome": "Inscrição Voluntários (Meia)", "sku": "INS-VOL-01", "preco": 25.00, "estoque": 9},
    {"nome": "Inscrição Voluntário (Inteira)", "sku": "INS-VOL-02", "preco": 45.00, "estoque": 9},
    {"nome": "Impressão Crachá", "sku": "CRACHA-01", "preco": 5.00, "estoque": 9},
]

for p_data in produtos_iniciais:
    # Use get_or_create to avoid dupes
    prod, created = Produto.objects.get_or_create(
        sku=p_data["sku"],
        defaults={
            "nome": p_data["nome"],
            "categoria": Produto.CATEGORIA_PRODUTO_ACABADO,
            "custo_medio_atual": Decimal(str(p_data["preco"] / 2)), # Fake custo
            "estoque_atual": Decimal("0.00")
        }
    )
    if created or prod.estoque_atual == 0:
        # Give it stock if new
        prod.registrar_entrada(p_data["estoque"] or 1, p_data["preco"] / 2)
        prod.save()
        # Mocking the price on custo_medio_atual to show up properly since MVP has only 1 price field
        prod.custo_medio_atual = p_data["preco"] 
        prod.save()

print("Produtos semeados com sucesso!")
