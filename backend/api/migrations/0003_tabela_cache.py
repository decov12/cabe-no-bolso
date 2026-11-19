"""Cria a tabela do cache de 24 horas (settings.CACHES, "cache_respostas").

Assim um "python manage.py migrate" basta, em desenvolvimento e no Render,
sem precisar lembrar de rodar "createcachetable". O comando não faz nada se a
tabela já existir ou se o cache configurado não for de banco (como nos testes).
"""

from django.core.management import call_command
from django.db import migrations


def criar_tabela_cache(apps, schema_editor):
    call_command("createcachetable", database=schema_editor.connection.alias, verbosity=0)


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_simulacao_cidade_destino"),
    ]

    operations = [
        migrations.RunPython(criar_tabela_cache, migrations.RunPython.noop),
    ]
