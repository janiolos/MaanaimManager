# Generated manually for estoque V3

import django.db.models.deletion
from decimal import Decimal
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="produto",
            name="custo_medio_atual",
            field=models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=12),
        ),
        migrations.AddField(
            model_name="produto",
            name="valor_estoque_atual",
            field=models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=14),
        ),
        migrations.CreateModel(
            name="RequisicaoSaida",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("numero", models.CharField(blank=True, max_length=30, unique=True)),
                (
                    "area",
                    models.CharField(
                        choices=[
                            ("COZINHA", "Cozinha"),
                            ("COPA", "Copa"),
                            ("CANTINA", "Cantina"),
                            ("COPA_PASTORES", "Copa Pastores"),
                            ("SECRETARIA", "Secretaria"),
                        ],
                        max_length=80,
                    ),
                ),
                ("data_solicitacao", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("ABERTA", "Aberta"), ("FINALIZADA", "Finalizada"), ("CANCELADA", "Cancelada")],
                        default="ABERTA",
                        max_length=12,
                    ),
                ),
                ("observacao", models.CharField(blank=True, max_length=255)),
                ("protocolo", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("finalizado_em", models.DateTimeField(blank=True, null=True)),
                ("impresso_em", models.DateTimeField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "criado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requisicoes_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "evento",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requisicoes_saida",
                        to="core.evento",
                    ),
                ),
                (
                    "finalizado_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requisicoes_finalizadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "impresso_por",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requisicoes_impressas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-id"]},
        ),
        migrations.CreateModel(
            name="RequisicaoSaidaImpressao",
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
                    "impresso_por",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "requisicao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="impressoes",
                        to="inventory.requisicaosaida",
                    ),
                ),
            ],
            options={"ordering": ["-impresso_em"]},
        ),
        migrations.CreateModel(
            name="RequisicaoSaidaItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("quantidade", models.DecimalField(decimal_places=2, max_digits=12)),
                (
                    "custo_medio_unitario",
                    models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=12),
                ),
                ("custo_total", models.DecimalField(decimal_places=4, default=Decimal("0.0000"), max_digits=14)),
                ("saldo_antes", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                ("saldo_depois", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12)),
                (
                    "produto",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="inventory.produto"),
                ),
                (
                    "requisicao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="itens",
                        to="inventory.requisicaosaida",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.AlterUniqueTogether(
            name="requisicaosaidaitem",
            unique_together={("requisicao", "produto")},
        ),
    ]
