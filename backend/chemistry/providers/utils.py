"""
Utility helpers for chemistry providers.

Encapsula llamadas al engine seleccionado (RDKit o mock) para obtener
identificadores estructurales y propiedades calculadas de una SMILES.

Esto permite centralizar el manejo de excepciones y normalizar la forma
en que se solicitan `inchi`, `inchikey`, `canonical_smiles` y descriptores.
"""

from typing import Dict, Tuple


def enrich_smiles(smiles: str) -> Tuple[Dict[str, str], Dict[str, object]]:
    """Return (structure_dict, descriptors_dict) for the given SMILES.

    structure_dict contains keys: inchi, inchikey, canonical_smiles, molecular_formula
    descriptors_dict is the result of calculate_properties() or an empty dict on failure.

    This function swallows provider errors and returns sensible defaults so callers
    can fall back to static data when needed.
    """
    try:
        from . import engine as chem_engine

        structure = chem_engine.smiles_to_inchi(smiles, return_dataclass=False)
        try:
            descriptors = chem_engine.calculate_properties(
                smiles, return_dataclass=False
            )
        except Exception:
            descriptors = {}

        # Normalize structure keys to strings
        structure = {k: (v if v is not None else "") for k, v in structure.items()}
        return structure, descriptors
    except Exception:
        # Provider not available or failed
        return {}, {}
