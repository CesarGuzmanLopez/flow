from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from ..models import MolecularProperty
from ..serializers import MolecularPropertySerializer
from ..services.properties import PropertyAlreadyExistsError
from .molecules import BaseChemistryViewSet


@extend_schema_view(
    list=extend_schema(
        summary="Listar propiedades moleculares", tags=["Chemistry • Properties"]
    ),
    create=extend_schema(
        summary="Crear propiedad molecular",
        description=(
            "Crea una propiedad EAV para una molécula con validación de unicidad compuesta.\n"
            "Devuelve 400 si ya existe una propiedad con la clave compuesta (molecule, property_type, method, relation, source_id)."
        ),
        responses={
            201: MolecularPropertySerializer,
            400: OpenApiResponse(response=dict),
        },
        tags=["Chemistry • Properties"],
        examples=[
            OpenApiExample(
                "Nueva propiedad",
                value={
                    "molecule": 8,
                    "property_type": "MolWt",
                    "value": "180.16",
                    "units": "g/mol",
                    "method": "aggregation",
                    "relation": "calc:mean",
                    "source_id": "exp:001",
                    "metadata": {"source": "labX"},
                    "is_invariant": False,
                },
                request_only=True,
            )
        ],
    ),
    retrieve=extend_schema(
        summary="Recuperar propiedad molecular",
        description="Obtiene una propiedad molecular por su ID.",
        responses={
            200: MolecularPropertySerializer,
            404: OpenApiResponse(description="Propiedad no encontrada", response=dict),
        },
        tags=["Chemistry • Properties"],
    ),
    destroy=extend_schema(
        summary="Eliminar propiedad molecular",
        description="Elimina la propiedad molecular indicada por ID. Retorna 204 en caso de éxito.",
        responses={
            204: OpenApiResponse(description="Eliminado con éxito", response=None),
            404: OpenApiResponse(description="Propiedad no encontrada", response=dict),
        },
        tags=["Chemistry • Properties"],
    ),
)
class MolecularPropertyViewSet(BaseChemistryViewSet):
    queryset = MolecularProperty.objects.all()
    serializer_class = MolecularPropertySerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        """Allow simple filtering by molecule id via query param `?molecule=<id>`.

        This is a lightweight convenience that avoids adding django-filter as a
        dependency. It keeps the default behavior (return all properties) when
        no query param is provided.
        """
        qs = super().get_queryset()
        molecule = self.request.query_params.get("molecule")
        if molecule:
            try:
                mq = int(molecule)
            except Exception:
                return qs.none()
            return qs.filter(molecule_id=mq)
        return qs

    def create(self, request, *args, **kwargs):
        """Create new molecular property with uniqueness validation.

        Raises 400 error if property with same composite key already exists,
        suggesting use of PATCH/PUT for updates.
        """
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            # Serializer.create handles uniqueness validation
            prop = serializer.save()
            out = self.get_serializer(prop)
            headers = self.get_success_headers(out.data)
            return Response(out.data, status=201, headers=headers)
        except PropertyAlreadyExistsError as e:
            return Response(
                {
                    "error": str(e),
                    "detail": "Property with this composite key already exists. Use PATCH or PUT to update.",
                    "property_type": e.property_type,
                    "method": e.method,
                    "relation": e.relation,
                    "source_id": e.source_id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    @extend_schema(
        summary="Actualizar propiedad molecular",
        description=(
            "Actualiza una propiedad existente. Si es invariante (is_invariant=True), solo permite modificar metadata."
        ),
        responses={
            200: MolecularPropertySerializer,
            400: OpenApiResponse(response=dict),
        },
        tags=["Chemistry • Properties"],
    )
    def update(self, request, *args, **kwargs):
        """Update existing molecular property with invariant protection."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        # Check if trying to modify invariant property value
        new_value = request.data.get("value")
        if (
            instance.is_invariant
            and new_value is not None
            and new_value != instance.value
        ):
            return Response(
                {
                    "error": f"Cannot modify value of invariant property (id={instance.id}). "
                    "Invariant properties can only have their metadata updated."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    @extend_schema(
        summary="Actualizar parcialmente propiedad molecular",
        responses={
            200: MolecularPropertySerializer,
            400: OpenApiResponse(response=dict),
        },
        tags=["Chemistry • Properties"],
    )
    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) with invariant protection."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

