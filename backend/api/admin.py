from django.contrib import admin

from .models import Simulacao


@admin.register(Simulacao)
class SimulacaoAdmin(admin.ModelAdmin):
    list_display = ["id", "usuario", "origem", "destino", "data_ida", "data_volta",
                    "orcamento", "veredito", "total_estimado", "criado_em"]
    list_filter = ["veredito"]
    search_fields = ["usuario__email", "origem", "destino"]
    readonly_fields = ["criado_em"]
