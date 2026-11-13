"""Alternativas automáticas para a viagem caber (tarefa #22).

Todas são calculadas com dados já buscados: nenhuma gasta busca extra na
SerpApi nem chamada extra ao Gemini. Só entram as que reduzem o total.

Recebem um "contexto" montado por simulacao.simular():
{
  "orcamento": Decimal, "total": Decimal, "veredito": str,
  "pessoas": int, "quartos": int, "noites": int, "data_ida": date,
  "passagem_por_pessoa": Decimal, "hotel": {"nome", "preco_noite", ...},
  "hoteis": [lista de buscar_hoteis], "gastos_diarios": Decimal (comida+passeios+transporte),
  "precos_por_mes": [{"mes", "menor_preco"}],
}
"""

from datetime import timedelta

from .veredito import CABE, arredondar, decidir_veredito

# Mínimo de noites que a alternativa "menos noites" aceita.
MINIMO_NOITES = 2

# Nota mínima (0 a 5) para um hotel entrar na alternativa "hotel mais simples".
NOTA_MINIMA_HOTEL_SIMPLES = 3.5

NOMES_MESES = (
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
)


def formatar_reais(valor):
    """Decimal('1234.5') -> 'R$ 1.234,50'."""
    texto = f"{arredondar(valor):,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def nome_do_mes(mes):
    """'2027-03' -> 'março de 2027'."""
    ano, numero = mes.split("-")
    return f"{NOMES_MESES[int(numero) - 1]} de {ano}"


def _alternativa(tipo, descricao, novo_total, contexto):
    novo_total = arredondar(novo_total)
    return {
        "tipo": tipo,
        "descricao": descricao,
        "novo_total": novo_total,
        "novo_veredito": decidir_veredito(novo_total, contexto["orcamento"]),
        "economia": arredondar(contexto["total"] - novo_total),
    }


def alternativa_outro_mes(contexto):
    """Viajar no mês mais barato do calendário já buscado.

    Troca só a passagem: o calendário do Google considera viagens de 7 noites,
    e hotel e gastos diários continuam com a estimativa atual.
    """
    mes_atual = contexto["data_ida"].strftime("%Y-%m")
    passagem_atual = contexto["passagem_por_pessoa"]
    candidatos = [
        item for item in contexto["precos_por_mes"]
        if item["mes"] != mes_atual and item["menor_preco"] < passagem_atual
    ]
    if not candidatos:
        return None
    melhor = min(candidatos, key=lambda item: item["menor_preco"])
    pessoas = contexto["pessoas"]
    novo_total = contexto["total"] - passagem_atual * pessoas + melhor["menor_preco"] * pessoas
    descricao = (
        f"Viajar em {nome_do_mes(melhor['mes'])}: passagem a partir de "
        f"{formatar_reais(melhor['menor_preco'])} por pessoa, ida e volta. "
        "O calendário do Google considera viagens de 7 noites; hotel e gastos "
        "diários mantidos como na estimativa atual."
    )
    return _alternativa("outro_mes", descricao, novo_total, contexto)


def alternativa_menos_noites(contexto):
    """Tira 1 noite por vez (mínimo MINIMO_NOITES) até caber ou chegar ao mínimo.

    Hotel e gastos diários são recalculados proporcionalmente às noites, sem
    nova busca. A passagem não muda.
    """
    noites = contexto["noites"]
    if noites <= MINIMO_NOITES:
        return None

    hotel_por_noite = contexto["hotel"]["preco_noite"] * contexto["quartos"]
    diarios_por_noite = contexto["gastos_diarios"] / noites
    custo_fixo = contexto["total"] - hotel_por_noite * noites - contexto["gastos_diarios"]

    novas_noites = noites
    novo_total = contexto["total"]
    while novas_noites > MINIMO_NOITES:
        novas_noites -= 1
        novo_total = custo_fixo + (hotel_por_noite + diarios_por_noite) * novas_noites
        if decidir_veredito(novo_total, contexto["orcamento"]) == CABE:
            break

    nova_volta = contexto["data_ida"] + timedelta(days=novas_noites)
    descricao = (
        f"Ficar {novas_noites} noites em vez de {noites} (voltar em "
        f"{nova_volta.strftime('%d/%m/%Y')}). Hotel e gastos diários recalculados "
        "proporcionalmente; o preço da passagem pode mudar com a nova data."
    )
    return _alternativa("menos_noites", descricao, novo_total, contexto)


def alternativa_hotel_mais_simples(contexto):
    """O hotel mais barato da lista já buscada com nota >= NOTA_MINIMA_HOTEL_SIMPLES."""
    atual = contexto["hotel"]
    candidatos = [
        hotel for hotel in contexto["hoteis"]
        if hotel["nota"] is not None
        and hotel["nota"] >= NOTA_MINIMA_HOTEL_SIMPLES
        and hotel["preco_noite"] < atual["preco_noite"]
    ]
    if not candidatos:
        return None
    novo = min(candidatos, key=lambda hotel: hotel["preco_noite"])
    multiplicador = contexto["noites"] * contexto["quartos"]
    novo_total = contexto["total"] - (atual["preco_noite"] - novo["preco_noite"]) * multiplicador
    estrelas = f"{novo['estrelas']} estrelas, " if novo.get("estrelas") else ""
    descricao = (
        f"Ficar no {novo['nome']} ({estrelas}nota {novo['nota']}) por "
        f"{formatar_reais(novo['preco_noite'])} a noite, em vez de "
        f"{formatar_reais(atual['preco_noite'])}."
    )
    return _alternativa("hotel_mais_simples", descricao, novo_total, contexto)


def gerar_alternativas(contexto):
    """Lista de alternativas que reduzem o total. Vazia se a viagem já cabe."""
    if contexto["veredito"] == CABE:
        return []
    alternativas = []
    for funcao in (alternativa_outro_mes, alternativa_menos_noites, alternativa_hotel_mais_simples):
        alternativa = funcao(contexto)
        if alternativa and alternativa["economia"] > 0:
            alternativas.append(alternativa)
    return alternativas
