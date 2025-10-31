"""BR-SAScore (Bayesian Retrosynthesis SAScore) provider.

This provider uses the BR-SAScore library to calculate synthetic accessibility scores.
BR-SAScore is a Bayesian approach that provides more accurate predictions than traditional SAScore.

Paper: https://jcheminf.biomedcentral.com/articles/10.1186/s13321-023-00678-z
GitHub: https://github.com/jcheminform/BR-SAScore

Design goals:
- Same output structure as AMBIT-SA (SyntheticAccessibilityResult)
- Pure Python implementation
- Contribution scores for interpretability
- NA (None) for unavailable descriptors
"""

import warnings
from typing import Any, Dict, List, Optional

from rdkit import Chem, RDLogger

from chemistry.types import (
    DescriptorValue,
    InvalidSmilesError,
    SyntheticAccessibilityDescriptors,
    SyntheticAccessibilityResult,
)

# Suppress RDKit warnings for cleaner output
RDLogger.DisableLog("rdApp.*")

# Try to import BR-SAScore
try:
    # Suppress pkg_resources deprecation warning from BRSAScore
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore", category=UserWarning, message=".*pkg_resources.*"
        )
        from BRSAScore import SAScorer as BRSAScorer

    HAS_BRSASCORE = True
except ImportError:
    HAS_BRSASCORE = False
    warnings.warn("BR-SAScore not available. Install with: pip install BRSAScore")


