"""Public views exports for chemistry.

This package exposes the smaller view modules created during the refactor.
It intentionally avoids importing the legacy monolith so that file can be
removed once tests validate the split.
"""

from drf_spectacular.views import SpectacularAPIView

from .families import FamilyDetailView, FamilyListCreateView
from .family_members import FamilyMemberDetailView, FamilyMemberListCreateView
from .molecules import BaseChemistryViewSet, MoleculeViewSet
from .properties import MolecularPropertyViewSet

# Lightweight schema view (kept for router inclusion)
schema_view = SpectacularAPIView.as_view()

__all__ = [
    "FamilyDetailView",
    "FamilyListCreateView",
    "FamilyMemberDetailView",
    "FamilyMemberListCreateView",
    "BaseChemistryViewSet",
    "MoleculeViewSet",
    "MolecularPropertyViewSet",
    "schema_view",
]
