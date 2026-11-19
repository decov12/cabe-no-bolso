"""Orquestrador da simulação: junta SerpApi, Gemini, veredito e alternativas.

Usado pela rota POST /api/simulacoes/ (tarefa #16, api/views.py).
Veja docs/servicos-ia.md.
"""

import calendar
import math
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from . import gemini, serpapi
from .alternativas import NOTA_MINIMA_HOTEL_SIMPLES, gerar_alternativas
from .erros import ErroEntrada
from .veredito import arredondar, calcular_diferenca, decidir_veredito, somar_gastos

# Limites de entrada
MAXIMO_NOITES = 30
MAXIMO_PESSOAS = 9  # o Google Voos aceita até 9 passageiros
MAXIMO_INTERESSES = 10

# Janela do calendário de preços: 2 meses antes do mês da ida (sem passar de
# amanhã) e 6 meses no total. Uma busca de até 6 meses conta como 1 busca.
MESES_ANTES_DA_IDA = 2
MESES_NA_JANELA = 6

# Hotel "padrão" da simulação: o mais barato com pelo menos 3 estrelas e nota 4.
# Assim a alternativa "hotel mais simples" (nota >= 3,5) ainda tem o que oferecer.
ESTRELAS_HOTEL_PADRAO = 3
NOTA_HOTEL_PADRAO = 4.0

_CODIGO_AEROPORTO = re.compile(r"^[A-Z]{3}$")


# ---------------------------------------------------------------------------
# Validação
# ---------------------------------------------------------------------------

def _validar_codigo(codigo, nome_campo):
    if not isinstance(codigo, str) or not _CODIGO_AEROPORTO.match(codigo.strip().upper()):
        raise ErroEntrada(f"Informe o código do aeroporto de {nome_campo} com 3 letras (ex.: GRU).")
    return codigo.strip().upper()


def _validar_data(valor, nome_campo):
    if isinstance(valor, datetime):
        return valor.date()
    if not isinstance(valor, date):
        raise ErroEntrada(f"Data de {nome_campo} inválida.")
    return valor


def validar_entradas(origem, destino, data_ida, data_volta, orcamento, pessoas, interesses):
    """Confere e normaliza as entradas. Levanta ErroEntrada com mensagem clara."""
    origem = _validar_codigo(origem, "origem")
    destino = _validar_codigo(destino, "destino")
    if origem == destino:
        raise ErroEntrada("A origem e o destino precisam ser diferentes.")

    data_ida = _validar_data(data_ida, "ida")
    data_volta = _validar_data(data_volta, "volta")
    if data_ida < timezone.localdate():
        raise ErroEntrada("A data de ida não pode estar no passado.")
    if data_volta <= data_ida:
        raise ErroEntrada("A data de volta precisa ser depois da data de ida.")
    if (data_volta - data_ida).days > MAXIMO_NOITES:
        raise ErroEntrada(f"A viagem pode ter no máximo {MAXIMO_NOITES} noites.")

    if isinstance(orcamento, bool):
        raise ErroEntrada("Orçamento inválido.")
    try:
        orcamento = Decimal(str(orcamento))
    except (InvalidOperation, ValueError):
        raise ErroEntrada("Orçamento inválido.")
    if not orcamento.is_finite() or orcamento <= 0:
        raise ErroEntrada("O orçamento precisa ser maior que zero.")
    orcamento = arredondar(orcamento)

    if isinstance(pessoas, bool) or not isinstance(pessoas, int) or pessoas < 1:
        raise ErroEntrada("O número de pessoas precisa ser pelo menos 1.")
    if pessoas > MAXIMO_PESSOAS:
        raise ErroEntrada(f"O número de pessoas pode ser no máximo {MAXIMO_PESSOAS}.")

    if interesses is None:
        interesses = []
    if not isinstance(interesses, (list, tuple)) or not all(isinstance(i, str) for i in interesses):
        raise ErroEntrada("Os interesses precisam ser uma lista de textos.")
    interesses = [i.strip()[:50] for i in interesses if i.strip()]
    if len(interesses) > MAXIMO_INTERESSES:
        raise ErroEntrada(f"Escolha no máximo {MAXIMO_INTERESSES} interesses.")

    return origem, destino, data_ida, data_volta, orcamento, pessoas, interesses


# ---------------------------------------------------------------------------
# Auxiliares
# ---------------------------------------------------------------------------

