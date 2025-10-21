"""
Renderizador de templates para notificaciones.

Implementa ITemplateRenderer usando templates simples con format().
Para producción, considerar usar Django templates o Jinja2.
"""

import logging

from ..domain.ports import ITemplateRenderer

logger = logging.getLogger(__name__)


class SimpleTemplateRenderer(ITemplateRenderer):
    """
    Renderizador simple de templates.

    Usa templates predefinidos con string.format().
    Para producción, usar Django templates o Jinja2.
    """

    def __init__(self):
        """Inicializa el renderizador con templates predefinidos."""
        self.templates = {
            "password_reset": {
                "subject": "Recuperación de contraseña - ChemFlow",
                "body": """Hola,

Has solicitado restablecer tu contraseña en ChemFlow.

Para crear una nueva contraseña, haz clic en el siguiente enlace:
{reset_url}

Si no solicitaste este cambio, ignora este email.

Saludos,
El equipo de ChemFlow
""",
                "html": """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>Recuperación de contraseña</h2>
    <p>Hola,</p>
    <p>Has solicitado restablecer tu contraseña en ChemFlow.</p>
    <p>Para crear una nueva contraseña, haz clic en el siguiente botón:</p>
    <a href="{reset_url}" 
       style="background-color: #4CAF50; color: white; padding: 14px 20px; 
              text-decoration: none; border-radius: 4px; display: inline-block;">
        Restablecer contraseña
    </a>
    <p>O copia este enlace: <br>{reset_url}</p>
    <p>Si no solicitaste este cambio, ignora este email.</p>
    <p>Saludos,<br>El equipo de ChemFlow</p>
</body>
</html>
""",
            },
            "email_verification": {
                "subject": "Verifica tu email - ChemFlow",
                "body": """Hola,

Gracias por registrarte en ChemFlow.

Para verificar tu email, haz clic en el siguiente enlace:
{verification_url}

Saludos,
El equipo de ChemFlow
""",
                "html": """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>Verificación de email</h2>
    <p>Hola,</p>
    <p>Gracias por registrarte en ChemFlow.</p>
    <p>Para verificar tu email, haz clic en el siguiente botón:</p>
    <a href="{verification_url}" 
       style="background-color: #2196F3; color: white; padding: 14px 20px; 
              text-decoration: none; border-radius: 4px; display: inline-block;">
        Verificar email
    </a>
    <p>O copia este enlace: <br>{verification_url}</p>
    <p>Saludos,<br>El equipo de ChemFlow</p>
</body>
</html>
""",
            },
            "welcome": {
                "subject": "Bienvenido a ChemFlow",
                "body": """Hola {username},

¡Bienvenido a ChemFlow!

Estamos emocionados de tenerte con nosotros. Comienza creando tu primer flujo de trabajo.

Saludos,
El equipo de ChemFlow
""",
                "html": """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2>¡Bienvenido a ChemFlow!</h2>
    <p>Hola {username},</p>
    <p>Estamos emocionados de tenerte con nosotros.</p>
    <p>Comienza creando tu primer flujo de trabajo.</p>
    <p>Saludos,<br>El equipo de ChemFlow</p>
</body>
</html>
""",
            },
            "step_failed": {
                "subject": "Error en step: {step_name}",
                "body": """Hola,

El step '{step_name}' en tu flujo de trabajo ha fallado.

Error: {error_message}

Flow ID: {flow_id}

Por favor revisa la configuración e intenta nuevamente.

Saludos,
El equipo de ChemFlow
""",
                "html": """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #f44336;">Error en step</h2>
    <p>Hola,</p>
    <p>El step <strong>'{step_name}'</strong> en tu flujo de trabajo ha fallado.</p>
    <p><strong>Error:</strong> {error_message}</p>
    <p><strong>Flow ID:</strong> {flow_id}</p>
    <p>Por favor revisa la configuración e intenta nuevamente.</p>
    <p>Saludos,<br>El equipo de ChemFlow</p>
</body>
</html>
""",
            },
            "flow_completed": {
                "subject": "Flujo completado: {flow_name}",
                "body": """Hola,

Tu flujo de trabajo '{flow_name}' se ha completado exitosamente.

Detalles:
- Flow ID: {flow_id}
- Total de steps: {total_steps}
- Duración: {duration} segundos

Saludos,
El equipo de ChemFlow
""",
                "html": """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #4CAF50;">✓ Flujo completado</h2>
    <p>Hola,</p>
    <p>Tu flujo de trabajo <strong>'{flow_name}'</strong> se ha completado exitosamente.</p>
    <h3>Detalles:</h3>
    <ul>
        <li><strong>Flow ID:</strong> {flow_id}</li>
        <li><strong>Total de steps:</strong> {total_steps}</li>
        <li><strong>Duración:</strong> {duration} segundos</li>
    </ul>
    <p>Saludos,<br>El equipo de ChemFlow</p>
</body>
</html>
""",
            },
        }

    def render(self, template_name: str, context: dict) -> str:
        """
        Renderiza un template con el contexto.

        Args:
            template_name: Nombre del template
            context: Diccionario con variables

        Returns:
            Template renderizado
        """
        if template_name not in self.templates:
            logger.warning(f"Template no encontrado: {template_name}")
            return ""

        try:
            return self.templates[template_name]["body"].format(**context)
        except KeyError as e:
            logger.error(f"Variable faltante en template {template_name}: {e}")
            return self.templates[template_name]["body"]

    def render_html(self, template_name: str, context: dict) -> str:
        """
        Renderiza un template HTML con el contexto.

        Args:
            template_name: Nombre del template
            context: Diccionario con variables

        Returns:
            Template HTML renderizado
        """
        if template_name not in self.templates:
            logger.warning(f"Template HTML no encontrado: {template_name}")
            return ""

        try:
            return self.templates[template_name]["html"].format(**context)
        except KeyError as e:
            logger.error(f"Variable faltante en template HTML {template_name}: {e}")
            return self.templates[template_name]["html"]

    def add_template(self, name: str, subject: str, body: str, html: str = "") -> None:
        """
        Agrega un nuevo template.

        Args:
            name: Nombre del template
            subject: Asunto del email
            body: Cuerpo en texto plano
            html: Cuerpo en HTML
        """
        self.templates[name] = {"subject": subject, "body": body, "html": html}
