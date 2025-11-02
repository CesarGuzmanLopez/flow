"""
Vistas de autenticación JWT personalizadas para ChemFlow.

Extiende SimpleJWT para incluir datos del usuario en la respuesta de login,
facilitando la inicialización del estado del frontend.
"""

from back.envelope import StandardEnvelopeMixin
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import UserSerializer

User = get_user_model()


class ChemflowTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializador JWT personalizado que incluye username en el token."""

    @classmethod
    def get_token(cls, user):
        """
        Genera el token JWT incluyendo el username en los claims.

        Args:
            user: Usuario para el que se genera el token

        Returns:
            Token JWT con claims personalizados
        """
        token = super().get_token(user)
        token["username"] = user.username
        return token

    def validate(self, attrs):
        """
        Valida las credenciales y añade datos del usuario a la respuesta.

        Args:
            attrs: Atributos de autenticación (username, password)

        Returns:
            dict: Datos del token (access, refresh) más objeto 'user' serializado
        """
        data = super().validate(attrs)
        # Attach user serialized data for frontend convenience
        data["user"] = UserSerializer(self.user).data
        return data


class ChemflowTokenObtainPairView(StandardEnvelopeMixin, TokenObtainPairView):
    """
    Vista JWT personalizada para login que retorna access, refresh y user.

    Endpoint de autenticación principal que permite a los usuarios iniciar sesión
    y obtener sus tokens JWT junto con su información de perfil completa.
    """

    serializer_class = ChemflowTokenObtainPairSerializer

    @extend_schema(
        tags=["Autenticación"],
        summary="Login de usuario",
        description="""
        Autentica un usuario y retorna tokens JWT junto con información del perfil.
        
        **Características:**
        - Valida credenciales (username/password)
        - Genera access token (válido 60 minutos)
        - Genera refresh token (válido 7 días)
        - Incluye datos completos del usuario (roles, permisos, perfil)
        
        **Uso del access token:**
        Incluir en el header de requests subsecuentes:
        ```
        Authorization: Bearer {access_token}
        ```
        
        **Renovación:**
        Cuando el access token expire, usar el endpoint `/api/token/refresh/`
        con el refresh token para obtener un nuevo access token sin necesidad
        de volver a autenticarse.
        """,
        request=TokenObtainPairSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                description="Autenticación exitosa",
                response={"type": "object"},
                examples=[
                    OpenApiExample(
                        "Ejemplo de respuesta exitosa",
                        value={
                            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                            "user": {
                                "id": 1,
                                "username": "admin",
                                "email": "admin@chemflow.com",
                                "first_name": "Carlos",
                                "last_name": "Administrador",
                                "universidad": "Universidad Nacional",
                                "roles": [
                                    {
                                        "id": 1,
                                        "name": "admin",
                                        "permissions": [
                                            {
                                                "resource": "users",
                                                "action": "read",
                                                "name": "Users: Read",
                                                "codename": "users_read",
                                            }
                                        ],
                                    }
                                ],
                            },
                        },
                        response_only=True,
                    )
                ],
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                description="Credenciales inválidas",
                examples=[
                    OpenApiExample(
                        "Credenciales incorrectas",
                        value={
                            "detail": "No active account found with the given credentials"
                        },
                        response_only=True,
                    )
                ],
            ),
        },
        examples=[
            OpenApiExample(
                "Login con username y password",
                value={"username": "chemflow_admin", "password": "ChemFlow2024!"},
                request_only=True,
            )
        ],
    )
    def post(self, request, *args, **kwargs):
        """Método POST para autenticación de usuarios."""
        return super().post(request, *args, **kwargs)
