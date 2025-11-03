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

from .views.families import FamilyPropertyViewSet, FamilyViewSet
from .views.family_members import FamilyMemberViewSet
from .views.molecules import MoleculeViewSet
from .views.properties import MolecularPropertyViewSet

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
    # Telemetría para external jobs (providers pesados)
    path(
        "external-jobs/health",
        __import__(
            "chemistry.providers.external_jobs.telemetry",
            fromlist=["health_check"],
        ).health_check,
        name="external_jobs_health",
    ),
    path(
        "external-jobs/readiness",
        __import__(
            "chemistry.providers.external_jobs.telemetry",
            fromlist=["readiness_check"],
        ).readiness_check,
        name="external_jobs_readiness",
    ),
    path(
        "external-jobs/metrics",
        __import__(
            "chemistry.providers.external_jobs.telemetry", fromlist=["metrics"]
        ).metrics,
        name="external_jobs_metrics",
    ),
]
