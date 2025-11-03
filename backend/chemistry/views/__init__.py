"""Public views exports for chemistry.

This package exposes the smaller view modules created during the refactor.
It intentionally avoids importing the legacy monolith so that file can be
removed once tests validate the split.
"""

from drf_spectacular.views import SpectacularAPIView

from .families import FamilyPropertyViewSet, FamilyViewSet
from .family_members import FamilyMemberViewSet
from .molecules import BaseChemistryViewSet, MoleculeViewSet
from .properties import MolecularPropertyViewSet

# Lightweight schema view (kept for router inclusion)
schema_view = SpectacularAPIView.as_view()

__all__ = [
    "FamilyViewSet",
    "FamilyPropertyViewSet",
    "FamilyMemberViewSet",
    "BaseChemistryViewSet",
    "MoleculeViewSet",
    "MolecularPropertyViewSet",
    "schema_view",
]