def _somar_meses(dia, meses):
    """Primeiro dia do mês que fica `meses` depois (ou antes) do mês de `dia`."""
    indice = dia.year * 12 + (dia.month - 1) + meses
    return date(indice // 12, indice % 12 + 1, 1)


def janela_calendario(data_ida):
    """(inicio, fim) da busca de calendário para esta ida."""
    inicio = max(_somar_meses(data_ida, -MESES_ANTES_DA_IDA), timezone.localdate() + timedelta(days=1))
    ultimo_mes = _somar_meses(inicio, MESES_NA_JANELA - 1)
    fim = ultimo_mes.replace(day=calendar.monthrange(ultimo_mes.year, ultimo_mes.month)[1])
    return inicio, fim


def calcular_quartos(pessoas):
    """O preço do hotel é de 1 quarto para 2 adultos."""
    return math.ceil(pessoas / 2)


def escolher_hotel(hoteis):
    """Hotel usado na simulação (a lista já vem ordenada por preço).

    1. o mais barato com >= ESTRELAS_HOTEL_PADRAO estrelas e nota >= NOTA_HOTEL_PADRAO;
    2. senão, o mais barato com nota >= NOTA_MINIMA_HOTEL_SIMPLES;
    3. senão, o mais barato.
    """
    for hotel in hoteis:
        if (hotel["estrelas"] or 0) >= ESTRELAS_HOTEL_PADRAO and (hotel["nota"] or 0) >= NOTA_HOTEL_PADRAO:
            return hotel
    for hotel in hoteis:
        if (hotel["nota"] or 0) >= NOTA_MINIMA_HOTEL_SIMPLES:
            return hotel
    return hoteis[0]


# ---------------------------------------------------------------------------
# simular()
# ---------------------------------------------------------------------------

def simular(origem, destino, data_ida, data_volta, orcamento, pessoas, interesses,
            versao_prompt=gemini.VERSAO_PADRAO):
    """Simula a viagem e diz se cabe no orçamento.

    Gasta 3 buscas da SerpApi (voos, hotéis, calendário), mais 1 se o código do
    destino não estiver em serpapi.CIDADES_POR_AEROPORTO, e 1 chamada ao Gemini.
    O Gemini é chamado primeiro: se ele falhar, nenhuma busca da SerpApi é gasta.

    Levanta ErroEntrada ou ErroServicoExterno (api.servicos.erros).
    """
    origem, destino, data_ida, data_volta, orcamento, pessoas, interesses = validar_entradas(
        origem, destino, data_ida, data_volta, orcamento, pessoas, interesses
    )
    noites = (data_volta - data_ida).days
    quartos = calcular_quartos(pessoas)

    cidade, buscas = serpapi.cidade_do_aeroporto(destino)

    estimativa = gemini.estimar_gastos_locais(
        f"{cidade} ({destino})", data_ida, data_volta, pessoas, interesses, versao_prompt
    )

    voo = serpapi.buscar_voos(origem, destino, data_ida, data_volta)
    buscas += 1

    hoteis = serpapi.buscar_hoteis(cidade, data_ida, data_volta)
    buscas += 1
    if not hoteis:
        raise ErroEntrada(f"Não encontramos hotéis em {cidade} nessas datas.")

    inicio, fim = janela_calendario(data_ida)
    precos_por_mes = serpapi.buscar_calendario(origem, destino, inicio, fim)
    buscas += 1

    hotel = escolher_hotel(hoteis)
    passagem_total = arredondar(voo["preco_por_pessoa"] * pessoas)
    hotel_total = arredondar(hotel["preco_noite"] * noites * quartos)

    gastos = [
        {"categoria": "passagem", "valor": passagem_total, "estimativa_ia": False},
        {"categoria": "hotel", "valor": hotel_total, "estimativa_ia": False},
    ] + [
        {"categoria": categoria, "valor": estimativa["totais"][categoria], "estimativa_ia": True}
        for categoria in gemini.CATEGORIAS
    ]

    total = somar_gastos(gastos)
    veredito = decidir_veredito(total, orcamento)

    alternativas = gerar_alternativas({
        "orcamento": orcamento,
        "total": total,
        "veredito": veredito,
        "pessoas": pessoas,
        "quartos": quartos,
        "noites": noites,
        "data_ida": data_ida,
        "passagem_por_pessoa": voo["preco_por_pessoa"],
        "hotel": hotel,
        "hoteis": hoteis,
        "gastos_diarios": somar_gastos(estimativa["totais"].values()),
        "precos_por_mes": precos_por_mes,
    })

    return {
        "cidade_destino": cidade,
        "veredito": veredito,
        "orcamento": orcamento,
        "total_estimado": total,
        "diferenca": calcular_diferenca(total, orcamento),
        "noites": noites,
        "gastos": gastos,
        "passagem": {
            "companhia": voo["companhia"],
            "preco_por_pessoa": voo["preco_por_pessoa"],
            "preco_total": passagem_total,
            "link_google_voos": voo["link_google_voos"],
        },
        "hotel": {
            "nome": hotel["nome"],
            "estrelas": hotel["estrelas"],
            "nota": hotel["nota"],
            "preco_noite": hotel["preco_noite"],
            "preco_total": hotel_total,
            "link": hotel["link"],
        },
        "precos_por_mes": precos_por_mes,
        "alternativas": alternativas,
        # Para a tela explicar de onde vêm comida, passeios e transporte.
        "estimativa_ia": {
            "por_pessoa_dia": estimativa["por_pessoa_dia"],
            "justificativas": estimativa["justificativas"],
        },
        "buscas_serpapi": buscas,
        "versao_prompt": estimativa["versao_prompt"],
    }
