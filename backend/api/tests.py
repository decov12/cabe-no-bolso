from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()

SENHA_BOA = "viagem-barata-2026"


class CadastroTests(APITestCase):
    url = reverse("cadastro")

    def test_cadastro_com_sucesso(self):
        resposta = self.client.post(
            self.url,
            {"email": "Ana@Exemplo.com", "senha": SENHA_BOA, "nome": "Ana"},
            format="json",
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", resposta.data)
        self.assertEqual(resposta.data["usuario"]["email"], "ana@exemplo.com")
        self.assertEqual(resposta.data["usuario"]["nome"], "Ana")
        self.assertNotIn("senha", resposta.data["usuario"])

        usuario = User.objects.get(email="ana@exemplo.com")
        self.assertEqual(usuario.username, "ana@exemplo.com")
        self.assertTrue(usuario.check_password(SENHA_BOA))
        self.assertEqual(Token.objects.get(user=usuario).key, resposta.data["token"])

    def test_cadastro_sem_nome(self):
        resposta = self.client.post(
            self.url, {"email": "bia@exemplo.com", "senha": SENHA_BOA}, format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resposta.data["usuario"]["nome"], "")

    def test_email_repetido(self):
        User.objects.create_user(
            username="ana@exemplo.com", email="ana@exemplo.com", password=SENHA_BOA
        )
        resposta = self.client.post(
            self.url, {"email": "ANA@exemplo.com", "senha": SENHA_BOA}, format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposta.data["email"], ["Já existe uma conta com este e-mail."])
        self.assertEqual(User.objects.count(), 1)

    def test_senha_curta(self):
        resposta = self.client.post(
            self.url, {"email": "ana@exemplo.com", "senha": "abc123"}, format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            resposta.data["senha"], ["A senha precisa ter pelo menos 8 caracteres."]
        )
        self.assertFalse(User.objects.exists())

    def test_email_invalido(self):
        resposta = self.client.post(
            self.url, {"email": "nao-e-email", "senha": SENHA_BOA}, format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", resposta.data)


class LoginTests(APITestCase):
    url = reverse("login")

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="ana@exemplo.com", email="ana@exemplo.com", password=SENHA_BOA
        )

    def test_login_certo(self):
        resposta = self.client.post(
            self.url, {"email": "Ana@Exemplo.com", "senha": SENHA_BOA}, format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(resposta.data["token"], Token.objects.get(user=self.usuario).key)
        self.assertEqual(resposta.data["usuario"]["email"], "ana@exemplo.com")

    def test_login_senha_errada(self):
        resposta = self.client.post(
            self.url, {"email": "ana@exemplo.com", "senha": "senha-errada"}, format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposta.data["non_field_errors"], ["E-mail ou senha incorretos."])
        self.assertNotIn("token", resposta.data)

    def test_login_email_inexistente(self):
        resposta = self.client.post(
            self.url, {"email": "ninguem@exemplo.com", "senha": SENHA_BOA}, format="json"
        )
        self.assertEqual(resposta.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(resposta.data["non_field_errors"], ["E-mail ou senha incorretos."])


class EuTests(APITestCase):
    url = reverse("eu")

    def setUp(self):
        self.usuario = User.objects.create_user(
            username="ana@exemplo.com",
            email="ana@exemplo.com",
            password=SENHA_BOA,
            first_name="Ana",
        )
        self.token = Token.objects.create(user=self.usuario)

    def test_eu_com_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_200_OK)
        self.assertEqual(
            resposta.data, {"id": self.usuario.id, "email": "ana@exemplo.com", "nome": "Ana"}
        )

    def test_eu_sem_token(self):
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_eu_com_token_invalido(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token token-que-nao-existe")
        resposta = self.client.get(self.url)
        self.assertEqual(resposta.status_code, status.HTTP_401_UNAUTHORIZED)
