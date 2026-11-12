from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

# Botão "Log in" da API navegável do DRF (só em desenvolvimento).
if settings.DEBUG:
    urlpatterns += [path("api-auth/", include("rest_framework.urls"))]
