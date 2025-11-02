"""RDKit-based Synthetic Accessibility provider.

This provider uses RDKit's SAScore implementation to calculate synthetic accessibility
scores with a similar structure to the AMBIT-SA provider.

For descriptors that RDKit cannot calculate, NA (Not Available) values are returned.

Design goals:
- Same output structure as AMBIT-SA (SyntheticAccessibilityResult)
- Graceful handling of missing descriptors with None values
- Pure Python implementation (no external JARs)
"""

import warnings
from typing import List, Optional

from rdkit import Chem, RDLogger
from rdkit.Chem import Descriptors, GraphDescriptors

from chemistry.type_definitions import (
    DescriptorValue,
    InvalidSmilesError,
    SyntheticAccessibilityDescriptors,
    SyntheticAccessibilityResult,
    SyntheticAccessibilityResultDict,
)

# Suppress RDKit warnings for cleaner output
if hasattr(RDLogger, "DisableLog"):
    DisableLog = getattr(RDLogger, "DisableLog")
    DisableLog("rdApp.*")

# Try to import SAScore (may not be available in all RDKit distributions)
try:
    import os
    import sys

    from rdkit.Chem import RDConfig

    # SAScore is usually in Contrib/SA_Score
    sa_score_path = os.path.join(RDConfig.RDContribDir, "SA_Score")
    sys.path.append(sa_score_path)
    from sascorer import calculateScore as calc_sascore

    HAS_SASCORE = True
except ImportError:
    HAS_SASCORE = False
    warnings.warn(
        "RDKit SAScore not available. SA scores will be approximated. "
        "Install with: pip install rdkit-pypi"
    )


