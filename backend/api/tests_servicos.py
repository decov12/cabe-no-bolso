"""Testes dos serviços de busca e IA (tarefa #28).

Nenhum teste chama a SerpApi ou o Gemini de verdade: as respostas vêm de
fixtures/serpapi/, fixtures/gemini/ e de mocks (unittest.mock).
"""

import copy
import json
import tempfile
from datetime import date
from decimal import Decimal
from io import StringIO
from pathlib import Path
from unittest import mock

import requests
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from api.servicos import alternativas, gemini, precisao, serpapi, simulacao, veredito
from api.servicos.erros import ErroEntrada, ErroServicoExterno

PASTA_FIXTURES = Path(settings.BASE_DIR).parent / "fixtures"
HOJE = date(2026, 11, 13)
CHAVES_TESTE = {"SERPAPI_KEY": "chave-serpapi-de-teste", "GEMINI_API_KEY": "chave-gemini-de-teste"}


def carregar(nome):
    with open(PASTA_FIXTURES / nome, encoding="utf-8") as arquivo:
        return json.load(arquivo)


AUTOCOMPLETE = carregar("serpapi/autocomplete_Lisboa.json")
VOOS = carregar("serpapi/voos_GRU-EZE_BRL.json")
HOTEIS = carregar("serpapi/hoteis_Lisboa_2027-03-10_BRL.json")
CALENDARIO = carregar("serpapi/calendario_GRU-LIS_2027-01_a_2027-06_BRL.json")
ESTIMATIVA = carregar("gemini/estimativa_exemplo.json")["resposta"]


def _rede_proibida(*args, **kwargs):
    raise AssertionError("Teste tentou chamar uma API de verdade. Use mock.")


_trava_rede = [
    mock.patch("api.servicos.serpapi.requests.get", side_effect=_rede_proibida),
    mock.patch("api.servicos.gemini.genai.Client", side_effect=_rede_proibida),
]


def setUpModule():
    # Rede de segurança: se algum teste esquecer um mock, ele falha em vez de gastar cota.
    for trava in _trava_rede:
        trava.start()


def tearDownModule():
    for trava in _trava_rede:
        trava.stop()


def resposta_gemini(**trocas):
    """JSON de resposta do Gemini baseado na fixture, com valores trocados."""
    dados = copy.deepcopy(ESTIMATIVA)
    for categoria, valor in trocas.items():
        dados[categoria]["valor_por_pessoa_dia"] = valor
    return json.dumps(dados)


# ---------------------------------------------------------------------------
# #15 Veredito
# ---------------------------------------------------------------------------

class VereditoTests(SimpleTestCase):
    orcamento = Decimal("1000.00")

    def test_igual_ao_orcamento_cabe(self):
        self.assertEqual(veredito.decidir_veredito(Decimal("1000.00"), self.orcamento), "cabe")

    def test_um_centavo_acima_cabe_com_ajustes(self):
        self.assertEqual(veredito.decidir_veredito(Decimal("1000.01"), self.orcamento), "cabe_com_ajustes")

    def test_exatamente_15_por_cento_acima_cabe_com_ajustes(self):
        self.assertEqual(veredito.decidir_veredito(Decimal("1150.00"), self.orcamento), "cabe_com_ajustes")

    def test_15_por_cento_mais_1_centavo_nao_cabe(self):
        self.assertEqual(veredito.decidir_veredito(Decimal("1150.01"), self.orcamento), "nao_cabe")

    def test_limite_com_orcamento_quebrado(self):
        # 1234,56 × 1,15 = 1419,744: 1419,74 ainda cabe com ajustes, 1419,75 não.
        orcamento = Decimal("1234.56")
        self.assertEqual(veredito.decidir_veredito(Decimal("1419.74"), orcamento), "cabe_com_ajustes")
        self.assertEqual(veredito.decidir_veredito(Decimal("1419.75"), orcamento), "nao_cabe")

    def test_margem_e_constante(self):
        self.assertEqual(veredito.MARGEM_AJUSTE, Decimal("0.15"))
        with mock.patch.object(veredito, "MARGEM_AJUSTE", Decimal("0.10")):
            self.assertEqual(veredito.decidir_veredito(Decimal("1150.00"), self.orcamento), "nao_cabe")

    def test_somar_gastos_com_dicts_e_valores(self):
        gastos = [
            {"categoria": "passagem", "valor": Decimal("3860.00")},
            {"categoria": "hotel", "valor": Decimal("2674.005")},
        ]
        self.assertEqual(veredito.somar_gastos(gastos), Decimal("6534.01"))
        self.assertEqual(veredito.somar_gastos([0.1, 0.2]), Decimal("0.30"))
        self.assertEqual(veredito.somar_gastos([]), Decimal("0.00"))

    def test_diferenca(self):
        self.assertEqual(veredito.calcular_diferenca(Decimal("1200"), self.orcamento), Decimal("-200.00"))
        self.assertEqual(veredito.calcular_diferenca(Decimal("800.5"), self.orcamento), Decimal("199.50"))

    def test_arredondar(self):
        self.assertEqual(veredito.arredondar(0.1 + 0.2), Decimal("0.30"))
        self.assertEqual(veredito.arredondar(Decimal("2.675")), Decimal("2.68"))


# ---------------------------------------------------------------------------
# #12 Cliente da SerpApi
# ---------------------------------------------------------------------------

def resposta_http(dados, status=200):
    resposta = mock.Mock()
    resposta.status_code = status
    resposta.json.return_value = dados
    return resposta


