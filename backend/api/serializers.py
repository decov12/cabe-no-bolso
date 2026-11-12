from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

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
