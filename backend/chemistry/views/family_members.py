from ..models import FamilyMember
from ..serializers import FamilyMemberSerializer
from .molecules import BaseChemistryViewSet


class FamilyMemberViewSet(BaseChemistryViewSet):
    queryset = FamilyMember.objects.all()
    serializer_class = FamilyMemberSerializer

    def perform_create(self, serializer):
        # Keep default behavior from legacy: no automatic created_by assignment
        serializer.save()
