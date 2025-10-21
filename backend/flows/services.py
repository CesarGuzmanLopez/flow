"""
Servicios de dominio para Flows (capa de aplicación - arquitectura hexagonal).

Aquí concentramos la lógica de negocio relacionada con propiedad, visibilidad y
operaciones de consulta sobre Flows y entidades relacionadas, para que las
vistas (adaptadores) queden delgadas y fáciles de testear.
"""

import hashlib
import json
from typing import Any, List

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet

from .models import (
    Artifact,
    ExecutionSnapshot,
    Flow,
    FlowBranch,
    FlowNode,
    FlowVersion,
    Step,
)

User = get_user_model()


def user_can_read_all_flows(user: Any) -> bool:
    """Devuelve True si el usuario tiene permiso global para leer todos los flows."""
    return bool(
        getattr(user, "is_superuser", False) or user.has_permission("flows", "read")
    )


def user_can_write_flows(user: Any) -> bool:
    """Devuelve True si el usuario puede crear/editar flows."""
    return bool(
        getattr(user, "is_superuser", False) or user.has_permission("flows", "write")
    )


def filter_flows_for_user(qs: QuerySet[Flow], user: Any) -> QuerySet[Flow]:
    """Filtra el queryset de Flows según permisos del usuario.

    - Si el usuario tiene permiso global de lectura: retorna todo el queryset.
    - Si no: restringe a flows propios (owner=user).
    """
    if user_can_read_all_flows(user):
        return qs
    return qs.filter(owner=user)


def filter_versions_for_user(
    qs: QuerySet[FlowVersion], user: Any
) -> QuerySet[FlowVersion]:
    """Restringe versiones por propiedad del flow si el usuario no puede leer todo."""
    if user_can_read_all_flows(user):
        return qs
    return qs.filter(flow__owner=user)


def filter_steps_for_user(qs: QuerySet[Step], user: Any) -> QuerySet[Step]:
    if user_can_read_all_flows(user):
        return qs
    return qs.filter(flow_version__flow__owner=user)


def filter_snapshots_for_user(
    qs: QuerySet[ExecutionSnapshot], user: Any
) -> QuerySet[ExecutionSnapshot]:
    if user_can_read_all_flows(user):
        return qs
    return qs.filter(flow_version__flow__owner=user)


def filter_artifacts_for_user(qs: QuerySet[Artifact], user: Any) -> QuerySet[Artifact]:
    """Por simplicidad, los artifacts se restringen a los producidos por el usuario o
    ligados a ejecuciones de sus flows si no tiene permiso global de lectura.
    """
    if user_can_read_all_flows(user):
        return qs
    return qs.filter(created_by=user)


# ========================================================================
# Servicios del árbol de nodos (algoritmo sin merges, sin ciclos)
# ========================================================================


def _compute_content_hash(content: dict) -> str:
    """Calcula el SHA256 del contenido del nodo de forma determinista."""
    content_str = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content_str.encode("utf-8")).hexdigest()


@transaction.atomic
def add_step(branch_name: str, flow: Flow, content: dict, user: Any) -> FlowNode:
    """Añade un paso (nodo) a una rama del flujo.

    Args:
        branch_name: Nombre de la rama donde añadir el paso.
        flow: Instancia del Flow.
        content: Configuración del paso (dict).
        user: Usuario que crea el nodo.

    Returns:
        El nuevo nodo creado.

    Raises:
        ValueError: Si la rama no existe o el contenido está duplicado.
    """
    try:
        branch = FlowBranch.objects.get(flow=flow, name=branch_name)
    except FlowBranch.DoesNotExist:
        raise ValueError(f"Rama '{branch_name}' no existe en el flujo {flow.name}")

    content_hash = _compute_content_hash(content)

    # Verificar duplicación global en el flujo
    if FlowNode.objects.filter(flow=flow, content_hash=content_hash).exists():
        raise ValueError(
            "Duplicación no permitida: ya existe un nodo con ese contenido"
        )

    # Crear nuevo nodo
    new_node = FlowNode.objects.create(
        flow=flow,
        parent=branch.head,
        content=content,
        content_hash=content_hash,
        created_by=user,
    )

    # Actualizar head de la rama
    branch.head = new_node
    branch.save(update_fields=["head"])

    return new_node


