import logging
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from django.db.models import QuerySet

logger = logging.getLogger(__name__)


def _compute_property_statistics(
    member_properties: List[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:
    from statistics import mean, stdev

    property_values: Dict[str, List[float]] = {}
    for member in member_properties:
        props_dict = member["properties"].to_dict()
        for prop_name, value in props_dict.items():
            if value is not None and isinstance(value, (int, float)):
                if prop_name not in property_values:
                    property_values[prop_name] = []
                property_values[prop_name].append(float(value))

    stats: Dict[str, Dict[str, float]] = {}
    for prop_name, values in property_values.items():
        if len(values) > 0:
            stats[prop_name] = {
                "mean": mean(values),
                "min": min(values),
                "max": max(values),
                "count": len(values),
            }
            if len(values) > 1:
                stats[prop_name]["std"] = stdev(values)
            else:
                stats[prop_name]["std"] = 0.0

    return stats


def filter_molecules_for_user(
    qs: "QuerySet[Any]", user: "AbstractUser"
) -> "QuerySet[Any]":
    """Restrict molecules to those created by the user unless they have global perms."""
    has_perm = getattr(user, "has_permission", lambda *args: False)
    if getattr(user, "is_superuser", False) or has_perm("chemistry", "read"):
        return qs
    return qs.filter(created_by=user)
