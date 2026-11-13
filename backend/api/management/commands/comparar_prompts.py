"""python manage.py comparar_prompts (tarefa #30)

Roda SÓ o Gemini (nenhuma busca da SerpApi) com as versões v1 e v2 do prompt
nas viagens de docs/teste-de-precisao/viagens.csv, compara com os gastos reais
de comida, passeios e transporte e gera docs/teste-de-precisao/comparacao-prompts.md.

Faz 2 chamadas ao Gemini por viagem (uma por versão). Pede confirmação, a não ser com --sim.
"""

from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.servicos import gemini, serpapi
from api.servicos.erros import ErroEntrada, ErroServicoExterno
from api.servicos.precisao import (
    CATEGORIAS_IA, CSV_PADRAO, PASTA_PRECISAO, ErroCSV, deslocar_para_o_futuro,
    erro_percentual, formatar_erro, ler_viagens, media,
)


class Command(BaseCommand):
    help = "Compara as versões do prompt do Gemini com os gastos reais (não usa a SerpApi)."

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(CSV_PADRAO), help="Caminho do CSV de viagens.")
        parser.add_argument("--saida", default=str(PASTA_PRECISAO / "comparacao-prompts.md"),
                            help="Arquivo Markdown de resultado.")
        parser.add_argument("--versoes", nargs="+", default=["v1", "v2"],
                            help="Versões do prompt a comparar (padrão: v1 v2).")
        parser.add_argument("--sim", action="store_true", help="Não pede confirmação.")

    def handle(self, *args, **opcoes):
        versoes = opcoes["versoes"]
        desconhecidas = [versao for versao in versoes if versao not in gemini.PROMPTS]
        if desconhecidas:
            raise CommandError(f"Versões desconhecidas: {', '.join(desconhecidas)}.")
        try:
            viagens = ler_viagens(opcoes["csv"])
        except ErroCSV as erro:
            raise CommandError(f"Erro no CSV: {erro}")
        if not viagens:
            raise CommandError("Nenhuma viagem real no CSV (as linhas de EXEMPLO são ignoradas).")

        chamadas = len(viagens) * len(versoes)
        self.stdout.write(self.style.WARNING(
            f"Isto vai fazer {chamadas} chamada(s) ao Gemini ({gemini.modelo_configurado()}) "
            "e nenhuma busca da SerpApi."
        ))
        if not opcoes["sim"]:
            resposta = input("Continuar? [s/N] ").strip().lower()
            if resposta not in ("s", "sim"):
                self.stdout.write("Cancelado. Nenhuma chamada foi feita.")
                return

        hoje = timezone.localdate()
        resultados = []
        for numero, viagem in enumerate(viagens, start=1):
            ida, volta, _ = deslocar_para_o_futuro(viagem["ida"], viagem["volta"], hoje)
            cidade = serpapi.CIDADES_POR_AEROPORTO.get(viagem["destino"], viagem["destino"])
            destino = f"{cidade} ({viagem['destino']})"
            self.stdout.write(f"[{numero}/{len(viagens)}] {destino}...")
            por_versao = {}
            for versao in versoes:
                try:
                    estimativa = gemini.estimar_gastos_locais(
                        destino, ida, volta, viagem["pessoas"], viagem["interesses"], versao
                    )
                except (ErroEntrada, ErroServicoExterno) as erro:
                    por_versao[versao] = {"erro": erro.mensagem}
                    self.stdout.write(self.style.ERROR(f"  {versao} falhou: {erro.mensagem}"))
                    continue
                por_versao[versao] = {
                    "erros": {
                        categoria: erro_percentual(estimativa["totais"][categoria], viagem["real"][categoria])
                        for categoria in CATEGORIAS_IA
                    }
                }
            resultados.append({"viagem": viagem, "destino": destino, "por_versao": por_versao})

        conteudo = gerar_comparacao(resultados, versoes)
        saida = Path(opcoes["saida"])
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(conteudo, encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Comparação salva em {saida}."))


def calcular_medias(resultados, versoes):
    """{versao: {categoria: erro médio, "geral": média das categorias}}."""
    medias = {}
    for versao in versoes:
        por_categoria = {}
        for categoria in CATEGORIAS_IA:
            por_categoria[categoria] = media([
                r["por_versao"][versao]["erros"][categoria]
                for r in resultados if "erros" in r["por_versao"].get(versao, {})
            ])
        por_categoria["geral"] = media(list(por_categoria.values()))
        medias[versao] = por_categoria
    return medias


def vencedora(medias, chave):
    """Versão com o menor erro médio em `chave` (None se empate ou sem dados)."""
    validos = {versao: valores[chave] for versao, valores in medias.items() if valores[chave] is not None}
    if not validos:
        return None
    menor = min(validos.values())
    melhores = [versao for versao, valor in validos.items() if valor == menor]
    return melhores[0] if len(melhores) == 1 else None


def gerar_comparacao(resultados, versoes):
    medias = calcular_medias(resultados, versoes)
    cabecalho_versoes = " | ".join(f"Erro {versao}" for versao in versoes)
    partes = [
        "# Comparação de versões do prompt",
        "",
        f"Gerado por `python manage.py comparar_prompts` em {datetime.now():%d/%m/%Y %H:%M}, "
        f"com {len(resultados)} viagem(ns) e o modelo {gemini.modelo_configurado()}. "
        "Só o Gemini foi chamado; passagem e hotel não entram.",
        "",
        "Erro percentual = |estimado − real| ÷ real × 100, sobre o gasto do grupo na viagem toda.",
        "",
        "## Qual versão erra menos",
        "",
        f"| Categoria | {cabecalho_versoes} | Erra menos |",
        "| --- | " + " | ".join("---" for _ in versoes) + " | --- |",
    ]
    for chave in (*CATEGORIAS_IA, "geral"):
        nome = "**Média geral**" if chave == "geral" else chave
        valores = " | ".join(formatar_erro(medias[versao][chave]) for versao in versoes)
        partes.append(f"| {nome} | {valores} | {vencedora(medias, chave) or 'empate / sem dados'} |")

    partes += [
        "",
        "## Viagem a viagem",
        "",
        "| # | Destino | Versão | Comida | Passeios | Transporte |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for numero, resultado in enumerate(resultados, start=1):
        for versao in versoes:
            dados = resultado["por_versao"].get(versao, {})
            if "erros" in dados:
                celulas = " | ".join(formatar_erro(dados["erros"][c]) for c in CATEGORIAS_IA)
            else:
                celulas = f"falhou: {dados.get('erro', '?')} | – | –"
            partes.append(f"| {numero} | {resultado['destino']} | {versao} | {celulas} |")
    partes += [
        "",
        "## As versões",
        "",
        "- **v1:** pedido direto, viajante de orçamento médio.",
        "- **v2:** pede para considerar a estação do ano, o custo de vida local e faixas de preço "
        "(econômica, média, confortável) antes de escolher o valor.",
        "",
        "O texto completo dos prompts está em `backend/api/servicos/gemini.py` (PROMPTS).",
        "",
    ]
    return "\n".join(partes)