@override_settings(**CHAVES_TESTE)
@mock.patch("api.servicos.serpapi.time.sleep")
@mock.patch("api.servicos.serpapi.requests.get")
class BuscarTests(SimpleTestCase):
    def test_sucesso_envia_engine_chave_e_timeout(self, get, _sleep):
        get.return_value = resposta_http(VOOS)
        dados = serpapi.buscar("google_flights", {"departure_id": "GRU"})
        self.assertEqual(dados, VOOS)
        _, kwargs = get.call_args
        self.assertEqual(kwargs["params"]["engine"], "google_flights")
        self.assertEqual(kwargs["params"]["api_key"], "chave-serpapi-de-teste")
        self.assertEqual(kwargs["timeout"], serpapi.TIMEOUT_SEGUNDOS)

    def test_nova_tentativa_depois_de_timeout(self, get, sleep):
        get.side_effect = [requests.Timeout("lento"), resposta_http(VOOS)]
        self.assertEqual(serpapi.buscar("google_flights", {}), VOOS)
        self.assertEqual(get.call_count, 2)
        sleep.assert_called_once()

    def test_duas_falhas_levantam_erro_sem_vazar_a_chave(self, get, _sleep):
        erro = requests.ConnectionError("falhou https://serpapi.com/search.json?api_key=chave-serpapi-de-teste")
        get.side_effect = [erro, erro]
        with self.assertRaises(ErroServicoExterno) as contexto:
            serpapi.buscar("google_hotels", {})
        self.assertEqual(get.call_count, 2)
        self.assertNotIn("chave-serpapi-de-teste", str(contexto.exception))
        self.assertIn("google_hotels", str(contexto.exception))

    def test_erro_da_api_tenta_de_novo_e_falha(self, get, _sleep):
        get.return_value = resposta_http({"error": "Invalid API key."}, status=401)
        with self.assertRaises(ErroServicoExterno) as contexto:
            serpapi.buscar("google_flights", {})
        self.assertEqual(get.call_count, 2)
        self.assertIn("Invalid API key", contexto.exception.mensagem)

    def test_json_invalido_conta_como_falha(self, get, _sleep):
        resposta = resposta_http(None)
        resposta.json.side_effect = ValueError("não é JSON")
        get.return_value = resposta
        with self.assertRaises(ErroServicoExterno):
            serpapi.buscar("google_flights", {})

    def test_sem_resultados_nao_e_falha(self, get, _sleep):
        vazio = {"error": "Google Flights hasn't returned any results for this query."}
        get.return_value = resposta_http(vazio)
        self.assertEqual(serpapi.buscar("google_flights", {}), vazio)
        self.assertEqual(get.call_count, 1)

    @override_settings(SERPAPI_KEY="")
    def test_sem_chave(self, get, _sleep):
        with self.assertRaises(ErroServicoExterno):
            serpapi.buscar("google_flights", {})
        get.assert_not_called()


# ---------------------------------------------------------------------------
# #12 Autocomplete e voos
# ---------------------------------------------------------------------------

class AutocompleteTests(SimpleTestCase):
    def test_lista_organizada(self):
        lugares = serpapi.interpretar_autocomplete(AUTOCOMPLETE)
        self.assertEqual(len(lugares), 6)  # 3 cidades + 3 aeroportos
        self.assertEqual(lugares[0], {
            "tipo": "cidade", "nome": "Lisboa", "codigo": "LIS",
            "pais": "Portugal", "descricao": "Capital de Portugal",
        })
        self.assertEqual(lugares[1]["tipo"], "aeroporto")
        self.assertEqual(lugares[1]["codigo"], "LIS")
        self.assertEqual(lugares[1]["nome"], "Aeroporto Humberto Delgado")
        self.assertEqual(lugares[1]["pais"], "Portugal")
        # Os irrelevantes continuam na lista: quem escolhe é a tela.
        self.assertIn("FLN", [lugar["codigo"] for lugar in lugares])
        self.assertIsNone(lugares[2]["pais"])  # "Santo Antônio de Lisboa" não tem país no nome

    def test_resposta_vazia(self):
        self.assertEqual(serpapi.interpretar_autocomplete({}), [])

    @mock.patch("api.servicos.serpapi.buscar")
    def test_buscar_lugares(self, buscar):
        buscar.return_value = AUTOCOMPLETE
        lugares = serpapi.buscar_lugares("  Lisboa ")
        buscar.assert_called_once_with("google_flights_autocomplete", {"q": "Lisboa", "hl": "pt", "gl": "br"})
        self.assertEqual(lugares[0]["nome"], "Lisboa")

    @mock.patch("api.servicos.serpapi.buscar")
    def test_texto_curto_nao_gasta_busca(self, buscar):
        self.assertEqual(serpapi.buscar_lugares("L"), [])
        self.assertEqual(serpapi.buscar_lugares(None), [])
        buscar.assert_not_called()

    @mock.patch("api.servicos.serpapi.buscar")
    def test_cidade_do_aeroporto_pelo_mapeamento(self, buscar):
        self.assertEqual(serpapi.cidade_do_aeroporto("lis"), ("Lisboa", 0))
        buscar.assert_not_called()

    @mock.patch("api.servicos.serpapi.buscar")
    def test_cidade_do_aeroporto_pelo_autocomplete(self, buscar):
        buscar.return_value = AUTOCOMPLETE
        self.assertNotIn("IMP", serpapi.CIDADES_POR_AEROPORTO)
        self.assertEqual(serpapi.cidade_do_aeroporto("IMP"), ("Imperatriz", 1))

    @mock.patch("api.servicos.serpapi.buscar")
    def test_cidade_do_aeroporto_desconhecido(self, buscar):
        buscar.return_value = AUTOCOMPLETE
        with self.assertRaises(ErroEntrada):
            serpapi.cidade_do_aeroporto("QQQ")


