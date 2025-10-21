"""
Servicios de dominio para la aplicación de usuarios.

Contiene la lógica de negocio relacionada con usuarios, autenticación,
tokens y recuperación de contraseña.
"""

import secrets
from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from notifications.container import container
from notifications.domain.events import (
    EmailVerificationRequested,
    PasswordResetRequested,
    UserRegistered,
)

from ..models import UserToken

User = get_user_model()


class UserAuthenticationService:
    """Servicio de dominio para autenticación y gestión de usuarios."""

    @staticmethod
    def create_user(
        username: str, email: str, password: str, **extra_fields
    ) -> Tuple[User, bool]:
        """
        Crea un nuevo usuario.

        Args:
            username: Nombre de usuario
            email: Email del usuario
            password: Contraseña
            **extra_fields: Campos adicionales

        Returns:
            Tupla (usuario creado, es_nuevo)
        """
        try:
            user = User.objects.get(username=username)
            return user, False
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username, email=email, password=password, **extra_fields
            )

            # Emitir evento de registro
            event = UserRegistered(
                event_id=secrets.token_urlsafe(16),
                user_id=user.id,
                username=user.username,
                email=user.email,
            )

            # Enviar email de bienvenida
            welcome_use_case = container.welcome_email_use_case()
            welcome_use_case.execute(event)

            return user, True

    @staticmethod
    def verify_password(user: User, password: str) -> bool:
        """
        Verifica la contraseña de un usuario.

        Args:
            user: Usuario a verificar
            password: Contraseña a verificar

        Returns:
            True si la contraseña es correcta
        """
        return user.check_password(password)

    @staticmethod
    def change_password(user: User, old_password: str, new_password: str) -> bool:
        """
        Cambia la contraseña de un usuario.

        Args:
            user: Usuario
            old_password: Contraseña actual
            new_password: Nueva contraseña

        Returns:
            True si se cambió exitosamente
        """
        if not user.check_password(old_password):
            return False

        user.set_password(new_password)
        user.save()
        return True

    @staticmethod
    def admin_change_password(user: User, new_password: str) -> bool:
        """
        Cambia la contraseña de un usuario (admin).

        Args:
            user: Usuario
            new_password: Nueva contraseña

        Returns:
            True siempre
        """
        user.set_password(new_password)
        user.save()
        return True


class UserTokenService:
    """Servicio de dominio para gestión de tokens de usuario."""

    @staticmethod
    def generate_password_reset_token(user: User) -> Tuple[UserToken, str]:
        """
        Genera un token de recuperación de contraseña.

        Args:
            user: Usuario

        Returns:
            Tupla (UserToken, URL de reset)
        """
        token = UserToken.generate_token(
            user=user, token_type="password_reset", expiry_hours=24
        )

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"

        # Emitir evento y enviar email
        event = PasswordResetRequested(
            event_id=secrets.token_urlsafe(16),
            user_id=user.id,
            email=user.email,
            token=token.token,
        )

        reset_use_case = container.password_reset_use_case()
        reset_use_case.execute(event, reset_url)

        return token, reset_url

    @staticmethod
    def reset_password_with_token(token_string: str, new_password: str) -> bool:
        """
        Restablece la contraseña usando un token.

        Args:
            token_string: Token de recuperación
            new_password: Nueva contraseña

        Returns:
            True si se restableció exitosamente
        """
        try:
            token = UserToken.objects.get(
                token=token_string, token_type="password_reset"
            )

            if not token.is_valid():
                return False

            user = token.user
            user.set_password(new_password)
            user.save()

            token.mark_as_used()
            return True

        except UserToken.DoesNotExist:
            return False

    @staticmethod
    def generate_email_verification_token(user: User) -> Tuple[UserToken, str]:
        """
        Genera un token de verificación de email.

        Args:
            user: Usuario

        Returns:
            Tupla (UserToken, URL de verificación)
        """
        token = UserToken.generate_token(
            user=user, token_type="email_verification", expiry_hours=48
        )

        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"

        # Emitir evento y enviar email
        event = EmailVerificationRequested(
            event_id=secrets.token_urlsafe(16),
            user_id=user.id,
            email=user.email,
            token=token.token,
        )

        verification_use_case = container.email_verification_use_case()
        verification_use_case.execute(event, verification_url)

        return token, verification_url

    @staticmethod
    def verify_email_with_token(token_string: str) -> Optional[User]:
        """
        Verifica el email de un usuario usando un token.

        Args:
            token_string: Token de verificación

        Returns:
            Usuario verificado o None si falla
        """
        try:
            token = UserToken.objects.get(
                token=token_string, token_type="email_verification"
            )

            if not token.is_valid():
                return None

            user = token.user
            # Aquí podrías agregar un campo email_verified al modelo User
            # user.email_verified = True
            # user.save()

            token.mark_as_used()
            return user

        except UserToken.DoesNotExist:
            return None


class UserActivationService:
    """Servicio de dominio para activación/desactivación de usuarios."""

    @staticmethod
    def activate_user(user: User) -> bool:
        """
        Activa un usuario.

        Args:
            user: Usuario a activar

        Returns:
            True si se activó
        """
        if not user.is_active:
            user.is_active = True
            user.save()
            return True
        return False

    @staticmethod
    def deactivate_user(user: User) -> bool:
        """
        Desactiva un usuario.

        Args:
            user: Usuario a desactivar

        Returns:
            True si se desactivó
        """
        if user.is_active:
            user.is_active = False
            user.save()
            return True
        return False

    @staticmethod
    def can_user_deactivate_self(user: User, target_user: User) -> bool:
        """
        Verifica si un usuario puede desactivarse a sí mismo.

        Args:
            user: Usuario que intenta desactivar
            target_user: Usuario objetivo

        Returns:
            False siempre (no permitido)
        """
        return user.id != target_user.id
