#!/usr/bin/env python
"""Unified comparison of all 3 Synthetic Accessibility providers.

This example compares:
- AMBIT-SA: Java-based reference implementation
- RDKit: Pure Python approximation
- BR-SAScore: Bayesian machine learning model

Shows SA scores and descriptor availability across providers.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional


def setup_django():
    """Setup Django environment."""
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
    import django

    django.setup()


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80)


def compare_basic_scores():
    """Compare basic SA scores across all 3 providers."""
    from chemistry.services.synthetic_accessibility import get_sa_service

    print_section("Basic SA Score Comparison")

    test_molecules = [
        ("CCO", "Ethanol"),
        ("CC(=O)O", "Acetic acid"),
        ("c1ccccc1", "Benzene"),
        ("CC(C)CC1=CC=C(C=C1)C(C)C(O)=O", "Ibuprofen"),
        ("CC(OC1=CC=CC=C1C(O)=O)=O", "Aspirin"),
        ("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "Caffeine"),
        ("CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C", "Testosterone"),
    ]

    # Table header
    print(
        f"\n{'Molecule':<20} {'SMILES':<40} {'AMBIT-SA':<12} {'RDKit':<12} {'BR-SAScore':<12}"
    )
    print("-" * 100)

    for smiles, name in test_molecules:
        # values can be numeric scores or error strings
        scores: Dict[str, float | str] = {}

        # AMBIT-SA
        try:
            service_ambit = get_sa_service(provider="ambit")
            result = service_ambit.calculate_for_molecule(smiles)
            scores["ambit"] = result["sa_score"]
        except Exception as e:
            scores["ambit"] = f"Error: {str(e)[:20]}"

        # RDKit
        try:
            service_rdkit = get_sa_service(provider="rdkit")
            result = service_rdkit.calculate_for_molecule(smiles)
            scores["rdkit"] = result["sa_score"]
        except Exception as e:
            scores["rdkit"] = f"Error: {str(e)[:20]}"

        # BR-SAScore
        try:
            service_brsascore = get_sa_service(provider="brsascore")
            result = service_brsascore.calculate_for_molecule(smiles)
            scores["brsascore"] = result["sa_score"]
        except Exception as e:
            scores["brsascore"] = f"Error: {str(e)[:20]}"

        # Format output
        ambit_str = (
            f"{scores['ambit']:.2f}"
            if isinstance(scores["ambit"], (int, float))
            else scores["ambit"]
        )
        rdkit_str = (
            f"{scores['rdkit']:.2f}"
            if isinstance(scores["rdkit"], (int, float))
            else scores["rdkit"]
        )
        brsascore_str = (
            f"{scores['brsascore']:.2f}"
            if isinstance(scores["brsascore"], (int, float))
            else scores["brsascore"]
        )

        smiles_display = smiles[:37] + "..." if len(smiles) > 40 else smiles
        print(
            f"{name:<20} {smiles_display:<40} {ambit_str:<12} {rdkit_str:<12} {brsascore_str:<12}"
        )

    print()


def compare_descriptors():
    """Compare descriptor availability across providers."""
    from chemistry.services.synthetic_accessibility import ProviderType, get_sa_service
    from chemistry.type_definitions import SyntheticAccessibilityResultDict

    print_section("Descriptor Availability Comparison")

    # Test with a complex molecule
    smiles = "CC(OC1=CC=CC=C1C(O)=O)=O"  # Aspirin
    molecule_name = "Aspirin"

    print(f"\nMolecule: {molecule_name}")
    print(f"SMILES: {smiles}\n")

    providers: List[ProviderType] = ["ambit", "rdkit", "brsascore"]
    provider_names = {
        "ambit": "AMBIT-SA",
        "rdkit": "RDKit",
        "brsascore": "BR-SAScore",
    }

    descriptor_names = [
        "molecular_complexity",
        "stereochemical_complexity",
        "cyclomatic_number",
        "ring_complexity",
    ]

    # Collect all results
    all_results: Dict[ProviderType, Optional[SyntheticAccessibilityResultDict]] = {}
    for provider in providers:
        try:
            service = get_sa_service(provider=provider)
            result = service.calculate_for_molecule(smiles, include_details=True)
            all_results[provider] = result
        except Exception as e:
            print(f"❌ {provider_names[provider]} Error: {e}")
            all_results[provider] = None

    # Print SA scores
    print("SA Scores:")
    print("-" * 80)
    for provider in providers:
        if all_results[provider]:
            res = all_results[provider]
            assert res is not None
            sa_score = res["sa_score"]
            print(f"  {provider_names[provider]:<15} {sa_score:.2f}")
        else:
            print(f"  {provider_names[provider]:<15} N/A")

    # Print descriptor comparison table
    print("\nDescriptor Comparison:")
    print("-" * 80)
    print(f"{'Descriptor':<30} {'AMBIT-SA':<20} {'RDKit':<20} {'BR-SAScore':<20}")
    print("-" * 80)

    for desc_name in descriptor_names:
        row = [desc_name.replace("_", " ").title()]

        for provider in providers:
            provider_result: Optional[SyntheticAccessibilityResultDict] = all_results[
                provider
            ]
            if (
                provider_result
                and isinstance(provider_result, dict)
                and isinstance(provider_result.get("descriptors"), dict)
            ):
                descriptors_dict = provider_result["descriptors"]
                desc = descriptors_dict.get(desc_name)
                if desc and isinstance(desc, dict) and desc.get("value") is not None:
                    value: float = float(desc["value"])
                    score_val = desc.get("score")
                    score: Optional[float] = (
                        float(score_val) if score_val is not None else None
                    )
                    if score is not None and score > 0:
                        cell = f"v:{value:.1f} s:{score:.1f}"
                    elif score is not None:
                        cell = f"v:{value:.1f} s:{score:.1f}"
                    else:
                        cell = f"v:{value:.1f} (NA)"
                else:
                    cell = "N/A"
            else:
                cell = "N/A"
            row.append(cell)

        print(f"{row[0]:<30} {row[1]:<20} {row[2]:<20} {row[3]:<20}")

    print("\nLegend:")
    print("  v: = descriptor value")
    print("  s: = contribution score to SA (0-100)")
    print(
        "  (no score) = value calculated but no contribution score available from provider"
    )
    print("  N/A = descriptor not available (calculation failed or not supported)")
    print()
    print("Note: BR-SAScore calculates cyclomatic_number and ring_complexity values")
    print("      but doesn't provide contribution scores (shown as 'no score')")
    print()


def compare_complex_molecules():
    """Compare SA scores for complex molecules across providers."""
    from chemistry.services.synthetic_accessibility import ProviderType, get_sa_service

    print_section("Complex Molecules Comparison")

    complex_molecules = [
        (
            "FC(F)(F)c1cc(ccc1)N5CCN(CCc2nnc3[C@H]4CCC[C@H]4Cn23)CC5",
            "Complex drug-like molecule",
        ),
        ("CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C", "Testosterone (steroid)"),
        ("CC(=O)OC1=CC=CC=C1C(=O)O", "Aspirin"),
        ("CCCCCCCCCCCCCCCCCC", "Octadecane (long chain)"),
        ("C1CCC2=C(C1)C=CC=C2", "Tetralin (fused rings)"),
    ]

    print(f"\n{'Molecule':<30} {'AMBIT':<12} {'RDKit':<12} {'BR-SA':<12} {'Δ Max':<10}")
    print("-" * 80)

    for smiles, name in complex_molecules:
        scores: List[Optional[float]] = []

        providers2: List[ProviderType] = ["ambit", "rdkit", "brsascore"]
        for provider in providers2:
            try:
                # provider literals match ProviderType
                service = get_sa_service(provider=provider)
                result = service.calculate_for_molecule(smiles)
                scores.append(result["sa_score"])
            except Exception:
                scores.append(None)

        # Calculate max difference
        valid_scores = [s for s in scores if s is not None]
        if len(valid_scores) >= 2:
            max_diff = max(valid_scores) - min(valid_scores)
        else:
            max_diff = None

        # Format output
        ambit_str = f"{scores[0]:.2f}" if scores[0] is not None else "N/A"
        rdkit_str = f"{scores[1]:.2f}" if scores[1] is not None else "N/A"
        brsascore_str = f"{scores[2]:.2f}" if scores[2] is not None else "N/A"
        diff_str = f"{max_diff:.2f}" if max_diff is not None else "N/A"

        print(
            f"{name:<30} {ambit_str:<12} {rdkit_str:<12} {brsascore_str:<12} {diff_str:<10}"
        )

    print("\nΔ Max = Maximum difference between providers for that molecule")
    print()


def compare_ranking():
    """Compare ranking of molecules across providers."""
    from chemistry.services.synthetic_accessibility import ProviderType, get_sa_service

    print_section("Ranking Comparison (Easiest to Hardest)")

    test_molecules = [
        ("CCO", "Ethanol"),
        ("c1ccccc1", "Benzene"),
        ("CC(=O)O", "Acetic acid"),
        ("CC(OC1=CC=CC=C1C(O)=O)=O", "Aspirin"),
        ("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "Caffeine"),
    ]

    smiles_list = [s for s, _ in test_molecules]
    name_dict = {s: n for s, n in test_molecules}

    providers: List[ProviderType] = ["ambit", "rdkit", "brsascore"]
    provider_names = {
        "ambit": "AMBIT-SA",
        "rdkit": "RDKit",
        "brsascore": "BR-SAScore",
    }

    rankings = {}
    for provider in providers:
        try:
            service = get_sa_service(provider=provider)
            ranked = service.rank_by_synthetic_accessibility(smiles_list)
            rankings[provider] = [(r["smiles"], r["sa_score"]) for r in ranked]
        except Exception as e:
            print(f"❌ {provider_names[provider]} Error: {e}")
            rankings[provider] = []

    # Print side-by-side rankings
    print()
    max_len = max(len(rankings.get(p, [])) for p in providers)

    # Header
    for provider in providers:
        print(f"{provider_names[provider]:^35}", end=" | ")
    print()
    print("-" * 110)

    # Rows
    for i in range(max_len):
        for provider in providers:
            if i < len(rankings.get(provider, [])):
                smiles, score = rankings[provider][i]
                name = name_dict.get(smiles, smiles[:20])
                cell = f"{i + 1}. {name:<20} ({score:.1f})"
            else:
                cell = ""
            print(f"{cell:<35}", end=" | ")
        print()

    print()


def main():
    """Run all comparison examples."""
    setup_django()

    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + "Synthetic Accessibility Provider Comparison".center(78) + "║")
    print("║" + "AMBIT-SA vs RDKit vs BR-SAScore".center(78) + "║")
    print("╚" + "═" * 78 + "╝")

    try:
        compare_basic_scores()
        compare_descriptors()
        compare_complex_molecules()
        compare_ranking()

        print_section("Summary")
        print("""