class VoosTests(SimpleTestCase):
    def test_menor_preco_de_best_flights(self):
        voo = serpapi.interpretar_voos(VOOS)
        self.assertEqual(voo["preco_por_pessoa"], Decimal("1930.00"))
        self.assertEqual(voo["companhia"], "LATAM")
        self.assertEqual(voo["criterio"], "menor_preco_best_flights")
        self.assertTrue(voo["link_google_voos"].startswith("https://www.google.com/travel/flights"))

    def test_sem_best_flights_usa_mediana_de_other_flights(self):
        dados = copy.deepcopy(VOOS)
        dados["best_flights"] = []
        voo = serpapi.interpretar_voos(dados)
        # other_flights: 1930, 2454 e 6777 -> mediana 2454 (o extremo 6777 não puxa o preço)
        self.assertEqual(voo["preco_por_pessoa"], Decimal("2454.00"))
        self.assertEqual(voo["companhia"], "LATAM")
        self.assertEqual(voo["criterio"], "mediana_other_flights")

    def test_mediana_com_numero_par_usa_opcao_real(self):
        dados = copy.deepcopy(VOOS)
        dados["best_flights"] = []
        dados["other_flights"] = dados["other_flights"][1:]  # 2454 e 6777
        self.assertEqual(serpapi.interpretar_voos(dados)["preco_por_pessoa"], Decimal("2454.00"))

    def test_sem_link(self):
        dados = copy.deepcopy(VOOS)
        del dados["search_metadata"]
        self.assertIsNone(serpapi.interpretar_voos(dados)["link_google_voos"])

    def test_resposta_vazia(self):
        self.assertIsNone(serpapi.interpretar_voos({"search_metadata": {}}))

    @mock.patch("api.servicos.serpapi.buscar")
    def test_buscar_voos_parametros(self, buscar):
        buscar.return_value = VOOS
        voo = serpapi.buscar_voos("gru", "eze", date(2027, 3, 10), date(2027, 3, 17))
        buscar.assert_called_once_with("google_flights", {
            "departure_id": "GRU", "arrival_id": "EZE",
            "outbound_date": "2027-03-10", "return_date": "2027-03-17",
            "hl": "pt", "gl": "br", "currency": "BRL",
        })
        self.assertEqual(voo["preco_por_pessoa"], Decimal("1930.00"))

    @mock.patch("api.servicos.serpapi.buscar")
    def test_buscar_voos_sem_resultado(self, buscar):
        buscar.return_value = {"error": "Google Flights hasn't returned any results for this query."}
        with self.assertRaises(ErroEntrada):
            serpapi.buscar_voos("GRU", "BUE", date(2027, 3, 10), date(2027, 3, 17))


# ---------------------------------------------------------------------------
# #13 Hotéis e calendário
# ---------------------------------------------------------------------------

class HoteisTests(SimpleTestCase):
    def setUp(self):
        self.hoteis = serpapi.interpretar_hoteis(HOTEIS, noites=7)

    def test_so_hoteis_sem_anuncios(self):
        self.assertEqual(len(self.hoteis), 15)
        nomes = {hotel["nome"] for hotel in self.hoteis}
        self.assertNotIn("Racing boat", nomes)  # vacation rental
        for anuncio in HOTEIS["ads"]:
            if anuncio["name"] not in {p["name"] for p in HOTEIS["properties"] if p.get("type") == "hotel"}:
                self.assertNotIn(anuncio["name"], nomes)

    def test_ordenado_por_preco(self):
        precos = [hotel["preco_noite"] for hotel in self.hoteis]
        self.assertEqual(precos, sorted(precos))
        self.assertEqual(self.hoteis[0], {
            "nome": "Ibis Lisboa Jose Malhoa Hotel", "estrelas": 2, "nota": 4.2,
            "preco_noite": Decimal("342.00"), "link": self.hoteis[0]["link"],
        })
        self.assertTrue(self.hoteis[0]["link"])

    def test_hotel_sem_link(self):
        freud = next(hotel for hotel in self.hoteis if hotel["nome"] == "R & Freud B&B")
        self.assertIsNone(freud["link"])

    def test_sem_preco_por_noite_usa_total(self):
        dados = {"properties": [{
            "type": "hotel", "name": "Só total", "total_rate": {"extracted_lowest": 700},
        }, {
            "type": "hotel", "name": "Sem preço",
        }]}
        hoteis = serpapi.interpretar_hoteis(dados, noites=7)
        self.assertEqual(len(hoteis), 1)
        self.assertEqual(hoteis[0]["preco_noite"], Decimal("100.00"))
        self.assertIsNone(hoteis[0]["nota"])

    @mock.patch("api.servicos.serpapi.buscar")
    def test_buscar_hoteis_parametros(self, buscar):
        buscar.return_value = HOTEIS
        hoteis = serpapi.buscar_hoteis("Lisboa", date(2027, 3, 10), date(2027, 3, 17))
        buscar.assert_called_once_with("google_hotels", {
            "q": "Lisboa", "check_in_date": "2027-03-10", "check_out_date": "2027-03-17",
            "adults": 2, "hl": "pt", "gl": "br", "currency": "BRL",
        })
        self.assertEqual(len(hoteis), 15)


class CalendarioTests(SimpleTestCase):
    def test_menor_preco_por_mes_calculado_de_prices(self):
        meses = serpapi.interpretar_calendario(CALENDARIO)
        self.assertEqual([m["mes"] for m in meses], ["2027-01", "2027-02", "2027-03", "2027-04", "2027-05", "2027-06"])
        esperado = {}
        for item in CALENDARIO["prices"]:
            mes = item["outbound_date"][:7]
            esperado[mes] = min(esperado.get(mes, item["price"]), item["price"])
        for mes in meses:
            self.assertEqual(mes["menor_preco"], Decimal(esperado[mes["mes"]]).quantize(Decimal("0.01")))
        self.assertEqual(meses[-1]["menor_preco"], Decimal("4828.00"))  # junho tem só 1 dia

    def test_ignora_low_price_e_precos_invalidos(self):
        dados = {"low_price": 1, "prices": [
            {"outbound_date": "2027-01-05", "price": 900},
            {"outbound_date": "2027-01-01", "price": 0},
            {"outbound_date": "2027-01-02", "price": None},
            {"outbound_date": "2027-02-01", "price": 800},
        ]}
        self.assertEqual(serpapi.interpretar_calendario(dados), [
            {"mes": "2027-01", "menor_preco": Decimal("900.00")},
            {"mes": "2027-02", "menor_preco": Decimal("800.00")},
        ])

    @mock.patch("api.servicos.serpapi.buscar")
    def test_buscar_calendario_parametros(self, buscar):
        buscar.return_value = CALENDARIO
        serpapi.buscar_calendario("GRU", "LIS", date(2027, 1, 1), date(2027, 6, 30))
        buscar.assert_called_once_with("google_flights_calendar", {
            "departure_id": "GRU", "arrival_id": "LIS",
            "date_range_start": "2027-01-01", "date_range_end": "2027-06-30",
            "hl": "pt", "gl": "br", "currency": "BRL",
        })


