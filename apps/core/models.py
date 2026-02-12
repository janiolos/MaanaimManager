from django.conf import settings
from django.db import models


class CentroCusto(models.Model):
    nome = models.CharField(max_length=120, unique=True)
    codigo = models.CharField(max_length=30, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Centro de custo"
        verbose_name_plural = "Centros de custo"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Evento(models.Model):
    PLANEJADO = "PLANEJADO"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    ENCERRADO = "ENCERRADO"
    STATUS_CHOICES = [
        (PLANEJADO, "Planejado"),
        (EM_ANDAMENTO, "Em andamento"),
        (ENCERRADO, "Encerrado"),
    ]

    nome = models.CharField(max_length=255)
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField()
    ativo = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PLANEJADO)
    fechado = models.BooleanField(default=False)
    taxa_base = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)
    taxa_trabalhador = models.DecimalField(max_digits=10, decimal_places=2, default=25.00)
    adicional_chale = models.DecimalField(max_digits=10, decimal_places=2, default=100.00)
    prev_participantes = models.PositiveIntegerField(null=True, blank=True)
    prev_trabalhadores = models.PositiveIntegerField(null=True, blank=True)
    responsavel_geral = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos_responsavel",
    )
    observacoes = models.TextField(blank=True)
    centro_custo = models.ForeignKey(
        CentroCusto,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="eventos",
    )

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-data_inicio"]

    def __str__(self):
        return self.nome


class AuditLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    method = models.CharField(max_length=10)
    path = models.CharField(max_length=2048)
    view_name = models.CharField(max_length=255, blank=True)
    status_code = models.PositiveSmallIntegerField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log de auditoria"
        verbose_name_plural = "Logs de auditoria"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.method} {self.path} ({self.status_code})"


class ConfiguracaoSistema(models.Model):
    nome_sistema = models.CharField(max_length=80, default="Eventa")
    rotulo_evento_singular = models.CharField(max_length=40, default="Evento")
    rotulo_evento_plural = models.CharField(max_length=40, default="Eventos")
    modulo_financeiro_ativo = models.BooleanField(default=True)
    modulo_estoque_ativo = models.BooleanField(default=True)
    modulo_hospedagem_ativo = models.BooleanField(default=True)
    modulo_notificacoes_ativo = models.BooleanField(default=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuracao do sistema"
        verbose_name_plural = "Configuracoes do sistema"

    def __str__(self):
        return "Configuracao geral"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
