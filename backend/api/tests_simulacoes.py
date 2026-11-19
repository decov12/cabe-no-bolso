"""Testes das rotas de simulação e de lugares (tarefa #16).

simular() e buscar_lugares() são sempre substituídos por mocks: nenhum teste
chama a SerpApi ou o Gemini de verdade.
"""

from datetime import date
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from api.models import Simulacao
from api.servicos.erros import ErroEntrada, ErroServicoExterno

User = get_user_model()


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


PEDIDO = {
    "origem": "gru",
    "destino": "LIS",
    "data_ida": "2027-03-10",
    "data_volta": "2027-03-17",
    "orcamento": "9000",
    "pessoas": 2,
    "interesses": ["museus", "gastronomia"],
}

# Saída de simular() no formato de docs/servicos-ia.md (com Decimal, como a de verdade).
RESULTADO = {
    "veredito": "cabe_com_ajustes",
    "orcamento": Decimal("9000.00"),
    "total_estimado": Decimal("10104.00"),
    "diferenca": Decimal("-1104.00"),
    "noites": 7,
    "gastos": [
        {"categoria": "passagem", "valor": Decimal("3860.00"), "estimativa_ia": False},
        {"categoria": "hotel", "valor": Decimal("2674.00"), "estimativa_ia": False},
        {"categoria": "comida", "valor": Decimal("2240.00"), "estimativa_ia": True},
        {"categoria": "passeios", "valor": Decimal("980.00"), "estimativa_ia": True},
        {"categoria": "transporte", "valor": Decimal("350.00"), "estimativa_ia": True},
    ],
    "passagem": {
        "companhia": "LATAM",
        "preco_por_pessoa": Decimal("1930.00"),
        "preco_total": Decimal("3860.00"),
        "link_google_voos": "https://www.google.com/travel/flights?exemplo",
    },
    "hotel": {
        "nome": "R & Freud B&B",
        "estrelas": 3,
        "nota": 4.5,
        "preco_noite": Decimal("382.00"),
        "preco_total": Decimal("2674.00"),
        "link": None,
    },
    "precos_por_mes": [{"mes": "2027-03", "menor_preco": Decimal("1800.00")}],
    "alternativas": [
        {
            "tipo": "menos_noites",
            "descricao": "Ficar 5 noites em vez de 7.",
            "novo_total": Decimal("8320.00"),
            "novo_veredito": "cabe",
            "economia": Decimal("1784.00"),
        }
    ],
    "buscas_serpapi": 3,
    "versao_prompt": "v1",
}

LUGARES = [
    {"tipo": "cidade", "nome": "Lisboa", "codigo": "LIS", "pais": "Portugal",
     "descricao": "Capital de Portugal"},
    {"tipo": "aeroporto", "nome": "Aeroporto Humberto Delgado", "codigo": "LIS",
     "pais": "Portugal", "cidade": "Lisboa", "distancia": "5 km"},
]


def criar_usuario(email):
    usuario = User.objects.create_user(username=email, email=email, password="viagem-barata-2026")
    return usuario, Token.objects.create(user=usuario)


def criar_simulacao(usuario, **trocas):
    dados = {
        "usuario": usuario, "origem": "GRU", "destino": "LIS",
        "data_ida": date(2027, 3, 10), "data_volta": date(2027, 3, 17),
        "orcamento": Decimal("9000.00"), "pessoas": 2, "interesses": [],
        "veredito": "cabe", "total_estimado": Decimal("8000.00"),
        "diferenca": Decimal("1000.00"),
        "resultado": {"veredito": "cabe", "total_estimado": "8000.00"},
    }
    dados.update(trocas)
    return Simulacao.objects.create(**dados)


class ComTokenTestCase(APITestCase):
    def setUp(self):
        self.usuario, token = criar_usuario("ana@exemplo.com")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


class SemTokenTests(APITestCase):
    def test_rotas_exigem_token(self):
        rotas = [
            ("get", reverse("simulacoes")),
            ("post", reverse("simulacoes")),
            ("get", reverse("simulacao-detalhe", args=[1])),
            ("get", reverse("lugares") + "?q=Lisboa"),
        ]
        for metodo, url in rotas:
            with self.subTest(metodo=metodo, url=url):
                resposta = getattr(self.client, metodo)(url, format="json")
                self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)


