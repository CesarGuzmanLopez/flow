"""
Servicios de dominio para gestión de moléculas.

Este módulo encapsula la lógica de negocio para crear, buscar y actualizar moléculas,
garantizando normalización estructural (vía ChemEngine) y unicidad por InChIKey.

Reglas de negocio implementadas:
- Normalización automática: SMILES → InChI, InChIKey, canonical SMILES, fórmula molecular.
- Unicidad: una sola instancia de Molecule por InChIKey (búsqueda/creación idempotente).
- Auditoría: todas las moléculas llevan created_by y updated_by.
- Opcionalidad de descriptores: se calculan solo si se piden explícitamente (para limitar peso).
- Validación de entrada: rechaza SMILES inválidos con errores descriptivos.

Objetivos:
- Facilitar creación desde API REST (via views) o scripts/migraciones.
- Proveer interfaz uniforme para casos de uso: moléculas nuevas, existentes, o idempotentes.
- Aislar dependencia en el ChemEngine (RDKit/mock) para facilitar pruebas.

Resumen en inglés:
Domain services for molecule management (creation, lookup, updates).
"""

import logging
from typing import Any, Dict

from django.core.exceptions import ValidationError

from .. import providers as providers
from ..models import Molecule
from ..types import (
    InvalidSmilesError,
    MolecularProperties,
    PropertyCalculationError,
    StructureIdentifiers,
)

logger = logging.getLogger(__name__)


def create_molecule_from_smiles(
    *,
    smiles: str,
    created_by: Any,
    name: str | None = None,
    extra_metadata: Dict[str, Any] | None = None,
    compute_descriptors: bool = False,
) -> Molecule:
    """Crea una molécula a partir de una SMILES, con normalización y deduplicación.

    Este servicio es el punto de entrada principal para crear moléculas desde:
    - API REST (views/molecules.py)
    - Servicios de familias (para construir familias desde listas de SMILES)
    - Scripts y comandos de importación

    Flujo:
    1. Valida SMILES vacíos/nulos
    2. Normaliza estructura vía ChemEngine (SMILES → InChI, InChIKey, canonical SMILES, fórmula)
    3. Opcionalmente calcula descriptores (MolWt, LogP, etc.) y los guarda en metadata
    4. Crea o busca molécula por InChIKey (idempotente)
    5. Retorna instancia de Molecule

    Args:
        smiles: Cadena SMILES de la molécula (requerido, no vacío)
        created_by: Usuario que crea la molécula (requerido)
        name: Nombre opcional (si no se proporciona, usa la fórmula molecular)
        extra_metadata: Metadatos adicionales para fusionar con los calculados
        compute_descriptors: Si True, calcula y guarda propiedades básicas en metadata

    Returns:
        Instancia de Molecule (nueva o existente si InChIKey coincide)

    Raises:
        ValidationError: Si SMILES vacío, inválido, o falla normalización/cálculo
        ValueError: Si created_by es None

    Examples:
        >>> # Crear molécula simple
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user,
        ...     name="Ethanol",
        ...     extra_metadata={"source": "pubchem"}
        ... )
        >>> print(mol.inchikey)
        IK_...

        >>> # Con descriptores
        >>> mol = create_molecule_from_smiles(
        ...     smiles="CCO",
        ...     created_by=user,
        ...     compute_descriptors=True
        ... )
        >>> print(mol.metadata["descriptors"]["MolWt"])
        46.07
    """
    if not smiles or not smiles.strip():
        raise ValidationError("SMILES cannot be empty")

    if not created_by:
        raise ValueError("created_by is required")

    try:
        from django.db import transaction

        with transaction.atomic():
            structure_info: StructureIdentifiers = providers.engine.smiles_to_inchi(
                smiles.strip(), return_dataclass=True
            )

            # Compute descriptors only when explicitly requested. By default we avoid
            # populating metadata with potentially heavy descriptor data.
            metadata = {}
            if compute_descriptors:
                properties: MolecularProperties = providers.engine.calculate_properties(
                    smiles.strip(), return_dataclass=True
                )
                properties_dict = properties.to_dict()
                metadata["descriptors"] = properties_dict

            if extra_metadata:
                metadata.update(extra_metadata)

            defaults = {
                "name": name or structure_info.molecular_formula or "",
                "smiles": smiles.strip(),
                "canonical_smiles": structure_info.canonical_smiles,
                "inchi": structure_info.inchi,
                "molecular_formula": structure_info.molecular_formula or "",
                "created_by": created_by,
                "metadata": metadata,
            }

            if structure_info.inchikey:
                molecule, created = Molecule.objects.get_or_create(
                    inchikey=structure_info.inchikey, defaults=defaults
                )
                if not created:
                    logger.info(
                        f"Molecule with InChIKey {structure_info.inchikey} already exists"
                    )
            else:
                molecule = Molecule.objects.create(**defaults)
            return molecule

    except InvalidSmilesError as e:
        logger.error(f"Invalid SMILES '{smiles}': {e}")
        raise ValidationError(f"Invalid SMILES: {e}")
    except PropertyCalculationError as e:
        logger.error(f"Property calculation failed for SMILES '{smiles}': {e}")
        raise ValidationError(f"Property calculation failed: {e}")
    except Exception as e:
        logger.error(f"Error creating molecule from SMILES '{smiles}': {e}")
        raise ValidationError(f"Invalid SMILES or chemistry engine error: {e}")


