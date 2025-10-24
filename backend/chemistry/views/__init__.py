"""Public views exports for chemistry.

This package exposes the smaller view modules created during the refactor.
It intentionally avoids importing the legacy monolith so that file can be
removed once tests validate the split.
"""

from drf_spectacular.views import SpectacularAPIView

from .families import *  # noqa: F401,F403
from .family_members import *  # noqa: F401,F403

# Re-export view modules
from .molecules import *  # noqa: F401,F403
from .properties import *  # noqa: F401,F403

# Lightweight schema view (kept for router inclusion)
schema_view = SpectacularAPIView.as_view()

__all__ = [name for name in globals().keys() if not name.startswith("_")]