def get_path(branch_name: str, flow: Flow) -> List[FlowNode]:
    """Obtiene el camino (path) de nodos desde la raíz hasta el head de la rama.

    Args:
        branch_name: Nombre de la rama.
        flow: Instancia del Flow.

    Returns:
        Lista de nodos desde raíz hasta head (orden: raíz primero).

    Raises:
        ValueError: Si la rama no existe.
    """
    try:
        branch = FlowBranch.objects.select_related("head").get(
            flow=flow, name=branch_name
        )
    except FlowBranch.DoesNotExist:
        raise ValueError(f"Rama '{branch_name}' no existe en el flujo {flow.name}")

    path = []
    current = branch.head
    while current is not None:
        path.append(current)
        current = current.parent

    path.reverse()  # Raíz primero
    return path


@transaction.atomic
def create_branch(
    new_branch_name: str,
    flow: Flow,
    from_branch_name: str,
    at_step: int,
    user: Any,
) -> FlowBranch:
    """Crea una nueva rama desde un paso específico de otra rama.

    Args:
        new_branch_name: Nombre de la nueva rama.
        flow: Instancia del Flow.
        from_branch_name: Rama padre desde la cual ramificar.
        at_step: Número de paso (1-indexed) donde iniciar la nueva rama.
        user: Usuario que crea la rama.

    Returns:
        La nueva rama creada.

    Raises:
        ValueError: Si la rama ya existe, la rama padre no existe, o el paso es inválido.
    """
    if FlowBranch.objects.filter(flow=flow, name=new_branch_name).exists():
        raise ValueError(f"Rama '{new_branch_name}' ya existe")

    try:
        parent_branch = FlowBranch.objects.get(flow=flow, name=from_branch_name)
    except FlowBranch.DoesNotExist:
        raise ValueError(f"Rama '{from_branch_name}' no existe")

    path = get_path(from_branch_name, flow)
    if at_step < 1 or at_step > len(path):
        raise ValueError(f"Paso {at_step} inválido (rama tiene {len(path)} pasos)")

    start_node = path[at_step - 1]

    # Crear nueva rama
    new_branch = FlowBranch.objects.create(
        flow=flow,
        name=new_branch_name,
        head=start_node,
        start_node=start_node,
        parent_branch=parent_branch,
        created_by=user,
    )

    return new_branch


@transaction.atomic
def delete_branch(branch_name: str, flow: Flow) -> None:
    """Elimina una rama recursivamente (primero subramas, luego nodos exclusivos).

    Args:
        branch_name: Nombre de la rama a eliminar.
        flow: Instancia del Flow.

    Raises:
        ValueError: Si se intenta eliminar la rama principal o la rama no existe.
    """
    if branch_name == "principal":
        raise ValueError("No se puede eliminar la rama principal")

    try:
        branch = FlowBranch.objects.select_related(
            "head", "start_node", "parent_branch"
        ).get(flow=flow, name=branch_name)
    except FlowBranch.DoesNotExist:
        raise ValueError(f"Rama '{branch_name}' no existe")

    # Eliminar subramas recursivamente
    child_branches = FlowBranch.objects.filter(parent_branch=branch)
    for child_branch in child_branches:
        delete_branch(child_branch.name, flow)

    # Eliminar nodos exclusivos (desde head hasta start_node, sin incluir start_node)
    current = branch.head
    start_node = branch.start_node

    nodes_to_delete = []
    while current is not None and current.id != start_node.id:
        nodes_to_delete.append(current)
        current = current.parent

    # Eliminar nodos en orden inverso (de head hacia start_node)
    for node in nodes_to_delete:
        node.delete()

    # Eliminar la rama
    branch.delete()


def initialize_main_branch(
    flow: Flow, user: Any, initial_content: dict = None
) -> FlowBranch:
    """Inicializa la rama principal de un flujo con un nodo raíz.

    Args:
        flow: Instancia del Flow.
        user: Usuario que crea la rama.
        initial_content: Contenido del nodo raíz (opcional).

    Returns:
        La rama principal creada.

    Raises:
        ValueError: Si ya existe la rama principal.
    """
    if FlowBranch.objects.filter(flow=flow, name="principal").exists():
        raise ValueError(f"El flujo {flow.name} ya tiene una rama principal")

    if initial_content is None:
        initial_content = {"step": "initial", "description": "Nodo raíz del flujo"}

    content_hash = _compute_content_hash(initial_content)

    # Crear nodo raíz
    root_node = FlowNode.objects.create(
        flow=flow,
        parent=None,
        content=initial_content,
        content_hash=content_hash,
        created_by=user,
    )

    # Crear rama principal
    main_branch = FlowBranch.objects.create(
        flow=flow,
        name="principal",
        head=root_node,
        start_node=root_node,
        parent_branch=None,
        created_by=user,
    )

    return main_branch