@mock.patch("api.views.simular")
class CriarSimulacaoTests(ComTokenTestCase):
    url = reverse("simulacoes")

    def test_sucesso_salva_e_devolve_resultado(self, simular):
        simular.return_value = RESULTADO
        resposta = self.client.post(self.url, PEDIDO, format="json")

        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        simular.assert_called_once_with(
            origem="GRU", destino="LIS",
            data_ida=date(2027, 3, 10), data_volta=date(2027, 3, 17),
            orcamento=Decimal("9000.00"), pessoas=2,
            interesses=["museus", "gastronomia"],
        )

        simulacao = Simulacao.objects.get()
        self.assertEqual(simulacao.usuario, self.usuario)
        self.assertEqual(simulacao.veredito, "cabe_com_ajustes")
        self.assertEqual(simulacao.total_estimado, Decimal("10104.00"))
        self.assertEqual(simulacao.diferenca, Decimal("-1104.00"))
        self.assertEqual(simulacao.resultado["gastos"][0]["valor"], "3860.00")

        dados = resposta.json()
        self.assertEqual(dados["id"], simulacao.id)
        self.assertIn("criado_em", dados)
        self.assertEqual(dados["origem"], "GRU")
        self.assertEqual(dados["veredito"], "cabe_com_ajustes")
        self.assertEqual(dados["orcamento"], "9000.00")
        self.assertEqual(dados["diferenca"], "-1104.00")
        self.assertEqual(dados["passagem"]["preco_total"], "3860.00")
        self.assertEqual(dados["hotel"]["nota"], 4.5)
        self.assertEqual(dados["alternativas"][0]["economia"], "1784.00")

    def test_erro_entrada_vira_400(self, simular):
        simular.side_effect = ErroEntrada("A data de volta precisa ser depois da data de ida.")
        resposta = self.client.post(self.url, PEDIDO, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposta.json(), {"erro": "A data de volta precisa ser depois da data de ida."})
        self.assertFalse(Simulacao.objects.exists())

    def test_erro_servico_externo_vira_503(self, simular):
        simular.side_effect = ErroServicoExterno("A busca de preços está fora do ar. Tente de novo.")
        resposta = self.client.post(self.url, PEDIDO, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(resposta.json(), {"erro": "A busca de preços está fora do ar. Tente de novo."})
        self.assertFalse(Simulacao.objects.exists())

    def test_campos_faltando_400_por_campo(self, simular):
        resposta = self.client.post(self.url, {}, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        erros = resposta.json()
        for campo in ["origem", "destino", "data_ida", "data_volta", "orcamento", "pessoas"]:
            self.assertIn(campo, erros)
        self.assertEqual(erros["orcamento"], ["Informe o orçamento."])
        self.assertNotIn("interesses", erros)  # opcional
        simular.assert_not_called()

    def test_formato_invalido_400_por_campo(self, simular):
        pedido = {**PEDIDO, "origem": "GRUX", "data_ida": "10/03/2027", "pessoas": 12,
                  "orcamento": "abc", "interesses": [f"i{n}" for n in range(11)]}
        resposta = self.client.post(self.url, pedido, format="json")
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        erros = resposta.json()
        self.assertEqual(erros["origem"], ["Use o código do aeroporto de origem com 3 letras (ex.: GRU)."])
        self.assertEqual(erros["data_ida"], ["Data de ida inválida. Use o formato AAAA-MM-DD."])
        self.assertEqual(erros["pessoas"], ["O número de pessoas pode ser no máximo 9."])
        self.assertIn("orcamento", erros)
        self.assertEqual(erros["interesses"], ["Escolha no máximo 10 interesses."])
        simular.assert_not_called()


class ListarSimulacoesTests(ComTokenTestCase):
    url = reverse("simulacoes")

    def test_lista_so_do_proprio_usuario_mais_recente_primeiro(self):
        outro, _ = criar_usuario("bia@exemplo.com")
        antiga = criar_simulacao(self.usuario, destino="EZE")
        nova = criar_simulacao(self.usuario, destino="LIS")
        criar_simulacao(outro, destino="MAD")

        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        dados = resposta.json()
        self.assertEqual([item["id"] for item in dados], [nova.id, antiga.id])
        self.assertEqual(
            set(dados[0]),
            {"id", "origem", "destino", "cidade_destino", "data_ida", "data_volta",
             "orcamento", "veredito", "total_estimado", "criado_em"},
        )
        self.assertEqual(dados[0]["orcamento"], "9000.00")

    def test_lista_vazia(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.json(), [])


class DetalheSimulacaoTests(ComTokenTestCase):
    def test_detalhe_do_proprio_usuario(self):
        simulacao = criar_simulacao(self.usuario)
        resposta = self.client.get(reverse("simulacao-detalhe", args=[simulacao.id]))
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        dados = resposta.json()
        self.assertEqual(dados["id"], simulacao.id)
        self.assertEqual(dados["total_estimado"], "8000.00")
        self.assertEqual(dados["destino"], "LIS")

    def test_detalhe_de_outro_usuario_404(self):
        outro, _ = criar_usuario("bia@exemplo.com")
        simulacao = criar_simulacao(outro)
        resposta = self.client.get(reverse("simulacao-detalhe", args=[simulacao.id]))
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)

    def test_detalhe_inexistente_404(self):
        resposta = self.client.get(reverse("simulacao-detalhe", args=[999]))
        self.assertEqual(resposta.status_code, status.HTTP_404_NOT_FOUND)


@mock.patch("api.views.buscar_lugares")
class LugaresTests(ComTokenTestCase):
    url = reverse("lugares")

    def test_sucesso(self, buscar_lugares):
        buscar_lugares.return_value = LUGARES
        resposta = self.client.get(self.url, {"q": " Lisboa "})
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.json(), LUGARES)
        buscar_lugares.assert_called_once_with("Lisboa")

    def test_q_curta_nao_gasta_busca(self, buscar_lugares):
        for q in [None, "", "L", " a "]:
            with self.subTest(q=q):
                resposta = self.client.get(self.url, {} if q is None else {"q": q})
                self.assertEqual(resposta.status_code, status.HTTP_200_OK)
                self.assertEqual(resposta.json(), [])
        buscar_lugares.assert_not_called()

    def test_erro_servico_externo_vira_503(self, buscar_lugares):
        buscar_lugares.side_effect = ErroServicoExterno("A busca de lugares falhou. Tente de novo.")
        resposta = self.client.get(self.url, {"q": "Lisboa"})
        self.assertEqual(resposta.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(resposta.json(), {"erro": "A busca de lugares falhou. Tente de novo."})
