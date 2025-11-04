import os
from typing import Any

import pytest
from chemistry.providers.factory import auto_register_providers, registry


def setup_function(func: Any) -> None:
    os.environ.setdefault("LC_ALL", "C.UTF-8")
    os.environ.setdefault("LANG", "C.UTF-8")
    try:
        registry.clear()
    except Exception:
        pass


def test_webtest_provider_single_smiles_properties() -> None:
    auto_register_providers()
    provider = registry.get_provider("webtest")

    # Two different categories through the same external tool
    try:
        props_toxic = provider.calculate_properties("c1ccccc1", "toxicology")
        for key in ["LD50", "Mutagenicity", "DevTox"]:
            assert key in props_toxic
            # Provider interface returns structured dict with 'value', 'units', etc
            assert isinstance(props_toxic[key], dict)
            assert "value" in props_toxic[key]

        props_phys = provider.calculate_properties("CCCNO", "physics")
        assert "Density" in props_phys
        assert isinstance(props_phys["Density"], dict)
        assert "value" in props_phys["Density"]
    except FileNotFoundError:
        pytest.skip("T.E.S.T. runner not available in this environment")


def test_webtest_provider_ld50_mgkg_values() -> None:
    """Verify that WebTEST provider returns LD50 in mg/kg as expected."""
    auto_register_providers()
    provider = registry.get_provider("webtest")

    try:
        # c1ccccc1 -> LD50 Pred_Value:_mg/kg should be ~6717.61
        props_benzene = provider.calculate_properties("c1ccccc1", "toxicology")
        assert "LD50" in props_benzene
        ld50_benzene = float(props_benzene["LD50"]["value"])  # mg/kg (preferred)
        # raw_data must preserve all values provided by the runner
        raw_benzene = props_benzene["LD50"].get("raw_data", {})
        assert "Exp_Value:_-Log10(mol/kg)" in raw_benzene
        assert "Pred_Value:_-Log10(mol/kg)" in raw_benzene
        assert "Exp_Value:_mg/kg" in raw_benzene
        assert "Pred_Value:_mg/kg" in raw_benzene
        assert pytest.approx(ld50_benzene, rel=0.01) == 6717.61

        # CCCNO -> LD50 Pred_Value:_mg/kg should be ~1068.25
        props_cccno = provider.calculate_properties("CCCNO", "toxicology")
        assert "LD50" in props_cccno
        ld50_cccno = float(props_cccno["LD50"]["value"])  # mg/kg (preferred)
        raw_cccno = props_cccno["LD50"].get("raw_data", {})
        assert "Pred_Value:_mg/kg" in raw_cccno
        assert pytest.approx(ld50_cccno, rel=0.01) == 1068.25

        # Also verify other toxicology endpoints are present
        assert "Mutagenicity" in props_benzene
        assert "DevTox" in props_benzene

        # For Mutagenicity and DevTox prefer Pred_Result (categorical). If not available, allow numeric/NA fallback.
        raw_mut = props_benzene["Mutagenicity"].get("raw_data", {})
        mut_val = props_benzene["Mutagenicity"].get("value")
        if str(raw_mut.get("Pred_Result", "")).strip():
            assert mut_val == str(raw_mut["Pred_Result"]).strip()
        else:
            assert mut_val in ("NA", None, "")

        raw_dev = props_benzene["DevTox"].get("raw_data", {})
        dev_val = props_benzene["DevTox"].get("value")
        if str(raw_dev.get("Pred_Result", "")).strip():
            assert dev_val == str(raw_dev["Pred_Result"]).strip()
        else:
            # Fallback: numeric probability if no Pred_Result
            float(dev_val)
    except FileNotFoundError:
        pytest.skip("T.E.S.T. runner not available in this environment")