class BRSAScoreProvider:
    """Provider for BR-SAScore synthetic accessibility calculations."""

    def __init__(self):
        """Initialize the BR-SAScore provider."""
        if not HAS_BRSASCORE:
            raise ImportError(
                "BR-SAScore not installed. Install with: pip install BRSAScore"
            )

        # Initialize the scorer (loads pre-trained model)
        self.scorer = BRSAScorer()
        self.has_brsascore = True

    def calculate_sa(
        self, smiles: str, verbose: bool = False
    ) -> SyntheticAccessibilityResult:
        """Calculate synthetic accessibility for a single SMILES.

        Args:
            smiles: SMILES string of the molecule
            verbose: If True, include detailed descriptor scores (contribution analysis)

        Returns:
            SyntheticAccessibilityResult with SA score and optional descriptors

        Raises:
            InvalidSmilesError: If SMILES cannot be parsed
        """
        clean_smiles = (smiles or "").strip()
        if not clean_smiles:
            raise InvalidSmilesError(smiles, "Empty SMILES string provided")

        # Parse SMILES first to validate
        mol = Chem.MolFromSmiles(clean_smiles)
        if mol is None:
            raise InvalidSmilesError(
                clean_smiles, f"Could not parse SMILES: {clean_smiles}"
            )

        # Calculate SA score using BR-SAScore
        try:
            score, contribution = self.scorer.calculateScore(clean_smiles)
        except Exception as e:
            raise InvalidSmilesError(
                clean_smiles, f"BR-SAScore calculation failed: {str(e)}"
            ) from e

        # BR-SAScore returns score in 1-10 range (1=easy, 10=hard)
        # Convert to 0-100 scale like AMBIT-SA (100=easy, 0=hard)
        sa_score = self._convert_score(score)

        # Build descriptors if verbose
        descriptors = SyntheticAccessibilityDescriptors()
        if verbose and contribution is not None:
            descriptors = self._build_descriptors_from_contribution(
                mol, contribution, sa_score
            )

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

    def _convert_score(self, raw_score: float) -> float:
        """Convert BR-SAScore (1-10) to AMBIT-SA scale (0-100).

        BR-SAScore: 1 (easy to synthesize) to 10 (hard to synthesize)
        AMBIT-SA: 100 (easy to synthesize) to 0 (hard to synthesize)

        Args:
            raw_score: BR-SAScore in 1-10 range

        Returns:
            SA score in 0-100 range
        """
        # Formula: 100 - (raw_score - 1) * (100 / 9)
        sa_score = 100.0 - ((raw_score - 1.0) * (100.0 / 9.0))
        return max(0.0, min(100.0, sa_score))  # Clamp to [0, 100]

    def _build_descriptors_from_contribution(
        self, mol: Chem.Mol, contribution: Any, sa_score: float
    ) -> SyntheticAccessibilityDescriptors:
        """Build descriptors from BR-SAScore contribution analysis.

        BR-SAScore provides contribution scores for different structural features.
        We calculate what we can from RDKit and set unavailable values to None (NA).

        Descriptor Availability:
        - molecular_complexity: From BR-SAScore contribution (if available), otherwise NA
        - stereochemical_complexity: Calculated from RDKit (chiral centers)
        - cyclomatic_number: Calculated from RDKit (value only, score=None/NA)
        - ring_complexity: Calculated from RDKit (value only, score=None/NA)

        Note: If calculation fails for any descriptor, it will be None (NA).
              Descriptors calculated from RDKit have score=None (no contribution score).

        Args:
            mol: RDKit molecule object
            contribution: Contribution dictionary from BR-SAScore
            sa_score: Overall SA score

        Returns:
            SyntheticAccessibilityDescriptors with calculated values (NA if unavailable)
        """
        # Note: BR-SAScore contribution format may vary
        # We'll extract what we can and set the rest to None (NA)

        # Try to extract basic molecular complexity from contribution
        molecular_complexity = None
        try:
            # If contribution is a dictionary with complexity info
            if isinstance(contribution, dict):
                complexity_value = contribution.get("complexity", None)
                if complexity_value is not None:
                    # Normalize to approximate AMBIT-SA range
                    complexity_score = max(0, 100 - (float(complexity_value) * 10))
                    molecular_complexity = DescriptorValue(
                        value=float(complexity_value),
                        score=complexity_score,
                    )
        except Exception:
            pass  # Leave as None

        # Stereochemical complexity - calculate from molecule
        stereochemical_complexity = None
        try:
            chiral_centers = Chem.FindMolChiralCenters(mol, includeUnassigned=True)
            num_stereo = float(len(chiral_centers))
            # Always calculate if we have stereo centers
            stereo_score = max(0, 100 - (num_stereo * 20))
            stereochemical_complexity = DescriptorValue(
                value=num_stereo,
                score=stereo_score,
            )
        except Exception:
            pass  # Leave as None

        # Cyclomatic number - calculate from RDKit but without score
        # (BR-SAScore doesn't provide a contribution score for this)
        cyclomatic_number = None
        try:
            # Cyclomatic complexity = number of bonds - number of atoms + number of rings
            num_bonds = mol.GetNumBonds()
            num_atoms = mol.GetNumAtoms()
            ring_info = mol.GetRingInfo()
            num_rings = ring_info.NumRings()

            if num_atoms > 0:
                cyclo_value = float(num_bonds - num_atoms + num_rings)
                # No score available from BR-SAScore, set to None
                cyclomatic_number = DescriptorValue(
                    value=cyclo_value,
                    score=None,  # No contribution score available
                )
        except Exception:
            pass  # Leave as None

        # Ring complexity - calculate from RDKit but without score
        ring_complexity = None
        try:
            ring_info = mol.GetRingInfo()
            num_rings = ring_info.NumRings()

            if num_rings > 0:
                # Count fused rings (rings sharing bonds)
                atom_rings = ring_info.AtomRings()
                ring_complexity_value = 0.0

                # Simple heuristic: complexity based on ring sizes and fusion
                for ring in atom_rings:
                    ring_size = len(ring)
                    # Larger rings and non-6-membered rings add complexity
                    size_factor = abs(ring_size - 6) * 0.5
                    ring_complexity_value += 1.0 + size_factor

                # Check for fused rings
                fused_count = 0
                for i, ring1 in enumerate(atom_rings):
                    j = i + 1
                    for ring2 in atom_rings[j:]:
                        if set(ring1) & set(ring2):  # Shared atoms
                            fused_count += 1

                ring_complexity_value += fused_count

                # No score available from BR-SAScore, set to None
                ring_complexity = DescriptorValue(
                    value=ring_complexity_value,
                    score=None,  # No contribution score available
                )
        except Exception:
            pass  # Leave as None

        return SyntheticAccessibilityDescriptors(
            molecular_complexity=molecular_complexity,  # From BR-SAScore contribution (if available)
            stereochemical_complexity=stereochemical_complexity,  # Calculated from RDKit
            cyclomatic_number=cyclomatic_number,  # Calculated from RDKit (value only, score=None)
            ring_complexity=ring_complexity,  # Calculated from RDKit (value only, score=None)
        )


# Global instance
_provider: Optional[BRSAScoreProvider] = None


def get_brsascore_provider() -> BRSAScoreProvider:
    """Get or create the global BR-SAScore provider instance."""
    global _provider
    if _provider is None:
        _provider = BRSAScoreProvider()
    return _provider


def calculate_synthetic_accessibility_brsascore(
    smiles: str, verbose: bool = False
) -> Dict[str, Any]:
    """Calculate synthetic accessibility using BR-SAScore.

    Convenience function that uses the global provider instance.

    Args:
        smiles: SMILES string
        verbose: Include detailed descriptor scores

    Returns:
        Dictionary with SA score and optional descriptors
    """
    provider = get_brsascore_provider()
    try:
        result = provider.calculate_sa(smiles, verbose=verbose)
        return result.to_dict()
    except InvalidSmilesError as e:
        # Structured error response for clients
        return {
            "smiles": smiles,
            "error": "invalid_smiles",
            "message": str(e),
        }
