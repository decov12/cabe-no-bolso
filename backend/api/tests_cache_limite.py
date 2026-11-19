"""Testes do cache de 24 horas (#24), do limite diário (#25) e de apagar do histórico.

Nenhum teste chama a SerpApi ou o Gemini de verdade: as respostas vêm de fixtures/.
"""

from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest import mock

from django.core.cache import cache as cache_django
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Simulacao
from api.servicos import cache, gemini, serpapi
from api.servicos.erros import ErroServicoExterno
from api.tests_servicos import (
    CHAVES_TESTE, HOJE, IDA, VOLTA, VOOS, _rede_proibida, buscar_falso, resposta_gemini, resposta_http,
)
from api.tests_simulacoes import PEDIDO, criar_simulacao, criar_usuario

# Cache que guarda de verdade (na memória), só para os testes que precisam dele.
CACHE_DE_VERDADE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

# Relógio parado em HOJE (13/11/2026): IDA e VOLTA continuam no futuro e a
# simulação é gravada no mesmo "hoje" que o limite diário confere.
AGORA = datetime(2026, 11, 13, 15, 0, tzinfo=dt_timezone.utc)

_trava_rede = [
    mock.patch("api.servicos.serpapi.requests.get", side_effect=_rede_proibida),
    mock.patch("api.servicos.gemini.genai.Client", side_effect=_rede_proibida),
]


def setUpModule():
    for trava in _trava_rede:
        trava.start()


def tearDownModule():
    for trava in _trava_rede:
        trava.stop()


class ComUsuario(APITestCase):
    def setUp(self):
        self.usuario, token = criar_usuario("ana@exemplo.com")
        self.outro, _ = criar_usuario("bia@exemplo.com")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


# ---------------------------------------------------------------------------
# POST /api/simulacoes/ de ponta a ponta, com o simular() de verdade
# ---------------------------------------------------------------------------

@mock.patch("django.utils.timezone.now", new=lambda: AGORA)
@mock.patch("api.servicos.simulacao.timezone.localdate", return_value=HOJE)
@mock.patch("api.servicos.gemini._chamar_modelo", return_value=resposta_gemini())
@mock.patch("api.servicos.serpapi.buscar", side_effect=buscar_falso)
@override_settings(**CHAVES_TESTE, GEMINI_MODEL="", LIMITE_SIMULACOES_DIA=5)
class PontaAPontaTests(ComUsuario):
    def test_simula_com_as_fixtures_e_salva_a_cidade(self, buscar, chamar, _hoje):
        resposta = self.client.post(reverse("simulacoes"), PEDIDO, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED, resposta.data)

        dados = resposta.json()
        self.assertEqual(dados["cidade_destino"], "Lisboa")
        self.assertEqual(dados["veredito"], "cabe_com_ajustes")
        self.assertEqual(dados["total_estimado"], "10104.00")
        self.assertEqual(dados["estimativa_ia"]["por_pessoa_dia"]["comida"], "160.00")
        self.assertIn("comida", dados["estimativa_ia"]["justificativas"])
        self.assertEqual(Simulacao.objects.get().cidade_destino, "Lisboa")

        historico = self.client.get(reverse("simulacoes")).json()
        self.assertEqual(historico[0]["cidade_destino"], "Lisboa")

        limite = self.client.get(reverse("simulacoes-limite")).json()
        self.assertEqual(limite, {"limite": 5, "usadas_hoje": 1, "restantes": 4})


# ---------------------------------------------------------------------------
# Limite diário (#25)
# ---------------------------------------------------------------------------

@override_settings(LIMITE_SIMULACOES_DIA=2)
@mock.patch("api.views.simular")
class LimiteDiarioTests(ComUsuario):
    url = reverse("simulacoes")

    def test_bloqueia_depois_do_limite_sem_gastar_cota(self, simular):
        criar_simulacao(self.usuario)
        criar_simulacao(self.usuario)
        resposta = self.client.post(self.url, PEDIDO, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("limite diário", resposta.data["erro"])
        self.assertEqual(resposta.data["limite_diario"], {"limite": 2, "usadas_hoje": 2, "restantes": 0})
        simular.assert_not_called()
        self.assertEqual(Simulacao.objects.count(), 2)

    def test_simulacoes_de_ontem_e_de_outros_nao_contam(self, simular):
        antiga = criar_simulacao(self.usuario)
        Simulacao.objects.filter(pk=antiga.pk).update(criado_em=timezone.now() - timedelta(days=1))
        criar_simulacao(self.outro)
        criar_simulacao(self.outro)
        resposta = self.client.get(reverse("simulacoes-limite"))
        self.assertEqual(resposta.data, {"limite": 2, "usadas_hoje": 0, "restantes": 2})

    def test_equipe_nao_tem_limite(self, simular):
        self.usuario.is_staff = True
        self.usuario.save()
        criar_simulacao(self.usuario)
        criar_simulacao(self.usuario)
        resposta = self.client.get(reverse("simulacoes-limite"))
        self.assertEqual(resposta.data, {"limite": None, "usadas_hoje": 2, "restantes": None})

    def test_rota_do_limite_exige_token(self, simular):
        self.client.credentials()
        resposta = self.client.get(reverse("simulacoes-limite"))
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)


