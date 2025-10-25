"""
Strongly typed data structures for chemistry engine interfaces.

This module defines all the data types returned by chemistry engine methods
to ensure type safety and consistency across implementations.

This module is part of the chemistry package to promote better cohesion
and reduce coupling between components.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict

# ========== Type definitions for smiles_to_inchi method ==========


class StructureIdentifiersDict(TypedDict):
    """Structure identifiers returned by smiles_to_inchi method."""

    inchi: str
    inchikey: str
    canonical_smiles: str
    molecular_formula: Optional[str]  # Optional for backward compatibility


@dataclass(frozen=True)
class StructureIdentifiers:
    """Immutable structure identifiers for a molecule."""

    inchi: str
    inchikey: str
    canonical_smiles: str
    molecular_formula: Optional[str] = None

    def to_dict(self) -> StructureIdentifiersDict:
        """Convert to dictionary format."""
        result = {
            "inchi": self.inchi,
            "inchikey": self.inchikey,
            "canonical_smiles": self.canonical_smiles,
        }
        if self.molecular_formula is not None:
            result["molecular_formula"] = self.molecular_formula
        return result

    @classmethod
    def from_dict(cls, data: StructureIdentifiersDict) -> "StructureIdentifiers":
        """Create from dictionary."""
        return cls(
            inchi=data["inchi"],
            inchikey=data["inchikey"],
            canonical_smiles=data["canonical_smiles"],
            molecular_formula=data.get("molecular_formula"),
        )


# ========== Type definitions for calculate_properties method ==========


class MolecularPropertiesDict(TypedDict, total=False):
    """Molecular properties returned by calculate_properties method.

    All fields are optional to allow different engines to return different sets.
    """

    # Basic physicochemical properties
    MolWt: float
    LogP: float
    TPSA: float
    PSA: float  # Alternative name for TPSA
    HBA: float
    HBD: float
    RB: float
    MR: float
    AtX: float

    # ADMET properties
    LD50: float
    Mutagenicity: float
    DevelopmentalToxicity: float
    SyntheticAccessibility: float


@dataclass(frozen=True)
class MolecularProperties:
    """Immutable molecular properties for a molecule."""

    # Required basic properties
    mol_wt: Optional[float] = None
    log_p: Optional[float] = None
    tpsa: Optional[float] = None
    hba: Optional[float] = None
    hbd: Optional[float] = None
    rotatable_bonds: Optional[float] = None

    # Optional extended properties
    molar_refractivity: Optional[float] = None
    atom_count: Optional[float] = None

    # ADMET properties
    ld50: Optional[float] = None
    mutagenicity: Optional[float] = None
    developmental_toxicity: Optional[float] = None
    synthetic_accessibility: Optional[float] = None

    def to_dict(self) -> MolecularPropertiesDict:
        """Convert to dictionary format with standard keys."""
        result = {}

        if self.mol_wt is not None:
            result["MolWt"] = self.mol_wt
        if self.log_p is not None:
            result["LogP"] = self.log_p
        if self.tpsa is not None:
            result["TPSA"] = self.tpsa
            result["PSA"] = self.tpsa  # Alternative key
        if self.hba is not None:
            result["HBA"] = self.hba
        if self.hbd is not None:
            result["HBD"] = self.hbd
        if self.rotatable_bonds is not None:
            result["RB"] = self.rotatable_bonds
        if self.molar_refractivity is not None:
            result["MR"] = self.molar_refractivity
        if self.atom_count is not None:
            result["AtX"] = self.atom_count
        if self.ld50 is not None:
            result["LD50"] = self.ld50
        if self.mutagenicity is not None:
            result["Mutagenicity"] = self.mutagenicity
        if self.developmental_toxicity is not None:
            result["DevelopmentalToxicity"] = self.developmental_toxicity
        if self.synthetic_accessibility is not None:
            result["SyntheticAccessibility"] = self.synthetic_accessibility

        return result

    @classmethod
    def from_dict(cls, data: MolecularPropertiesDict) -> "MolecularProperties":
        """Create from dictionary with flexible key mapping."""
        return cls(
            mol_wt=data.get("MolWt"),
            log_p=data.get("LogP"),
            tpsa=data.get("TPSA") or data.get("PSA"),
            hba=data.get("HBA"),
            hbd=data.get("HBD"),
            rotatable_bonds=data.get("RB"),
            molar_refractivity=data.get("MR"),
            atom_count=data.get("AtX"),
            ld50=data.get("LD50"),
            mutagenicity=data.get("Mutagenicity"),
            developmental_toxicity=data.get("DevelopmentalToxicity"),
            synthetic_accessibility=data.get("SyntheticAccessibility"),
        )


# ========== Type definitions for generate_substitutions method ==========


@dataclass(frozen=True)
class SubstitutionResult:
    """Result from molecular substitution generation."""

    substitutions: List[str]
    original_smiles: str
    count_requested: int

    def __post_init__(self):
        """Validate the substitution result."""
        if not isinstance(self.substitutions, list):
            raise TypeError("substitutions must be a list")
        if not all(isinstance(s, str) for s in self.substitutions):
            raise TypeError("All substitutions must be strings")
        if len(self.substitutions) > self.count_requested:
            raise ValueError(
                f"Too many substitutions returned: {len(self.substitutions)} > {self.count_requested}"
            )

    def to_list(self) -> List[str]:
        """Convert to simple list format for backward compatibility."""
        return list(self.substitutions)


# ========== Exception types ==========


class ChemEngineError(Exception):
    """Base exception for chemistry engine errors."""

    pass


class InvalidSmilesError(ChemEngineError):
    """Raised when an invalid SMILES string is provided."""

    def __init__(self, smiles: str, message: Optional[str] = None):
        self.smiles = smiles
        if message is None:
            message = f"Invalid SMILES string: {smiles}"
        super().__init__(message)


class PropertyCalculationError(ChemEngineError):
    """Raised when property calculation fails."""

    def __init__(
        self,
        smiles: str,
        property_name: Optional[str] = None,
        message: Optional[str] = None,
    ):
        self.smiles = smiles
        self.property_name = property_name
        if message is None:
            if property_name:
                message = f"Failed to calculate property '{property_name}' for SMILES: {smiles}"
            else:
                message = f"Failed to calculate properties for SMILES: {smiles}"
        super().__init__(message)


class SubstitutionGenerationError(ChemEngineError):
    """Raised when substitution generation fails."""

    def __init__(self, smiles: str, count: int, message: Optional[str] = None):
        self.smiles = smiles
        self.count = count
        if message is None:
            message = f"Failed to generate {count} substitutions for SMILES: {smiles}"
        super().__init__(message)


# ========== Property Generation System Types ==========


class PropertyCategory(str, Enum):
    """Categories of molecular/family properties that can be generated.

    Each category represents a group of related properties that can be
    calculated using different providers.
    """

    ADMETSA = "admetsa"  # Basic ADMET properties (MolWt, LogP, TPSA, HBA, HBD, RB)
    ADMET = "admet"  # Extended ADMET properties
    PHYSICS = "physics"  # Physical properties
    PHARMACODYNAMIC = "pharmacodynamic"  # Pharmacodynamic properties
    CUSTOM = "custom"  # User-defined custom properties


class PropertyProvider(str, Enum):
    """Providers that can calculate molecular properties.

    Each provider represents a different source or method for calculating
    property values.
    """

    RDKIT = "rdkit"  # RDKit-based calculations
    MANUAL = "manual"  # User-provided values via JSON
    PROVIDER_EXTRA = (
        "provider-extra"  # Additional providers (random, external APIs, etc.)
    )


@dataclass
class PropertyGenerationRequest:
    """Request for property generation with metadata support.

    This dataclass represents a request to generate properties for molecules
    in a family, with support for both global and per-molecule metadata.

    Attributes:
        family_id: ID of the family to generate properties for
        category: Category of properties to generate (admetsa, physics, etc.)
        provider: Provider to use for calculations (rdkit, manual, etc.)
        persist: Whether to save properties to database (True) or just preview (False)
        metadata: Global metadata applied to all molecules
        per_molecule_metadata: Metadata specific to each molecule {mol_id: {key: value}}
        properties_data: Pre-calculated property values (required for manual provider)
        created_by: User initiating the generation

    Examples:
        # RDKit with global metadata
        PropertyGenerationRequest(
            family_id=5,
            category=PropertyCategory.ADMETSA,
            provider=PropertyProvider.RDKIT,
            metadata={"experiment_id": "EXP-001"}
        )

        # Manual with per-molecule metadata
        PropertyGenerationRequest(
            family_id=5,
            category=PropertyCategory.PHYSICS,
            provider=PropertyProvider.MANUAL,
            properties_data={
                8: {"MolWt": "180.16", "LogP": "2.45"},
                9: {"MolWt": "194.19", "LogP": "2.89"}
            },
            per_molecule_metadata={
                8: {"technician": "John"},
                9: {"technician": "Jane"}
            }
        )
    """

    family_id: int
    category: PropertyCategory
    provider: PropertyProvider
    persist: bool = True
    metadata: Optional[Dict[str, Any]] = None
    per_molecule_metadata: Optional[Dict[int, Dict[str, Any]]] = None
    properties_data: Optional[Dict[int, Dict[str, str]]] = None
    created_by: Optional[Any] = None

    def get_merged_metadata(self, molecule_id: int) -> Dict[str, Any]:
        """Get merged metadata for a specific molecule.

        Merges global metadata with per-molecule metadata, with per-molecule
        taking precedence in case of conflicts.

        Args:
            molecule_id: ID of the molecule

        Returns:
            Merged metadata dictionary
        """
        result = {}
        if self.metadata:
            result.update(self.metadata)
        if self.per_molecule_metadata and molecule_id in self.per_molecule_metadata:
            result.update(self.per_molecule_metadata[molecule_id])
        return result


@dataclass
class PropertyGenerationResult:
    """Result from property generation operation.

    Contains information about the generated properties and whether they
    were persisted to the database.

    Attributes:
        family_id: ID of the family
        category: Category of properties generated
        provider: Provider used for generation
        persisted: Whether properties were saved to database
        properties_created: Number of properties created (only if persisted)
        molecules: List of molecule results with their properties
    """

    family_id: int
    category: str
    provider: str
    persisted: bool
    molecules: List[Dict[str, Any]]
    properties_created: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        result = {
            "family_id": self.family_id,
            "category": self.category,
            "provider": self.provider,
            "persisted": self.persisted,
            "molecules": self.molecules,
        }
        if self.properties_created is not None:
            result["properties_created"] = self.properties_created
        return result
