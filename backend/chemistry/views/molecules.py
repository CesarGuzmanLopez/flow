import logging

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import HasAppPermission

from .. import services as chem_services
from ..models import MolecularProperty, Molecule
from ..serializers import (
    AddPropertySerializer,
    CreateMoleculeFromSmilesSerializer,
    CreateMoleculeSerializer,
    MolecularPropertySerializer,
    MoleculeSerializer,
    MoleculeUpdateSerializer,
)

logger = logging.getLogger(__name__)


class BaseChemistryViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Listar moléculas", description="Obtiene la lista de moléculas."
    ),
    create=extend_schema(
        summary="Crear molécula", description="Crea una nueva molécula."
    ),
)
class MoleculeViewSet(BaseChemistryViewSet):
    queryset = Molecule.objects.all()
    serializer_class = MoleculeSerializer

    def get_permissions(self):
        if getattr(self, "action", None) == "mine" or (
            getattr(self, "action", None) == "list"
            and self.request.query_params.get("mine") == "true"
        ):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if user and (
            getattr(user, "is_superuser", False) or getattr(user, "is_staff", False)
        ):
            qs = qs
        else:
            base_qs = qs.exclude(created_by__isnull=True)
            qs = chem_services.filter_molecules_for_user(base_qs, user)

        if self.request.query_params.get("mine") == "true":
            qs = qs.filter(created_by=user)

        return qs

    @extend_schema(
        summary="Crear o recuperar molécula",
        request=CreateMoleculeSerializer,
        responses={
            200: MoleculeSerializer,
            201: MoleculeSerializer,
            400: {"type": "object"},
        },
    )
    def create(self, request, *args, **kwargs):
        from django.core.exceptions import ValidationError

        payload = request.data if isinstance(request.data, dict) else dict(request.data)
        try:
            molecule, created = chem_services.create_or_get_molecule(
                payload=payload, created_by=request.user
            )
            serializer = MoleculeSerializer(molecule, context={"request": request})
            status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            headers = {}
            if created:
                headers["Location"] = f"/api/chemistry/molecules/{molecule.id}/"
            return Response(serializer.data, status=status_code, headers=headers)
        except ValidationError as e:
            msg = e.message if hasattr(e, "message") else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"])
    def mine(self, request):
        qs = super().get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def from_smiles(self, request):
        serializer = CreateMoleculeFromSmilesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            molecule = chem_services.create_molecule_from_smiles(
                smiles=serializer.validated_data["smiles"],
                created_by=request.user,
                name=serializer.validated_data.get("name"),
                extra_metadata=serializer.validated_data.get("extra_metadata"),
                compute_descriptors=bool(
                    serializer.validated_data.get("compute_descriptors", False)
                ),
            )
            return Response(MoleculeSerializer(molecule).data, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    def update(self, request, *args, **kwargs):
        from django.core.exceptions import ValidationError

        molecule = self.get_object()
        serializer = MoleculeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            mol, warning = chem_services.update_molecule(
                molecule=molecule,
                payload=serializer.validated_data,
                user=request.user,
                partial=False,
            )
            out = MoleculeSerializer(mol, context={"request": request})
            resp = {**out.data}
            if warning:
                resp["warning"] = warning
            return Response(resp, status=status.HTTP_200_OK)
        except ValidationError as e:
            msg = e.message if hasattr(e, "message") else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        from django.core.exceptions import ValidationError

        molecule = self.get_object()
        serializer = MoleculeUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        try:
            mol, warning = chem_services.update_molecule(
                molecule=molecule,
                payload=serializer.validated_data,
                user=request.user,
                partial=True,
            )
            out = MoleculeSerializer(mol, context={"request": request})
            resp = {**out.data}
            if warning:
                resp["warning"] = warning
            return Response(resp, status=status.HTTP_200_OK)
        except ValidationError as e:
            msg = e.message if hasattr(e, "message") else str(e)
            return Response({"error": msg}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def add_property(self, request, pk=None):
        molecule = self.get_object()
        serializer = AddPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.setdefault("method", "")
        data.setdefault("units", "")
        data.setdefault("relation", "")
        data.setdefault("source_id", "")
        data.setdefault("metadata", {})

        # Permit creating new property types via this endpoint. The previous
        # behavior rejected unknown property_type values; that made the API
        # brittle because descriptors (which used to populate types) are not
        # created by default anymore.
        prop_type = data["property_type"]

        lookup = {
            "molecule": molecule,
            "property_type": prop_type,
            "method": data.get("method", ""),
        }
        defaults = {
            "value": data.get("value"),
            "is_invariant": data.get("is_invariant", False),
            "units": data.get("units", ""),
            "relation": data.get("relation", ""),
            "source_id": data.get("source_id", ""),
            "metadata": data.get("metadata", {}),
        }

        try:
            molecular_property, created = MolecularProperty.objects.update_or_create(
                defaults=defaults, **lookup
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if created and getattr(molecular_property, "created_by", None) is None:
            molecular_property.created_by = request.user
            molecular_property.save(update_fields=["created_by", "updated_at"])

        resp_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            MolecularPropertySerializer(molecular_property).data, status=resp_status
        )


# MolecularPropertyViewSet has been moved to views/properties.py to keep
# molecule-related views focused and to follow SRP / modularization.