Provider Characteristics:

1. AMBIT-SA (Java-based)
   ✓ Reference implementation with all 4 descriptors with scores
   ✓ High accuracy with contribution scores
   ✗ Requires external Java 8 + JAR file
   
2. RDKit (Pure Python)
   ✓ Fast, no external dependencies
   ✓ Approximates all 4 descriptors with scores
   ✓ Good correlation with AMBIT-SA
   ✗ Slightly less accurate than specialized models
   
3. BR-SAScore (Bayesian ML)
   ✓ State-of-the-art accuracy (ML-based)
   ✓ Provides molecular_complexity with score (from BR-SAScore model)
   ✓ Calculates stereochemical_complexity with score (from RDKit)
   ✓ Calculates cyclomatic_number value (from RDKit, no score)
   ✓ Calculates ring_complexity value (from RDKit, no score)
   ⚠ Some descriptors may be NA if calculation fails
   ✗ Requires BRSAScore package installation
   
NA (Not Available) Handling:
- All providers return NA (None) for descriptors that cannot be calculated
- Check for None/null values before using descriptor data
- BR-SAScore: cyclomatic_number and ring_complexity have score=0.0 (no contribution score)
   
Recommendation:
- Development/Testing: Use RDKit (fast, no dependencies)
- Production (high accuracy): Use BR-SAScore (best ML model)
- Maximum detail: Use AMBIT-SA (all descriptors with contribution scores)
        """)

        print("\n" + "=" * 80)
        print("✅ Comparison completed successfully!")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Error during comparison: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
