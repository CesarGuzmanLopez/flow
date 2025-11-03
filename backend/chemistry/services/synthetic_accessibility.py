"""Service for synthetic accessibility calculations.

Supports multiple providers:
- AMBIT-SA: Java-based, requires external JAR (high accuracy, reference implementation)
- RDKit: Pure Python, built-in (good approximation, fast)
- BR-SAScore: Bayesian model, machine learning-based (state-of-the-art accuracy)
"""

from typing import Dict, List, Literal, Union

from chemistry.providers.synthetic_accessibility.ambit import AmbitSAProvider
from chemistry.providers.synthetic_accessibility.brsascore import BRSAScoreProvider
from chemistry.providers.synthetic_accessibility.rdkit import RDKitSAProvider
from chemistry.type_definitions import SyntheticAccessibilityResultDict

ProviderType = Literal["ambit", "rdkit", "brsascore"]
SAProviderUnion = Union[AmbitSAProvider, RDKitSAProvider, BRSAScoreProvider]


class SyntheticAccessibilityService:
    """Service for calculating synthetic accessibility of molecules."""

    provider: SAProviderUnion
    provider_name: ProviderType

    def __init__(self, provider: ProviderType = "ambit"):
        """Initialize the service with the specified provider.

        Args:
            provider: Provider to use ("ambit", "rdkit", or "brsascore")
        """
        if provider == "ambit":
            self.provider = AmbitSAProvider()
        elif provider == "rdkit":
            self.provider = RDKitSAProvider()
        elif provider == "brsascore":
            self.provider = BRSAScoreProvider()
        else:
            raise ValueError(
                f"Unknown provider: {provider}. Use 'ambit', 'rdkit', or 'brsascore'."
            )
        self.provider_name = provider

    def calculate_for_molecule(
        self, smiles: str, include_details: bool = False
    ) -> SyntheticAccessibilityResultDict:
        """Calculate synthetic accessibility for a single molecule.

        Args:
            smiles: SMILES string of the molecule
            include_details: Whether to include detailed descriptor breakdown

        Returns:
            Dictionary with SA score and optional descriptors:
            {
                "smiles": str,
                "sa_score": float,  # 0-100, higher = easier to synthesize
                "descriptors": {  # only if include_details=True
                    "molecular_complexity": {"value": float, "score": float},
                    "stereochemical_complexity": {"value": float, "score": float},
                    "cyclomatic_number": {"value": float, "score": float},
                    "ring_complexity": {"value": float, "score": float}
                }
            }
        """
        result = self.provider.calculate_sa(smiles, verbose=include_details)
        return result.to_dict()

    def calculate_for_molecules(
        self, smiles_list: List[str], include_details: bool = False
    ) -> List[SyntheticAccessibilityResultDict]:
        """Calculate synthetic accessibility for multiple molecules.

        Args:
            smiles_list: List of SMILES strings
            include_details: Whether to include detailed descriptor breakdown

        Returns:
            List of dictionaries with SA scores
        """
        results = self.provider.calculate_sa_batch(smiles_list, verbose=include_details)
        return [r.to_dict() for r in results]

    def rank_by_synthetic_accessibility(
        self, smiles_list: List[str], reverse: bool = True
    ) -> List[SyntheticAccessibilityResultDict]:
        """Rank molecules by synthetic accessibility.

        Args:
            smiles_list: List of SMILES strings
            reverse: If True, rank from easiest to hardest to synthesize (default)

        Returns:
            List of dictionaries sorted by SA score
        """
        results = self.calculate_for_molecules(smiles_list)
        return sorted(
            results,
            key=lambda x: x["sa_score"] if x["sa_score"] > 0 else -1,
            reverse=reverse,
        )

    def filter_synthesizable(
        self, smiles_list: List[str], min_sa_score: float = 50.0
    ) -> List[str]:
        """Filter molecules by minimum synthetic accessibility threshold.

        Args:
            smiles_list: List of SMILES strings
            min_sa_score: Minimum SA score (default: 50.0)

        Returns:
            List of SMILES strings that meet the threshold
        """
        results = self.calculate_for_molecules(smiles_list)
        return [
            r["smiles"]
            for r in results
            if r["sa_score"] > 0 and r["sa_score"] >= min_sa_score
        ]


# Singleton instances per provider
_services: Dict[str, SyntheticAccessibilityService] = {}


def get_sa_service(provider: ProviderType = "ambit") -> SyntheticAccessibilityService:
    """Get or create a synthetic accessibility service instance for the given provider.

    Args:
        provider: Provider to use ("ambit", "rdkit", or "brsascore")

    Returns:
        SyntheticAccessibilityService instance
    """
    global _services
    if provider not in _services:
        _services[provider] = SyntheticAccessibilityService(provider=provider)
    return _services[provider]
