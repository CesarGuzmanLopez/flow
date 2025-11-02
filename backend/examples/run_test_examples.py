#!/usr/bin/env python3
"""Example: use the registered `toxicology` property provider and print results.

This example follows the style of other `backend/examples/*` scripts: it sets up
the Django environment, imports the provider from the registry, computes the
requested endpoints for a small set of SMILES and prints values together with
their units so you can verify the unit labels used by the provider.

This script does not call the external Java-based T.E.S.T. runner and does not
write temporary files; it uses the in-process `ToxicologyProvider` added to the
providers registry.
"""

import os
import sys

SMILES = [
    "CCO",
    "NNCNO",
    "CCCNNCNO",
    "c1ccccc1NNCNO",
    "smilefalso",
    "CCNc1ccOccc1",
]


def print_provider_results(provider, smiles_list):
    print("=" * 60)
    print("Toxicology provider outputs (values with units)")
    print("=" * 60)

    for s in smiles_list:
        print(f"SMILES: {s}")
        try:
            props = provider.calculate_properties(s, "toxicology")
        except Exception as e:
            print(f"  ERROR calculating properties: {e}")
            continue

        # props is a mapping property -> {value, units, source, method, raw_data?}
        for name, info in props.items():
            val = info.get("value")
            units = info.get("units") or ""
            source = info.get("source")
            method = info.get("method")
            raw = info.get("raw_data") or info.get("row_data") or info.get("raw")

            # Pretty-format the value: floats with 2 decimals, otherwise str()
            pretty_val = None
            if isinstance(val, float):
                pretty_val = f"{val:.2f}"
            else:
                # Try to coerce numeric-looking strings
                try:
                    fv = float(str(val))
                    pretty_val = f"{fv:.2f}"
                except Exception:
                    pretty_val = str(val)

            print(f"  {name}: {pretty_val} {units}  (source={source}, method={method})")
            if raw is not None:
                # Compactly show a few keys from raw data if it's a dict
                if isinstance(raw, dict):
                    sample = {k: raw[k] for k in list(raw.keys())[:6]}
                    print(f"    raw_data sample: {sample}")
                else:
                    print(f"    raw_data: {raw}")
        print()


def main():
    # Setup Django and project path like other examples
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "back.settings")
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    import django

    django.setup()

    # Import the registry and obtain the toxicology provider
    from chemistry.providers.factory import auto_register_providers, registry

    # Ensure providers are auto-registered (AppConfig.ready normally does this)
    auto_register_providers()

    if not registry.has_provider("toxicology"):
        print("Toxicology provider not registered", file=sys.stderr)
        sys.exit(2)

    provider = registry.get_provider("toxicology")

    print_provider_results(provider, SMILES)


if __name__ == "__main__":
    main()
