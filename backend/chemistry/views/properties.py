from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from ..models import MolecularProperty
from ..serializers import MolecularPropertySerializer
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
        return Response(out.data, status=201, headers=headers)
