"""Postprocessing hooks for drf-spectacular to fix path-specific schema issues.

This module contains a small hook that repairs the generated OpenAPI schema
for the `add_property` endpoints when drf-spectacular infers the wrong
request/response schema (it sometimes falls back to the viewset `serializer_class`).

The hook is defensive (checks existence of keys) and only changes the two
paths `/api/chemistry/molecules/{id}/add_property/` and
`/api/chemistry/families/{id}/add_property/` to reference the correct
components:
  - requestBody -> AddProperty
  - responses 201 -> MolecularProperty / FamilyProperty

Register this function in SPECTACULAR_SETTINGS.POSTPROCESSING_HOOKS.
"""

from typing import Any, Dict


def fix_add_property_schema(
    result: Dict[str, Any], generator=None, request=None, public: bool = False
) -> Dict[str, Any]:
    """Postprocess generated schema to fix add_property request/response shapes.

    drf-spectacular calls postprocessing hooks with keyword argument `result`.
    Keep the function signature compatible so it can be registered in
    SPECTACULAR_SETTINGS.POSTPROCESSING_HOOKS.

    Args:
        result: The OpenAPI schema dict produced by drf-spectacular.
        generator: Schema generator instance (optional).
        request: The original request (optional).
        public: Whether schema is public (optional).

    Returns:
        The possibly-modified schema dict.
    """
    schema = result
    paths = schema.setdefault("paths", {})
    # Ensure components.schemas exists and contains AddProperty definition
    components = schema.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    if "AddProperty" not in schemas:
        schemas["AddProperty"] = {
            "type": "object",
            "description": "Serializador para agregar propiedades a moléculas o familias.",
            "properties": {
                "property_type": {"type": "string", "maxLength": 200},
                "value": {"type": "string", "maxLength": 500},
                "method": {"type": "string", "maxLength": 100},
                "units": {"type": "string", "maxLength": 50},
                "source_id": {"type": "string", "maxLength": 100},
                "metadata": {"type": "object", "additionalProperties": True},
            },
            "required": ["property_type", "value"],
        }

    def _set_path(path: str, response_ref: str):
        entry = paths.get(path)
        if not entry:
            return
        post = entry.get("post")
        if not post:
            return

        # Force requestBody to be AddProperty component for JSON
        post["requestBody"] = {
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/AddProperty"}
                }
            },
            "required": True,
        }

        # Ensure 201 response points to the correct component
        responses = post.setdefault("responses", {})
        responses["201"] = {
            "content": {"application/json": {"schema": {"$ref": response_ref}}},
            "description": "",
        }

    # Molecule add_property
    _set_path(
        "/api/chemistry/molecules/{id}/add_property/",
        "#/components/schemas/MolecularProperty",
    )

    # Family add_property
    _set_path(
        "/api/chemistry/families/{id}/add_property/",
        "#/components/schemas/FamilyProperty",
    )

    return schema
