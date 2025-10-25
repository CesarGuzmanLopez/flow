from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .. import services as chem_services
from ..models import Family, FamilyProperty
from ..providers import registry as provider_registry
from ..serializers import (
    AddPropertySerializer,
    CreateFamilyFromSmilesSerializer,
    FamilyPropertySerializer,
    FamilySerializer,
    PropertyGenerationRequestSerializer,
)
from ..services.properties import (
    InvariantPropertyError,
    PropertyAlreadyExistsError,
    create_or_update_family_property,
)
from ..services.property_generator import (
    generate_properties_for_family,
    preview_properties_for_family,
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

    @action(
        detail=True,
        methods=["post"],
        url_path="generate-properties/(?P<category>[^/.]+)/(?P<provider>[^/.]+)",
    )
    def generate_properties(self, request, pk=None, category=None, provider=None):
        """Generate properties for family using specified category and provider.

        This is the unified endpoint for property generation. It supports:
        - Multiple property categories (admetsa, physics, pharmacodynamic, etc.)
        - Multiple providers (rdkit, manual, provider-extra)
        - Global and per-molecule metadata
        - Properties are persisted to database

        URL Examples:
            POST /api/chemistry/families/5/generate-properties/admetsa/rdkit/
            POST /api/chemistry/families/5/generate-properties/physics/manual/
            POST /api/chemistry/families/5/generate-properties/admet/provider-extra/

        Request Body Examples:
            # RDKit with global metadata
            {
                "metadata": {
                    "experiment_id": "EXP-001",
                    "batch": "batch-42"
                }
            }

            # Manual provider with per-molecule data
            {
                "properties_data": {
                    "8": {"MolWt": "180.16", "LogP": "2.45"},
                    "9": {"MolWt": "194.19"}
                },
                "per_molecule_metadata": {
                    "8": {"technician": "John"},
                    "9": {"technician": "Jane"}
                }
            }

        Response:
            {
                "family_id": 5,
                "category": "admetsa",
                "provider": "rdkit",
                "persisted": true,
                "properties_created": 42,
                "molecules": [...]
            }
        """
        family = self.get_object()
        serializer = PropertyGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = generate_properties_for_family(
                family_id=family.id,
                category=category,
                provider=provider,
                persist=True,
                metadata=data.get("metadata"),
                per_molecule_metadata=data.get("per_molecule_metadata"),
                properties_data=data.get("properties_data"),
                created_by=request.user,
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response(
                {"error": f"Unknown provider or category: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Property generation failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="generate-properties-preview/(?P<category>[^/.]+)/(?P<provider>[^/.]+)",
    )
    def generate_properties_preview(
        self, request, pk=None, category=None, provider=None
    ):
        """Preview property generation without persisting to database.

        This endpoint calculates properties but DOES NOT save them. Useful for:
        - Validating input data before saving
        - Testing different providers/categories
        - Exploring property values before committing

        URL Examples:
            POST /api/chemistry/families/5/generate-properties-preview/admetsa/rdkit/
            POST /api/chemistry/families/5/generate-properties-preview/physics/manual/

        Request Body: Same as generate-properties endpoint

        Response:
            {
                "family_id": 5,
                "category": "admetsa",
                "provider": "rdkit",
                "persisted": false,
                "molecules": [...]
            }

        Note: Response does NOT include 'properties_created' since nothing was saved.
        """
        family = self.get_object()
        serializer = PropertyGenerationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = preview_properties_for_family(
                family_id=family.id,
                category=category,
                provider=provider,
                metadata=data.get("metadata"),
                per_molecule_metadata=data.get("per_molecule_metadata"),
                properties_data=data.get("properties_data"),
            )
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            return Response(
                {"error": f"Unknown provider or category: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Property generation failed: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="List all property categories",
        description=(
            "Returns a list of all property categories available across all providers, "
            "with their metadata and which providers support them."
        ),
        responses={
            200: OpenApiResponse(
                response=dict,
                description="List of all categories",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        value={
                            "categories": [
                                {
                                    "name": "admet",
                                    "display_name": "ADMET Extended",
                                    "description": "Extended ADMET properties including toxicity predictions",
                                    "property_count": 9,
                                    "available_providers": [
                                        "rdkit",
                                        "manual",
                                        "random",
                                    ],
                                },
                                {
                                    "name": "admetsa",
                                    "display_name": "ADMET-SA (Basic)",
                                    "description": "Basic ADMET properties: MolWt, LogP, TPSA, HBA, HBD, RB",
                                    "property_count": 6,
                                    "available_providers": [
                                        "rdkit",
                                        "manual",
                                        "random",
                                    ],
                                },
                                {
                                    "name": "pharmacodynamic",
                                    "display_name": "Pharmacodynamic Properties",
                                    "description": "Drug-like properties: LogP, HBA, HBD, TPSA, SA",
                                    "property_count": 5,
                                    "available_providers": [
                                        "rdkit",
                                        "manual",
                                        "random",
                                    ],
                                },
                                {
                                    "name": "physics",
                                    "display_name": "Physical Properties",
                                    "description": "Physical properties: MolWt, LogP, TPSA, MR, AtX",
                                    "property_count": 5,
                                    "available_providers": [
                                        "rdkit",
                                        "manual",
                                        "random",
                                    ],
                                },
                            ]
                        },
                    )
                ],
            )
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="generate-properties/categories",
    )
    def list_categories(self, request):
        """List all available property categories.

        Returns a list of all property categories available across all providers,
        with their metadata and which providers support them.

        URL Example:
            GET /api/chemistry/families/generate-properties/categories/

        Response:
            {
                "categories": [
                    {
                        "name": "admet",
                        "display_name": "ADMET Extended",
                        "description": "Extended ADMET properties including toxicity predictions",
                        "property_count": 9,
                        "available_providers": [
                            "rdkit",
                            "manual",
                            "random"
                        ]
                    },
                    {
                        "name": "admetsa",
                        "display_name": "ADMET-SA (Basic)",
                        "description": "Basic ADMET properties: MolWt, LogP, TPSA, HBA, HBD, RB",
                        "property_count": 6,
                        "available_providers": [
                            "rdkit",
                            "manual",
                            "random"
                        ]
                    },
                    {
                        "name": "pharmacodynamic",
                        "display_name": "Pharmacodynamic Properties",
                        "description": "Drug-like properties: LogP, HBA, HBD, TPSA, SA",
                        "property_count": 5,
                        "available_providers": [
                            "rdkit",
                            "manual",
                            "random"
                        ]
                    },
                    {
                        "name": "physics",
                        "display_name": "Physical Properties",
                        "description": "Physical properties: MolWt, LogP, TPSA, MR, AtX",
                        "property_count": 5,
                        "available_providers": [
                            "rdkit",
                            "manual",
                            "random"
                        ]
                    }
                ]
            }
        """
        try:
            # Get all unique categories from all providers
            categories_dict = {}

            for provider_name in provider_registry.list_provider_names():
                provider = provider_registry.get_provider(provider_name)
                for category_name in provider.list_categories():
                    if category_name not in categories_dict:
                        # Get category info
                        category_info = provider.get_category_info(category_name)
                        categories_dict[category_name] = {
                            "name": category_info.name,
                            "display_name": category_info.display_name,
                            "description": category_info.description,
                            "property_count": len(category_info.properties),
                            "available_providers": category_info.available_providers,
                        }

            # Sort by name
            categories_list = sorted(categories_dict.values(), key=lambda x: x["name"])

            return Response({"categories": categories_list}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to list categories: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="List providers for a category",
        description="Returns detailed information about all providers that can generate properties for the specified category.",
        responses={
            200: OpenApiResponse(
                response=dict,
                description="List of providers for the category",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        value={
                            "category": "admetsa",
                            "providers": [
                                {
                                    "name": "rdkit",
                                    "display_name": "RDKit Computational",
                                    "description": "Calculate properties using RDKit library",
                                    "requires_external_data": False,
                                    "is_computational": True,
                                    "supported_categories": [
                                        "admetsa",
                                        "admet",
                                        "physics",
                                        "pharmacodynamic",
                                    ],
                                },
                                {
                                    "name": "manual",
                                    "display_name": "Manual Data Entry",
                                    "description": "Use manually provided property data",
                                    "requires_external_data": True,
                                    "is_computational": False,
                                    "supported_categories": [
                                        "admetsa",
                                        "admet",
                                        "physics",
                                        "pharmacodynamic",
                                    ],
                                },
                                {
                                    "name": "random",
                                    "display_name": "Random Generator (Testing)",
                                    "description": "Generate random property values for testing purposes",
                                    "requires_external_data": False,
                                    "is_computational": True,
                                    "supported_categories": [
                                        "admetsa",
                                        "admet",
                                        "physics",
                                        "pharmacodynamic",
                                    ],
                                },
                            ],
                        },
                    )
                ],
            ),
            404: OpenApiResponse(description="Category not found"),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="generate-properties/categories/(?P<category>[^/.]+)/providers",
    )
    def list_providers_for_category(self, request, category=None):
        """List all providers available for a specific category.

        Returns detailed information about all providers that can generate
        properties for the specified category.

        URL Examples:
            GET /api/chemistry/families/generate-properties/categories/admetsa/providers/
            GET /api/chemistry/families/generate-properties/categories/physics/providers/

        Response:
            {
                "category": "admetsa",
                "providers": [
                    {
                        "name": "rdkit",
                        "display_name": "RDKit Computational",
                        "description": "Calculate properties using RDKit library",
                        "requires_external_data": false,
                        "is_computational": true,
                        "supported_categories": [
                            "admetsa",
                            "admet",
                            "physics",
                            "pharmacodynamic"
                        ]
                    },
                    {
                        "name": "manual",
                        "display_name": "Manual Data Entry",
                        "description": "Use manually provided property data",
                        "requires_external_data": true,
                        "is_computational": false,
                        "supported_categories": [
                            "admetsa",
                            "admet",
                            "physics",
                            "pharmacodynamic"
                        ]
                    },
                    {
                        "name": "random",
                        "display_name": "Random Generator (Testing)",
                        "description": "Generate random property values for testing purposes",
                        "requires_external_data": false,
                        "is_computational": true,
                        "supported_categories": [
                            "admetsa",
                            "admet",
                            "physics",
                            "pharmacodynamic"
                        ]
                    }
                ]
            }
        """
        try:
            # Get all providers that support this category
            provider_names = provider_registry.get_providers_for_category(category)

            if not provider_names:
                return Response(
                    {
                        "error": f"Category '{category}' not supported by any provider",
                        "available_categories": self._get_available_categories(),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get detailed info for each provider
            providers_list = []
            for provider_name in provider_names:
                provider = provider_registry.get_provider(provider_name)
                provider_info = provider.get_info()
                providers_list.append(
                    {
                        "name": provider_info.name,
                        "display_name": provider_info.display_name,
                        "description": provider_info.description,
                        "requires_external_data": provider_info.requires_external_data,
                        "is_computational": provider_info.is_computational,
                        "supported_categories": provider_info.supported_categories,
                    }
                )

            return Response(
                {"category": category, "providers": providers_list},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Failed to list providers: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Get category information",
        description=(
            "Returns metadata about what properties are available in this category "
            "and which providers can calculate them."
        ),
        responses={
            200: OpenApiResponse(
                response=dict,
                description="Category information with properties",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        value={
                            "category": "admetsa",
                            "display_name": "ADMET-SA (Basic)",
                            "description": "Basic ADMET properties: MolWt, LogP, TPSA, HBA, HBD, RB",
                            "properties": [
                                {
                                    "name": "MolWt",
                                    "description": "Molecular Weight",
                                    "units": "g/mol",
                                    "value_type": "float",
                                    "range_min": 0.0,
                                    "range_max": 2000.0,
                                },
                                {
                                    "name": "LogP",
                                    "description": "Partition Coefficient (octanol-water)",
                                    "units": "dimensionless",
                                    "value_type": "float",
                                    "range_min": -5.0,
                                    "range_max": 10.0,
                                },
                                {
                                    "name": "TPSA",
                                    "description": "Topological Polar Surface Area",
                                    "units": "Ų",
                                    "value_type": "float",
                                    "range_min": 0.0,
                                    "range_max": 300.0,
                                },
                            ],
                            "available_providers": ["rdkit", "manual", "random"],
                        },
                    )
                ],
            ),
            404: OpenApiResponse(description="Category not found"),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="generate-properties/(?P<category>[^/.]+)/info",
    )
    def category_info(self, request, category=None):
        """Get information about a property category.

        Returns metadata about what properties are available in this category
        and which providers can calculate them.

        URL Examples:
            GET /api/chemistry/families/generate-properties/admetsa/info/
            GET /api/chemistry/families/generate-properties/physics/info/

        Response:
            {
                "category": "admetsa",
                "display_name": "ADMET-SA (Basic)",
                "description": "Basic ADMET properties: MolWt, LogP, TPSA, HBA, HBD, RB",
                "properties": [
                    {
                        "name": "MolWt",
                        "description": "Molecular Weight",
                        "units": "g/mol",
                        "value_type": "float",
                        "range_min": 0.0,
                        "range_max": 2000.0
                    },
                    {
                        "name": "LogP",
                        "description": "Partition Coefficient (octanol-water)",
                        "units": "dimensionless",
                        "value_type": "float",
                        "range_min": -5.0,
                        "range_max": 10.0
                    },
                    {
                        "name": "TPSA",
                        "description": "Topological Polar Surface Area",
                        "units": "Ų",
                        "value_type": "float",
                        "range_min": 0.0,
                        "range_max": 300.0
                    }
                ],
                "available_providers": [
                    "rdkit",
                    "manual",
                    "random"
                ]
            }
        """
        try:
            # Get all providers that support this category
            providers_for_category = provider_registry.get_providers_for_category(
                category
            )

            if not providers_for_category:
                return Response(
                    {
                        "error": f"Category '{category}' not supported by any provider",
                        "available_categories": self._get_available_categories(),
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Get category info from first available provider (they all have same structure)
            provider = provider_registry.get_provider(providers_for_category[0])
            category_info = provider.get_category_info(category)

            # Convert to dict for JSON response
            response_data = {
                "category": category_info.name,
                "display_name": category_info.display_name,
                "description": category_info.description,
                "properties": [
                    {
                        "name": prop.name,
                        "description": prop.description,
                        "units": prop.units,
                        "value_type": prop.value_type,
                        "range_min": prop.range_min,
                        "range_max": prop.range_max,
                    }
                    for prop in category_info.properties
                ],
                "available_providers": category_info.available_providers,
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Failed to get category info: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Get provider capabilities for a category",
        description=(
            "Returns what properties this specific provider can calculate for the category, "
            "along with provider metadata."
        ),
        responses={
            200: OpenApiResponse(
                response=dict,
                description="Provider and category information",
                examples=[
                    OpenApiExample(
                        "Success Response",
                        value={
                            "provider": {
                                "name": "rdkit",
                                "display_name": "RDKit Computational",
                                "description": "Calculate properties using RDKit library",
                                "requires_external_data": False,
                                "is_computational": True,
                                "supported_categories": [
                                    "admetsa",
                                    "admet",
                                    "physics",
                                    "pharmacodynamic",
                                ],
                            },
                            "category": {
                                "name": "admetsa",
                                "display_name": "ADMET-SA (Basic)",
                                "description": "Basic ADMET properties",
                                "properties": [
                                    {
                                        "name": "MolWt",
                                        "description": "Molecular Weight",
                                        "units": "g/mol",
                                        "value_type": "float",
                                        "range_min": 0.0,
                                        "range_max": 2000.0,
                                    },
                                    {
                                        "name": "LogP",
                                        "description": "Partition Coefficient (octanol-water)",
                                        "units": "dimensionless",
                                        "value_type": "float",
                                        "range_min": -5.0,
                                        "range_max": 10.0,
                                    },
                                ],
                                "available_providers": ["rdkit", "manual", "random"],
                            },
                        },
                    )
                ],
            ),
            404: OpenApiResponse(description="Provider not found"),
            400: OpenApiResponse(description="Category not supported by provider"),
        },
    )
    @action(
        detail=False,
        methods=["get"],
        url_path="generate-properties/(?P<category>[^/.]+)/(?P<provider>[^/.]+)/info",
    )
    def provider_category_info(self, request, category=None, provider=None):
        """Get detailed information about a specific provider's capabilities for a category.

        Returns what properties this specific provider can calculate for the category,
        along with provider metadata.

        URL Examples:
            GET /api/chemistry/families/generate-properties/admetsa/rdkit/info/
            GET /api/chemistry/families/generate-properties/physics/manual/info/

        Response:
            {
                "provider": {
                    "name": "rdkit",
                    "display_name": "RDKit Computational",
                    "description": "Calculate properties using RDKit library",
                    "requires_external_data": false,
                    "is_computational": true,
                    "supported_categories": [
                        "admetsa",
                        "admet",
                        "physics",
                        "pharmacodynamic"
                    ]
                },
                "category": {
                    "name": "admetsa",
                    "display_name": "ADMET-SA (Basic)",
                    "description": "Basic ADMET properties",
                    "properties": [
                        {
                            "name": "MolWt",
                            "description": "Molecular Weight",
                            "units": "g/mol",
                            "value_type": "float",
                            "range_min": 0.0,
                            "range_max": 2000.0
                        },
                        {
                            "name": "LogP",
                            "description": "Partition Coefficient (octanol-water)",
                            "units": "dimensionless",
                            "value_type": "float",
                            "range_min": -5.0,
                            "range_max": 10.0
                        }
                    ],
                    "available_providers": [
                        "rdkit",
                        "manual",
                        "random"
                    ]
                }
            }
        """
        try:
            # Get provider
            provider_instance = provider_registry.get_provider(provider)
            provider_info = provider_instance.get_info()

            # Get category info from this provider
            category_info = provider_instance.get_category_info(category)

            # Build response
            response_data = {
                "provider": {
                    "name": provider_info.name,
                    "display_name": provider_info.display_name,
                    "description": provider_info.description,
                    "requires_external_data": provider_info.requires_external_data,
                    "is_computational": provider_info.is_computational,
                    "supported_categories": provider_info.supported_categories,
                },
                "category": {
                    "name": category_info.name,
                    "display_name": category_info.display_name,
                    "description": category_info.description,
                    "properties": [
                        {
                            "name": prop.name,
                            "description": prop.description,
                            "units": prop.units,
                            "value_type": prop.value_type,
                            "range_min": prop.range_min,
                            "range_max": prop.range_max,
                        }
                        for prop in category_info.properties
                    ],
                    "available_providers": category_info.available_providers,
                },
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except KeyError as e:
            return Response(
                {
                    "error": f"Provider '{provider}' not found {str(e)}",
                    "available_providers": provider_registry.list_provider_names(),
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response(
                {
                    "error": str(e),
                    "provider_supported_categories": provider_instance.list_categories()
                    if "provider_instance" in locals()
                    else [],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to get provider info: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_available_categories(self):
        """Helper to get all available categories across all providers."""
        categories = set()
        for provider_name in provider_registry.list_provider_names():
            provider = provider_registry.get_provider(provider_name)
            categories.update(provider.list_categories())
        return sorted(list(categories))


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