class RDKitSAProvider:
    """Provider for RDKit-based synthetic accessibility calculations."""

    def __init__(self):
        """Initialize the RDKit SA provider."""
        self.has_sascore = HAS_SASCORE

    def calculate_sa(
        self, smiles: str, verbose: bool = False
    ) -> SyntheticAccessibilityResult:
        """Calculate synthetic accessibility for a single SMILES.

        Args:
            smiles: SMILES string of the molecule
            verbose: If True, include detailed descriptor scores

        Returns:
            SyntheticAccessibilityResult with SA score and optional descriptors

        Raises:
            InvalidSmilesError: If SMILES cannot be parsed
        """
        clean_smiles = (smiles or "").strip()
        if not clean_smiles:
            raise InvalidSmilesError(smiles, "Empty SMILES string provided")

        # Parse SMILES
        mol = Chem.MolFromSmiles(clean_smiles)
        if mol is None:
            raise InvalidSmilesError(
                clean_smiles, f"Could not parse SMILES: {clean_smiles}"
            )

        # Calculate SA score
        sa_score = self._calculate_sa_score(mol)

        # Build descriptors if verbose
        descriptors = SyntheticAccessibilityDescriptors()
        if verbose:
            descriptors = self._calculate_descriptors(mol, sa_score)

        # Canonicalize SMILES for consistency
        canonical_smiles = Chem.MolToSmiles(mol)

        return SyntheticAccessibilityResult(
            smiles=canonical_smiles,
            sa_score=sa_score,
            descriptors=descriptors,
        )

    def calculate_sa_batch(
        self, smiles_list: List[str], verbose: bool = False
    ) -> List[SyntheticAccessibilityResult]:
        """Calculate synthetic accessibility for multiple SMILES.

        Args:
            smiles_list: List of SMILES strings
            verbose: If True, include detailed descriptor scores

        Returns:
            List of SyntheticAccessibilityResult objects
        """
        results: List[SyntheticAccessibilityResult] = []
        for smiles in smiles_list:
            try:
                result = self.calculate_sa(smiles, verbose=verbose)
                results.append(result)
            except Exception as e:
                # Log error but continue with other molecules
                warnings.warn(f"Failed to calculate SA for {smiles}: {e}")
        return results

    def _calculate_sa_score(self, mol: Chem.Mol) -> float:
        """Calculate SA score (0-100, higher = easier to synthesize).

        RDKit's SAScore ranges from 1 (easy) to 10 (hard).
        We convert it to 0-100 scale like AMBIT-SA (100 = easiest).

        Args:
            mol: RDKit molecule object

        Returns:
            SA score in 0-100 range
        """
        if self.has_sascore:
            # SAScore: 1 (easy) to 10 (hard)
            raw_score = calc_sascore(mol)
            # Convert: 1->100, 10->0
            # Formula: 100 - (raw_score - 1) * (100 / 9)
            sa_score = 100.0 - ((raw_score - 1.0) * (100.0 / 9.0))
        else:
            # Fallback approximation based on complexity descriptors
            sa_score = self._approximate_sa_score(mol)

        return max(0.0, min(100.0, sa_score))  # Clamp to [0, 100]

    def _approximate_sa_score(self, mol: Chem.Mol) -> float:
        """Approximate SA score when SAScore is not available.

        Uses a heuristic based on:
        - Molecular weight
        - Number of rings
        - Number of rotatable bonds
        - Number of heteroatoms
        - Number of chiral centers

        Returns:
            Approximate SA score (0-100)
        """
        # Start with a base score
        score = 100.0

        # Penalties for complexity factors
        mw = Descriptors.MolWt(mol)
        score -= min(30, (mw - 150) / 15)  # Penalty for high MW

        num_rings = mol.GetRingInfo().NumRings()
        score -= min(20, num_rings * 5)  # Penalty for multiple rings

        num_rot_bonds = Descriptors.NumRotatableBonds(mol)
        score -= min(15, num_rot_bonds * 2)  # Penalty for flexibility

        num_hetero = Descriptors.NumHeteroatoms(mol)
        score -= min(10, (num_hetero - 2) * 2)  # Penalty for heteroatoms

        # Chiral centers (stereo complexity)
        chiral_centers = Chem.FindMolChiralCenters(mol, includeUnassigned=True)
        score -= min(15, len(chiral_centers) * 5)  # Penalty for chirality

        return max(0.0, score)

    def _calculate_descriptors(
        self, mol: Chem.Mol, sa_score: float
    ) -> SyntheticAccessibilityDescriptors:
        """Calculate detailed descriptors for synthetic accessibility.

        Attempts to approximate AMBIT-SA descriptors using RDKit functions.
        Returns None for descriptors that cannot be reliably calculated.

        Args:
            mol: RDKit molecule object
            sa_score: Overall SA score

        Returns:
            SyntheticAccessibilityDescriptors with available values
        """
        # Molecular complexity - use BertzCT (complexity index)
        molecular_complexity = None
        try:
            bertz_ct = GraphDescriptors.BertzCT(mol)
            # Normalize to approximate AMBIT-SA range (typically 0-500)
            # Score inversely correlated with complexity
            complexity_score = max(0, 100 - (bertz_ct / 5))
            molecular_complexity = DescriptorValue(
                value=bertz_ct,
                score=complexity_score,
            )
        except Exception:
            pass  # Leave as None

        # Stereochemical complexity - number of chiral centers
        stereochemical_complexity = None
        try:
            chiral_centers = Chem.FindMolChiralCenters(mol, includeUnassigned=True)
            num_stereo = float(len(chiral_centers))
            # Score inversely correlated with stereo elements
            stereo_score = max(0, 100 - (num_stereo * 20))
            stereochemical_complexity = DescriptorValue(
                value=num_stereo,
                score=stereo_score,
            )
        except Exception:
            pass  # Leave as None

        # Cyclomatic number - graph complexity (rings + branches)
        cyclomatic_number = None
        try:
            # Approximate cyclomatic number from ring count
            num_rings = float(mol.GetRingInfo().NumRings())
            cyclo_value = num_rings
            # Score inversely correlated with ring count
            cyclo_score = max(0, 100 - (num_rings * 10))
            cyclomatic_number = DescriptorValue(
                value=cyclo_value,
                score=cyclo_score,
            )
        except Exception:
            pass  # Leave as None

        # Ring complexity - fused/bridged ring systems
        ring_complexity = None
        try:
            ring_info = mol.GetRingInfo()
            num_ring_systems = len(ring_info.AtomRings())

            # Calculate fusion factor (shared atoms between rings)
            fusion_factor = 0.0
            if num_ring_systems > 1:
                # Count atoms in multiple rings
                atom_ring_count = [0] * mol.GetNumAtoms()
                for ring in ring_info.AtomRings():
                    for atom_idx in ring:
                        atom_ring_count[atom_idx] += 1
                fusion_factor = sum(1 for c in atom_ring_count if c > 1) / max(
                    1, len(atom_ring_count)
                )

            ring_complexity_value = num_ring_systems * (1 + fusion_factor)
            # Score inversely correlated with complexity
            ring_complexity_score = max(0, 100 - (ring_complexity_value * 15))
            ring_complexity = DescriptorValue(
                value=ring_complexity_value,
                score=ring_complexity_score,
            )
        except Exception:
            pass  # Leave as None

        return SyntheticAccessibilityDescriptors(
            molecular_complexity=molecular_complexity,
            stereochemical_complexity=stereochemical_complexity,
            cyclomatic_number=cyclomatic_number,
            ring_complexity=ring_complexity,
        )


# Global instance
_provider: Optional[RDKitSAProvider] = None


def get_rdkit_sa_provider() -> RDKitSAProvider:
    """Get or create the global RDKit SA provider instance."""
    global _provider
    if _provider is None:
        _provider = RDKitSAProvider()
    return _provider


def calculate_synthetic_accessibility_rdkit(
    smiles: str, verbose: bool = False
) -> SyntheticAccessibilityResultDict:
    """Calculate synthetic accessibility using RDKit.

    Convenience function that uses the global provider instance.

    Args:
        smiles: SMILES string
        verbose: Include detailed descriptor scores

    Returns:
        Dictionary with SA score and optional descriptors

    Raises:
        InvalidSmilesError: If the SMILES string is invalid
    """
    provider = get_rdkit_sa_provider()
    result = provider.calculate_sa(smiles, verbose=verbose)
    return result.to_dict()
