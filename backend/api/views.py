from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CadastroSerializer, LoginSerializer, UsuarioSerializer


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
