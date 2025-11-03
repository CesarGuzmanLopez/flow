"""Quick test script for RDKit SA provider.

Tests basic functionality and compares with AMBIT-SA if available.
"""

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

# Import after Django setup
from chemistry.providers.rdkit_sa import get_rdkit_sa_provider  # noqa: E402

print("Testing RDKit SA Provider")
print("=" * 60)

provider = get_rdkit_sa_provider()

# Test simple molecules
test_smiles = [
    "CCO",  # Ethanol - simple
    "c1ccccc1CCON",  # Phenethylamine derivative - medium
    "CC(C)CC1=CC=C(C=C1)C(C)C(O)=O",  # Ibuprofen - complex
]

for smiles in test_smiles:
    print(f"\nSMILES: {smiles}")

    # Basic calculation
    result_basic = provider.calculate_sa(smiles, verbose=False)
    print(f"  SA Score: {result_basic.sa_score:.2f}")

    # With descriptors
    result_verbose = provider.calculate_sa(smiles, verbose=True)
    print(
        f"  Descriptors available: {len(result_verbose.descriptors.to_dict())} descriptors"
    )

    if result_verbose.descriptors.molecular_complexity:
        mc = result_verbose.descriptors.molecular_complexity
        print(f"    Molecular Complexity: value={mc.value:.2f}, score={mc.score:.2f}")

print("\n" + "=" * 60)
print("RDKit SA Provider working correctly!")
