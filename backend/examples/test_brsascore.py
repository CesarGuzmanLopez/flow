"""Quick test for BR-SAScore provider.

Tests basic functionality of the BR-SAScore integration.
"""

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()


print("Testing BR-SAScore Provider")
print("=" * 60)

try:
    from chemistry.providers.brsascore_sa import get_brsascore_provider

    provider = get_brsascore_provider()

    # Test with Aspirin (example from paper)
    smiles = "CC(OC1=CC=CC=C1C(O)=O)=O"
    print("\nTest molecule: Aspirin")
    print(f"SMILES: {smiles}")

    # Basic calculation
    result = provider.calculate_sa(smiles, verbose=False)
    print(f"SA Score: {result.sa_score:.2f}")

    # With contribution
    result_v = provider.calculate_sa(smiles, verbose=True)
    print("\nWith descriptors:")
    descriptors = result_v.descriptors.to_dict()
    print(f"  Available descriptors: {len(descriptors)}")
    for name, desc in descriptors.items():
        if isinstance(desc, dict):
            value = desc.get("value")
            score = desc.get("score")
            if score is not None and value is not None:
                print(f"  {name}: value={value:.2f}, score={score:.2f}")
            elif value is not None:
                print(f"  {name}: value={value:.2f}, score=NA")
        else:
            print(f"  {name}: {desc}")

    # Test simple molecules
    print("\n" + "=" * 60)
    print("Testing multiple molecules:\n")

    test_molecules = [
        ("CCO", "Ethanol"),
        ("c1ccccc1", "Benzene"),
        ("CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "Caffeine"),
    ]

    for smi, name in test_molecules:
        result = provider.calculate_sa(smi, verbose=False)
        print(f"{name:20} SA: {result.sa_score:.2f}")

    print("\n" + "=" * 60)
    print("✅ BR-SAScore Provider working correctly!")

except ImportError as e:
    print(f"\n❌ Error: {e}")
    print("\nBR-SAScore not installed. Install with:")
    print("  pip install BRSAScore")
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback

    traceback.print_exc()
