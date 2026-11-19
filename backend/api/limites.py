"""Limite diário por usuário (tarefa #25).

A cota gratuita da SerpApi é de 250 buscas por mês, e cada simulação gasta 3 ou
4. Por isso cada pessoa pode fazer LIMITE_SIMULACOES_DIA simulações por dia
(padrão 5, configurável no .env). O dia vira à meia-noite de Brasília
(TIME_ZONE do settings). Contas da equipe (is_staff) não têm limite, para a
demonstração não travar.

As sugestões de lugar (GET /api/lugares/) também gastam busca quando não estão
no cache, então têm um limite próprio, LIMITE_LUGARES_DIA (padrão 60).
"""

from django.conf import settings
from django.utils import timezone

from .models import Simulacao
from .servicos import cache


def sem_limite(usuario):
    return usuario.is_staff


def situacao_simulacoes(usuario):
    """{"limite", "usadas_hoje", "restantes"}. limite e restantes são None para a equipe."""
    usadas = Simulacao.objects.filter(
        usuario=usuario, criado_em__date=timezone.localdate()
    ).count()
    if sem_limite(usuario):
        return {"limite": None, "usadas_hoje": usadas, "restantes": None}
    limite = settings.LIMITE_SIMULACOES_DIA
    return {"limite": limite, "usadas_hoje": usadas, "restantes": max(limite - usadas, 0)}


def pode_simular(usuario):
    situacao = situacao_simulacoes(usuario)
    return situacao["restantes"] is None or situacao["restantes"] > 0, situacao


def _chave_lugares(usuario):
    return f"limite-lugares:{usuario.pk}:{timezone.localdate().isoformat()}"


def registrar_busca_de_lugar(usuario):
    """Conta 1 busca de lugar. Devolve False se o usuário já passou do limite do dia.

    O contador fica no cache do Django e expira em 24 horas.
    """
    if sem_limite(usuario):
        return True
    chave = _chave_lugares(usuario)
    usadas = cache.obter(chave) or 0
    if usadas >= settings.LIMITE_LUGARES_DIA:
        return False
    cache.guardar(chave, usadas + 1)
    return True