@mock.patch("api.views.buscar_lugares", return_value=[])
@override_settings(CACHES=CACHE_DE_VERDADE, LIMITE_LUGARES_DIA=2)
class LimiteLugaresTests(ComUsuario):
    def setUp(self):
        super().setUp()
        cache_django.clear()

    def test_bloqueia_depois_do_limite(self, buscar_lugares):
        url = reverse("lugares")
        for _ in range(2):
            self.assertEqual(self.client.get(url, {"q": "Lisboa"}).status_code, status.HTTP_200_OK)
        resposta = self.client.get(url, {"q": "Lisboa"})
        self.assertEqual(resposta.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertEqual(buscar_lugares.call_count, 2)

    def test_texto_curto_nao_conta(self, buscar_lugares):
        url = reverse("lugares")
        for _ in range(5):
            self.client.get(url, {"q": "L"})
        self.assertEqual(self.client.get(url, {"q": "Lisboa"}).status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# DELETE /api/simulacoes/<id>/
# ---------------------------------------------------------------------------

class ApagarSimulacaoTests(ComUsuario):
    def test_apaga_a_propria(self):
        simulacao = criar_simulacao(self.usuario)
        resposta = self.client.delete(reverse("simulacao-detalhe", args=[simulacao.id]))
        self.assertEqual(resposta.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Simulacao.objects.exists())

    def test_nao_apaga_a_de_outro_usuario(self):
        alheia = criar_simulacao(self.outro)
        resposta = self.client.delete(reverse("simulacao-detalhe", args=[alheia.id]))
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Simulacao.objects.filter(pk=alheia.pk).exists())


# ---------------------------------------------------------------------------
# Cache de 24 horas (#24)
# ---------------------------------------------------------------------------

@override_settings(**CHAVES_TESTE, GEMINI_MODEL="", CACHES=CACHE_DE_VERDADE)
class CacheTests(SimpleTestCase):
    def setUp(self):
        cache_django.clear()

    def test_chave_nao_depende_da_ordem_dos_parametros(self):
        self.assertEqual(
            cache.montar_chave("serpapi", "google_flights", {"a": 1, "b": 2}),
            cache.montar_chave("serpapi", "google_flights", {"b": 2, "a": 1}),
        )
        self.assertNotEqual(
            cache.montar_chave("serpapi", "google_flights", {"a": 1}),
            cache.montar_chave("serpapi", "google_hotels", {"a": 1}),
        )

    @mock.patch("api.servicos.serpapi.requests.get")
    def test_mesma_busca_nao_gasta_cota_de_novo(self, get):
        get.return_value = resposta_http(VOOS)
        params = {"departure_id": "GRU", "arrival_id": "LIS"}
        self.assertEqual(serpapi.buscar("google_flights", params), VOOS)
        self.assertEqual(serpapi.buscar("google_flights", dict(params)), VOOS)
        self.assertEqual(get.call_count, 1)

        serpapi.buscar("google_flights", {**params, "arrival_id": "OPO"})  # outra rota
        self.assertEqual(get.call_count, 2)

    @mock.patch("api.servicos.serpapi.time.sleep")
    @mock.patch("api.servicos.serpapi.requests.get")
    def test_falha_nao_fica_no_cache(self, get, _sleep):
        get.side_effect = [resposta_http({"error": "x"}, status=500)] * 2 + [resposta_http(VOOS)]
        with self.assertRaises(ErroServicoExterno):
            serpapi.buscar("google_flights", {})
        self.assertEqual(serpapi.buscar("google_flights", {}), VOOS)
        self.assertEqual(get.call_count, 3)

    @mock.patch("api.servicos.serpapi.requests.get")
    def test_cache_quebrado_nao_derruba_a_busca(self, get):
        get.return_value = resposta_http(VOOS)
        with mock.patch.object(cache.cache, "get", side_effect=RuntimeError("tabela não existe")), \
                mock.patch.object(cache.cache, "set", side_effect=RuntimeError("tabela não existe")), \
                self.assertLogs("api.servicos.cache", level="WARNING"):
            self.assertEqual(serpapi.buscar("google_flights", {}), VOOS)

    @mock.patch("api.servicos.gemini._chamar_modelo", return_value=resposta_gemini())
    def test_mesma_viagem_nao_chama_o_gemini_de_novo(self, chamar):
        argumentos = ("Lisboa (LIS)", IDA, VOLTA, 2, ["museus"])
        primeira = gemini.estimar_gastos_locais(*argumentos)
        segunda = gemini.estimar_gastos_locais(*argumentos)
        self.assertEqual(primeira, segunda)
        self.assertEqual(chamar.call_count, 1)

        gemini.estimar_gastos_locais("Lisboa (LIS)", IDA, VOLTA, 3, ["museus"])  # outro nº de pessoas
        self.assertEqual(chamar.call_count, 2)
