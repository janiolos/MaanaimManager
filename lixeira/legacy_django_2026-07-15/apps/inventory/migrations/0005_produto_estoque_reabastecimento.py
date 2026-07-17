# Generated manually for restock alert threshold

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0004_aprovacao_cotacao_ordem_compra"),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="estoque_reabastecimento",
            field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12),
        ),
    ]