# ---------------------------------------------------------------------------
# #14 Gemini
# ---------------------------------------------------------------------------

IDA, VOLTA = date(2027, 3, 10), date(2027, 3, 17)


@override_settings(**CHAVES_TESTE, GEMINI_MODEL="")
@mock.patch("api.servicos.gemini.time.sleep")
@mock.patch("api.servicos.gemini._chamar_modelo")
class GeminiTests(SimpleTestCase):
    def estimar(self, **kwargs):
        argumentos = {"destino": "Lisboa (LIS)", "data_ida": IDA, "data_volta": VOLTA,
                      "pessoas": 2, "interesses": ["museus"]}
        argumentos.update(kwargs)
        return gemini.estimar_gastos_locais(**argumentos)

    def test_json_valido_codigo_multiplica(self, chamar, _sleep):
        chamar.return_value = resposta_gemini()
        estimativa = self.estimar()
        self.assertEqual(estimativa["dias"], 7)
        self.assertEqual(estimativa["por_pessoa_dia"]["comida"], Decimal("160.00"))
        # 160 × 7 dias × 2 pessoas
        self.assertEqual(estimativa["totais"], {
            "comida": Decimal("2240.00"), "passeios": Decimal("980.00"), "transporte": Decimal("350.00"),
        })
        self.assertTrue(estimativa["justificativas"]["comida"])
        self.assertEqual(estimativa["versao_prompt"], "v1")
        self.assertEqual(estimativa["modelo"], gemini.MODELO_PADRAO)
        chamar.assert_called_once()

    def test_json_invalido_tenta_de_novo(self, chamar, _sleep):
        chamar.side_effect = ["{isto não é json", resposta_gemini()]
        self.assertEqual(self.estimar()["totais"]["comida"], Decimal("2240.00"))
        self.assertEqual(chamar.call_count, 2)

    def test_json_invalido_duas_vezes(self, chamar, _sleep):
        chamar.side_effect = ["{quebrado", '{"comida": 10}']
        with self.assertRaises(ErroServicoExterno):
            self.estimar()
        self.assertEqual(chamar.call_count, 2)

    def test_valores_absurdos(self, chamar, _sleep):
        for absurdo in (50000, -10, "160", True, None):
            chamar.reset_mock()
            chamar.side_effect = [resposta_gemini(comida=absurdo)] * 2
            with self.subTest(valor=absurdo), self.assertRaises(ErroServicoExterno):
                self.estimar()

    def test_falta_categoria_ou_justificativa(self, chamar, _sleep):
        sem_transporte = copy.deepcopy(ESTIMATIVA)
        del sem_transporte["transporte"]
        sem_justificativa = copy.deepcopy(ESTIMATIVA)
        sem_justificativa["passeios"]["justificativa"] = "  "
        for resposta in (sem_transporte, sem_justificativa, [1, 2]):
            chamar.side_effect = [json.dumps(resposta)] * 2
            with self.subTest(resposta=resposta), self.assertRaises(ErroServicoExterno):
                self.estimar()

    def test_passeios_zero_e_valido(self, chamar, _sleep):
        chamar.return_value = resposta_gemini(passeios=0)
        self.assertEqual(self.estimar()["totais"]["passeios"], Decimal("0.00"))

    def test_falha_do_sdk_tenta_de_novo(self, chamar, _sleep):
        chamar.side_effect = [RuntimeError("503 do servidor"), resposta_gemini()]
        self.assertEqual(self.estimar()["totais"]["transporte"], Decimal("350.00"))
        chamar.side_effect = [RuntimeError("x"), TimeoutError("y")]
        with self.assertRaises(ErroServicoExterno):
            self.estimar()

    @override_settings(GEMINI_API_KEY="")
    def test_sem_chave(self, chamar, _sleep):
        with self.assertRaises(ErroServicoExterno):
            self.estimar()
        chamar.assert_not_called()

    def test_versao_desconhecida(self, chamar, _sleep):
        with self.assertRaises(ErroEntrada):
            self.estimar(versao_prompt="v99")

    def test_versao_v2(self, chamar, _sleep):
        chamar.return_value = resposta_gemini()
        self.assertEqual(self.estimar(versao_prompt="v2")["versao_prompt"], "v2")
        texto_enviado = chamar.call_args.args[0]
        self.assertIn("estação do ano", texto_enviado)


class PromptsTests(SimpleTestCase):
    def test_prompts_versionados_e_diferentes(self):
        self.assertIn("v1", gemini.PROMPTS)
        self.assertIn("v2", gemini.PROMPTS)
        v1 = gemini.montar_prompt("Lisboa (LIS)", IDA, VOLTA, 2, ["museus", "praia"], "v1")
        v2 = gemini.montar_prompt("Lisboa (LIS)", IDA, VOLTA, 2, ["museus", "praia"], "v2")
        self.assertNotEqual(v1, v2)
        for texto in (v1, v2):
            self.assertIn("Lisboa (LIS)", texto)
            self.assertIn("10/03/2027", texto)
            self.assertIn("7 noites", texto)
            self.assertIn("museus, praia", texto)
            self.assertIn("POR PESSOA POR DIA", texto)
            self.assertIn("NÃO some", texto)
        self.assertIn("custo de vida", v2)
        self.assertIn("faixa", v2)

    def test_sem_interesses(self):
        self.assertIn("nenhum em especial", gemini.montar_prompt("X", IDA, VOLTA, 1, [], "v1"))


