#!/usr/bin/env python
"""Test script to demonstrate NA (None) handling in BR-SAScore provider.

Shows when descriptors are available vs. NA (Not Available).
"""

import os
import sys
from pathlib import Path


def setup_django() -> None:
    """Setup Django environment."""
    backend_dir = Path(__file__).parent.parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
    import django

    django.setup()


def test_na_values() -> None:
    """Test NA value handling."""
    from chemistry.services.synthetic_accessibility import get_sa_service

    print("=" * 80)
    print("Testing NA (Not Available) Values in BR-SAScore Provider")
    print("=" * 80)

    service = get_sa_service(provider="brsascore")

    test_molecules = [
        ("CCO", "Ethanol (simple, no rings, no stereo)"),
        ("c1ccccc1", "Benzene (simple ring, no stereo)"),
        ("C[C@H](O)C(=O)O", "Lactic acid (has stereo center)"),
        ("C1CCC2=C(C1)C=CC=C2", "Tetralin (fused rings)"),
    ]

    for smiles, name in test_molecules:
        print(f"\n{name}")
        print(f"SMILES: {smiles}")
        print("-" * 80)

        # Calculate with details
        result = service.calculate_for_molecule(smiles, include_details=True)

        print(f"SA Score: {result['sa_score']:.2f}")

        if result.get("descriptors"):
            descriptors = result["descriptors"]
            print("\nDescriptors:")

            # Check each descriptor
            desc_names = [
                ("molecular_complexity", "Molecular Complexity"),
                ("stereochemical_complexity", "Stereochemical Complexity"),
                ("cyclomatic_number", "Cyclomatic Number"),
                ("ring_complexity", "Ring Complexity"),
            ]

            for key, display_name in desc_names:
                desc = descriptors.get(key)
                if desc and desc.get("value") is not None:
                    value = desc["value"]
                    score = desc["score"]
                    if score is not None and score > 0:
                        status = f"✓ value={value:.2f}, score={score:.2f}"
                    else:
                        status = (
                            f"✓ value={value:.2f} (no score - calculated from RDKit)"
                        )
                else:
                    status = "✗ NA (Not Available)"

                print(f"  {display_name:<30} {status}")
        else:
            print("  No descriptors available (use include_details=True)")

    print("\n" + "=" * 80)
    print("Legend:")
    print("  ✓ = Descriptor calculated successfully")
    print("  ✗ NA = Not Available (calculation failed or not supported)")
    print("  (no score) = Value calculated but no contribution score from BR-SAScore")
    print("=" * 80)


def main() -> None:
    """Run NA value tests."""
    setup_django()

    try:
        test_na_values()
        print("\n✅ Test completed successfully!\n")
    except ImportError as e:
        print(f"\n❌ Import Error: {e}")
        print("\nBR-SAScore not installed. Install with:")
        print("  pip install setuptools>=65.0")
        print("  pip install BRSAScore --no-deps")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
