# Generated manually for cotacao multi-item with dynamic suppliers

import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_requisicao_saida_v3"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="categoria",
            field=models.CharField(
                choices=[
                    ("MATERIA_PRIMA", "Materia-Prima"),
                    ("PRODUTO_ACABADO", "Produto Acabado"),
                    ("COMPONENTE", "Componente"),
                ],
                default="MATERIA_PRIMA",
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="Fornecedor",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("nome", models.CharField(max_length=140, unique=True)),
                ("documento", models.CharField(blank=True, max_length=30)),
                ("contato", models.CharField(blank=True, max_length=120)),
                ("telefone", models.CharField(blank=True, max_length=30)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["nome"]},
        ),
        migrations.CreateModel(
            name="CotacaoCompra",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("numero", models.CharField(blank=True, max_length=30, unique=True)),
                ("data_cotacao", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("ABERTA", "Aberta"), ("FECHADA", "Fechada"), ("CANCELADA", "Cancelada")],
                        default="ABERTA",
                        max_length=12,
                    ),
                ),
                ("observacao", models.CharField(blank=True, max_length=255)),
                ("fechado_em", models.DateTimeField(blank=True, null=True)),
                (
                    "criado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cotacoes_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "evento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cotacoes_compra",
                        to="core.evento",
                    ),
                ),
                (
                    "fechado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cotacoes_fechadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="CotacaoCompraImpressao",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("impresso_em", models.DateTimeField(auto_now_add=True)),
                (
                    "via",
                    models.CharField(
                        choices=[("ORIGINAL", "Original"), ("2A_VIA", "2a via")], default="ORIGINAL", max_length=20
                    ),
                ),
                (
                    "cotacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="impressoes",
                        to="inventory.cotacaocompra",
                    ),
                ),
                (
                    "impresso_por",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["-impresso_em"]},
        ),
        migrations.CreateModel(
            name="CotacaoCompraItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "cotacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="inventory.cotacaocompra",
                    ),
                ),
                (
                    "produto",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="inventory.produto"),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.CreateModel(
            name="CotacaoCompraPreco",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("valor_unitario", models.DecimalField(decimal_places=2, max_digits=12)),
                ("valor_total", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14)),
                (
                    "cotacao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="precos",
                        to="inventory.cotacaocompra",
                    ),
                ),
                (
                    "fornecedor",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="inventory.fornecedor"),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="precos",
                        to="inventory.cotacaocompraitem",
                    ),
                ),
            ],
            options={"ordering": ["fornecedor__nome", "item__id"]},
        ),
        migrations.AlterUniqueTogether(
            name="cotacaocompraitem",
            unique_together={("cotacao", "produto")},
        ),
        migrations.AlterUniqueTogether(
            name="cotacaocomprapreco",
            unique_together={("item", "fornecedor")},
        ),
    ]
