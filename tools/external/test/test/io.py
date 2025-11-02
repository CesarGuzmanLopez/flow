"""
I/O helpers for waiting on and reading T.E.S.T. output files.

Provides small, well-documented classes that other programs can import
to wait for output files (with timeout) and parse them into simple
Python data structures (using existing endpoint descriptions).

API summary:
- FileWaiter(output_paths, timeout_sec).wait() -> bool
- ResultsReader(output_dir, endpoints_desc).read(wait_timeout)->dict

These helpers intentionally return plain dicts (and use the project's
dataclasses elsewhere) so other programs (including non-python) can
consume JSON-serializable output easily.
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from .core import try_parse_csv
from .models import EndpointResult, MoleculeResult, TestResults


class FileWaiter:
    """Wait for one or more files to exist and be non-empty.

    Example:
        waiter = FileWaiter(["/tmp/out1.csv","/tmp/out2.csv"], timeout_sec=60)
        ok = waiter.wait()

    Returns True if all files appeared within timeout, False otherwise.
    """

    def __init__(
        self, paths: List[str], timeout_sec: int = 60, poll_interval: float = 0.5
    ):
        self.paths = paths
        self.timeout_sec = timeout_sec
        self.poll_interval = poll_interval

    def wait(self) -> bool:
        deadline = time.time() + (self.timeout_sec or 0)
        while True:
            all_good = True
            for p in self.paths:
                if not (
                    os.path.exists(p) and os.path.isfile(p) and os.path.getsize(p) > 0
                ):
                    all_good = False
                    break

            if all_good:
                return True

            if self.timeout_sec and time.time() >= deadline:
                return False

            time.sleep(self.poll_interval)


class ResultsReader:
    """Read and assemble endpoint outputs from an output directory.

    - `output_dir` is the directory where endpoint CSVs are written.
    - `endpoints_desc` is a mapping like `test.config.ENDPOINTS_DESCRIPTION`.

    Methods return plain dicts ready to be serialized to JSON and consumed
    by other programs.
    """

    def __init__(self, output_dir: str, endpoints_desc: Dict[str, Dict[str, Any]]):
        self.output_dir = output_dir
        self.endpoints_desc = endpoints_desc

    def _find_endpoint_file(self, endpoint: str) -> Optional[str]:
        # Expect CSV filenames in output dir that contain the endpoint abbreviation
        # Common naming produced by the runner: propiedad<uuid>_<EP>.csv
        if not os.path.isdir(self.output_dir):
            return None
        for fn in os.listdir(self.output_dir):
            if fn.lower().endswith(".csv") and f"_{endpoint}" in fn:
                return os.path.join(self.output_dir, fn)
        # fallback: exact name
        candidate = os.path.join(self.output_dir, f"{endpoint}.csv")
        if os.path.exists(candidate):
            return candidate
        return None

    def read(self, wait_timeout: int = 60) -> TestResults:
        """Wait for and read all endpoint files, return structured dict.

        The returned dict has keys:
        - metadata
        - molecules: mapping index -> {smiles, properties}
        - diagnostics: info about found/missing files
        """
        endpoints = list(self.endpoints_desc.keys())
        files = []
        ep_to_path: Dict[str, Optional[str]] = {}
        for ep in endpoints:
            p = self._find_endpoint_file(ep)
            ep_to_path[ep] = p
            if p:
                files.append(p)

        # Wait for files that exist (if none exist we still proceed)
        if files:
            waiter = FileWaiter(files, timeout_sec=wait_timeout)
            all_ready = waiter.wait()
        else:
            all_ready = True

        molecules: Dict[int, MoleculeResult] = {}

        # When parsing CSVs we expect an Index column referring to molecule position
        for ep, path in ep_to_path.items():
            desc = self.endpoints_desc.get(ep, {})
            if path and os.path.exists(path):
                parsed = try_parse_csv(path)
                if parsed.get("type") == "csv":
                    for row in parsed["data"]:
                        try:
                            idx = int(row.get("Index", 0))
                        except Exception:
                            idx = 0
                        if idx not in molecules:
                            molecules[idx] = MoleculeResult(smiles=None, properties={})
                        # classify row into a typed EndpointResult
                        ep_res = EndpointResult.from_row_data(row, desc)
                        molecules[idx].properties[ep] = ep_res
                elif parsed.get("type") == "text":
                    # attach text blob to diagnostic of each molecule
                    for idx in molecules:
                        molecules[idx].properties[ep] = EndpointResult(
                            name=desc.get("name", ep),
                            unit=desc.get("unit", "N/A"),
                            description=desc.get("description", ""),
                            application=desc.get("application", ""),
                            value=None,
                            error=None,
                            raw_data=parsed,
                        )
                else:
                    # error reading
                    for idx in molecules:
                        molecules[idx].properties[ep] = EndpointResult(
                            name=desc.get("name", ep),
                            unit=desc.get("unit", "N/A"),
                            description=desc.get("description", ""),
                            application=desc.get("application", ""),
                            value=None,
                            error=parsed.get("error", "unknown"),
                            raw_data=None,
                        )
            else:
                # missing file: record missing for diagnostics
                # ensure molecules map has at least a placeholder
                if not molecules:
                    molecules[0] = MoleculeResult(smiles=None, properties={})
                for idx in molecules:
                    molecules[idx].properties[ep] = EndpointResult(
                        name=desc.get("name", ep),
                        unit=desc.get("unit", "N/A"),
                        description=desc.get("description", ""),
                        application=desc.get("application", ""),
                        value=None,
                        error=None,
                        raw_data={"missing": True},
                    )

        # Build output
        # Convert molecules dict to ordered list by index
        ordered = [molecules[k] for k in sorted(molecules.keys())]

        result = TestResults(
            molecules=ordered,
            metadata={"endpoint_count": len(endpoints), "all_ready": all_ready},
            diagnostics={"found_files": {ep: bool(p) for ep, p in ep_to_path.items()}},
        )

        return result


def watch_and_parse(output_dir: str, wait_timeout: int = 60) -> TestResults:
    """Convenience function: use embedded endpoint descriptions and parse output_dir.

    Imports `ENDPOINTS_DESCRIPTION` lazily to avoid import cycles at module import time.
    """
    from .config import ENDPOINTS_DESCRIPTION

    reader = ResultsReader(output_dir, ENDPOINTS_DESCRIPTION)
    return reader.read(wait_timeout=wait_timeout)
