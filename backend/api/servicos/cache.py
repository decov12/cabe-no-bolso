"""Cache de 24 horas das respostas da SerpApi e do Gemini (tarefa #24).

Usa o cache do Django (settings.CACHES). Em desenvolvimento e produção ele fica
numa tabela do banco ("cache_respostas", criada pela migração 0002), então vale
para todos os processos do servidor e sobrevive a reinícios. Nos testes o
settings troca por um cache que não guarda nada (DummyCache).

Se o cache falhar (tabela ausente, banco fora), o site continua funcionando:
a busca é feita de verdade e só não fica guardada.
"""

import hashlib
import json
import logging

from django.core.cache import cache

DURACAO_SEGUNDOS = 24 * 60 * 60

logger = logging.getLogger(__name__)


def montar_chave(prefixo, *partes):
    """Chave curta e estável: prefixo + SHA-256 das partes em JSON ordenado.

    Ex.: montar_chave("serpapi", "google_flights", {"departure_id": "GRU", ...}).
    A ordem das chaves dos dicionários não importa.
    """
    texto = json.dumps(partes, sort_keys=True, default=str, ensure_ascii=False)
    return f"{prefixo}:{hashlib.sha256(texto.encode('utf-8')).hexdigest()}"


def obter(chave):
    """Valor guardado ou None (também None se o cache estiver com problema)."""
    try:
        return cache.get(chave)
    except Exception:  # noqa: BLE001 - o cache nunca pode derrubar a simulação
        logger.warning("Cache indisponível ao ler %s", chave, exc_info=True)
        return None


def guardar(chave, valor, duracao=DURACAO_SEGUNDOS):
    try:
        cache.set(chave, valor, duracao)
    except Exception:  # noqa: BLE001
        logger.warning("Cache indisponível ao gravar %s", chave, exc_info=True)
