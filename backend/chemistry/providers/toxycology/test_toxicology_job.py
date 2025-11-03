import os
from typing import Any

import pytest
from chemistry.providers.background_jobs.models import Execution
from chemistry.providers.background_jobs.toxicology import (
    ToxicologyExternalJobProvider,
)
from django.utils import timezone


def setup_function(func: Any) -> None:
    # Run external jobs in FAST sync mode for tests
    os.environ["EXTERNAL_JOBS_FAST"] = "1"


@pytest.mark.django_db(transaction=True)
def test_toxicology_batch_job_waits_until_completion() -> None:
    provider = ToxicologyExternalJobProvider()

    # 20 SMILES including known and unknown mappings
    smiles_list = [
        "CCO",
        "NNCNO",
        "CCCNNCNO",
        "c1ccccc1NNCNO",
        "smilefalso",
        "CCNc1ccOccc1",
    ]
    # pad to 20 with generic unknowns
    smiles_list += [f"C{i}C" for i in range(1, 15)]  # 14 items → total 20

    meta = provider.start(
        payload={"smiles_list": smiles_list, "started_at": timezone.now().isoformat()},
        idempotency_key="tox-batch-20",
    )

    # In FAST mode, execution runs synchronously, but the returned metadata
    # may still reflect the pre-run state. Query fresh status.
    meta = provider.status(meta.execution_id)
    assert meta.status.name == "SUCCEEDED"

    # Fetch Execution to inspect results
    exec_obj = Execution.objects.get(execution_id=meta.execution_id)
    assert exec_obj.status == "succeeded"
    assert "results" in exec_obj.payload
    results = exec_obj.payload["results"]

    # Verify we processed all 20 entries
    assert isinstance(results, list)
    assert len(results) == 20

    # Each result should contain the smiles and a properties dict
    for item in results:
        assert "smiles" in item and "properties" in item
        props = item["properties"]
        # At least LD50 should be present in toxicology outputs
        assert "LD50" in props


@pytest.mark.django_db(transaction=True)
def test_toxicology_batch_job_idempotency() -> None:
    provider = ToxicologyExternalJobProvider()

    smiles_list = ["CCO", "NNCNO"]
    meta1 = provider.start(
        payload={"smiles_list": smiles_list}, idempotency_key="tox-dup"
    )
    meta2 = provider.start(
        payload={"smiles_list": smiles_list}, idempotency_key="tox-dup"
    )

    assert meta1.execution_id == meta2.execution_id
    # status should be succeeded in FAST mode
    assert meta2.status.name == "SUCCEEDED"
