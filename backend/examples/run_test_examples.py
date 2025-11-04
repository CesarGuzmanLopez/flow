#!/usr/bin/env python3
"""Example: call the WebTEST provider (real tool) and print results.

This example uses the chemistry providers registry to obtain the 'webtest'
provider, which wraps the local runner under `tools/external/test/run_test.py`.
It prints a compact table of results for LD50 (mg/kg), Mutagenicity, DevTox,
and Density. LD50 is reported as the predicted value in mg/kg (not log), and
all raw details are preserved in metadata under `raw_data` if you need them.
"""

import os
import sys
from typing import List

SMILES = [
    "CCO",
    "NNCNO",
    "CCCNNCNO",
    "c1ccccc1NNCNO",
    "smilefalso",
    "CCNc1ccOccc1",
    # exametilciclohexano
    "C1(C(C(C(C(C1C)C)C)C)C)C",
    # ibuprofeno
    "CC(C)CC1=CC=C(C=C1)C(C)C(O)=O",
    # cafeina
    "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
    # aspirina
    "CC(OC1=CC=CC=C1C(O)=O)=O",
    # fluorouracilo
    "C1=CN(C(=O)NC1=O)C(F)(F)F",
]
def print_provider_results(smiles_list: List[str]) -> None:
    print("=" * 80)
    print("WebTEST provider outputs (LD50 mg/kg, Mutagenicity, DevTox, Density)")
    print("=" * 80)

    from chemistry.providers.factory import auto_register_providers, registry

    auto_register_providers()
    provider = registry.get_provider("webtest")

    # Header
    print(
        f"{'SMILES':<24} {'LD50(mg/kg)':>12} {'Mutag':>8} {'DevTox':>8} {'Density':>8}"
    )
    print("-" * 80)

    for s in smiles_list:
        try:
            tox = provider.calculate_properties(s, "toxicology")
            phys = provider.calculate_properties(s, "physics")
        except FileNotFoundError as e:
            print("Runner not available:", e)
            return

        ld50 = tox.get("LD50", {}).get("value")
        muta = tox.get("Mutagenicity", {}).get("value")
        dev = tox.get("DevTox", {}).get("value")
        dens = phys.get("Density", {}).get("value")

        def fmt(v):
            return (
                f"{v:.2f}"
                if isinstance(v, (int, float))
                else (v if v is not None else "NA")
            )

        smile_cell = s[:21] + ("…" if len(s) > 24 else "")
        print(
            f"{smile_cell:<24} {fmt(ld50):>12} {fmt(muta):>8} {fmt(dev):>8} {fmt(dens):>8}"
        )


def main() -> None:
    # Ensure project path is importable
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Call provider and print results (first 10 to keep output short)
    print_provider_results(SMILES[:10])


if __name__ == "__main__":
    main()
