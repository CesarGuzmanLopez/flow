#!/usr/bin/env python
"""Example script demonstrating AMBIT-SA usage.

This script shows how to use the AMBIT-SA provider to calculate
synthetic accessibility scores for molecules.

Usage:
    python examples/ambit_sa_example.py
"""

import os
import sys
from pathlib import Path


def main():
    """Run AMBIT-SA examples."""
    # Add backend to sys.path (project root/backend)
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    # Setup Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
    import django

    django.setup()

    # Import service after Django is configured
    from chemistry.services.synthetic_accessibility import get_sa_service

    print("=" * 60)
    print("AMBIT-SA Synthetic Accessibility Examples")
    print("=" * 60)

    service = get_sa_service()

    # Example 1: Single molecule calculation
    print("\n1. Single molecule (simple):")
    smiles1 = "CCO"  # Ethanol
    result1 = service.calculate_for_molecule(smiles1)
    print(f"   SMILES: {result1['smiles']}")
    print(f"   SA Score: {result1['sa_score']:.2f}")

    # Example 2: Single molecule with details
    print("\n2. Single molecule (with details):")
    smiles2 = "FC(F)(F)c1cc(ccc1)N5CCN(CCc2nnc3[C@H]4CCC[C@H]4Cn23)CC5"
    result2 = service.calculate_for_molecule(smiles2, include_details=True)
    print(f"   SMILES: {result2['smiles'][:50]}...")
    print(f"   SA Score: {result2['sa_score']:.2f}")
    if result2.get("descriptors"):
        descriptors = result2["descriptors"]
        print("   Descriptors:")
        if "molecular_complexity" in descriptors:
            mc = descriptors["molecular_complexity"]
            print(
                f"     - Molecular complexity: value={mc['value']:.2f}, "
                f"score={mc['score']:.2f}"
            )
        if "stereochemical_complexity" in descriptors:
            sc = descriptors["stereochemical_complexity"]
            print(
                f"     - Stereochemical complexity: value={sc['value']:.2f}, "
                f"score={sc['score']:.2f}"
            )
        if "cyclomatic_number" in descriptors:
            cn = descriptors["cyclomatic_number"]
            print(
                f"     - Cyclomatic number: value={cn['value']:.2f}, "
                f"score={cn['score']:.2f}"
            )
        if "ring_complexity" in descriptors:
            rc = descriptors["ring_complexity"]
            print(
                f"     - Ring complexity: value={rc['value']:.2f}, "
                f"score={rc['score']:.2f}"
            )

    # Example 3: Batch calculation
    print("\n3. Batch calculation:")
    smiles_list = [
        "CCO",  # Ethanol - very easy
        "CC(C)Cc1ccc(cc1)C(C)C(O)=O",  # Ibuprofen - moderate
        "CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C",  # Testosterone - complex
    ]
    results = service.calculate_for_molecules(smiles_list)
    for i, res in enumerate(results, 1):
        print(f"   {i}. SA Score: {res['sa_score']:.2f} - {res['smiles'][:40]}...")

    # Example 4: Ranking by synthetic accessibility
    print("\n4. Ranking by synthetic accessibility (easiest first):")
    ranked = service.rank_by_synthetic_accessibility(smiles_list)
    for i, res in enumerate(ranked, 1):
        print(f"   {i}. SA Score: {res['sa_score']:.2f} - {res['smiles'][:40]}...")

    # Example 5: Filter by threshold
    print("\n5. Filter molecules with SA >= 70:")
    filtered = service.filter_synthesizable(smiles_list, min_sa_score=70.0)
    print(f"   Found {len(filtered)} molecule(s):")
    for smiles in filtered:
        print(f"   - {smiles}")

    print("\n" + "=" * 60)
    print("Examples completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