@override_settings(**CHAVES_TESTE)
class ChamadaSdkGeminiTests(SimpleTestCase):
    """Confere a forma da chamada ao SDK google-genai (sem rede)."""

    @override_settings(GEMINI_MODEL="")
    @mock.patch("api.servicos.gemini.genai.Client")
    def test_chamada_com_schema_e_modelo_padrao(self, cliente):
        cliente.return_value.interactions.create.return_value.output_text = resposta_gemini()
        self.assertEqual(gemini._chamar_modelo("prompt"), resposta_gemini())
        cliente.assert_called_once_with(api_key="chave-gemini-de-teste")
        kwargs = cliente.return_value.interactions.create.call_args.kwargs
        self.assertEqual(kwargs["model"], "gemini-3.5-flash-lite")
        self.assertEqual(kwargs["input"], "prompt")
        self.assertEqual(kwargs["response_format"]["mime_type"], "application/json")
        self.assertEqual(kwargs["response_format"]["schema"], gemini.SCHEMA_RESPOSTA)
        self.assertEqual(kwargs["timeout"], gemini.TIMEOUT_SEGUNDOS)
        self.assertFalse(kwargs["store"])

    @override_settings(GEMINI_MODEL="gemini-outro-modelo")
    @mock.patch("api.servicos.gemini.genai.Client")
    def test_modelo_configuravel(self, cliente):
        gemini._chamar_modelo("prompt")
        self.assertEqual(cliente.return_value.interactions.create.call_args.kwargs["model"], "gemini-outro-modelo")

    def test_schema_exige_as_tres_categorias(self):
        self.assertEqual(set(gemini.SCHEMA_RESPOSTA["required"]), {"comida", "passeios", "transporte"})


# ---------------------------------------------------------------------------
# #22 Alternativas
# ---------------------------------------------------------------------------

def contexto_base(**trocas):
    """Viagem de 7 noites, 2 pessoas, 1 quarto: passagem 2×1930, hotel 7×382, diários 3570."""
    hoteis = serpapi.interpretar_hoteis(HOTEIS, noites=7)
    hotel = next(h for h in hoteis if h["nome"] == "R & Freud B&B")
    contexto = {
        "orcamento": Decimal("9000.00"),
        "total": Decimal("10104.00"),
        "veredito": "cabe_com_ajustes",
        "pessoas": 2, "quartos": 1, "noites": 7, "data_ida": IDA,
        "passagem_por_pessoa": Decimal("1930.00"),
        "hotel": hotel, "hoteis": hoteis,
        "gastos_diarios": Decimal("3570.00"),
        "precos_por_mes": [],
    }
    contexto.update(trocas)
    return contexto


class AlternativasTests(SimpleTestCase):
    def test_viagem_que_cabe_nao_tem_alternativas(self):
        self.assertEqual(alternativas.gerar_alternativas(contexto_base(veredito="cabe")), [])

    def test_outro_mes_usa_o_calendario(self):
        precos = [
            {"mes": "2027-02", "menor_preco": Decimal("1500.00")},
            {"mes": "2027-03", "menor_preco": Decimal("1000.00")},  # mês atual: não conta
            {"mes": "2027-05", "menor_preco": Decimal("1200.00")},
            {"mes": "2027-06", "menor_preco": Decimal("2500.00")},
        ]
        alternativa = alternativas.alternativa_outro_mes(contexto_base(precos_por_mes=precos))
        self.assertEqual(alternativa["tipo"], "outro_mes")
        # 10104 − 2×1930 + 2×1200
        self.assertEqual(alternativa["novo_total"], Decimal("8644.00"))
        self.assertEqual(alternativa["economia"], Decimal("1460.00"))
        self.assertEqual(alternativa["novo_veredito"], "cabe")
        self.assertIn("maio de 2027", alternativa["descricao"])
        self.assertIn("7 noites", alternativa["descricao"])
        self.assertIn("R$ 1.200,00", alternativa["descricao"])

    def test_outro_mes_sem_mes_mais_barato(self):
        precos = serpapi.interpretar_calendario(CALENDARIO)  # todos acima de R$ 1.930
        self.assertIsNone(alternativas.alternativa_outro_mes(contexto_base(precos_por_mes=precos)))

    def test_menos_noites_ate_caber(self):
        alternativa = alternativas.alternativa_menos_noites(contexto_base())
        # Por noite: hotel 382 + diários 510 = 892. 3860 + 892 × 5 = 8320 <= 9000.
        self.assertEqual(alternativa["novo_total"], Decimal("8320.00"))
        self.assertEqual(alternativa["novo_veredito"], "cabe")
        self.assertEqual(alternativa["economia"], Decimal("1784.00"))
        self.assertIn("5 noites em vez de 7", alternativa["descricao"])
        self.assertIn("15/03/2027", alternativa["descricao"])

    def test_menos_noites_para_no_minimo(self):
        alternativa = alternativas.alternativa_menos_noites(contexto_base(orcamento=Decimal("3000.00")))
        # 2 noites: 3860 + 892 × 2 = 5644, ainda não cabe
        self.assertEqual(alternativa["novo_total"], Decimal("5644.00"))
        self.assertEqual(alternativa["novo_veredito"], "nao_cabe")
        self.assertIn("2 noites", alternativa["descricao"])

    def test_menos_noites_com_minimo_de_noites(self):
        self.assertIsNone(alternativas.alternativa_menos_noites(contexto_base(noites=2)))

    def test_hotel_mais_simples(self):
        alternativa = alternativas.alternativa_hotel_mais_simples(contexto_base())
        # Ibis José Malhoa (nota 4,2) a 342: economia 40 × 7 noites
        self.assertEqual(alternativa["economia"], Decimal("280.00"))
        self.assertEqual(alternativa["novo_total"], Decimal("9824.00"))
        self.assertIn("Ibis Lisboa Jose Malhoa Hotel", alternativa["descricao"])

    def test_hotel_mais_simples_respeita_nota_minima(self):
        hoteis = [
            {"nome": "Barato ruim", "estrelas": 2, "nota": 3.2, "preco_noite": Decimal("100.00"), "link": None},
            {"nome": "Barato ok", "estrelas": 2, "nota": 3.5, "preco_noite": Decimal("150.00"), "link": None},
        ]
        atual = {"nome": "Atual", "estrelas": 3, "nota": 4.5, "preco_noite": Decimal("200.00"), "link": None}
        contexto = contexto_base(hoteis=hoteis + [atual], hotel=atual)
        alternativa = alternativas.alternativa_hotel_mais_simples(contexto)
        self.assertIn("Barato ok", alternativa["descricao"])
        self.assertEqual(alternativa["economia"], Decimal("350.00"))

    def test_hotel_atual_ja_e_o_mais_barato(self):
        contexto = contexto_base()
        contexto["hotel"] = contexto["hoteis"][0]
        self.assertIsNone(alternativas.alternativa_hotel_mais_simples(contexto))

    def test_gerar_so_as_que_reduzem(self):
        lista = alternativas.gerar_alternativas(contexto_base())
        self.assertEqual([a["tipo"] for a in lista], ["menos_noites", "hotel_mais_simples"])
        for alternativa in lista:
            self.assertGreater(alternativa["economia"], 0)
            self.assertEqual(set(alternativa), {"tipo", "descricao", "novo_total", "novo_veredito", "economia"})


