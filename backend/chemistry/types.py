"""
Strongly typed data structures for chemistry engine interfaces.

This module defines all the data types returned by chemistry engine methods
to ensure type safety and consistency across implementations.

This module is part of the chemistry package to promote better cohesion
and reduce coupling between components.
"""

from dataclasses import dataclass
from typing import List, Optional

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
