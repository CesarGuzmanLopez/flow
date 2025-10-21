"""
Configuración de URLs para la app Chemistry.

Registra todos los endpoints REST de la app usando el router de DRF:
- /api/chemistry/molecules/ - Gestión de moléculas
- /api/chemistry/molecular-properties/ - Propiedades moleculares
- /api/chemistry/families/ - Familias de moléculas
- /api/chemistry/family-properties/ - Propiedades de familias
- /api/chemistry/family-members/ - Membresías molécula-familia
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    FamilyMemberViewSet,
    FamilyPropertyViewSet,
    FamilyViewSet,
    MolecularPropertyViewSet,
    MoleculeViewSet,
)

router = DefaultRouter()
router.register(r"molecules", MoleculeViewSet, basename="molecule")
router.register(
    r"molecular-properties", MolecularPropertyViewSet, basename="molecularproperty"
)
router.register(r"families", FamilyViewSet, basename="family")
router.register(r"family-properties", FamilyPropertyViewSet, basename="familyproperty")
router.register(r"family-members", FamilyMemberViewSet, basename="familymember")

urlpatterns = [
    path("", include(router.urls)),
]
