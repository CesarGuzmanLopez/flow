from drf_spectacular.utils import OpenApiResponse, extend_schema, extend_schema_view

from ..models import FamilyMember
from ..serializers import FamilyMemberSerializer
from .molecules import BaseChemistryViewSet


@extend_schema_view(
    list=extend_schema(
        summary="Listar miembros de familia",
        description="Obtiene la lista de miembros (asociaciones molécula-familia).",
        tags=["Chemistry • Families"],
    ),
    create=extend_schema(
        summary="Crear miembro de familia",
        description="Crea una asociación entre una molécula y una familia.",
        tags=["Chemistry • Families"],
    ),
    retrieve=extend_schema(
        summary="Recuperar miembro de familia",
        description="Obtiene un miembro de familia por su ID.",
        responses={
            200: FamilyMemberSerializer,
            404: OpenApiResponse(description="No encontrado", response=dict),
        },
        tags=["Chemistry • Families"],
    ),
    update=extend_schema(
        summary="Actualizar miembro de familia (PUT)",
        description="Reemplaza todos los campos del miembro de familia. Use PATCH para cambios parciales.",
        responses={200: FamilyMemberSerializer, 400: OpenApiResponse(response=dict)},
        tags=["Chemistry • Families"],
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente miembro de familia (PATCH)",
        description="Actualiza uno o más campos del miembro de familia.",
        responses={200: FamilyMemberSerializer, 400: OpenApiResponse(response=dict)},
        tags=["Chemistry • Families"],
    ),
    destroy=extend_schema(
        summary="Eliminar miembro de familia",
        description="Elimina la asociación molécula-familia por ID.",
        responses={
            204: OpenApiResponse(description="Eliminado con éxito", response=None),
            404: OpenApiResponse(description="No encontrado", response=dict),
        },
        tags=["Chemistry • Families"],
    ),
)
class FamilyMemberViewSet(BaseChemistryViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer

    def perform_create(self, serializer):
        # Keep default behavior from legacy: no automatic created_by assignment
        serializer.save()
