"""
Adaptador para envío de webhooks HTTP.

Implementa IWebhookSender usando requests para hacer llamadas HTTP reales.
"""

import logging
from typing import List, Optional

import requests

from notifications.domain.entities import Notification, WebhookNotification
from notifications.domain.ports import IWebhookSender

logger = logging.getLogger(__name__)


class WebhookSender(IWebhookSender):
    """
    Adaptador para envío de webhooks HTTP.

    Implementa IWebhookSender usando la librería requests.
    """

    def __init__(self, default_timeout: int = 30):
        """
        Inicializa el adaptador.

        Args:
            default_timeout: Timeout por defecto en segundos
        """
        self.default_timeout = default_timeout

    def send(self, notification: Notification) -> bool:
        """
        Envía un webhook HTTP.

        Args:
            notification: Notificación (debe ser WebhookNotification)

        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        if not isinstance(notification, WebhookNotification):
            logger.error(f"Notificación no es de tipo webhook: {type(notification)}")
            return False

        try:
            response = requests.request(
                method=notification.http_method,
                url=notification.webhook_url,
                json=notification.payload,
                headers=notification.headers,
                timeout=notification.timeout or self.default_timeout,
            )

            response.raise_for_status()

            logger.info(f"🔗 Webhook enviado a {notification.webhook_url}")
            logger.info(f"Status: {response.status_code}")

            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando webhook a {notification.webhook_url}: {e}")
            return False

    def send_batch(self, notifications: List[Notification]) -> List[bool]:
        """
        Envía un lote de webhooks.

        Args:
            notifications: Lista de notificaciones webhook

        Returns:
            Lista de booleanos indicando éxito/fallo
        """
        return [self.send(n) for n in notifications]

    def send_webhook(
        self, url: str, payload: dict, headers: Optional[dict] = None
    ) -> bool:
        """
        Envía un webhook directamente sin usar entidad.

        Args:
            url: URL del webhook
            payload: Datos a enviar
            headers: Encabezados HTTP opcionales

        Returns:
            True si se envió exitosamente
        """
        try:
            response = requests.post(
                url=url,
                json=payload,
                headers=headers or {},
                timeout=self.default_timeout,
            )

            response.raise_for_status()

            logger.info(f"🔗 Webhook enviado a {url}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando webhook a {url}: {e}")
            return False
