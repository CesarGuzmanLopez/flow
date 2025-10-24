from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from ..models import MolecularProperty
from ..serializers import MolecularPropertySerializer
from ..services.properties import PropertyAlreadyExistsError
from .molecules import BaseChemistryViewSet


@extend_schema_view(
    list=extend_schema(summary="Listar propiedades moleculares"),
    create=extend_schema(summary="Crear propiedad molecular"),
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

    def partial_update(self, request, *args, **kwargs):
        """Partial update (PATCH) with invariant protection."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
