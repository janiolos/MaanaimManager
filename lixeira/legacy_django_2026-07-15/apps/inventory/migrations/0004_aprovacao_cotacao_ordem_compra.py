# Generated manually for cotacao approval workflow

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finance", "0001_initial"),
        ("inventory", "0003_cotacao_fornecedores"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="cotacaocompra",
            name="aprovado_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="cotacaocompra",
            name="valor_aprovado",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=14, null=True),
        ),
        migrations.AddField(
            model_name="cotacaocompra",
            name="aprovado_por",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cotacoes_aprovadas_por",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="cotacaocompra",
            name="fornecedor_aprovado",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cotacoes_aprovadas",
                to="inventory.fornecedor",
            ),
        ),
        migrations.AddField(
            model_name="cotacaocompra",
            name="lancamento_financeiro",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="cotacoes_origem",
                to="finance.lancamentofinanceiro",
            ),
        ),
        migrations.CreateModel(
            name="OrdemCompra",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID"),
                ),
                ("numero", models.CharField(blank=True, max_length=30, unique=True)),
                ("mensagem", models.TextField()),
                ("valor_total", models.DecimalField(decimal_places=2, max_digits=14)),
                (
                    "status_envio",
                    models.CharField(
                        choices=[("PENDENTE", "Pendente"), ("ENVIADA", "Enviada"), ("FALHA", "Falha")],
                        default="PENDENTE",
                        max_length=12,
                    ),
                ),
                ("twilio_sid", models.CharField(blank=True, max_length=100)),
                ("erro_envio", models.CharField(blank=True, max_length=255)),
                ("enviada_em", models.DateTimeField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                (
                    "cotacao",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ordem_compra",
                        to="inventory.cotacaocompra",
                    ),
                ),
                (
                    "criado_por",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ordens_compra_criadas",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "fornecedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ordens_compra",
                        to="inventory.fornecedor",
                    ),
                ),
            ],
            options={"ordering": ["-id"]},
        ),
    ]
