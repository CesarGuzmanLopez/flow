"""
Adaptador mock para envío de emails.

Implementa IEmailSender simulando el envío de emails.
Útil para desarrollo y testing.
"""

import logging
from typing import List

from ..domain.entities import Notification
from ..domain.ports import IEmailSender

logger = logging.getLogger(__name__)


class MockEmailSender(IEmailSender):
    """
    Adaptador mock que simula envío de emails.

    Implementa IEmailSender registrando los emails en logs
    sin enviarlos realmente.
    """

    def __init__(self):
        """Inicializa el adaptador mock."""
        self.sent_emails = []

    def send(self, notification: Notification) -> bool:
        """
        Simula el envío de un email.

        Args:
            notification: Notificación a enviar

        Returns:
            True siempre (simula éxito)
        """
        logger.info("=" * 80)
        logger.info("📧 MOCK EMAIL ENVIADO")
        logger.info(f"Para: {notification.recipient}")
        logger.info(f"Asunto: {notification.subject}")
        logger.info(f"Mensaje: {notification.message}")
        if hasattr(notification, "html_message") and notification.html_message:
            logger.info(f"HTML: {notification.html_message[:100]}...")
        logger.info("=" * 80)

        self.sent_emails.append(
            {
                "to": notification.recipient,
                "subject": notification.subject,
                "message": notification.message,
            }
        )
        return True

    def send_batch(self, notifications: List[Notification]) -> List[bool]:
        """
        Simula el envío de un lote de emails.

        Args:
            notifications: Lista de notificaciones

        Returns:
            Lista de True (simula éxito para todos)
        """
        return [self.send(n) for n in notifications]

    def send_html_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        plain_content: str = "",
        from_email: str = None,
    ) -> bool:
        """
        Simula envío de email HTML.

        Args:
            to: Destinatario
            subject: Asunto
            html_content: Contenido HTML
            plain_content: Contenido en texto plano
            from_email: Email de origen

        Returns:
            True siempre (simula éxito)
        """
        logger.info("=" * 80)
        logger.info("📧 MOCK EMAIL HTML ENVIADO")
        logger.info(f"De: {from_email or 'noreply@chemflow.com'}")
        logger.info(f"Para: {to}")
        logger.info(f"Asunto: {subject}")
        logger.info(f"Texto: {plain_content[:100] if plain_content else 'N/A'}...")
        logger.info(f"HTML: {html_content[:100]}...")
        logger.info("=" * 80)

        self.sent_emails.append(
            {"to": to, "subject": subject, "html": html_content, "from": from_email}
        )
        return True

    def get_sent_count(self) -> int:
        """Retorna el número de emails enviados."""
        return len(self.sent_emails)

    def clear_sent(self) -> None:
        """Limpia la lista de emails enviados."""
        self.sent_emails.clear()
