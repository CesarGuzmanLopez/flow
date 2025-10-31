"""Example usage of RDKit SA provider.

This example demonstrates:
1. Basic SA calculation with RDKit
2. Comparison between AMBIT-SA and RDKit providers
3. Batch processing with detailed descriptors
"""

import os
import sys


def example_basic_rdkit(get_rdkit_sa_provider):
    """Example 1: Basic calculation with RDKit provider."""
    print("=" * 60)
    print("Example 1: Basic RDKit SA Calculation")
    print("=" * 60)

    provider = get_rdkit_sa_provider()

    # Simple molecule
    smiles = "CCO"  # Ethanol
    result = provider.calculate_sa(smiles, verbose=False)

    print(f"SMILES: {result.smiles}")
    print(f"SA Score: {result.sa_score:.2f}")
    print()


def example_with_descriptors(get_rdkit_sa_provider):
    """Example 2: Calculation with detailed descriptors."""
    print("=" * 60)
    print("Example 2: RDKit with Descriptors")
    print("=" * 60)

    provider = get_rdkit_sa_provider()

    smiles = "c1ccccc1CCON"  # Phenethylamine derivative
    result = provider.calculate_sa(smiles, verbose=True)

    print(f"SMILES: {result.smiles}")
    print(f"SA Score: {result.sa_score:.2f}\n")

    print("Descriptors:")
    descriptors_dict = result.descriptors.to_dict()
    for name, desc in descriptors_dict.items():
        print(f"  {name}:")
        print(f"    value: {desc['value']:.3f}")
        print(f"    score: {desc['score']:.3f}")
    print()


def example_provider_comparison(get_sa_service):
    """Example 3: Compare AMBIT-SA vs RDKit."""
    print("=" * 60)
    print("Example 3: Provider Comparison (AMBIT-SA vs RDKit)")
    print("=" * 60)

    test_molecules = [
        ("CCO", "Ethanol"),
        ("CC(C)CC1=CC=C(C=C1)C(C)C(O)=O", "Ibuprofen"),
        ("c1ccccc1", "Benzene"),
        ("C1CCCCC1", "Cyclohexane"),
    ]

    print(f"{'Molecule':<20} {'AMBIT-SA':<12} {'RDKit':<12} {'Diff':<8}")
    print("-" * 60)

    for smiles, name in test_molecules:
        try:
            # AMBIT-SA
            ambit_service = get_sa_service(provider="ambit")
            ambit_result = ambit_service.calculate_for_molecule(smiles)
            ambit_score = ambit_result["sa_score"]
        except Exception:
            ambit_score = None
            print(f"{name:<20} {'ERROR':<12}", end=" ")

        try:
            # RDKit
            rdkit_service = get_sa_service(provider="rdkit")
            rdkit_result = rdkit_service.calculate_for_molecule(smiles)
            rdkit_score = rdkit_result["sa_score"]
        except Exception:
            rdkit_score = None
            print(f"{'ERROR':<12}", end=" ")

        if ambit_score is not None and rdkit_score is not None:
            diff = abs(ambit_score - rdkit_score)
            print(f"{name:<20} {ambit_score:<12.2f} {rdkit_score:<12.2f} {diff:<8.2f}")
        else:
            print()

    print()


def example_batch_processing(get_sa_service):
    """Example 4: Batch processing with RDKit."""
    print("=" * 60)
    print("Example 4: Batch Processing with RDKit")
    print("=" * 60)

    service = get_sa_service(provider="rdkit")

    smiles_list = [
        "CCO",  # Ethanol
        "CC(=O)O",  # Acetic acid
        "c1ccccc1",  # Benzene
        "CC(C)CC1=CC=C(C=C1)C(C)C(O)=O",  # Ibuprofen
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine
    ]

    results = service.calculate_for_molecules(smiles_list, include_details=False)

    print(f"{'SMILES':<40} {'SA Score':<10}")
    print("-" * 60)
    for result in results:
        print(f"{result['smiles']:<40} {result['sa_score']:<10.2f}")
    print()


def example_ranking(get_sa_service):
    """Example 5: Rank molecules by synthetic accessibility."""
    print("=" * 60)
    print("Example 5: Ranking by SA Score (RDKit)")
    print("=" * 60)

    service = get_sa_service(provider="rdkit")

    smiles_list = [
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",  # Caffeine (complex)
        "CC(C)CC1=CC=C(C=C1)C(C)C(O)=O",  # Ibuprofen (medium)
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


def example_filtering(get_sa_service):
    """Example 6: Filter synthesizable molecules."""
    print("=" * 60)
    print("Example 6: Filter by SA Threshold (RDKit)")
    print("=" * 60)

    service = get_sa_service(provider="rdkit")

    smiles_list = [
        "CCO",
        "CC(=O)O",
        "c1ccccc1",
        "CC(C)CC1=CC=C(C=C1)C(C)C(O)=O",
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    ]

    threshold = 70.0
    easy_to_synthesize = service.filter_synthesizable(
        smiles_list, min_sa_score=threshold
    )

    print(f"Molecules with SA score >= {threshold}:\n")
    for smiles in easy_to_synthesize:
        print(f"  {smiles}")
    print()


def main():
    """Run all examples."""
    # Setup Django inside main to avoid module-level imports
    import django

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

    from chemistry.providers.rdkit_sa import get_rdkit_sa_provider
    from chemistry.services.synthetic_accessibility import get_sa_service

    example_basic_rdkit(get_rdkit_sa_provider)
    example_with_descriptors(get_rdkit_sa_provider)
    example_provider_comparison(get_sa_service)
    example_batch_processing(get_sa_service)
    example_ranking(get_sa_service)
    example_filtering(get_sa_service)


if __name__ == "__main__":
    main()
