from django.conf import settings
from django.db import models


class Simulacao(models.Model):
    """Uma simulação de viagem feita por um usuário, com o resultado de simular()."""

    VEREDITOS = [
        ("cabe", "Cabe"),
        ("cabe_com_ajustes", "Cabe com ajustes"),
        ("nao_cabe", "Não cabe"),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="simulacoes"
    )

    # O que a pessoa pediu
    origem = models.CharField(max_length=3)
    destino = models.CharField(max_length=3)
    cidade_destino = models.CharField(max_length=100, blank=True, default="")  # ex.: "Lisboa"
    data_ida = models.DateField()
    data_volta = models.DateField()
    orcamento = models.DecimalField(max_digits=12, decimal_places=2)
    pessoas = models.PositiveSmallIntegerField()
    interesses = models.JSONField(default=list, blank=True)

    # O que o código respondeu (colunas próprias para listar e filtrar sem abrir o JSON)
    veredito = models.CharField(max_length=20, choices=VEREDITOS)
    total_estimado = models.DecimalField(max_digits=12, decimal_places=2)
    diferenca = models.DecimalField(max_digits=12, decimal_places=2)
    resultado = models.JSONField()  # saída completa de simular(), com dinheiro em string

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em", "-id"]
        verbose_name = "simulação"
        verbose_name_plural = "simulações"

    def __str__(self):
        return f"{self.origem} → {self.destino} ({self.data_ida:%d/%m/%Y}) - {self.usuario}"
