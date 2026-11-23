"""python manage.py teste_precisao (tarefa #29)

Lê docs/teste-de-precisao/viagens.csv, roda simular() em cada viagem e gera
docs/teste-de-precisao/resultado.md com o erro percentual por categoria.

ATENÇÃO: gasta cota real da SerpApi (3 ou 4 buscas por viagem) e 1 chamada ao
Gemini por viagem. Pede confirmação antes, a não ser com --sim.
"""

from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.servicos import gemini, serpapi
from api.servicos.erros import ErroEntrada, ErroServicoExterno
from api.servicos.precisao import (
    CATEGORIAS, CSV_PADRAO, PASTA_PRECISAO, ErroCSV, deslocar_para_o_futuro,
    erro_percentual, formatar_erro, formatar_valor, ler_viagens, media,
)
from api.servicos.simulacao import simular

LIMITE_BUSCAS_POR_HORA = 50


def buscas_previstas(viagem):
    return 3 + (0 if viagem["destino"] in serpapi.CIDADES_POR_AEROPORTO else 1)


class Command(BaseCommand):
    help = "Roda as viagens reais do CSV e mede o erro das estimativas (gasta cota da SerpApi)."

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(CSV_PADRAO), help="Caminho do CSV de viagens.")
        parser.add_argument("--saida", default=str(PASTA_PRECISAO / "resultado.md"),
                            help="Arquivo Markdown de resultado.")
        parser.add_argument("--versao-prompt", default=gemini.VERSAO_PADRAO,
                            choices=sorted(gemini.PROMPTS), help="Versão do prompt do Gemini.")
        parser.add_argument("--limite", type=int, default=None,
                            help="Roda só as N primeiras viagens (para dividir a cota por hora).")
        parser.add_argument("--sim", action="store_true", help="Não pede confirmação.")

    def handle(self, *args, **opcoes):
        try:
            viagens = ler_viagens(opcoes["csv"])
        except ErroCSV as erro:
            raise CommandError(f"Erro no CSV: {erro}")
        if opcoes["limite"]:
            viagens = viagens[: opcoes["limite"]]
        if not viagens:
            raise CommandError("Nenhuma viagem real no CSV (as linhas de EXEMPLO são ignoradas).")

        total_buscas = sum(buscas_previstas(viagem) for viagem in viagens)
        self.stdout.write(self.style.WARNING(
            f"Isto vai rodar {len(viagens)} simulação(ões) reais: até {total_buscas} buscas da "
            f"SerpApi (cota: 250 por mês, {LIMITE_BUSCAS_POR_HORA} por hora) e "
            f"{len(viagens)} chamada(s) ao Gemini."
        ))
        if total_buscas > LIMITE_BUSCAS_POR_HORA:
            self.stdout.write(self.style.WARNING(
                f"Passa de {LIMITE_BUSCAS_POR_HORA} buscas: use --limite para dividir em mais de uma hora."
            ))
        if not opcoes["sim"]:
            resposta = input("Continuar? [s/N] ").strip().lower()
            if resposta not in ("s", "sim"):
                self.stdout.write("Cancelado. Nenhuma busca foi feita.")
                return

        hoje = timezone.localdate()
        resultados = []
        for numero, viagem in enumerate(viagens, start=1):
            ida, volta, anos = deslocar_para_o_futuro(viagem["ida"], viagem["volta"], hoje)
            rota = f"{viagem['origem']}→{viagem['destino']}"
            self.stdout.write(f"[{numero}/{len(viagens)}] {rota} {ida:%d/%m/%Y}...")
            resultado = {"viagem": viagem, "ida": ida, "volta": volta, "anos": anos}
            try:
                simulacao = simular(
                    viagem["origem"], viagem["destino"], ida, volta,
                    viagem["orcamento"], viagem["pessoas"], viagem["interesses"],
                    versao_prompt=opcoes["versao_prompt"],
                )
            except (ErroEntrada, ErroServicoExterno) as erro:
                resultado["erro"] = erro.mensagem
                self.stdout.write(self.style.ERROR(f"  falhou: {erro.mensagem}"))
            else:
                resultado["simulacao"] = simulacao
            resultados.append(resultado)

        conteudo = gerar_relatorio(resultados, opcoes["versao_prompt"])
        saida = Path(opcoes["saida"])
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(conteudo, encoding="utf-8")
        gastas = sum(r["simulacao"]["buscas_serpapi"] for r in resultados if "simulacao" in r)
        self.stdout.write(self.style.SUCCESS(f"Resultado salvo em {saida} ({gastas} buscas gastas)."))


