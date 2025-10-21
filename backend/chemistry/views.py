"""
Vistas (ViewSets) de la aplicación de química.

Define los endpoints REST API para:
- Gestión de moléculas (CRUD, búsqueda, filtrado)
- Propiedades moleculares (peso molecular, puntos de fusión/ebullición, etc.)
- Familias de moléculas (clasificación y agrupación)
- Propiedades de familias
- Miembros de familias (relaciones molécula-familia)

Implementa control de acceso basado en propiedad y permisos de usuario.
Los datos siguen estándares ChEMBL/PubChem para compatibilidad.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import HasAppPermission

from . import services as chem_services
from .models import Family, FamilyMember, FamilyProperty, MolecularProperty, Molecule
from .serializers import (
    FamilyMemberSerializer,
    FamilyPropertySerializer,
    FamilySerializer,
    MolecularPropertySerializer,
    MoleculeSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="Listar moléculas",
        description="Obtiene todas las moléculas del sistema alineadas con estándares "
        "ChEMBL/PubChem. Incluye invariantes como InChIKey, SMILES canónico y fórmula molecular.",
        tags=["Chemistry - Molecules"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de molécula",
        description="Recupera información completa de una molécula específica, incluyendo "
        "todas sus propiedades moleculares asociadas (modelo EAV).",
        tags=["Chemistry - Molecules"],
    ),
    create=extend_schema(
        summary="Crear nueva molécula",
        description="Registra una nueva molécula en el sistema. Debe incluir al menos uno de "
        "los identificadores estándar (InChIKey, SMILES). El usuario autenticado se "
        "asigna como creador.",
        tags=["Chemistry - Molecules"],
    ),
    update=extend_schema(
        summary="Actualizar molécula completa",
        description="Actualiza todos los campos de una molécula (solo si no está congelada).",
        tags=["Chemistry - Molecules"],
    ),
    partial_update=extend_schema(
        summary="Actualizar molécula parcialmente",
        description="Actualiza campos específicos de una molécula (solo si no está congelada).",
        tags=["Chemistry - Molecules"],
    ),
    destroy=extend_schema(
        summary="Eliminar molécula",
        description="Elimina una molécula del sistema (solo si no está congelada ni referenciada).",
        tags=["Chemistry - Molecules"],
    ),
)
class MoleculeViewSet(viewsets.ModelViewSet):
    """ViewSet para gestión de moléculas alineadas con estándares ChEMBL/PubChem."""

    queryset = Molecule.objects.all()
    serializer_class = MoleculeSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"

    def get_queryset(self):  # type: ignore[override]
        qs = super().get_queryset()
        if self.request.query_params.get("mine") == "true":
            return qs.filter(created_by=self.request.user)
        return chem_services.filter_molecules_for_user(qs, self.request.user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"])
    @extend_schema(
        summary="Listar mis moléculas",
        description="Obtiene únicamente las moléculas creadas por el usuario autenticado, "
        "independientemente de los permisos globales que pueda tener.",
        tags=["Chemistry - Molecules"],
    )
    def mine(self, request):
        """Devuelve moléculas creadas por el usuario autenticado."""
        qs = self.get_queryset().filter(created_by=request.user)
        serializer = MoleculeSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Listar propiedades moleculares",
        description="Obtiene todas las propiedades moleculares del sistema. Usa modelo EAV "
        "(Entity-Attribute-Value) para almacenar propiedades flexibles con contexto "
        "(método, unidades, fuente).",
        tags=["Chemistry - Properties"],
    ),
    retrieve=extend_schema(
        summary="Obtener propiedad molecular",
        description="Recupera información detallada de una propiedad molecular específica.",
        tags=["Chemistry - Properties"],
    ),
    create=extend_schema(
        summary="Crear propiedad molecular",
        description="Registra una nueva propiedad para una molécula (ej: peso molecular, "
        "punto de fusión, actividad biológica).",
        tags=["Chemistry - Properties"],
    ),
    update=extend_schema(
        summary="Actualizar propiedad molecular",
        description="Actualiza todos los campos de una propiedad molecular existente.",
        tags=["Chemistry - Properties"],
    ),
    partial_update=extend_schema(
        summary="Actualizar propiedad parcialmente",
        description="Actualiza campos específicos de una propiedad molecular.",
        tags=["Chemistry - Properties"],
    ),
    destroy=extend_schema(
        summary="Eliminar propiedad molecular",
        description="Elimina una propiedad molecular del sistema.",
        tags=["Chemistry - Properties"],
    ),
)
class MolecularPropertyViewSet(viewsets.ModelViewSet):
    queryset = MolecularProperty.objects.all()
    serializer_class = MolecularPropertySerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"


@extend_schema_view(
    list=extend_schema(
        summary="Listar familias de moléculas",
        description="Obtiene todas las familias (agregaciones) de moléculas relacionadas. "
        "Las familias agrupan moléculas por características comunes (ej: misma serie, "
        "mismo scaffold, mismo proyecto).",
        tags=["Chemistry - Families"],
    ),
    retrieve=extend_schema(
        summary="Obtener detalles de familia",
        description="Recupera información completa de una familia de moléculas, incluyendo "
        "sus propiedades y lista de miembros.",
        tags=["Chemistry - Families"],
    ),
    create=extend_schema(
        summary="Crear familia de moléculas",
        description="Crea una nueva familia para agrupar moléculas relacionadas. "
        "Identifica la familia por hash y procedencia.",
        tags=["Chemistry - Families"],
    ),
    update=extend_schema(
        summary="Actualizar familia completa",
        description="Actualiza todos los campos de una familia (solo si no está congelada).",
        tags=["Chemistry - Families"],
    ),
    partial_update=extend_schema(
        summary="Actualizar familia parcialmente",
        description="Actualiza campos específicos de una familia (solo si no está congelada).",
        tags=["Chemistry - Families"],
    ),
    destroy=extend_schema(
        summary="Eliminar familia",
        description="Elimina una familia de moléculas del sistema.",
        tags=["Chemistry - Families"],
    ),
)
class FamilyViewSet(viewsets.ModelViewSet):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"


@extend_schema_view(
    list=extend_schema(
        summary="Listar propiedades de familias",
        description="Obtiene todas las propiedades de familias de moléculas. Similar al modelo "
        "EAV de propiedades moleculares pero aplicado a nivel de familia.",
        tags=["Chemistry - Properties"],
    ),
    retrieve=extend_schema(
        summary="Obtener propiedad de familia",
        description="Recupera información detallada de una propiedad específica de familia.",
        tags=["Chemistry - Properties"],
    ),
    create=extend_schema(
        summary="Crear propiedad de familia",
        description="Registra una nueva propiedad para una familia de moléculas "
        "(ej: promedio de actividad, rango de peso molecular).",
        tags=["Chemistry - Properties"],
    ),
    update=extend_schema(
        summary="Actualizar propiedad de familia",
        description="Actualiza todos los campos de una propiedad de familia existente.",
        tags=["Chemistry - Properties"],
    ),
    partial_update=extend_schema(
        summary="Actualizar propiedad parcialmente",
        description="Actualiza campos específicos de una propiedad de familia.",
        tags=["Chemistry - Properties"],
    ),
    destroy=extend_schema(
        summary="Eliminar propiedad de familia",
        description="Elimina una propiedad de familia del sistema.",
        tags=["Chemistry - Properties"],
    ),
)
class FamilyPropertyViewSet(viewsets.ModelViewSet):
    queryset = FamilyProperty.objects.all()
    serializer_class = FamilyPropertySerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"


@extend_schema_view(
    list=extend_schema(
        summary="Listar membresías molécula-familia",
        description="Obtiene todas las relaciones de pertenencia entre moléculas y familias. "
        "Una molécula puede pertenecer a múltiples familias.",
        tags=["Chemistry - Families"],
    ),
    retrieve=extend_schema(
        summary="Obtener membresía específica",
        description="Recupera información de una relación específica molécula-familia.",
        tags=["Chemistry - Families"],
    ),
    create=extend_schema(
        summary="Añadir molécula a familia",
        description="Crea una relación de pertenencia entre una molécula y una familia. "
        "Se valida unicidad (una molécula no puede estar duplicada en la misma familia).",
        tags=["Chemistry - Families"],
    ),
    update=extend_schema(
        summary="Actualizar membresía",
        description="Actualiza una relación molécula-familia (uso poco común).",
        tags=["Chemistry - Families"],
    ),
    partial_update=extend_schema(
        summary="Actualizar membresía parcialmente",
        description="Actualiza campos de una membresía molécula-familia.",
        tags=["Chemistry - Families"],
    ),
    destroy=extend_schema(
        summary="Remover molécula de familia",
        description="Elimina la relación de pertenencia, removiendo una molécula de una familia.",
        tags=["Chemistry - Families"],
    ),
)
class FamilyMemberViewSet(viewsets.ModelViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"
