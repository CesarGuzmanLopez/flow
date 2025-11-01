#!/usr/bin/env python
"""Quick test for AMBIT-SA parser with comma decimal separator."""

import os
import sys
from pathlib import Path


def main() -> None:
    # Add backend to path
    backend_dir = Path(__file__).parent
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    # Setup Django
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
    import django

    django.setup()

    # Import provider after Django setup
    from chemistry.providers.ambit_sa import get_ambit_provider

    print("Testing AMBIT-SA provider...")
    provider = get_ambit_provider()

    # Test cases from output examples
    test_cases = [
        ("CCO", "Ethanol"),
        ("c1ccccc1CCON", "Phenylethanol with amine"),
    ]

    for smiles, name in test_cases:
        print(f"\n{name} ({smiles}):")
        try:
            result = provider.calculate_sa(smiles, verbose=False)
            print(f"  SA Score: {result.sa_score:.3f}")

            result_v = provider.calculate_sa(smiles, verbose=True)
            print(f"  SA Score (verbose): {result_v.sa_score:.3f}")
            desc = result_v.descriptors
            if desc.molecular_complexity is not None:
                print(
                    f"  Molecular Complexity: value={desc.molecular_complexity.value:.3f}, "
                    f"score={desc.molecular_complexity.score:.3f}"
                )
            if desc.cyclomatic_number is not None:
                print(
                    f"  Cyclomatic Number: value={desc.cyclomatic_number.value:.3f}, "
                    f"score={desc.cyclomatic_number.score:.3f}"
                )
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n✅ Test completed!")


if __name__ == "__main__":
    main()