def create_or_get_molecule(*, payload: dict, created_by: Any) -> tuple[Molecule, bool]:
    """Crea o recupera una molécula según payload con SMILES y/o InChIKey.

    Servicio idempotente usado por la API REST para endpoints que aceptan tanto
    SMILES nuevos como referencias a moléculas existentes vía InChIKey. Útil para:
    - Crear nuevas moléculas desde SMILES
    - Referenciar moléculas ya registradas (por InChIKey)
    - Migrar/importar listas mixtas (algunos duplicados, algunos nuevos)

    Lógica:
    - Solo InChIKey (sin SMILES): busca existente; error si no existe
    - SMILES provisto: normaliza y crea/deduplica por InChIKey
    - SMILES + InChIKey: verifica consistencia; actualiza nombre si difiere

    Args:
        payload: Dict con claves "smiles", "inchikey", "name", "extra_metadata"
        created_by: Usuario que solicita la operación

    Returns:
        Tupla (Molecule, created: bool)

    Raises:
        ValueError: Si created_by es None o payload inválido
        ValidationError: Si solo InChIKey y no existe, o SMILES inválido, o inconsistencia

    Examples:
        >>> # Crear desde SMILES
        >>> mol, created = create_or_get_molecule(
        ...     payload={"smiles": "CCO", "name": "Ethanol"},
        ...     created_by=user
        ... )
        >>> print(created)
        True

        >>> # Referenciar existente por InChIKey
        >>> mol, created = create_or_get_molecule(
        ...     payload={"inchikey": "IK_12345abc"},
        ...     created_by=user
        ... )
        >>> print(created)
        False
    """
    if not created_by:
        raise ValueError("created_by is required")

    inchikey = (payload.get("inchikey") or "").strip() or None
    smiles = (payload.get("smiles") or "").strip() or None
    name = payload.get("name")
    extra_metadata = payload.get("extra_metadata") or {}

    # Case: only inchikey (no smiles) -> lookup existing only
    if inchikey and not smiles:
        try:
            mol = Molecule.objects.get(inchikey__iexact=inchikey)
            if mol.created_by is None:
                mol.created_by = created_by
                mol.save(update_fields=["created_by", "updated_at"])
            else:
                try:
                    collabs = list(mol.metadata.get("collaborators", []))
                except Exception:
                    collabs = []
                uid = getattr(created_by, "id", None)
                if (
                    uid
                    and uid != getattr(mol.created_by, "id", None)
                    and uid not in collabs
                ):
                    collabs.append(uid)
                    mol.metadata = dict(mol.metadata or {})
                    mol.metadata["collaborators"] = collabs
                    mol.save(update_fields=["metadata", "updated_at"])
            return mol, False
        except Molecule.DoesNotExist:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                "Cannot create molecule with only InChIKey; SMILES or additional structural data is required"
            )

    # Case: SMILES provided (primary creation path)
    if smiles:
        try:
            structure_info = providers.engine.smiles_to_inchi(
                smiles, return_dataclass=True
            )
        except Exception as e:
            from ..types import InvalidSmilesError

            raise InvalidSmilesError(str(e))

        if inchikey and structure_info.inchikey and inchikey != structure_info.inchikey:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                "Provided InChIKey does not match one computed from SMILES"
            )

        if not name and not (
            structure_info.molecular_formula
            and structure_info.molecular_formula.strip()
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError(
                "A 'name' is required when SMILES does not provide a molecular formula; please include 'name' in payload"
            )

        # Compute descriptors only when requested in payload (avoid doing it by default)
        compute_descriptors = bool(payload.get("compute_descriptors", False))
        properties_dict = {}
        if compute_descriptors:
            try:
                properties = providers.engine.calculate_properties(
                    smiles, return_dataclass=True
                )
                properties_dict = properties.to_dict()
            except Exception:
                properties_dict = {}

        metadata = dict(extra_metadata or {})
        if properties_dict:
            metadata.setdefault("descriptors", properties_dict)

        defaults = {
            "name": name or structure_info.molecular_formula or "",
            "smiles": smiles,
            "canonical_smiles": structure_info.canonical_smiles,
            "inchi": structure_info.inchi,
            "molecular_formula": structure_info.molecular_formula or "",
            "created_by": created_by,
            "metadata": metadata,
        }

        if structure_info.inchikey:
            mol, created = Molecule.objects.get_or_create(
                inchikey=structure_info.inchikey, defaults=defaults
            )
            if not created:
                if mol.created_by is None:
                    mol.created_by = created_by
                    mol.save(update_fields=["created_by", "updated_at"])
                else:
                    try:
                        collabs = list(mol.metadata.get("collaborators", []))
                    except Exception:
                        collabs = []
                    uid = getattr(created_by, "id", None)
                    if (
                        uid
                        and uid != getattr(mol.created_by, "id", None)
                        and uid not in collabs
                    ):
                        collabs.append(uid)
                        mol.metadata = dict(mol.metadata or {})
                        mol.metadata["collaborators"] = collabs
                        mol.save(update_fields=["metadata", "updated_at"])
            return mol, bool(created)

        mol = Molecule.objects.create(**defaults)
        return mol, True

    from django.core.exceptions import ValidationError

    raise ValidationError(
        "Payload must include at least 'smiles' or an existing 'inchikey'"
    )


def rehydrate_molecule_properties(molecule: Molecule) -> MolecularProperties:
    if molecule.metadata and "descriptors" in molecule.metadata:
        try:
            return MolecularProperties.from_dict(molecule.metadata["descriptors"])
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(
                f"Failed to rehydrate from metadata for molecule {molecule.id}: {e}"
            )

    properties = {}
    for prop in molecule.properties.all():
        try:
            properties[prop.property_type] = float(prop.value)
        except (ValueError, TypeError):
            logger.warning(
                f"Invalid property value for molecule {molecule.id}, property {prop.property_type}: {prop.value}"
            )
            continue

    return MolecularProperties.from_dict(properties)


def get_molecule_structure_info(molecule: Molecule) -> StructureIdentifiers:
    return StructureIdentifiers(
        inchi=molecule.inchi or "",
        inchikey=molecule.inchikey or "",
        canonical_smiles=molecule.canonical_smiles or molecule.smiles or "",
        molecular_formula=molecule.molecular_formula or None,
    )


def update_molecule(
    *, molecule: Molecule, payload: Dict[str, Any], user: Any, partial: bool = False
) -> tuple[Molecule, str]:
    if not user:
        raise ValueError("user is required")

    is_admin = getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)
    structural_fields = {"smiles", "inchi", "inchikey", "canonical_smiles"}

    attempted_structurals = structural_fields.intersection(set(payload.keys()))
    if attempted_structurals and not is_admin:
        from django.core.exceptions import ValidationError

        raise ValidationError(
            f"Updating structural identifiers ({', '.join(sorted(attempted_structurals))}) is forbidden for non-admin users"
        )

    if "inchikey" in payload and payload.get("inchikey"):
        provided = (payload.get("inchikey") or "").strip()
        if (
            provided
            and molecule.inchikey
            and provided != molecule.inchikey
            and not is_admin
        ):
            from django.core.exceptions import ValidationError

            raise ValidationError(
                "Provided InChIKey in payload does not match the resource's InChIKey; cannot update"
            )

    warning = ""
    changed_smiles = False
    for key, val in payload.items():
        if hasattr(molecule, key):
            if key in ("id", "created_by", "updated_by"):
                continue
            setattr(molecule, key, val)
            if key == "smiles":
                changed_smiles = True

    if is_admin and changed_smiles and (molecule.smiles or ""):
        try:
            structure_info = providers.engine.smiles_to_inchi(
                molecule.smiles, return_dataclass=True
            )
            molecule.inchi = structure_info.inchi or molecule.inchi
            molecule.inchikey = structure_info.inchikey or molecule.inchikey
            molecule.canonical_smiles = (
                structure_info.canonical_smiles or molecule.canonical_smiles
            )
            molecule.molecular_formula = (
                structure_info.molecular_formula or molecule.molecular_formula
            )
            try:
                props = providers.engine.calculate_properties(
                    molecule.smiles, return_dataclass=True
                )
                molecule.metadata = dict(molecule.metadata or {})
                molecule.metadata["descriptors"] = props.to_dict()
            except Exception:
                logger.warning(
                    "Failed to recompute descriptors for molecule %s", molecule.pk
                )
        except Exception as e:
            from django.core.exceptions import ValidationError

            raise ValidationError(
                f"Failed to recompute structure identifiers from SMILES: {e}"
            )

    molecule.updated_by = user
    molecule.save()

    if not is_admin:
        warning = (
            "Warning: updating molecules can corrupt structural data. "
            "Structural identifiers are protected; admins may perform structural changes."
        )

    return molecule, warning
