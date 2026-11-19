from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import limites
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

        # Limite diário (#25): conferido antes de simular, para não gastar cota.
        pode, situacao = limites.pode_simular(request.user)
        if not pode:
            return Response(
                {
                    "erro": f"Você já fez {situacao['limite']} simulações hoje, que é o limite "
                            "diário. Tente de novo amanhã ou abra uma simulação do histórico.",
                    "limite_diario": situacao,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            resultado = simular(**dados)
        except ErroEntrada as erro:
            return Response({"erro": erro.mensagem}, status=status.HTTP_400_BAD_REQUEST)
        except ErroServicoExterno as erro:
            return Response({"erro": erro.mensagem}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        simulacao = Simulacao.objects.create(
            usuario=request.user,
            **dados,
            cidade_destino=resultado.get("cidade_destino") or "",
            veredito=resultado["veredito"],
            total_estimado=resultado["total_estimado"],
            diferenca=resultado["diferenca"],
            resultado=para_json(resultado),
        )
        return Response(
            SimulacaoDetalheSerializer(simulacao).data, status=status.HTTP_201_CREATED
        )


class SimulacaoDetalheView(APIView):
    """GET    /api/simulacoes/<id>/ — resultado completo.
    DELETE /api/simulacoes/<id>/ — apaga do histórico.
    De outro usuário: 404."""

    def get(self, request, pk):
        simulacao = get_object_or_404(Simulacao, pk=pk, usuario=request.user)
        return Response(SimulacaoDetalheSerializer(simulacao).data)

    def delete(self, request, pk):
        get_object_or_404(Simulacao, pk=pk, usuario=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LimiteView(APIView):
    """GET /api/simulacoes/limite/ — {"limite", "usadas_hoje", "restantes"} de hoje."""

    def get(self, request):
        return Response(limites.situacao_simulacoes(request.user))


class LugaresView(APIView):
    """GET /api/lugares/?q=texto — sugestões de cidades e aeroportos (SerpApi).

    O mesmo texto em 24 horas vem do cache. Há um limite diário por usuário
    (LIMITE_LUGARES_DIA), porque cada texto novo gasta 1 busca."""

    def get(self, request):
        texto = request.query_params.get("q", "").strip()
        if len(texto) < 2:
            return Response([])  # não gasta busca
        if not limites.registrar_busca_de_lugar(request.user):
            return Response(
                {"erro": "Você fez muitas buscas de lugar hoje. Tente de novo amanhã."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            return Response(buscar_lugares(texto))
        except ErroServicoExterno as erro:
            return Response({"erro": erro.mensagem}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
