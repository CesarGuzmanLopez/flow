import logging

from back.envelope import StandardEnvelopeMixin
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from users.permissions import HasAppPermission

from .. import services as chem_services
from ..models import Molecule
from ..serializers import (
    AddPropertySerializer,
    CreateMoleculeFromSmilesSerializer,
    CreateMoleculeSerializer,
    MolecularPropertySerializer,
    MoleculeSerializer,
    MoleculeUpdateSerializer,
)
from ..services.properties import (
    InvariantPropertyError,
    PropertyAlreadyExistsError,
    create_or_update_molecular_property,
)

logger = logging.getLogger(__name__)


class BaseChemistryViewSet(StandardEnvelopeMixin, viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Listar moléculas",
        description="Obtiene la lista de moléculas.",
        tags=["Chemistry • Molecules"],
    ),
    create=extend_schema(
        summary="Crear o recuperar molécula",
        description=(
            "Crea una nueva molécula o devuelve una existente si coincide por inchikey.\n"
            "Se aceptan SMILES (preferente) y/o InChIKey."
        ),
        request=CreateMoleculeSerializer,
        responses={
            200: MoleculeSerializer,
            201: MoleculeSerializer,
            400: OpenApiResponse(response=dict),
        },
        examples=[
            OpenApiExample(
                "Crear por SMILES",
                value={
                    "smiles": "CCO",
                    "name": "Ethanol",
                    "extra_metadata": {"source": "demo"},
                },
                request_only=True,
            )
        ],
        tags=["Chemistry • Molecules"],
    ),
    retrieve=extend_schema(
        summary="Recuperar molécula",
        description="Obtiene la representación completa de una molécula por su ID.",
        responses={
            200: MoleculeSerializer,
            404: OpenApiResponse(description="Molécula no encontrada", response=dict),
        },
        tags=["Chemistry • Molecules"],
    ),
    update=extend_schema(
        summary="Actualizar molécula (PUT)",
        description=(
            "Reemplaza todos los campos de la molécula. Use PATCH para actualizaciones parciales."
        ),
        responses={200: MoleculeSerializer, 400: OpenApiResponse(response=dict)},
        tags=["Chemistry • Molecules"],
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente molécula (PATCH)",
        description="Actualiza uno o más campos de la molécula sin reemplazar la entidad completa.",
        responses={200: MoleculeSerializer, 400: OpenApiResponse(response=dict)},
        tags=["Chemistry • Molecules"],
    ),
    destroy=extend_schema(
        summary="Eliminar molécula",
        description="Elimina la molécula indicada por ID. Retorna 204 en caso de éxito.",
        responses={
            204: OpenApiResponse(description="Eliminado con éxito", response=None),
            404: OpenApiResponse(description="Molécula no encontrada", response=dict),
        },
        tags=["Chemistry • Molecules"],
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

    @extend_schema(summary="Mis moléculas", tags=["Chemistry • Molecules"])
    @action(detail=False, methods=["get"])
    def mine(self, request):
        qs = super().get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Crear desde SMILES",
        description=(
            "Crea una molécula a partir de una cadena SMILES, normalizando estructuras\n"
            "y opcionalmente calculando descriptores si 'compute_descriptors' es True."
        ),
        request=CreateMoleculeFromSmilesSerializer,
        responses={201: MoleculeSerializer, 400: OpenApiResponse(response=dict)},
        examples=[
            OpenApiExample(
                "Ejemplo",
                value={
                    "smiles": "CC(=O)O",
                    "name": "Acetic acid",
                    "compute_descriptors": True,
                },
                request_only=True,
            )
        ],
        tags=["Chemistry • Molecules"],
    )
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
            result = chem_services.update_molecule(
                molecule=molecule,
                payload=serializer.validated_data,
                user=request.user,
                partial=False,
            )
            # Support both return shapes: Molecule or (Molecule, warning)
            if isinstance(result, tuple):
                mol, warning = result
            else:
                mol, warning = result, None
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
            result = chem_services.update_molecule(
                molecule=molecule,
                payload=serializer.validated_data,
                user=request.user,
                partial=True,
            )
            if isinstance(result, tuple):
                mol, warning = result
            else:
                mol, warning = result, None
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

    @extend_schema(
        summary="Agregar propiedad a una molécula",
        description=(
            "Crea una nueva propiedad EAV para la molécula. Previene duplicados estrictamente\n"
            "por la clave compuesta (molecule, property_type, method, relation, source_id)."
        ),
        request=AddPropertySerializer,
        responses={
            201: MolecularPropertySerializer,
            400: OpenApiResponse(
                description="Propiedad duplicada o inválida", response=dict
            ),
        },
        examples=[
            OpenApiExample(
                "Agregar LogP computacional",
                value={
                    "property_type": "LogP",
                    "value": "2.45",
                    "units": "",
                    "method": "rdkit",
                    "relation": "calc:baseline",
                    "source_id": "provider:rdkit",
                    "metadata": {"dataset": "batch-42"},
                    "is_invariant": False,
                },
                request_only=True,
            )
        ],
        tags=["Chemistry • Molecules"],
    )
    @action(detail=True, methods=["post"])
    def add_property(self, request, pk=None):
        """Add property to molecule with strict duplicate prevention.

        This endpoint creates a NEW property only. If a property with the same
        composite key already exists, it returns a 400 error suggesting PATCH/PUT.

        Composite key: (molecule, property_type, method, relation, source_id)
        """
        molecule = self.get_object()
        serializer = AddPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)

        try:
            # Use force_create=True to reject duplicates
            result = create_or_update_molecular_property(
                molecule=molecule,
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
            # Support both return shapes
            if isinstance(result, tuple):
                prop = result[0]
            else:
                prop = result
            return Response(
                MolecularPropertySerializer(prop).data, status=status.HTTP_201_CREATED
            )

        except PropertyAlreadyExistsError as e:
            return Response(
                {
                    "error": str(e),
                    "detail": (
                        "A property with this composite key already exists. "
                        "Use PATCH /api/chemistry/molecular-properties/{id}/ "
                        "or PUT /api/chemistry/molecular-properties/{id}/ to update it."
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


# MolecularPropertyViewSet has been moved to views/properties.py to keep
# molecule-related views focused and to follow SRP / modularization.
