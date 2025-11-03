from typing import Any

import pytest
from chemistry.providers.factory import auto_register_providers, registry
from chemistry.providers.property_providers import ToxicologyProvider


def setup_function(func: Any) -> None:
    # Ensure registry clean state for tests
    try:
        registry.clear()
    except Exception:
        pass


def test_auto_register_includes_toxicology() -> None:
    # Auto-register built-in providers and assert toxicology is present
    auto_register_providers()
    names = registry.list_provider_names()
    assert "toxicology" in names


def test_toxicology_provider_returns_expected_values_for_known_smiles() -> None:
    auto_register_providers()
    provider = registry.get_provider("toxicology")

    # Sanity: provider is instance of our class
    assert isinstance(provider, ToxicologyProvider)

    # Known mapping test: CCO -> numeric values
    res = provider.calculate_properties("CCO", "toxicology")
    assert "LD50" in res
    assert pytest.approx(float(res["LD50"]["value"])) == 1.77
    assert pytest.approx(float(res["LC50DM"]["value"])) == 1.55
    assert pytest.approx(float(res["DevTox"]["value"])) == 0.46
    assert pytest.approx(float(res["Mutagenicity"]["value"])) == -0.01


def test_toxicology_provider_handles_invalid_smiles_by_returning_NA() -> None:
    auto_register_providers()
    provider = registry.get_provider("toxicology")

    res = provider.calculate_properties("smilefalso", "toxicology")
    # For invalid smiles mapping we expect string 'NA' preserved (no numeric conversion)
    assert res["LD50"]["value"] == "NA"
    assert res["Mutagenicity"]["value"] == "NA"
