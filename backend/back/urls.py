"""
Configuración principal de URLs del proyecto ChemFlow.

Define los endpoints principales del backend:
- /admin/ - Panel de administración de Django
- /api/health/ - Endpoint de healthcheck
- /api/token/ - Autenticación JWT (login)
- /api/token/refresh/ - Refresh del token JWT
- /api/schema/ - Esquema OpenAPI 3.1
- /api/docs/swagger/ - Documentación interactiva Swagger UI
- /api/docs/redoc/ - Documentación Redoc
- /api/users/ - Endpoints de usuarios, roles y permisos
- /api/flows/ - Endpoints de flujos, versiones, pasos, artefactos, ejecuciones
- /api/chemistry/ - Endpoints de moléculas, familias y propiedades
"""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework_simplejwt.views import TokenRefreshView
from users.auth import ChemflowTokenObtainPairView

urlpatterns = [
    path("admin/", admin.site.urls),
    # Healthcheck
    path("api/health/", lambda request: JsonResponse({"status": "ok"})),
    # JWT Authentication
    path("api/token/", ChemflowTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # OpenAPI schema and docs
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
    ),
    path("api/users/", include("users.urls")),
    path("api/flows/", include("flows.urls")),
    path("api/chemistry/", include("chemistry.urls")),
]
