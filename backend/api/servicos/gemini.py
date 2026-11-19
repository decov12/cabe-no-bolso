"""Estimativa de comida, passeios e transporte local com o Gemini (tarefa #14).

A IA só estima valores POR PESSOA POR DIA. Quem valida, multiplica por dias e
pessoas e soma é o código. Os testes nunca chamam o Gemini de verdade.

Forma da chamada conferida na documentação oficial em 13/11/2026
(ai.google.dev/gemini-api/docs/structured-output, que redireciona para
aistudio.google.com/docs/structured-output) e no SDK google-genai 3.3:
client.interactions.create(..., response_format={"type": "text",
"mime_type": "application/json", "schema": {...}}) e o texto em output_text.

Modelo padrão: gemini-3.5-flash-lite, estável, no nível gratuito e indicado
pela página de modelos para projetos novos. Troque com a variável GEMINI_MODEL.
"""

import json
import time

from django.conf import settings
from google import genai

from . import cache
from .erros import ErroEntrada, ErroServicoExterno
from .veredito import arredondar

MODELO_PADRAO = "gemini-3.5-flash-lite"
TIMEOUT_SEGUNDOS = 30
PAUSA_NOVA_TENTATIVA = 1

CATEGORIAS = ("comida", "passeios", "transporte")

# Faixa plausível de cada valor, em BRL por pessoa por dia. Fora dela a resposta
# é tratada como inválida. Passeios e transporte podem ser 0 (cidade pequena,
# tudo a pé, interesses gratuitos); comida não.
FAIXAS_PLAUSIVEIS = {
    "comida": (15, 2000),
    "passeios": (0, 3000),
    "transporte": (0, 1500),
}

TAMANHO_MAXIMO_JUSTIFICATIVA = 300

_CATEGORIA_SCHEMA = {
    "type": "object",
    "properties": {
        "valor_por_pessoa_dia": {
            "type": "number",
            "description": "Valor em reais (BRL) por pessoa por dia.",
        },
        "justificativa": {
            "type": "string",
            "description": "Uma frase curta explicando o valor.",
        },
    },
    "required": ["valor_por_pessoa_dia", "justificativa"],
}

SCHEMA_RESPOSTA = {
    "type": "object",
    "properties": {categoria: _CATEGORIA_SCHEMA for categoria in CATEGORIAS},
    "required": list(CATEGORIAS),
}

_INSTRUCOES_COMUNS = """
Responda só com o JSON pedido, com valores POR PESSOA POR DIA, em reais (BRL):
- comida: café da manhã, almoço, jantar e lanches;
- passeios: ingressos, tours e atrações ligadas aos interesses (0 se forem gratuitos);
- transporte: transporte local na cidade (metrô, ônibus, aplicativo). NÃO inclua a
  passagem aérea nem o trajeto do aeroporto além do razoável diluído nos dias.
Para cada um, escreva uma justificativa curta (uma frase).
NÃO some valores, NÃO multiplique por dias ou pessoas e NÃO inclua hotel."""

PROMPTS = {
    # v1: pedido direto, perfil de viajante econômico-médio.
    "v1": """Você estima custos de viagem para brasileiros.
Viagem: destino {destino}, de {data_ida} a {data_volta} ({noites} noites), {pessoas} pessoa(s).
Interesses: {interesses}.
Considere um viajante de orçamento médio, que come em restaurantes simples e usa
transporte público.""" + _INSTRUCOES_COMUNS,

    # v2: mesma tarefa, mas pede para considerar a estação do ano e o custo de
    # vida local e para pensar em faixas antes de escolher o valor (tarefa #30).
    "v2": """Você estima custos de viagem para brasileiros.
Viagem: destino {destino}, de {data_ida} a {data_volta} ({noites} noites), {pessoas} pessoa(s).
Interesses: {interesses}.
Antes de responder, considere:
1. a estação do ano no destino nessas datas (alta ou baixa temporada, clima, feriados);
2. o custo de vida local comparado ao do Brasil e a cotação atual da moeda local em reais;
3. para cada categoria, uma faixa de preço (econômica, média e confortável) para esse destino.
Devolva o valor do MEIO da faixa média e cite a faixa na justificativa
(ex.: "faixa média de R$ 120 a R$ 180").""" + _INSTRUCOES_COMUNS,
}

VERSAO_PADRAO = "v1"


class RespostaInvalida(ValueError):
    """A resposta do Gemini não passou na validação."""


def modelo_configurado():
    return getattr(settings, "GEMINI_MODEL", "") or MODELO_PADRAO


