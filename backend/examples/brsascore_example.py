"""Example usage of BR-SAScore provider.

This example demonstrates:
1. Basic SA calculation with BR-SAScore
2. Comparison between AMBIT-SA, RDKit, and BR-SAScore providers
3. Detailed contribution analysis
"""

import os
import sys


def example_basic_brsascore(get_brsascore_provider):
    """Example 1: Basic calculation with BR-SAScore provider."""
    print("=" * 60)
    print("Example 1: Basic BR-SAScore Calculation")
    print("=" * 60)

    provider = get_brsascore_provider()

    # Simple molecule
    smiles = "CCO"  # Ethanol
    result = provider.calculate_sa(smiles, verbose=False)

    print(f"SMILES: {result.smiles}")
    print(f"SA Score: {result.sa_score:.2f}")
    print()


def example_with_contribution(get_brsascore_provider):
    """Example 2: Calculation with contribution analysis."""
    print("=" * 60)
    print("Example 2: BR-SAScore with Contribution Analysis")
    print("=" * 60)

    provider = get_brsascore_provider()

    # Example from paper - Aspirin
    smiles = "CC(OC1=CC=CC=C1C(O)=O)=O"
    result = provider.calculate_sa(smiles, verbose=True)

    print(f"SMILES: {result.smiles}")
    print(f"SA Score: {result.sa_score:.2f}\n")

    print("Descriptors:")
    descriptors_dict = result.descriptors.to_dict()
    if descriptors_dict:
        for name, desc in descriptors_dict.items():
            print(f"  {name}:")
            print(f"    value: {desc['value']:.3f}")
            score = desc.get("score")
            if score is not None:
                print(f"    score: {score:.3f}")
            else:
                print("    score: NA (not available)")
    else:
        print("  No descriptors available (verbose mode provides limited info)")
    print()


def example_three_way_comparison(get_sa_service):
    """Example 3: Compare AMBIT-SA vs RDKit vs BR-SAScore."""
    print("=" * 60)
    print("Example 3: Three-Way Provider Comparison")
    print("=" * 60)

    test_molecules = [
        ("CCO", "Ethanol"),
        ("CC(OC1=CC=CC=C1C(O)=O)=O", "Aspirin"),
        ("CC(C)CC1=CC=C(C=C1)C(C)C(O)=O", "Ibuprofen"),
        ("c1ccccc1", "Benzene"),
        ("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "Caffeine"),
    ]

    print(f"{'Molecule':<15} {'AMBIT-SA':<10} {'RDKit':<10} {'BR-SAScore':<12}")
    print("-" * 60)

    for smiles, name in test_molecules:
        scores = {}

        # AMBIT-SA
        try:
            ambit_service = get_sa_service(provider="ambit")
            ambit_result = ambit_service.calculate_for_molecule(smiles)
            scores["ambit"] = ambit_result["sa_score"]
        except Exception:
            scores["ambit"] = None

        # RDKit
        try:
            rdkit_service = get_sa_service(provider="rdkit")
            rdkit_result = rdkit_service.calculate_for_molecule(smiles)
            scores["rdkit"] = rdkit_result["sa_score"]
        except Exception:
            scores["rdkit"] = None

        # BR-SAScore
        try:
            brsascore_service = get_sa_service(provider="brsascore")
            brsascore_result = brsascore_service.calculate_for_molecule(smiles)
            scores["brsascore"] = brsascore_result["sa_score"]
        except Exception:
            scores["brsascore"] = None

        # Print results
        ambit_str = f"{scores['ambit']:.2f}" if scores["ambit"] else "ERROR"
        rdkit_str = f"{scores['rdkit']:.2f}" if scores["rdkit"] else "ERROR"
        brsascore_str = f"{scores['brsascore']:.2f}" if scores["brsascore"] else "ERROR"

        print(f"{name:<15} {ambit_str:<10} {rdkit_str:<10} {brsascore_str:<12}")

    print()


def example_batch_processing(get_sa_service):
    """Example 4: Batch processing with BR-SAScore."""
    print("=" * 60)
    print("Example 4: Batch Processing with BR-SAScore")
    print("=" * 60)

    service = get_sa_service(provider="brsascore")

    smiles_list = [
        "CCO",  # Ethanol
        "CC(=O)O",  # Acetic acid
        "c1ccccc1",  # Benzene
        "CC(OC1=CC=CC=C1C(O)=O)=O",  # Aspirin
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
    ]

    results = service.calculate_for_molecules(smiles_list, include_details=False)

    print(f"{'SMILES':<40} {'SA Score':<10}")
    print("-" * 60)
    for result in results:
        print(f"{result['smiles']:<40} {result['sa_score']:<10.2f}")
    print()


def example_ranking_brsascore(get_sa_service):
    """Example 5: Rank molecules by BR-SAScore."""
    print("=" * 60)
    print("Example 5: Ranking by SA Score (BR-SAScore)")
    print("=" * 60)

    service = get_sa_service(provider="brsascore")

    smiles_list = [
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine (complex)
        "CC(OC1=CC=CC=C1C(O)=O)=O",  # Aspirin (medium)
        "CCO",  # Ethanol (simple)
        "c1ccccc1",  # Benzene (simple)
        "CC(=O)O",  # Acetic acid (simple)
    ]

    ranked = service.rank_by_synthetic_accessibility(smiles_list)

    print("Molecules ranked from easiest to hardest to synthesize:\n")
    for i, result in enumerate(ranked, 1):
        print(f"{i}. SA Score: {result['sa_score']:.2f}")
        print(f"   SMILES: {result['smiles']}")
        print()


def example_na_descriptors(get_brsascore_provider):
    """Example 6: Show NA (None) descriptors."""
    print("=" * 60)
    print("Example 6: NA Descriptors in BR-SAScore")
    print("=" * 60)

    provider = get_brsascore_provider()

    smiles = "c1ccccc1CCON"
    result = provider.calculate_sa(smiles, verbose=True)

    print(f"SMILES: {result.smiles}")
    print(f"SA Score: {result.sa_score:.2f}\n")

    print("Descriptor Availability:")
    print(
        f"  Molecular Complexity: {'Available' if result.descriptors.molecular_complexity else 'NA'}"
    )
    print(
        f"  Stereochemical Complexity: {'Available' if result.descriptors.stereochemical_complexity else 'NA'}"
    )
    print(
        f"  Cyclomatic Number: {'Available' if result.descriptors.cyclomatic_number else 'NA (not in BR-SAScore)'}"
    )
    print(
        f"  Ring Complexity: {'Available' if result.descriptors.ring_complexity else 'NA (not in BR-SAScore)'}"
    )
    print()


def main():
    """Run all examples."""
    # Setup Django inside main to avoid module-level imports
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

    from chemistry.providers.brsascore_sa import get_brsascore_provider
    from chemistry.services.synthetic_accessibility import get_sa_service

    print("\n🧪 BR-SAScore Provider Examples")
    print(
        "Paper: https://jcheminf.biomedcentral.com/articles/10.1186/s13321-023-00678-z\n"
    )

    try:
        example_basic_brsascore(get_brsascore_provider)
        example_with_contribution(get_brsascore_provider)
        example_three_way_comparison(get_sa_service)
        example_batch_processing(get_sa_service)
        example_ranking_brsascore(get_sa_service)
        example_na_descriptors(get_brsascore_provider)
    except ImportError as e:
        print(f"⚠️  Error: {e}")
        print("\nPlease install BR-SAScore:")
        print("  pip install BRSAScore")


if __name__ == "__main__":
    main()
