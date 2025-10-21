"""
Value Objects para el dominio de notificaciones.

Value objects inmutables que representan conceptos del dominio sin identidad propia.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class EmailAddress:
    """Value object para direcciones de email validadas."""

    address: str

    def __post_init__(self):
        """Valida el formato del email."""
        if "@" not in self.address or "." not in self.address.split("@")[1]:
            raise ValueError(f"Email inválido: {self.address}")

    def __str__(self) -> str:
        return self.address


@dataclass(frozen=True)
class NotificationTemplate:
    """Value object para templates de notificaciones."""

    name: str
    subject_template: str
    body_template: str
    html_template: str = ""

    def render_subject(self, context: Dict[str, Any]) -> str:
        """Renderiza el asunto del template con el contexto."""
        return self.subject_template.format(**context)

    def render_body(self, context: Dict[str, Any]) -> str:
        """Renderiza el cuerpo del template con el contexto."""
        return self.body_template.format(**context)

    def render_html(self, context: Dict[str, Any]) -> str:
        """Renderiza el HTML del template con el contexto."""
        if self.html_template:
            return self.html_template.format(**context)
        return ""


@dataclass(frozen=True)
class WebhookEndpoint:
    """Value object para endpoints de webhooks."""

    url: str
    secret: str = ""

    def __post_init__(self):
        """Valida la URL del webhook."""
        if not self.url.startswith(("http://", "https://")):
            raise ValueError(f"URL de webhook inválida: {self.url}")

    def __str__(self) -> str:
        return self.url
