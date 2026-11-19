"""
Configurações do Django para o projeto "Cabe no bolso?".

Tudo que muda entre desenvolvimento e produção (chaves, banco, hosts, CORS)
vem de variáveis de ambiente. Em desenvolvimento elas ficam no arquivo
backend/.env, que nunca vai para o Git (veja backend/.env.example).
"""

import os
import sys
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega backend/.env, se existir. Variáveis já definidas no ambiente
# (como no Render) têm prioridade.
load_dotenv(BASE_DIR / ".env")


def env_bool(nome, padrao=False):
    valor = os.getenv(nome)
    if valor is None:
        return padrao
    return valor.strip().lower() in ("1", "true", "yes", "sim", "on")


def env_int(nome, padrao):
    valor = os.getenv(nome, "").strip()
    return int(valor) if valor else padrao


def env_list(nome, padrao=""):
    valor = os.getenv(nome, padrao)
    return [item.strip() for item in valor.split(",") if item.strip()]


# Segurança
DEBUG = env_bool("DEBUG", False)

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        # Só para desenvolvimento local: evita travar quem ainda não criou o .env.
        SECRET_KEY = "django-insecure-apenas-para-desenvolvimento"
    else:
        raise RuntimeError("Defina a variável de ambiente SECRET_KEY.")

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1" if DEBUG else "")

# O Render informa o domínio do serviço (ex.: cabe-no-bolso-api.onrender.com) nesta variável.
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Atrás do proxy do Render, o Django só sabe que a conexão é HTTPS por este cabeçalho.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

if not DEBUG:
    # Em produção os cookies (admin e API navegável) só trafegam por HTTPS.
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# Aplicações
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework.authtoken",
    "corsheaders",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Banco de dados: PostgreSQL via DATABASE_URL em produção; SQLite se não houver.
# (DATABASE_URL vazia também conta como "não houver".)
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL") or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}

# Estamos rodando "python manage.py test"?
TESTANDO = len(sys.argv) > 1 and sys.argv[1] == "test"


# Cache de 24 horas das respostas da SerpApi e do Gemini (api/servicos/cache.py).
# Fica numa tabela do banco, criada pela migração api/0003: vale para todos os
# processos do servidor e sobrevive a reinícios e deploys. Nos testes não guarda
# nada, para um teste não reaproveitar a resposta de outro.
CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
        if TESTANDO
        else {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "cache_respostas",
            "TIMEOUT": 24 * 60 * 60,
            "OPTIONS": {"MAX_ENTRIES": 5000},
        }
    )
}


# Validação de senha (o mínimo de 8 caracteres também é checado no cadastro)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Idioma e fuso
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True


# Arquivos estáticos (servidos pelo WhiteNoise em produção)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Django REST Framework: tudo exige token, a não ser que a view diga o contrário.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}

# A API navegável do DRF usa sessão para o login pelo navegador; só em desenvolvimento.
if DEBUG:
    REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"].append(
        "rest_framework.authentication.SessionAuthentication"
    )


# CORS: quais sites podem chamar a API pelo navegador (o React, no caso).
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173" if DEBUG else ""
)


# Chaves das APIs externas (usadas pelos serviços do Felipe)
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Modelo do Gemini; vazio usa o padrão definido em api/servicos/gemini.py.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "")


# Limite diário por usuário (api/limites.py). Contas da equipe (is_staff) não têm limite.
LIMITE_SIMULACOES_DIA = env_int("LIMITE_SIMULACOES_DIA", 5)
LIMITE_LUGARES_DIA = env_int("LIMITE_LUGARES_DIA", 60)