# ---------------------------------------------------------------------------
# simular() de ponta a ponta, com tudo mockado
# ---------------------------------------------------------------------------

def buscar_falso(engine, params):
    return {
        "google_flights": VOOS,
        "google_hotels": HOTEIS,
        "google_flights_calendar": CALENDARIO,
        "google_flights_autocomplete": AUTOCOMPLETE,
    }[engine]


@mock.patch("api.servicos.simulacao.timezone.localdate", return_value=HOJE)
@mock.patch("api.servicos.gemini._chamar_modelo", return_value=resposta_gemini())
@mock.patch("api.servicos.serpapi.buscar", side_effect=buscar_falso)
@override_settings(**CHAVES_TESTE, GEMINI_MODEL="")
class SimularTests(SimpleTestCase):
    def simular(self, **trocas):
        argumentos = {
            "origem": "GRU", "destino": "LIS", "data_ida": IDA, "data_volta": VOLTA,
            "orcamento": Decimal("9000"), "pessoas": 2, "interesses": ["museus", "gastronomia"],
        }
        argumentos.update(trocas)
        return simulacao.simular(**argumentos)

    def test_ponta_a_ponta(self, buscar, chamar, _hoje):
        resultado = self.simular()
        self.assertEqual(resultado["veredito"], "cabe_com_ajustes")
        self.assertEqual(resultado["orcamento"], Decimal("9000.00"))
        self.assertEqual(resultado["noites"], 7)
        self.assertEqual(resultado["gastos"], [
            {"categoria": "passagem", "valor": Decimal("3860.00"), "estimativa_ia": False},
            {"categoria": "hotel", "valor": Decimal("2674.00"), "estimativa_ia": False},
            {"categoria": "comida", "valor": Decimal("2240.00"), "estimativa_ia": True},
            {"categoria": "passeios", "valor": Decimal("980.00"), "estimativa_ia": True},
            {"categoria": "transporte", "valor": Decimal("350.00"), "estimativa_ia": True},
        ])
        self.assertEqual(resultado["total_estimado"], Decimal("10104.00"))
        self.assertEqual(resultado["diferenca"], Decimal("-1104.00"))
        self.assertEqual(resultado["passagem"], {
            "companhia": "LATAM", "preco_por_pessoa": Decimal("1930.00"),
            "preco_total": Decimal("3860.00"), "link_google_voos": VOOS["search_metadata"]["google_flights_url"],
        })
        self.assertEqual(resultado["hotel"]["nome"], "R & Freud B&B")  # mais barato com 3 estrelas e nota >= 4
        self.assertEqual(resultado["hotel"]["preco_total"], Decimal("2674.00"))
        self.assertEqual(len(resultado["precos_por_mes"]), 6)
        self.assertEqual([a["tipo"] for a in resultado["alternativas"]], ["menos_noites", "hotel_mais_simples"])
        self.assertEqual(resultado["buscas_serpapi"], 3)
        self.assertEqual(resultado["versao_prompt"], "v1")
        self.assertEqual(set(resultado), {
            "cidade_destino", "veredito", "orcamento", "total_estimado", "diferenca", "noites", "gastos",
            "passagem", "hotel", "precos_por_mes", "alternativas", "estimativa_ia", "buscas_serpapi",
            "versao_prompt",
        })
        self.assertEqual(resultado["cidade_destino"], "Lisboa")
        self.assertEqual(set(resultado["estimativa_ia"]), {"por_pessoa_dia", "justificativas"})
        engines = [chamada.args[0] for chamada in buscar.call_args_list]
        self.assertEqual(engines, ["google_flights", "google_hotels", "google_flights_calendar"])
        calendario_params = buscar.call_args_list[2].args[1]
        self.assertEqual(calendario_params["date_range_start"], "2027-01-01")
        self.assertEqual(calendario_params["date_range_end"], "2027-06-30")

    def test_cabe_sem_alternativas(self, buscar, chamar, _hoje):
        resultado = self.simular(orcamento=Decimal("20000"))
        self.assertEqual(resultado["veredito"], "cabe")
        self.assertEqual(resultado["diferenca"], Decimal("9896.00"))
        self.assertEqual(resultado["alternativas"], [])

    def test_tres_pessoas_usam_dois_quartos(self, buscar, chamar, _hoje):
        resultado = self.simular(pessoas=3)
        self.assertEqual(resultado["hotel"]["preco_total"], Decimal("5348.00"))  # 382 × 7 × 2
        self.assertEqual(resultado["passagem"]["preco_total"], Decimal("5790.00"))

    def test_destino_fora_do_mapeamento_gasta_uma_busca_a_mais(self, buscar, chamar, _hoje):
        resultado = self.simular(destino="IMP")
        self.assertEqual(resultado["buscas_serpapi"], 4)
        self.assertEqual(buscar.call_args_list[2].args[1]["q"], "Imperatriz")

    def test_gemini_falha_antes_de_gastar_busca(self, buscar, chamar, _hoje):
        chamar.side_effect = ["{quebrado", "{quebrado"]
        with mock.patch("api.servicos.gemini.time.sleep"), self.assertRaises(ErroServicoExterno):
            self.simular()
        buscar.assert_not_called()

    def test_sem_hoteis(self, buscar, chamar, _hoje):
        buscar.side_effect = lambda engine, params: {"properties": []} if engine == "google_hotels" else buscar_falso(engine, params)
        with self.assertRaises(ErroEntrada):
            self.simular()

    def test_entradas_invalidas(self, buscar, chamar, _hoje):
        casos = [
            {"data_volta": date(2027, 3, 9)},          # volta antes da ida
            {"data_volta": IDA},                        # mesmo dia
            {"data_ida": date(2026, 11, 1)},            # passado
            {"data_volta": date(2027, 4, 20)},          # mais de 30 noites
            {"orcamento": Decimal("0")},
            {"orcamento": Decimal("-10")},
            {"orcamento": "abc"},
            {"orcamento": True},
            {"pessoas": 0},
            {"pessoas": True},
            {"pessoas": 10},
            {"pessoas": "2"},
            {"origem": "GR"},
            {"destino": "Lisboa"},
            {"destino": "GRU"},                         # igual à origem
            {"data_ida": "2027-03-10"},
            {"interesses": "museus"},
            {"interesses": ["x"] * 11},
        ]
        for caso in casos:
            with self.subTest(caso=caso), self.assertRaises(ErroEntrada):
                self.simular(**caso)
        buscar.assert_not_called()
        chamar.assert_not_called()

    def test_normaliza_entradas(self, buscar, chamar, _hoje):
        resultado = self.simular(origem=" gru ", destino="lis", orcamento=9000, interesses=None)
        self.assertEqual(resultado["orcamento"], Decimal("9000.00"))
        self.assertEqual(buscar.call_args_list[0].args[1]["departure_id"], "GRU")


