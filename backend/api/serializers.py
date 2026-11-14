from datetime import date
from decimal import Decimal

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Simulacao

User = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    """Dados públicos do usuário devolvidos pela API (nunca a senha)."""

    nome = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "nome"]


class CadastroSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "Informe o e-mail.",
            "blank": "Informe o e-mail.",
            "invalid": "Informe um e-mail válido.",
        }
    )
    senha = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False,
        error_messages={
            "required": "Informe a senha.",
            "blank": "Informe a senha.",
            "min_length": "A senha precisa ter pelo menos 8 caracteres.",
        },
    )
    nome = serializers.CharField(
        required=False, allow_blank=True, max_length=150, default=""
    )

    def validate_email(self, valor):
        email = valor.strip().lower()
        if User.objects.filter(username__iexact=email).exists():
            raise serializers.ValidationError("Já existe uma conta com este e-mail.")
        return email

    def validate(self, dados):
        # Validadores de senha do Django (senha comum, só números, parecida com o e-mail).
        usuario_temporario = User(username=dados["email"], email=dados["email"])
        try:
            validate_password(dados["senha"], user=usuario_temporario)
        except DjangoValidationError as erro:
            raise serializers.ValidationError({"senha": list(erro.messages)})
        return dados

    def create(self, dados):
        # O e-mail também vira o username, porque o User padrão exige um username único.
        return User.objects.create_user(
            username=dados["email"],
            email=dados["email"],
            password=dados["senha"],
            first_name=dados.get("nome", "").strip(),
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        error_messages={
            "required": "Informe o e-mail.",
            "blank": "Informe o e-mail.",
            "invalid": "Informe um e-mail válido.",
        }
    )
    senha = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        error_messages={"required": "Informe a senha.", "blank": "Informe a senha."},
    )

    def validate(self, dados):
        usuario = authenticate(
            request=self.context.get("request"),
            username=dados["email"].strip().lower(),
            password=dados["senha"],
        )
        if usuario is None:
            # Mesma mensagem para e-mail inexistente e senha errada, para não
            # revelar quais e-mails têm conta.
            raise serializers.ValidationError(
                "E-mail ou senha incorretos.", code="authorization"
            )
        dados["usuario"] = usuario
        return dados


# ---------------------------------------------------------------------------
# Simulações
# ---------------------------------------------------------------------------

def para_json(valor):
    """Converte a saída de simular() para algo que cabe num JSONField.

    Decimal vira string com 2 casas ("9000.00"), para não perder centavos com float.
    """
    if isinstance(valor, Decimal):
        return f"{valor:.2f}"
    if isinstance(valor, date):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {chave: para_json(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [para_json(item) for item in valor]
    return valor


def _campo_aeroporto(nome):
    return serializers.RegexField(
        r"^[A-Za-z]{3}$",
        error_messages={
            "required": f"Informe o aeroporto de {nome}.",
            "blank": f"Informe o aeroporto de {nome}.",
            "invalid": f"Use o código do aeroporto de {nome} com 3 letras (ex.: GRU).",
        },
    )


def _campo_data(nome):
    return serializers.DateField(
        input_formats=["%Y-%m-%d"],
        error_messages={
            "required": f"Informe a data de {nome}.",
            "invalid": f"Data de {nome} inválida. Use o formato AAAA-MM-DD.",
        },
    )


class SimulacaoEntradaSerializer(serializers.Serializer):
    """Confere só o formato do pedido. As regras da viagem (volta depois da ida,
    no máximo 30 noites...) ficam em simular(), que levanta ErroEntrada."""

    origem = _campo_aeroporto("origem")
    destino = _campo_aeroporto("destino")
    data_ida = _campo_data("ida")
    data_volta = _campo_data("volta")
    orcamento = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.01"),
        error_messages={
            "required": "Informe o orçamento.",
            "invalid": "Informe o orçamento como número (ex.: 9000 ou 9000.50).",
            "min_value": "O orçamento precisa ser maior que zero.",
        },
    )
    pessoas = serializers.IntegerField(
        min_value=1,
        max_value=9,
        error_messages={
            "required": "Informe o número de pessoas.",
            "invalid": "Informe o número de pessoas como número inteiro.",
            "min_value": "O número de pessoas precisa ser pelo menos 1.",
            "max_value": "O número de pessoas pode ser no máximo 9.",
        },
    )
    interesses = serializers.ListField(
        child=serializers.CharField(max_length=50),
        max_length=10,
        required=False,
        default=list,
        error_messages={
            "not_a_list": "Envie os interesses como uma lista de textos.",
            "max_length": "Escolha no máximo 10 interesses.",
        },
    )

    def validate_origem(self, valor):
        return valor.upper()

    def validate_destino(self, valor):
        return valor.upper()


class SimulacaoResumoSerializer(serializers.ModelSerializer):
    """Item da lista do histórico (GET /api/simulacoes/)."""

    class Meta:
        model = Simulacao
        fields = ["id", "origem", "destino", "data_ida", "data_volta", "orcamento",
                  "veredito", "total_estimado", "criado_em"]


class SimulacaoDetalheSerializer(serializers.ModelSerializer):
    """Resultado completo (POST e GET /api/simulacoes/<id>/): o que simular()
    devolveu, mais o id, a data de criação e o que a pessoa pediu."""

    class Meta:
        model = Simulacao
        fields = ["id", "criado_em", "origem", "destino", "data_ida", "data_volta",
                  "pessoas", "interesses"]

    def to_representation(self, instancia):
        return {**instancia.resultado, **super().to_representation(instancia)}
