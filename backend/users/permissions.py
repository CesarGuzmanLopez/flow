"""
Permisos personalizados de DRF para verificación de roles y permisos.

Implementa una capa de seguridad que define verificaciones de permisos a nivel
de aplicación que las vistas usan para hacer cumplir las reglas de ACL del dominio.
"""

from typing import Dict, Optional, Tuple

from rest_framework.permissions import SAFE_METHODS, BasePermission


class HasAppPermission(BasePermission):
    """
    Verifica si request.user tiene el permiso (recurso, acción) requerido.

    Las vistas pueden declarar:
      - permission_resource: str  # ej: "flow", "chemistry", "users"
      - permission_required: Dict[str, Tuple[str, str]]  # action -> (resource, action)

    Si no se proporciona, se usa un mapeo por defecto basado en el método HTTP/acción:
      - read: list, retrieve, SAFE_METHODS
      - write: create, update, partial_update, non-safe POST/PATCH/PUT
      - delete: destroy, DELETE

    Los superusuarios siempre tienen acceso.
    """

    message = "No tienes permiso para realizar esta acción."

    def _resolve_required(
        self, view, action: Optional[str]
    ) -> Optional[Tuple[str, str]]:
        """
        Resuelve el permiso requerido (recurso, acción) para una acción de vista.

        Args:
            view: Vista DRF
            action: Nombre de la acción (list, retrieve, create, etc.)

        Returns:
            Tupla (recurso, acción) requerida o None si no se puede resolver
        """
        # Explicit mapping on the view takes precedence
        mapping: Optional[Dict[str, Tuple[str, str]]] = getattr(
            view, "permission_required", None
        )
        if mapping and action in mapping:
            return mapping[action]

        # Fallback to resource + default verb mapping
        resource: Optional[str] = getattr(view, "permission_resource", None)
        if not resource:
            return None

        if action in {"list", "retrieve"}:
            return (resource, "read")
        if action in {"create", "update", "partial_update"}:
            return (resource, "write")
        if action in {"destroy"}:
            return (resource, "delete")

        # For custom actions, views should define mapping; otherwise treat safe as read
        return None

    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        """
        Verifica si el usuario tiene permiso para acceder a la vista.

        Args:
            request: Request HTTP
            view: Vista DRF

        Returns:
            True si el usuario tiene permiso, False en caso contrario
        """
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, "is_superuser", False):
            return True

        # DRF sets view.action for ViewSets; if missing, infer from method
        action = getattr(view, "action", None)
        if action is None:
            if request.method in SAFE_METHODS:
                required = (getattr(view, "permission_resource", ""), "read")
            elif request.method in {"POST", "PUT", "PATCH"}:
                required = (getattr(view, "permission_resource", ""), "write")
            elif request.method == "DELETE":
                required = (getattr(view, "permission_resource", ""), "delete")
            else:
                required = None
        else:
            required = self._resolve_required(view, action)

        if not required or not required[0]:
            # If no resource/action mapping is defined, fallback to allow
            # (so legacy views continue to work). Prefer explicit mapping.
            return True

        resource, action_name = required
        # User model implements has_permission(resource, action)
        try:
            return bool(user.has_permission(resource, action_name))
        except AttributeError:
            # If custom method not present, deny by default
            return False

    def has_object_permission(self, request, view, obj) -> bool:  # type: ignore[override]
        """
        Verifica permiso a nivel de objeto.

        Args:
            request: Request HTTP
            view: Vista DRF
            obj: Objeto específico

        Returns:
            True si el usuario tiene permiso sobre el objeto
        """
        # Default to same as has_permission; override in view if resource-level ACL is needed
        return self.has_permission(request, view)