class JanelaCalendarioTests(SimpleTestCase):
    @mock.patch("api.servicos.simulacao.timezone.localdate", return_value=HOJE)
    def test_janela(self, _hoje):
        self.assertEqual(simulacao.janela_calendario(IDA), (date(2027, 1, 1), date(2027, 6, 30)))
        # Ida próxima: começa amanhã e cobre 6 meses
        self.assertEqual(simulacao.janela_calendario(date(2026, 12, 5)), (date(2026, 11, 14), date(2027, 4, 30)))

    def test_quartos(self):
        self.assertEqual([simulacao.calcular_quartos(p) for p in (1, 2, 3, 4, 5)], [1, 1, 2, 2, 3])


# ---------------------------------------------------------------------------
# #29 e #30 Comandos de precisão
# ---------------------------------------------------------------------------

CABECALHO_CSV = ",".join(precisao.COLUNAS)


class ComandosPrecisaoBase(SimpleTestCase):
    def setUp(self):
        self.pasta = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        self.csv = Path(self.pasta.name) / "viagens.csv"
        self.csv.write_text("\n".join([
            CABECALHO_CSV,
            "GRU,LIS,2025-03-10,2025-03-17,2,museus;gastronomia,15000,4000,2800,2000,1000,400,Fatura do Felipe",
            "GRU,EZE,2027-03-10,2027-03-17,1,,8000,\"1.930,00\",2500,1500,,300,André",
            "GRU,LIS,2025-01-01,2025-01-05,2,,1,1,1,1,1,1,EXEMPLO - ignorar",
        ]) + "\n", encoding="utf-8")
        self.saida = Path(self.pasta.name) / "saida.md"


class LeituraCsvTests(ComandosPrecisaoBase):
    def test_le_e_ignora_exemplo(self):
        viagens = precisao.ler_viagens(self.csv)
        self.assertEqual(len(viagens), 2)
        self.assertEqual(viagens[0]["interesses"], ["museus", "gastronomia"])
        self.assertEqual(viagens[1]["real"]["passagem"], Decimal("1930.00"))
        self.assertIsNone(viagens[1]["real"]["passeios"])

    def test_csv_do_repositorio_so_tem_exemplo(self):
        self.assertEqual(precisao.ler_viagens(precisao.CSV_PADRAO), [])

    def test_colunas_faltando(self):
        self.csv.write_text("origem,destino\nGRU,LIS\n", encoding="utf-8")
        with self.assertRaises(precisao.ErroCSV):
            precisao.ler_viagens(self.csv)

    def test_erro_percentual_e_datas(self):
        self.assertEqual(precisao.erro_percentual(Decimal("110"), Decimal("100")), Decimal("10.0"))
        self.assertEqual(precisao.erro_percentual(Decimal("90"), Decimal("100")), Decimal("10.0"))
        self.assertIsNone(precisao.erro_percentual(Decimal("90"), None))
        self.assertIsNone(precisao.erro_percentual(Decimal("90"), Decimal("0")))
        self.assertEqual(
            precisao.deslocar_para_o_futuro(date(2025, 3, 10), date(2025, 3, 17), HOJE),
            (date(2027, 3, 10), date(2027, 3, 17), 2),
        )
        self.assertEqual(
            precisao.deslocar_para_o_futuro(date(2024, 2, 29), date(2024, 3, 3), HOJE),
            (date(2027, 2, 28), date(2027, 3, 3), 3),
        )


