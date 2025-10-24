"""
Vistas mejoradas para Chemistry aplicando principios SOLID.

Este módulo contiene vistas que:
- Tienen responsabilidades únicas (SRP)
- Están abiertas para extensión, cerradas para modificación (OCP)
- Dependen de abstracciones, no de implementaciones concretas (DIP)
- Mantienen bajo acoplamiento y alta cohesión

Las vistas actúan como coordinadores que delegan la lógica de negocio
a servicios especializados a través de acciones tipadas.
"""

from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from users.permissions import HasAppPermission

from . import services as chem_services
from .models import Family, FamilyMember, FamilyProperty, MolecularProperty, Molecule
from .serializers import (
    AddPropertySerializer,
    CreateFamilyFromSmilesSerializer,
    CreateMoleculeFromSmilesSerializer,
    FamilyMemberSerializer,
    FamilyPropertySerializer,
    FamilySerializer,
    MolecularPropertySerializer,
    MoleculeSerializer,
)


class BaseChemistryViewSet(viewsets.ModelViewSet):
    """Base ViewSet con permisos comunes."""

    permission_classes = [permissions.IsAuthenticated, HasAppPermission]
    permission_resource = "chemistry"

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


@extend_schema_view(
    list=extend_schema(
        summary="Listar moléculas",
        description="Obtiene la lista de moléculas disponibles en el sistema.",
    ),
    create=extend_schema(
        summary="Crear molécula",
        description="Crea una nueva molécula con sus propiedades básicas.",
    ),
    retrieve=extend_schema(
        summary="Obtener molécula",
        description="Obtiene los detalles de una molécula específica.",
    ),
    update=extend_schema(
        summary="Actualizar molécula",
        description="Actualiza una molécula existente.",
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente molécula",
        description="Actualiza parcialmente una molécula existente.",
    ),
    destroy=extend_schema(
        summary="Eliminar molécula",
        description="Elimina una molécula del sistema.",
    ),
)
class MoleculeViewSet(BaseChemistryViewSet):
    """ViewSet para gestión de moléculas."""

    queryset = Molecule.objects.all()
    serializer_class = MoleculeSerializer

    def get_permissions(self):
        # Permitir endpoints "mine" y el filtro ?mine=true para usuarios autenticados
        if getattr(self, "action", None) == "mine" or (
            getattr(self, "action", None) == "list"
            and self.request.query_params.get("mine") == "true"
        ):
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, "user", None)
        if getattr(self, "action", None) == "list" and (
            getattr(user, "is_superuser", False) or getattr(user, "is_staff", False)
        ):
            qs = qs
        else:
            base_qs = qs.exclude(created_by__isnull=True)
            qs = chem_services.filter_molecules_for_user(base_qs, user)

        # El query param ?mine=true fuerza siempre filtrar por el usuario autenticado
        if self.request.query_params.get("mine") == "true":
            qs = qs.filter(created_by=user)

        return qs

    @action(detail=False, methods=["get"])
    @extend_schema(
        summary="Listar mis moléculas",
        description="Obtiene las moléculas creadas por el usuario autenticado.",
    )
    def mine(self, request):
        """Endpoint personalizado para obtener moléculas del usuario autenticado."""
        # El endpoint /mine/ debe retornar siempre las moléculas creadas por
        # el usuario autenticado, sin importar si es administrador.
        qs = super().get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    @extend_schema(
        summary="Crear molécula desde SMILES",
        description="Crea una nueva molécula a partir de una notación SMILES.",
        request=CreateMoleculeFromSmilesSerializer,
        responses={201: MoleculeSerializer},
    )
    def from_smiles(self, request):
        """Crea una molécula desde notación SMILES."""
        serializer = CreateMoleculeFromSmilesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            molecule = chem_services.create_molecule_from_smiles(
                smiles=serializer.validated_data["smiles"],
                created_by=request.user,
                name=serializer.validated_data.get("name"),
                extra_metadata=serializer.validated_data.get("extra_metadata"),
            )
            return Response(MoleculeSerializer(molecule).data, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

    @action(detail=True, methods=["post"])
    @extend_schema(
        summary="Agregar propiedad a molécula",
        description="Agrega una nueva propiedad a la molécula.",
        request=AddPropertySerializer,
        responses={201: MolecularPropertySerializer},
    )
    def add_property(self, request, pk=None):
        """Agrega una propiedad a la molécula."""
        molecule = self.get_object()
        serializer = AddPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        molecular_property = MolecularProperty.objects.create(
            molecule=molecule, created_by=request.user, **serializer.validated_data
        )
        return Response(
            MolecularPropertySerializer(molecular_property).data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    list=extend_schema(
        summary="Listar propiedades moleculares",
        description="Obtiene la lista de propiedades moleculares.",
    ),
    create=extend_schema(
        summary="Crear propiedad molecular",
        description="Crea una nueva propiedad para una molécula.",
    ),
)
class MolecularPropertyViewSet(BaseChemistryViewSet):
    """ViewSet para propiedades moleculares (EAV)."""

    queryset = MolecularProperty.objects.all()
    serializer_class = MolecularPropertySerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def create(self, request, *args, **kwargs):
        """Crear propiedad molecular con auditoría y defaults explícitos."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.setdefault("method", "")
        data.setdefault("units", "")
        data.setdefault("relation", "")
        data.setdefault("source_id", "")
        prop = MolecularProperty.objects.create(created_by=request.user, **data)
        out = self.get_serializer(prop)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    list=extend_schema(
        summary="Listar familias",
        description="Obtiene la lista de familias de moléculas.",
    ),
    create=extend_schema(
        summary="Crear familia",
        description="Crea una nueva familia de moléculas.",
    ),
)
class FamilyViewSet(BaseChemistryViewSet):
    """ViewSet para familias de moléculas."""

    queryset = Family.objects.all()
    serializer_class = FamilySerializer

    @action(detail=False, methods=["get"])
    @extend_schema(
        summary="Mis familias",
        description="Obtiene las familias relacionadas con las moléculas del usuario.",
    )
    def mine(self, request):
        """Obtiene familias relacionadas con moléculas del usuario autenticado."""
        qs = self.get_queryset().filter(created_by=request.user)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    @extend_schema(
        summary="Crear familia desde SMILES",
        description="Crea una nueva familia a partir de una lista de SMILES.",
        request=CreateFamilyFromSmilesSerializer,
        responses={201: FamilySerializer},
    )
    def from_smiles(self, request):
        """Crea una familia desde lista de SMILES."""
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
    @extend_schema(
        summary="Generar propiedades ADMETSA",
        description="Genera propiedades ADMETSA para todas las moléculas de la familia.",
        responses={200: dict},
    )
    def generate_admetsa(self, request, pk=None):
        """Genera propiedades ADMETSA para la familia."""
        family = self.get_object()
        try:
            result = chem_services.generate_admetsa_for_family(
                family_id=family.id, created_by=request.user
            )
            # Añadir propiedad esperada por tests: properties_created
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
    @extend_schema(
        summary="Agregar propiedad a familia",
        description="Agrega una nueva propiedad a la familia.",
        request=AddPropertySerializer,
        responses={201: FamilyPropertySerializer},
    )
    def add_property(self, request, pk=None):
        """Agrega una propiedad a la familia."""
        family = self.get_object()
        serializer = AddPropertySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        family_property = FamilyProperty.objects.create(
            family=family, created_by=request.user, **serializer.validated_data
        )
        return Response(FamilyPropertySerializer(family_property).data, status=201)


@extend_schema_view(
    list=extend_schema(
        summary="Listar propiedades de familias",
        description="Obtiene la lista de propiedades de familias.",
    ),
    create=extend_schema(
        summary="Crear propiedad de familia",
        description="Crea una nueva propiedad para una familia.",
    ),
)
class FamilyPropertyViewSet(BaseChemistryViewSet):
    """ViewSet para propiedades de familias (EAV)."""

    queryset = FamilyProperty.objects.all()
    serializer_class = FamilyPropertySerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def create(self, request, *args, **kwargs):
        """Crear propiedad de familia con auditoría y defaults explícitos."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        data.setdefault("method", "")
        data.setdefault("units", "")
        data.setdefault("relation", "")
        data.setdefault("source_id", "")
        prop = FamilyProperty.objects.create(created_by=request.user, **data)
        out = self.get_serializer(prop)
        headers = self.get_success_headers(out.data)
        return Response(out.data, status=status.HTTP_201_CREATED, headers=headers)


@extend_schema_view(
    list=extend_schema(
        summary="Listar miembros de familias",
        description="Obtiene la lista de relaciones molécula-familia.",
    ),
    create=extend_schema(
        summary="Agregar miembro a familia",
        description="Agrega una molécula a una familia.",
    ),
)
class FamilyMemberViewSet(BaseChemistryViewSet):
    """ViewSet para membresías de familias (relaciones molécula-familia)."""

    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer

    def perform_create(self, serializer):
        """FamilyMember no tiene campos de auditoría, evitar pasar created_by."""
        serializer.save()