def montar_prompt(destino, data_ida, data_volta, pessoas, interesses, versao_prompt=VERSAO_PADRAO):
    if versao_prompt not in PROMPTS:
        raise ErroEntrada(f"Versão de prompt desconhecida: {versao_prompt}.")
    return PROMPTS[versao_prompt].format(
        destino=destino,
        data_ida=data_ida.strftime("%d/%m/%Y"),
        data_volta=data_volta.strftime("%d/%m/%Y"),
        noites=(data_volta - data_ida).days,
        pessoas=pessoas,
        interesses=", ".join(interesses) if interesses else "nenhum em especial",
    )


def _chamar_modelo(texto):
    """Uma chamada ao Gemini. Devolve o texto (JSON) da resposta."""
    cliente = genai.Client(api_key=settings.GEMINI_API_KEY)
    interacao = cliente.interactions.create(
        model=modelo_configurado(),
        input=texto,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": SCHEMA_RESPOSTA,
        },
        store=False,
        timeout=TIMEOUT_SEGUNDOS,
    )
    return interacao.output_text


def validar_resposta(texto):
    """Confere o JSON do Gemini e devolve (valores, justificativas).

    valores: {categoria: Decimal por pessoa por dia}. Levanta RespostaInvalida.
    """
    try:
        dados = json.loads(texto or "")
    except (TypeError, ValueError):
        raise RespostaInvalida("a resposta não é um JSON válido")
    if not isinstance(dados, dict):
        raise RespostaInvalida("a resposta não é um objeto JSON")

    valores, justificativas = {}, {}
    for categoria in CATEGORIAS:
        item = dados.get(categoria)
        if not isinstance(item, dict):
            raise RespostaInvalida(f"falta a categoria {categoria}")
        valor = item.get("valor_por_pessoa_dia")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor != valor:
            raise RespostaInvalida(f"valor de {categoria} não é número")
        minimo, maximo = FAIXAS_PLAUSIVEIS[categoria]
        if not minimo <= valor <= maximo:
            raise RespostaInvalida(f"valor de {categoria} fora da faixa plausível")
        justificativa = item.get("justificativa")
        if not isinstance(justificativa, str) or not justificativa.strip():
            raise RespostaInvalida(f"falta a justificativa de {categoria}")
        valores[categoria] = arredondar(valor)
        justificativas[categoria] = justificativa.strip()[:TAMANHO_MAXIMO_JUSTIFICATIVA]
    return valores, justificativas


def estimar_gastos_locais(destino, data_ida, data_volta, pessoas, interesses, versao_prompt=VERSAO_PADRAO):
    """Estima comida, passeios e transporte da viagem inteira.

    Dias de gasto = noites (o dia de chegada e o de partida juntos contam como 1).
    Devolve:
    {
      "versao_prompt": "v1", "modelo": str, "dias": int,
      "por_pessoa_dia": {"comida": Decimal, "passeios": Decimal, "transporte": Decimal},
      "justificativas": {categoria: str},
      "totais": {categoria: Decimal}   # por_pessoa_dia × dias × pessoas
    }
    Levanta ErroServicoExterno se o Gemini falhar ou responder algo inválido
    duas vezes seguidas.
    """
    if not settings.GEMINI_API_KEY:
        raise ErroServicoExterno("A chave do Gemini não está configurada (GEMINI_API_KEY).")

    texto = montar_prompt(destino, data_ida, data_volta, pessoas, interesses, versao_prompt)
    dias = max((data_volta - data_ida).days, 1)

    # Cache de 24 horas (#24): a mesma viagem com o mesmo prompt e modelo devolve
    # a mesma estimativa, sem nova chamada (e sem o número mudar ao repetir).
    chave_cache = cache.montar_chave("gemini", modelo_configurado(), texto)
    guardado = cache.obter(chave_cache)
    if guardado is not None:
        return guardado

    motivo = ""
    for tentativa in range(2):
        if tentativa:
            time.sleep(PAUSA_NOVA_TENTATIVA)
        try:
            resposta = _chamar_modelo(texto)
        except Exception as erro:  # erros do SDK, de rede ou de tempo esgotado
            # Só o tipo do erro: a mensagem do SDK pode trazer detalhes da requisição.
            motivo = f"falha na chamada ({type(erro).__name__})"
            continue
        try:
            valores, justificativas = validar_resposta(resposta)
        except RespostaInvalida as erro:
            motivo = str(erro)
            continue
        estimativa = {
            "versao_prompt": versao_prompt,
            "modelo": modelo_configurado(),
            "dias": dias,
            "por_pessoa_dia": valores,
            "justificativas": justificativas,
            "totais": {
                categoria: arredondar(valor * dias * pessoas)
                for categoria, valor in valores.items()
            },
        }
        cache.guardar(chave_cache, estimativa)
        return estimativa

    raise ErroServicoExterno(f"A estimativa de gastos com IA falhou: {motivo}.")