def erros_da_simulacao(simulacao, real):
    """{categoria: erro %}, o erro do total e os dois totais comparados.

    O total compara só as categorias que têm valor real (a referência pode não
    trazer transporte, por exemplo), somando as mesmas categorias dos dois lados.
    Com as 5 categorias preenchidas, é o total da viagem.
    """
    estimado = {gasto["categoria"]: gasto["valor"] for gasto in simulacao["gastos"]}
    erros = {categoria: erro_percentual(estimado.get(categoria), real[categoria]) for categoria in CATEGORIAS}
    comparadas = [categoria for categoria in CATEGORIAS
                  if real[categoria] is not None and estimado.get(categoria) is not None]
    if comparadas:
        total_estimado = sum(estimado[categoria] for categoria in comparadas)
        total_real = sum(real[categoria] for categoria in comparadas)
    else:
        total_estimado = total_real = None
    erros["total"] = erro_percentual(total_estimado, total_real)
    return erros, total_estimado, total_real, len(comparadas)


def gerar_relatorio(resultados, versao_prompt):
    linhas_viagens = []
    erros_por_categoria = {categoria: [] for categoria in (*CATEGORIAS, "total")}
    deslocadas = 0
    parciais = 0
    falhas = []

    for numero, resultado in enumerate(resultados, start=1):
        viagem = resultado["viagem"]
        rota = f"{viagem['origem']}→{viagem['destino']}"
        if resultado["anos"]:
            deslocadas += 1
        if "simulacao" not in resultado:
            falhas.append(f"- Viagem {numero} ({rota}, linha {viagem['linha']} do CSV): {resultado['erro']}")
            continue
        simulacao = resultado["simulacao"]
        erros, total_estimado, total_real, comparadas = erros_da_simulacao(simulacao, viagem["real"])
        if comparadas < len(CATEGORIAS):
            parciais += 1
        for chave, valor in erros.items():
            erros_por_categoria[chave].append(valor)
        linhas_viagens.append(
            f"| {numero} | {rota} | {resultado['ida']:%d/%m/%Y} a {resultado['volta']:%d/%m/%Y} "
            f"| {viagem['pessoas']} | {formatar_valor(total_estimado)} "
            f"| {formatar_valor(total_real)} | "
            + " | ".join(formatar_erro(erros[categoria]) for categoria in CATEGORIAS)
            + f" | {formatar_erro(erros['total'])} | {simulacao['veredito']} |"
        )

    partes = [
        "# Resultado do teste de precisão",
        "",
        f"Gerado por `python manage.py teste_precisao` em {datetime.now():%d/%m/%Y %H:%M}. "
        f"Prompt do Gemini: {versao_prompt} ({gemini.modelo_configurado()}).",
        "",
        "Erro percentual = |estimado − real| ÷ real × 100. Gastos reais e estimados são do grupo, "
        "na viagem toda. Todo valor do site é uma estimativa.",
        "",
    ]
    if deslocadas:
        partes += [
            f"> {deslocadas} viagem(ns) já aconteceram e foram simuladas no mesmo período de um ano "
            "futuro (a SerpApi só busca datas futuras). Preços de outro ano podem explicar parte do erro.",
            "",
        ]
    if parciais:
        partes += [
            f"> {parciais} viagem(ns) não têm valor real em todas as categorias. Nelas, o total "
            "soma só as categorias com valor real, dos dois lados, para comparar a mesma coisa.",
            "",
        ]
    partes += [
        "## Erro médio por categoria",
        "",
        "| Categoria | Erro médio | Viagens com valor real |",
        "| --- | --- | --- |",
    ]
    for chave in (*CATEGORIAS, "total"):
        valores = [valor for valor in erros_por_categoria[chave] if valor is not None]
        nome = "**Total**" if chave == "total" else chave
        partes.append(f"| {nome} | {formatar_erro(media(valores))} | {len(valores)} |")
    medias_categorias = [media(erros_por_categoria[categoria]) for categoria in CATEGORIAS]
    partes += [
        "",
        f"**Erro médio geral (média das categorias com valor real): {formatar_erro(media(medias_categorias))}**",
        "",
        "## Viagem a viagem",
        "",
        "| # | Rota | Datas simuladas | Pessoas | Total estimado (R$) | Total real (R$) | "
        "Passagem | Hotel | Comida | Passeios | Transporte | Total | Veredito |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        *linhas_viagens,
        "",
    ]
    if falhas:
        partes += ["## Viagens que falharam", "", *falhas, ""]
    return "\n".join(partes)
