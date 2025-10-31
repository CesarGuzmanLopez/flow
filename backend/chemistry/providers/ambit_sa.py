"""AMBIT-SA (Synthetic Accessibility) provider.

This provider executes the AMBIT SyntheticAccessibilityCli.jar tool to calculate
synthetic accessibility scores for molecules.

The tool outputs a score from 0 to 100 where 100 is maximal synthetic accessibility
(easiest to synthesize).

Design goals:
- Strongly typed results using chemistry.types structures
- Robust parsing supporting both comma and dot decimal separators
- Clear error mapping to domain exceptions (InvalidSmilesError)
"""

import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings

from chemistry.types import (
    DescriptorValue,
    InvalidSmilesError,
    SyntheticAccessibilityDescriptors,
    SyntheticAccessibilityResult,
)

# Backward-compatibility note: Previously this module exposed AmbitSAResult.
# Now we use SyntheticAccessibilityResult from chemistry.types for stronger typing.


class AmbitSAProvider:
    """Provider for AMBIT-SA synthetic accessibility calculations."""

    def __init__(
        self,
        java_path: Optional[str] = None,
        jar_path: Optional[str] = None,
    ):
        """Initialize the AMBIT-SA provider.

        Args:
            java_path: Path to Java 8 executable. If None, uses settings or auto-detect.
            jar_path: Path to SyntheticAccessibilityCli.jar. If None, uses settings or auto-detect.
        """
        self.java_path = java_path or self._get_java_path()
        self.jar_path = jar_path or self._get_jar_path()
        self._validate_setup()

    def _get_java_path(self) -> str:
        """Get Java 8 path from settings or project structure."""
        # Try settings first
        if hasattr(settings, "AMBIT_JAVA_PATH"):
            return settings.AMBIT_JAVA_PATH

        # Try project portable Java 8
        project_root = Path(__file__).parent.parent.parent.parent
        portable_java = project_root / "tools" / "java" / "jre8" / "bin" / "java"
        if portable_java.exists():
            return str(portable_java)

        # Fallback to system java
        return "java"

    def _get_jar_path(self) -> str:
        """Get AMBIT-SA jar path from settings or project structure."""
        # Try settings first
        if hasattr(settings, "AMBIT_JAR_PATH"):
            return settings.AMBIT_JAR_PATH

        # Try project structure
        project_root = Path(__file__).parent.parent.parent.parent
        jar_path = (
            project_root
            / "tools"
            / "external"
            / "ambitSA"
            / "SyntheticAccessibilityCli.jar"
        )
        if jar_path.exists():
            return str(jar_path)

        raise FileNotFoundError(
            "AMBIT-SA jar not found. Run scripts/download_external_tools.sh"
        )

    def _validate_setup(self) -> None:
        """Validate that Java and the jar file are accessible."""
        # Check jar exists
        if not Path(self.jar_path).exists():
            raise FileNotFoundError(
                f"AMBIT-SA jar not found at {self.jar_path}. "
                "Run scripts/download_external_tools.sh"
            )

        # Check Java is executable
        try:
            result = subprocess.run(
                [self.java_path, "-version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Java executable failed: {result.stderr}")
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            raise RuntimeError(
                f"Java not found or not executable at {self.java_path}. "
                "Run scripts/download_java_runtimes.sh"
            ) from e

    def calculate_sa(
        self, smiles: str, verbose: bool = False
    ) -> SyntheticAccessibilityResult:
        """Calculate synthetic accessibility for a single SMILES.

        Args:
            smiles: SMILES string of the molecule
            verbose: If True, include detailed descriptor scores

        Returns:
            AmbitSAResult with SA score and optional details

        Raises:
            subprocess.SubprocessError: If the calculation fails
            ValueError: If the output cannot be parsed
        """
        clean_smiles = (smiles or "").strip()
        if not clean_smiles:
            raise InvalidSmilesError(smiles, "Empty SMILES string provided")

        cmd = [self.java_path, "-jar", self.jar_path, "-s", clean_smiles]
        if verbose:
            cmd.append("-v")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            # Map known parse errors to domain exception
            combined = (e.stdout or "") + "\n" + (e.stderr or "")
            if "could not parse" in combined.lower():
                raise InvalidSmilesError(clean_smiles, combined.strip()) from e
            raise RuntimeError(
                f"AMBIT-SA calculation failed: {e.stderr or e.stdout}"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("AMBIT-SA calculation timed out") from e

        # Parse using both stdout and stderr (tool may mix outputs)
        combined_out = (result.stdout or "") + "\n" + (result.stderr or "")
        return self._parse_output(combined_out, clean_smiles, verbose)

    def calculate_sa_batch(
        self, smiles_list: List[str], verbose: bool = False
    ) -> List[SyntheticAccessibilityResult]:
        """Calculate synthetic accessibility for multiple SMILES.

        Args:
            smiles_list: List of SMILES strings
            verbose: If True, include detailed descriptor scores

        Returns:
            List of AmbitSAResult objects
        """
        results: List[SyntheticAccessibilityResult] = []
        for smiles in smiles_list:
            try:
                result = self.calculate_sa(smiles, verbose=verbose)
                results.append(result)
            except Exception as e:
                # Log error but continue with other molecules
                print(f"Failed to calculate SA for {smiles}: {e}")
                # Maintain order but skip invalid entries (or push sentinel)
        return results

    def calculate_sa_from_file(
        self, input_file: str, verbose: bool = False
    ) -> List[SyntheticAccessibilityResult]:
        """Calculate synthetic accessibility from a file with SMILES.

        Args:
            input_file: Path to file with SMILES (one per line or .smi format)
            verbose: If True, include detailed descriptor scores

        Returns:
            List of AmbitSAResult objects

        Raises:
            FileNotFoundError: If input file doesn't exist
            subprocess.SubprocessError: If the calculation fails
        """
        if not Path(input_file).exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        cmd = [self.java_path, "-jar", self.jar_path, "-i", input_file]
        if verbose:
            cmd.append("-v")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for batch
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"AMBIT-SA batch calculation failed: {e.stderr or e.stdout}"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError("AMBIT-SA batch calculation timed out") from e

        combined_out = (result.stdout or "") + "\n" + (result.stderr or "")
        return self._parse_batch_output(combined_out, verbose)

    def _normalize_number(self, value: str) -> float:
        """Normalize number format (handle both comma and dot as decimal separator).

        Args:
            value: String representation of a number (e.g., "99,467" or "99.467")

        Returns:
            Float value
        """
        return float(value.replace(",", "."))

    def _parse_output(
        self, output: str, smiles: str, verbose: bool
    ) -> SyntheticAccessibilityResult:
        """Parse AMBIT-SA output for single molecule."""
        # Look for SA score line: "SA = 54.116" or "SA = 54,116" (handles both formats)
        sa_match = re.search(r"SA\s*=\s*([\d,\.]+)", output)
        if not sa_match:
            raise ValueError(f"Could not parse SA score from output: {output}")

        sa_score = self._normalize_number(sa_match.group(1))
        descriptors = SyntheticAccessibilityDescriptors()

        if verbose:
            # Parse detailed output - build descriptor objects
            # MOL_COMPLEXITY_01  88.751  score = 40.833
            mol_complexity_match = re.search(
                r"MOL_COMPLEXITY_01\s+([\d,\.]+)\s+score\s*=\s*([\d,\.]+)", output
            )
            molecular_complexity = None
            if mol_complexity_match:
                molecular_complexity = DescriptorValue(
                    value=self._normalize_number(mol_complexity_match.group(1)),
                    score=self._normalize_number(mol_complexity_match.group(2)),
                )

            # WEIGHTED_NUMBER_OF_STEREO_ELEMENTS  2.000  score = 40.000
            stereo_match = re.search(
                r"WEIGHTED_NUMBER_OF_STEREO_ELEMENTS\s+([\d,\.]+)\s+score\s*=\s*([\d,\.]+)",
                output,
            )
            stereochemical_complexity = None
            if stereo_match:
                stereochemical_complexity = DescriptorValue(
                    value=self._normalize_number(stereo_match.group(1)),
                    score=self._normalize_number(stereo_match.group(2)),
                )

            # CYCLOMATIC_NUMBER  5.000  score = 50.000
            cyclo_match = re.search(
                r"CYCLOMATIC_NUMBER\s+([\d,\.]+)\s+score\s*=\s*([\d,\.]+)", output
            )
            cyclomatic_number = None
            if cyclo_match:
                cyclomatic_number = DescriptorValue(
                    value=self._normalize_number(cyclo_match.group(1)),
                    score=self._normalize_number(cyclo_match.group(2)),
                )

            # RING_COMPLEXITY  1.174  score = 82.609
            ring_match = re.search(
                r"RING_COMPLEXITY\s+([\d,\.]+)\s+score\s*=\s*([\d,\.]+)", output
            )
            ring_complexity = None
            if ring_match:
                ring_complexity = DescriptorValue(
                    value=self._normalize_number(ring_match.group(1)),
                    score=self._normalize_number(ring_match.group(2)),
                )

            descriptors = SyntheticAccessibilityDescriptors(
                molecular_complexity=molecular_complexity,
                stereochemical_complexity=stereochemical_complexity,
                cyclomatic_number=cyclomatic_number,
                ring_complexity=ring_complexity,
            )

        return SyntheticAccessibilityResult(
            smiles=smiles, sa_score=sa_score, descriptors=descriptors
        )

    def _parse_batch_output(
        self, output: str, verbose: bool
    ) -> List[SyntheticAccessibilityResult]:
        """Parse AMBIT-SA batch output."""
        results = []
        lines = output.strip().split("\n")

        # Skip header and parse data lines
        for line in lines:
            # Skip headers and empty lines
            if (
                not line.strip()
                or line.startswith("#")
                or line.startswith("Calculating")
                or line.startswith("Reading")
            ):
                continue

            # Parse tab-separated values: #  smiles  NumAtoms  SA
            parts = line.split("\t")
            if len(parts) >= 4:
                try:
                    smiles = parts[1].strip()
                    sa_score = self._normalize_number(parts[3].strip())
                    results.append(
                        SyntheticAccessibilityResult(smiles=smiles, sa_score=sa_score)
                    )
                except (ValueError, IndexError):
                    continue

        return results


# Global instance
_provider: Optional[AmbitSAProvider] = None


def get_ambit_provider() -> AmbitSAProvider:
    """Get or create the global AMBIT-SA provider instance."""
    global _provider
    if _provider is None:
        _provider = AmbitSAProvider()
    return _provider


def calculate_synthetic_accessibility(
    smiles: str, verbose: bool = False
) -> Dict[str, Any]:
    """Calculate synthetic accessibility for a SMILES string.

    Convenience function that uses the global provider instance.

    Args:
        smiles: SMILES string
        verbose: Include detailed descriptor scores

    Returns:
        Dictionary with SA score and optional details
    """
    provider = get_ambit_provider()
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
