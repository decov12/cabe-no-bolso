"""Regra do veredito (tarefa #15).

Funções puras: quem soma os custos e decide o veredito é o código, nunca a IA.
"""

from decimal import ROUND_HALF_UP, Decimal

# Até 15% acima do orçamento a viagem "cabe com ajustes".
MARGEM_AJUSTE = Decimal("0.15")

CABE = "cabe"
CABE_COM_AJUSTES = "cabe_com_ajustes"
NAO_CABE = "nao_cabe"

CENTAVO = Decimal("0.01")


def arredondar(valor):
    """Converte para Decimal e arredonda a 2 casas (meio centavo para cima)."""
    if isinstance(valor, float):
        # str() evita levar o erro binário do float para o Decimal.
        valor = str(valor)
    return Decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def somar_gastos(gastos):
    """Soma os gastos e devolve o total em Decimal com 2 casas.

    Aceita a lista no formato de simular() ([{"categoria", "valor", ...}])
    ou uma lista de valores soltos.
    """
    total = Decimal("0")
    for gasto in gastos:
        valor = gasto["valor"] if isinstance(gasto, dict) else gasto
        total += arredondar(valor)
    return arredondar(total)


def decidir_veredito(total, orcamento):
    """"cabe" se total <= orçamento; "cabe_com_ajustes" se total <= orçamento * 1,15;
    "nao_cabe" acima disso. A comparação é feita sem arredondar o limite."""
    total = arredondar(total)
    orcamento = arredondar(orcamento)
    if total <= orcamento:
        return CABE
    if total <= orcamento * (1 + MARGEM_AJUSTE):
        return CABE_COM_AJUSTES
    return NAO_CABE


def calcular_diferenca(total, orcamento):
    """Orçamento menos total. Negativo quando falta dinheiro."""
    return arredondar(arredondar(orcamento) - arredondar(total))
