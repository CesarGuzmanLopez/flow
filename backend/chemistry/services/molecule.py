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
) -> Molecule:
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

            properties: MolecularProperties = providers.engine.calculate_properties(
                smiles.strip(), return_dataclass=True
            )

            properties_dict = properties.to_dict()

            metadata = {"descriptors": properties_dict}
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
