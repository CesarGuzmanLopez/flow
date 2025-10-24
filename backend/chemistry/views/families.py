from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .. import services as chem_services
from ..models import Family, FamilyProperty
from ..serializers import (
    AddPropertySerializer,
    CreateFamilyFromSmilesSerializer,
    FamilyPropertySerializer,
    FamilySerializer,
)
from ..services.properties import (
    InvariantPropertyError,
    PropertyAlreadyExistsError,
    create_or_update_family_property,
)
from .molecules import BaseChemistryViewSet


@extend_schema_view(
    list=extend_schema(summary="Listar familias"),
    create=extend_schema(summary="Crear familia"),
)
class FamilyViewSet(BaseChemistryViewSet):
    queryset = Family.objects.all()
    serializer_class = FamilySerializer

    @action(detail=False, methods=["get"])
    def mine(self, request):
        qs = self.get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def from_smiles(self, request):
        serializer = CreateFamilyFromSmilesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            family = chem_services.create_family_from_smiles(
                name=serializer.validated_data["name"],
                smiles_list=serializer.validated_data["smiles_list"],
                created_by=request.user,
                provenance=serializer.validated_data.get("provenance", "user"),
            )
            return Response(FamilySerializer(family).data, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    def generate_admetsa(self, request, pk=None):
        family = self.get_object()
        try:
            result = chem_services.generate_admetsa_for_family(
                family_id=family.id, created_by=request.user
            )
            try:
                properties_created = 0
                for m in result.get("molecules", []):
                    props = m.get("properties", {})
                    properties_created += sum(
                        1 for v in props.values() if v is not None
                    )
                enriched = {**result, "properties_created": properties_created}
            except Exception:
                enriched = {**result, "properties_created": 0}

            return Response(enriched, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    def add_property(self, request, pk=None):
        """Add property to family with strict duplicate prevention.

        This endpoint creates a NEW property only. If a property with the same
        composite key already exists, it returns a 400 error suggesting PATCH/PUT.

        Composite key: (family, property_type, method, relation, source_id)
        """
        family = self.get_object()
        serializer = AddPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        try:
            # Use force_create=True to reject duplicates
            prop, created = create_or_update_family_property(
                family=family,
                property_type=data["property_type"],
                value=data["value"],
                method=data.get("method", ""),
                relation=data.get("relation", ""),
                source_id=data.get("source_id", ""),
                units=data.get("units", ""),
                is_invariant=data.get("is_invariant", False),
                metadata=data.get("metadata", {}),
                created_by=request.user,
                force_create=True,  # ← Reject duplicates
            )

            return Response(
                FamilyPropertySerializer(prop).data, status=status.HTTP_201_CREATED
            )

        except PropertyAlreadyExistsError as e:
            return Response(
                {
                    "error": str(e),
                    "detail": (
                        "A property with this composite key already exists. "
                        "Use PATCH /api/chemistry/family-properties/{id}/ "
                        "or PUT /api/chemistry/family-properties/{id}/ to update it."
                    ),
                    "property_type": e.property_type,
                    "method": e.method,
                    "relation": e.relation,
                    "source_id": e.source_id,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InvariantPropertyError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


@extend_schema_view(
    list=extend_schema(summary="Listar propiedades de familias"),
    create=extend_schema(summary="Crear propiedad de familia"),
)
class FamilyPropertyViewSet(BaseChemistryViewSet):
    queryset = FamilyProperty.objects.all()
    serializer_class = FamilyPropertySerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def create(self, request, *args, **kwargs):
        """Create new family property with uniqueness validation."""
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            prop = serializer.save()
            out = self.get_serializer(prop)
            headers = self.get_success_headers(out.data)
            return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)
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
        """Update existing family property with invariant protection."""
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
