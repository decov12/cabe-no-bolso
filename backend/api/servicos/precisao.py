"""Leitura do CSV de viagens reais e cálculo de erro (tarefas #29 e #30).

Usado pelos comandos teste_precisao e comparar_prompts.

Formato do CSV (docs/teste-de-precisao/viagens.csv):
- datas em AAAA-MM-DD;
- interesses separados por ";" (ex.: "museus;praia");
- valores em reais, com ponto ou vírgula decimal (1234.56 ou 1234,56);
- gastos reais são do GRUPO inteiro, na viagem toda;
- linhas cuja "fonte" começa com "EXEMPLO" são ignoradas.
"""

import csv
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings

from .veredito import arredondar

PASTA_PRECISAO = Path(settings.BASE_DIR).parent / "docs" / "teste-de-precisao"
CSV_PADRAO = PASTA_PRECISAO / "viagens.csv"

COLUNAS = [
    "origem", "destino", "ida", "volta", "pessoas", "interesses", "orcamento",
    "gasto_real_passagem", "gasto_real_hotel", "gasto_real_comida",
    "gasto_real_passeios", "gasto_real_transporte", "fonte",
]
CATEGORIAS = ("passagem", "hotel", "comida", "passeios", "transporte")
CATEGORIAS_IA = ("comida", "passeios", "transporte")


class ErroCSV(ValueError):
    """Problema no arquivo de viagens."""


def ler_valor(texto):
    """'1.234,56', '1234,56' ou '1234.56' -> Decimal. Vazio -> None."""
    texto = (texto or "").strip().replace("R$", "").replace(" ", "")
    if not texto:
        return None
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    try:
        return arredondar(Decimal(texto))
    except InvalidOperation:
        raise ErroCSV(f"valor inválido: {texto!r}")


def deslocar_para_o_futuro(ida, volta, hoje):
    """Leva datas passadas para o mesmo dia do próximo ano possível.

    As viagens reais já aconteceram, mas a SerpApi só busca datas futuras.
    Mover anos inteiros mantém a estação do ano e o dia da semana aproximado.
    Devolve (ida, volta, anos_deslocados).
    """
    anos = 0
    while ida <= hoje:
        anos += 1
        ida = _mesmo_dia_outro_ano(ida, 1)
        volta = _mesmo_dia_outro_ano(volta, 1)
    return ida, volta, anos


def _mesmo_dia_outro_ano(dia, anos):
    try:
        return dia.replace(year=dia.year + anos)
    except ValueError:  # 29/02 em ano não bissexto
        return dia.replace(year=dia.year + anos, day=28)


def ler_viagens(caminho=CSV_PADRAO):
    """Lê o CSV e devolve uma lista de viagens (dicts já convertidos)."""
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroCSV(f"arquivo não encontrado: {caminho}")
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        faltando = [coluna for coluna in COLUNAS if coluna not in (leitor.fieldnames or [])]
        if faltando:
            raise ErroCSV(f"colunas faltando: {', '.join(faltando)}")
        viagens = []
        for numero, linha in enumerate(leitor, start=2):
            if (linha.get("fonte") or "").strip().upper().startswith("EXEMPLO"):
                continue
            if not any((valor or "").strip() for valor in linha.values()):
                continue
            try:
                viagens.append({
                    "linha": numero,
                    "origem": linha["origem"].strip().upper(),
                    "destino": linha["destino"].strip().upper(),
                    "ida": date.fromisoformat(linha["ida"].strip()),
                    "volta": date.fromisoformat(linha["volta"].strip()),
                    "pessoas": int(linha["pessoas"]),
                    "interesses": [i.strip() for i in (linha["interesses"] or "").split(";") if i.strip()],
                    "orcamento": ler_valor(linha["orcamento"]),
                    "real": {categoria: ler_valor(linha[f"gasto_real_{categoria}"]) for categoria in CATEGORIAS},
                    "fonte": (linha["fonte"] or "").strip(),
                })
            except (ValueError, KeyError) as erro:
                raise ErroCSV(f"linha {numero}: {erro}")
    return viagens


def erro_percentual(estimado, real):
    """|estimado - real| / real × 100, com 1 casa. None se não há valor real > 0."""
    if estimado is None or real is None or real <= 0:
        return None
    return (abs(Decimal(estimado) - real) / real * 100).quantize(Decimal("0.1"))


def media(valores):
    valores = [valor for valor in valores if valor is not None]
    if not valores:
        return None
    return (sum(valores) / len(valores)).quantize(Decimal("0.1"))


def formatar_erro(valor):
    return "–" if valor is None else f"{valor}%".replace(".", ",")


def formatar_valor(valor):
    if valor is None:
        return "–"
    texto = f"{arredondar(valor):,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")
