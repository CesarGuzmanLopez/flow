import os

from test.config import ENDPOINTS_DESCRIPTION
from test.io import FileWaiter, ResultsReader
from test.models import EndpointResult


def test_endpointresult_from_row_numeric():
    row = {"Index": "1", "Pred_Value": "3.14", "Note": "ok"}
    desc = ENDPOINTS_DESCRIPTION.get("LC50", {})
    res = EndpointResult.from_row_data(row, desc)
    assert isinstance(res.value, float)
    assert abs(res.value - 3.14) < 1e-6
    assert res.error is None or res.error == ""


def test_endpointresult_from_row_error_text():
    row = {"Index": "1", "Pred_Value": "n/a", "Error": "Calculation failed"}
    desc = ENDPOINTS_DESCRIPTION.get("LC50", {})
    res = EndpointResult.from_row_data(row, desc)
    assert res.value is None
    assert res.error is not None


def test_filewaiter_wait_success(tmp_path):
    p = tmp_path / "out.txt"
    # create file before waiting
    p.write_text("data")
    waiter = FileWaiter([str(p)], timeout_sec=1)
    assert waiter.wait() is True


def test_resultsreader_reads_csv(tmp_path):
    # Prepare output dir and a fake CSV for LC50
    outdir = str(tmp_path)
    fn = os.path.join(outdir, "propiedad123_LC50.csv")
    csv_text = "Index,Pred_Value,Other\n1,2.5,foo\n2,5.0,bar\n"
    with open(fn, "w", encoding="utf-8") as fh:
        fh.write(csv_text)

    reader = ResultsReader(outdir, ENDPOINTS_DESCRIPTION)
    results = reader.read(wait_timeout=1)

    # results is a TestResults object
    assert hasattr(results, "molecules")
    # convert to list
    mols = results.molecules
    # since indices in CSV start at 1, ensure we have entries for 1 and 2
    vals = [m.properties.get("LC50").value for m in mols if "LC50" in m.properties]
    assert 2.5 in vals
    assert 5.0 in vals