def simulacao_falsa(origem, destino, ida, volta, orcamento, pessoas, interesses, versao_prompt="v1"):
    valores = {"passagem": "4400", "hotel": "2800", "comida": "2200", "passeios": "800", "transporte": "400"}
    gastos = [{"categoria": c, "valor": Decimal(v), "estimativa_ia": c in precisao.CATEGORIAS_IA}
              for c, v in valores.items()]
    total = veredito.somar_gastos(gastos)
    return {"gastos": gastos, "total_estimado": total, "veredito": veredito.decidir_veredito(total, orcamento),
            "buscas_serpapi": 3}


@mock.patch("django.utils.timezone.localdate", return_value=HOJE)
class TestePrecisaoComandoTests(ComandosPrecisaoBase):
    @mock.patch("api.management.commands.teste_precisao.simular", side_effect=simulacao_falsa)
    def test_gera_resultado(self, simular, _hoje):
        saida = StringIO()
        call_command("teste_precisao", csv=str(self.csv), saida=str(self.saida), sim=True, stdout=saida)
        self.assertEqual(simular.call_count, 2)
        self.assertEqual(simular.call_args_list[0].args[2], date(2027, 3, 10))  # 2025 deslocado
        texto = self.saida.read_text(encoding="utf-8")
        self.assertIn("# Resultado do teste de precisão", texto)
        # passagem: viagem 1 erra 10% (4400 vs 4000); viagem 2 erra 128% (4400 vs 1930)
        self.assertIn("| passagem | 69,0% | 2 |", texto)
        self.assertIn("| passeios | 20,0% | 1 |", texto)  # viagem 2 sem valor real
        # total: viagem 1 erra 3,9% (10600 vs 10200); viagem 2 compara só as 4
        # categorias com valor real e erra 57,3% (9800 vs 6230)
        self.assertIn("| **Total** | 30,6% | 2 |", texto)
        self.assertIn("1 viagem(ns) não têm valor real em todas as categorias", texto)
        self.assertIn("Erro médio geral", texto)
        self.assertIn("1 viagem(ns) já aconteceram", texto)
        self.assertIn("até 6 buscas", saida.getvalue())

    @mock.patch("api.management.commands.teste_precisao.simular")
    @mock.patch("builtins.input", return_value="n")
    def test_pede_confirmacao(self, _input, simular, _hoje):
        call_command("teste_precisao", csv=str(self.csv), saida=str(self.saida), stdout=StringIO())
        simular.assert_not_called()
        self.assertFalse(self.saida.exists())

    @mock.patch("api.management.commands.teste_precisao.simular")
    def test_falha_de_uma_viagem_nao_para_as_outras(self, simular, _hoje):
        simular.side_effect = [ErroServicoExterno("SerpApi fora do ar"), simulacao_falsa(*[None] * 4, Decimal("1"), 1, [])]
        call_command("teste_precisao", csv=str(self.csv), saida=str(self.saida), sim=True, stdout=StringIO())
        texto = self.saida.read_text(encoding="utf-8")
        self.assertIn("SerpApi fora do ar", texto)
        self.assertIn("| 2 | GRU→EZE", texto)

    def test_csv_sem_viagens(self, _hoje):
        self.csv.write_text(CABECALHO_CSV + "\n", encoding="utf-8")
        with self.assertRaises(CommandError):
            call_command("teste_precisao", csv=str(self.csv), sim=True, stdout=StringIO())


@mock.patch("django.utils.timezone.localdate", return_value=HOJE)
@override_settings(**CHAVES_TESTE, GEMINI_MODEL="")
class CompararPromptsComandoTests(ComandosPrecisaoBase):
    @mock.patch("api.servicos.serpapi.buscar")
    @mock.patch("api.servicos.gemini._chamar_modelo")
    def test_compara_v1_e_v2_sem_serpapi(self, chamar, buscar, _hoje):
        def responder(texto):
            # v2 erra menos de propósito: comida mais perto do real
            return resposta_gemini(comida=150 if "estação do ano" in texto else 250)
        chamar.side_effect = responder
        call_command("comparar_prompts", csv=str(self.csv), saida=str(self.saida), sim=True, stdout=StringIO())
        buscar.assert_not_called()
        self.assertEqual(chamar.call_count, 4)  # 2 viagens × 2 versões
        texto = self.saida.read_text(encoding="utf-8")
        self.assertIn("# Comparação de versões do prompt", texto)
        linha_comida = next(linha for linha in texto.splitlines() if linha.startswith("| comida |"))
        self.assertTrue(linha_comida.endswith("| v2 |"))
        self.assertIn("**Média geral**", texto)

    @mock.patch("api.servicos.gemini._chamar_modelo")
    @mock.patch("builtins.input", return_value="")
    def test_pede_confirmacao(self, _input, chamar, _hoje):
        call_command("comparar_prompts", csv=str(self.csv), saida=str(self.saida), stdout=StringIO())
        chamar.assert_not_called()

    def test_versao_desconhecida(self, _hoje):
        with self.assertRaises(CommandError):
            call_command("comparar_prompts", csv=str(self.csv), versoes=["v1", "v9"], sim=True, stdout=StringIO())

    def test_vencedora(self, _hoje):
        from api.management.commands.comparar_prompts import vencedora
        self.assertEqual(vencedora({"v1": {"geral": Decimal("20")}, "v2": {"geral": Decimal("10")}}, "geral"), "v2")
        self.assertIsNone(vencedora({"v1": {"geral": Decimal("10")}, "v2": {"geral": Decimal("10")}}, "geral"))
        self.assertIsNone(vencedora({"v1": {"geral": None}}, "geral"))
