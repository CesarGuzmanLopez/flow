import os
from typing import Any

import pytest
from chemistry.providers.external_tools.test_runner import run_test


def setup_function(func: Any) -> None:
    # No special env needed; ensure consistent locale for number parsing if runner depends on it
    os.environ.setdefault("LC_ALL", "C.UTF-8")
    os.environ.setdefault("LANG", "C.UTF-8")


def test_run_test_two_smiles_returns_expected_shape() -> None:
    try:
        data = run_test(
            ["c1ccccc1", "CCCNO"], ["LD50", "Mutagenicity", "DevTox", "Density"]
        )
    except FileNotFoundError:
        pytest.skip("T.E.S.T. runner not available in this environment")

    assert isinstance(data, dict)
    mols = data.get("molecules")
    assert isinstance(mols, list)
    assert len(mols) == 2
    for m in mols:
        assert "smiles" in m
        props = m.get("properties") or {}
        for p in ["LD50", "Mutagenicity", "DevTox", "Density"]:
            assert p in props
            # Each property includes at least a value or an error
            prop = props[p]
            assert isinstance(prop, dict)
            assert "value" in prop or "error" in prop


def test_run_test_ld50_mgkg_values() -> None:
    """Verify that LD50 Pred_Value:_mg/kg returns expected values for known SMILES."""
    try:
        data = run_test(["c1ccccc1", "CCCNO"], ["LD50"])
    except FileNotFoundError:
        pytest.skip("T.E.S.T. runner not available in this environment")

    mols = data.get("molecules", [])
    assert len(mols) == 2

    # Helper to parse locale-safe floats
    def parse_float(x):
        if x is None or str(x).strip().upper() == "N/A":
            return None
        s = str(x).replace(" ", "").replace(",", ".")
        try:
            return float(s)
        except Exception:
            return None

    # c1ccccc1 -> Pred_Value:_mg/kg should be ~6717.61
    ld50_benzene = mols[0]["properties"]["LD50"]
    raw_benzene = ld50_benzene.get("raw_data", {})
    mg_benzene = parse_float(raw_benzene.get("Pred_Value:_mg/kg"))
    assert mg_benzene is not None
    assert pytest.approx(mg_benzene, rel=0.01) == 6717.61

    # CCCNO -> Pred_Value:_mg/kg should be ~1068.25
    ld50_cccno = mols[1]["properties"]["LD50"]
    raw_cccno = ld50_cccno.get("raw_data", {})
    mg_cccno = parse_float(raw_cccno.get("Pred_Value:_mg/kg"))
    assert mg_cccno is not None
    assert pytest.approx(mg_cccno, rel=0.01) == 1068.25
