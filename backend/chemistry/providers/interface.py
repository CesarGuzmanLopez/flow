"""
Strongly typed interface for chemistry engines.

This module defines the contract that all chemistry engine implementations must follow,
with precise type annotations and detailed documentation for each method.
"""

from typing import Protocol, Union, overload

from ..types import (
    MolecularProperties,
    MolecularPropertiesDict,
    StructureIdentifiers,
    StructureIdentifiersDict,
    SubstitutionResult,
)


class ChemEngineInterface(Protocol):
    """
    Protocol defining the interface for chemistry computation engines.

    All chemistry engines must implement these methods with the specified
    type signatures to ensure consistency across different backends.
    """

    @overload
    def smiles_to_inchi(
        self, smiles: str, *, return_dataclass: bool = True
    ) -> StructureIdentifiers:
        """Return structure identifiers as a dataclass (default)."""
        ...

    @overload
    def smiles_to_inchi(
        self, smiles: str, *, return_dataclass: bool = False
    ) -> StructureIdentifiersDict:
        """Return structure identifiers as a dictionary."""
        ...

    def smiles_to_inchi(
        self, smiles: str, *, return_dataclass: bool = True
    ) -> Union[StructureIdentifiers, StructureIdentifiersDict]:
        """
        Convert a SMILES string to structure identifiers.

        Args:
            smiles: Valid SMILES string representing the molecule
            return_dataclass: If True, return StructureIdentifiers dataclass,
                            if False, return StructureIdentifiersDict

        Returns:
            Structure identifiers containing:
            - inchi: InChI string
            - inchikey: InChI key
            - canonical_smiles: Canonical SMILES representation
            - molecular_formula: Molecular formula (optional)

        Raises:
            InvalidSmilesError: If the SMILES string is invalid or cannot be parsed
        """
        ...

    @overload
    def calculate_properties(
        self, smiles: str, *, return_dataclass: bool = True
    ) -> MolecularProperties:
        """Return molecular properties as a dataclass (default)."""
        ...

    @overload
    def calculate_properties(
        self, smiles: str, *, return_dataclass: bool = False
    ) -> MolecularPropertiesDict:
        """Return molecular properties as a dictionary."""
        ...

    def calculate_properties(
        self, smiles: str, *, return_dataclass: bool = True
    ) -> Union[MolecularProperties, MolecularPropertiesDict]:
        """
        Calculate molecular properties for a given SMILES string.

        Args:
            smiles: Valid SMILES string representing the molecule
            return_dataclass: If True, return MolecularProperties dataclass,
                            if False, return MolecularPropertiesDict

        Returns:
            Molecular properties including:
            - Basic physicochemical properties (MolWt, LogP, TPSA, HBA, HBD, RB)
            - Extended properties (MR, AtX) - optional
            - ADMET properties (LD50, Mutagenicity, etc.) - optional

        Raises:
            InvalidSmilesError: If the SMILES string is invalid
            PropertyCalculationError: If property calculation fails
        """
        ...

    @overload
    def generate_substitutions(
        self, smiles: str, count: int = 3, *, return_dataclass: bool = True
    ) -> SubstitutionResult:
        """Return substitutions as a dataclass (default)."""
        ...

    @overload
    def generate_substitutions(
        self, smiles: str, count: int = 3, *, return_dataclass: bool = False
    ) -> list[str]:
        """Return substitutions as a list."""
        ...

    def generate_substitutions(
        self, smiles: str, count: int = 3, *, return_dataclass: bool = True
    ) -> Union[SubstitutionResult, list[str]]:
        """
        Generate molecular substitutions/variants for a given SMILES string.

        Args:
            smiles: Valid SMILES string representing the base molecule
            count: Maximum number of substitutions to generate (default: 3)
            return_dataclass: If True, return SubstitutionResult dataclass,
                            if False, return list[str]

        Returns:
            Either SubstitutionResult containing substitutions and metadata,
            or a simple list of SMILES strings representing molecular variants

        Raises:
            InvalidSmilesError: If the SMILES string is invalid
            SubstitutionGenerationError: If substitution generation fails
            ValueError: If count is negative or zero
        """
        ...
