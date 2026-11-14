from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Simulacao
from .serializers import (
    CadastroSerializer,
    LoginSerializer,
    SimulacaoDetalheSerializer,
    SimulacaoEntradaSerializer,
    SimulacaoResumoSerializer,
    UsuarioSerializer,
    para_json,
)
from .servicos.erros import ErroEntrada, ErroServicoExterno
from .servicos.serpapi import buscar_lugares
from .servicos.simulacao import simular


def resposta_com_token(usuario, codigo):
    token, _ = Token.objects.get_or_create(user=usuario)
    return Response(
        {"token": token.key, "usuario": UsuarioSerializer(usuario).data},
        status=codigo,
    )


class CadastroView(APIView):
    """POST /api/auth/cadastro/ — cria a conta e já devolve o token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = CadastroSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        usuario = serializer.save()
        return resposta_com_token(usuario, status.HTTP_201_CREATED)


class LoginView(APIView):
    """POST /api/auth/login/ — troca e-mail e senha pelo token."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return resposta_com_token(serializer.validated_data["usuario"], status.HTTP_200_OK)


class EuView(APIView):
    """GET /api/auth/eu/ — devolve o usuário dono do token (exige login)."""

    def get(self, request):
        return Response(UsuarioSerializer(request.user).data)


class SimulacoesView(APIView):
    """GET /api/simulacoes/ — histórico do usuário logado (resumido).
    POST /api/simulacoes/ — faz uma simulação nova e salva."""

    def get(self, request):
        simulacoes = Simulacao.objects.filter(usuario=request.user)
        return Response(SimulacaoResumoSerializer(simulacoes, many=True).data)

    def post(self, request):
        entrada = SimulacaoEntradaSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        dados = entrada.validated_data

        try:
            resultado = simular(**dados)
        except ErroEntrada as erro:
            return Response({"erro": erro.mensagem}, status=status.HTTP_400_BAD_REQUEST)
        except ErroServicoExterno as erro:
            return Response({"erro": erro.mensagem}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        simulacao = Simulacao.objects.create(
            usuario=request.user,
            **dados,
            veredito=resultado["veredito"],
            total_estimado=resultado["total_estimado"],
            diferenca=resultado["diferenca"],
            resultado=para_json(resultado),
        )
        return Response(
            SimulacaoDetalheSerializer(simulacao).data, status=status.HTTP_201_CREATED
        )


class SimulacaoDetalheView(APIView):
    """GET /api/simulacoes/<id>/ — resultado completo. De outro usuário: 404."""

    def get(self, request, pk):
        simulacao = get_object_or_404(Simulacao, pk=pk, usuario=request.user)
        return Response(SimulacaoDetalheSerializer(simulacao).data)


class LugaresView(APIView):
    """GET /api/lugares/?q=texto — sugestões de cidades e aeroportos (SerpApi)."""

    def get(self, request):
        texto = request.query_params.get("q", "").strip()
        if len(texto) < 2:
            return Response([])  # não gasta busca
        try:
            return Response(buscar_lugares(texto))
        except ErroServicoExterno as erro:
            return Response({"erro": erro.mensagem}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
