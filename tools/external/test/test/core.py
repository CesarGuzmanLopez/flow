"""
Core functionality for T.E.S.T. runner
"""

import base64
import csv
import os
import shutil
import subprocess
import sys
import tempfile as tf_module
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import EndpointResult, MoleculeResult, TestResults
from .utils import collect_smiles, ensure_dir, write_smiles_file


def get_endpoints_description() -> Dict:
    """Return embedded endpoint descriptions."""
    from test.config import ENDPOINTS_DESCRIPTION

    return ENDPOINTS_DESCRIPTION.copy()


def get_endpoints_from_description(endpoints_desc: Dict) -> List[Tuple[str, str]]:
    """Extract endpoint list from parsed descriptions."""
    endpoints = []
    for abbrev in endpoints_desc.keys():
        out_name = f"{abbrev}.csv"
        endpoints.append((abbrev, f"output/{out_name}"))
    return endpoints


def build_command(
    java_bin: str, input_path: str, out_path: str, endpoint: str, script_dir: str
) -> List[str]:
    """Build command for running T.E.S.T. endpoint."""
    jar_path = os.path.join(script_dir, "WebTEST.jar")
    return [
        java_bin,
        "-cp",
        jar_path,
        "ToxPredictor.Application.Calculations.RunFromCommandLine",
        "-i",
        input_path,
        "-o",
        out_path,
        "-e",
        endpoint,
        "-m",
        "consensus",
    ]


def run_command(
    cmd: List[str], timeout: Optional[int] = None, cwd: Optional[str] = None
) -> Dict[str, Any]:
    """Run a command and return its results."""
    start = time.time()
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        rc = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as e:
        rc = -1
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + f"\nTIMEOUT after {timeout}s"
    except Exception as e:
        rc = -2
        stdout = ""
        stderr = str(e)
    duration = time.time() - start
    return {"rc": rc, "stdout": stdout, "stderr": stderr, "duration": duration}


def try_parse_csv(path: str) -> Dict[str, Any]:
    """Try to parse a CSV file and return its contents."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            snip = fh.read()
            fh.seek(0)
            first = fh.readline()
            if "," in first:
                fh.seek(0)
                reader = csv.DictReader(fh)
                rows = list(reader)
                return {"type": "csv", "data": rows}
            else:
                return {"type": "text", "data": snip}
    except Exception as e:
        return {"type": "error", "error": str(e)}


def load_binary_as_b64(path: str) -> str:
    """Load a binary file and return its base64 encoded content."""
    with open(path, "rb") as fh:
        return base64.b64encode(fh.read()).decode("ascii")


class EndpointJobRunner:
    """Handles the execution and output processing of endpoint jobs."""

    def __init__(self, args, script_dir: str, java_bin: str, xvfb_path: Optional[str]):
        self.args = args
        self.script_dir = script_dir
        self.java_bin = java_bin
        self.xvfb_path = xvfb_path

    def prepare_jobs(
        self,
        commands: List[Tuple[str, str]],
        unique_id: str,
        tmpdir: str,
        inp_path: str,
    ) -> List[Dict]:
        """Prepare jobs for execution."""
        jobs = []
        output_dir = os.path.join(tmpdir, "output")
        ensure_dir(output_dir)

        for endpoint, out_rel in commands:
            out_filename = f"propiedad{unique_id}_{endpoint}.csv"
            out_path = os.path.join(output_dir, out_filename)

            # Build command
            base_cmd = build_command(
                self.java_bin, inp_path, out_path, endpoint, self.script_dir
            )

            cmd = base_cmd
            if self.xvfb_path:
                cmd = [
                    self.xvfb_path,
                    "-n",
                    "99",
                    "--server-args=-screen 0 1024x768x24",
                ] + base_cmd

            jobs.append(
                {
                    "endpoint": endpoint,
                    "out_name": out_filename,
                    "out_path": out_path,
                    "cmd": cmd,
                    "cwd": self.script_dir,
                }
            )

        return jobs

    def execute_jobs(self, jobs: List[Dict]) -> Dict[str, Dict]:
        """Execute jobs concurrently and return results."""
        results = {}
        futures = []

        with ThreadPoolExecutor(max_workers=self.args.workers) as executor:
            # Submit jobs
            for job in jobs:
                fut = executor.submit(
                    run_command, job["cmd"], self.args.timeout, job["cwd"]
                )
                futures.append((job, fut))

            # Process results
            for job, fut in futures:
                res = fut.result()
                ep = job["endpoint"]
                results[ep] = {
                    "out_name": job["out_name"],
                    "out_path": job["out_path"],
                    "rc": res["rc"],
                    "duration_sec": res["duration"],
                    "stderr": res.get("stderr", ""),
                }

                stderr = res.get("stderr", "")
                is_xvfb_cleanup_error = (
                    res["rc"] == 1
                    and stderr
                    and "kill:" in stderr
                    and "No existe el proceso" in stderr
                )

                if is_xvfb_cleanup_error:
                    self._handle_xvfb_cleanup(job, results, ep)

        return results

    def _handle_xvfb_cleanup(self, job: Dict, results: Dict, ep: str) -> None:
        """Handle xvfb cleanup related issues."""
        # Wait for file
        file_appeared = False
        for _ in range(20):
            time.sleep(0.5)
            if (
                os.path.exists(job["out_path"])
                and os.path.isfile(job["out_path"])
                and os.path.getsize(job["out_path"]) > 0
            ):
                file_appeared = True
                break

        if file_appeared:
            results[ep]["rc"] = 0
            results[ep]["stderr"] = "xvfb-run cleanup error ignored"


class TESTRunner:
    """Main class for running T.E.S.T. predictions."""

    def __init__(self, args):
        self.args = args
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.java_bin = self._resolve_java_binary()
        self.xvfb_path = self._resolve_xvfb()
        self.endpoints_desc = self._get_filtered_endpoints()

    def _resolve_java_binary(self) -> str:
        """Resolve and validate Java binary path."""
        java_candidate = self.args.java
        java_bin_resolved = None

        if os.path.isabs(java_candidate) or (os.path.sep in java_candidate):
            if os.path.isfile(java_candidate) and os.access(java_candidate, os.X_OK):
                java_bin_resolved = java_candidate
            else:
                found = shutil.which(os.path.basename(java_candidate))
                if found:
                    java_bin_resolved = found
        else:
            found = shutil.which(java_candidate)
            if found:
                java_bin_resolved = found

        if not java_bin_resolved:
            msg = "Java binary not found. Provide a correct --java path or install java in PATH"
            raise ValueError(msg)

        return java_bin_resolved

    def _resolve_xvfb(self) -> Optional[str]:
        """Resolve xvfb-run path."""
        if not self.args.no_xvfb:
            xvfb_path = shutil.which("xvfb-run")
            if not xvfb_path:
                print("Warning: 'xvfb-run' not found in PATH. Will run java directly.")
            return xvfb_path
        return None

    def _get_filtered_endpoints(self) -> Dict:
        """Get filtered endpoint descriptions based on args."""
        endpoints_desc = get_endpoints_description()
        if not endpoints_desc:
            raise ValueError("No endpoints found in embedded descriptions")

        if self.args.calculate:
            requested = [e.strip() for e in self.args.calculate.split(",")]
            invalid = [e for e in requested if e not in endpoints_desc]
            if invalid:
                raise ValueError(f"Invalid endpoints: {', '.join(invalid)}")
            endpoints_desc = {k: v for k, v in endpoints_desc.items() if k in requested}

        return endpoints_desc

    def run(self) -> Dict:
        """Run T.E.S.T. predictions and return results."""
        # Generate unique ID
        unique_id = str(uuid.uuid4())[:8]

        # Prepare tmp directory
        tmp_root = (
            self.args.tmp_dir
            if self.args.tmp_dir
            else os.path.join(os.getcwd(), ".test_tmp")
        )
        ensure_dir(tmp_root)

        # Create temporary directory
        try:
            tmpdir = tf_module.mkdtemp(dir=tmp_root, prefix=f"test_{unique_id}_")
        except Exception as e:
            raise RuntimeError(f"Error creating temporary directory: {e}")

        # Set up input/output paths
        inp_filename = f"entrada{unique_id}.smi"
        inp_path = os.path.join(tmpdir, inp_filename)
        output_dir = os.path.join(tmpdir, "output")
        ensure_dir(output_dir)

        # Collect SMILES input
        smiles_all = collect_smiles(self.args.smiles, self.args.smiles_file)
        if not smiles_all:
            raise ValueError("No SMILES provided")

        # Write input file
        write_smiles_file(smiles_all, inp_path)

        # Get endpoints and prepare jobs
        commands = get_endpoints_from_description(self.endpoints_desc)
        runner = EndpointJobRunner(
            self.args, self.script_dir, self.java_bin, self.xvfb_path
        )
        jobs = runner.prepare_jobs(commands, unique_id, tmpdir, inp_path)
        results = runner.execute_jobs(jobs)

        # Process outputs into typed objects
        molecules_map: Dict[int, MoleculeResult] = {}

        # Initialize molecule data (index starts at 1)
        for idx, smiles in enumerate(smiles_all, 1):
            molecules_map[idx] = MoleculeResult(smiles=smiles, properties={})

        # Process all endpoint outputs and classify into EndpointResult
        for endpoint, meta in results.items():
            path = meta.get("out_path")
            desc = self.endpoints_desc.get(endpoint, {})

            # Handle output file
            if path and os.path.exists(path) and os.path.isfile(path):
                try:
                    parsed = try_parse_csv(path)

                    if parsed.get("type") == "csv" and parsed.get("data"):
                        for row in parsed["data"]:
                            try:
                                mol_idx = int(row.get("Index", 0))
                            except Exception:
                                mol_idx = 0
                            if mol_idx in molecules_map:
                                ep_res = EndpointResult.from_row_data(row, desc)
                                molecules_map[mol_idx].properties[endpoint] = ep_res
                    else:
                        # Non-CSV - attach parsed blob to each molecule as raw_data
                        for mol_idx in molecules_map:
                            molecules_map[mol_idx].properties[endpoint] = (
                                EndpointResult(
                                    name=desc.get("name", endpoint),
                                    unit=desc.get("unit", "N/A"),
                                    description=desc.get("description", ""),
                                    application=desc.get("application", ""),
                                    value=None,
                                    error=None,
                                    raw_data=parsed,
                                )
                            )

                except Exception as e:
                    for mol_idx in molecules_map:
                        molecules_map[mol_idx].properties[endpoint] = EndpointResult(
                            name=desc.get("name", endpoint),
                            unit=desc.get("unit", "N/A"),
                            description=desc.get("description", ""),
                            application=desc.get("application", ""),
                            value=None,
                            error=str(e),
                            raw_data=None,
                        )
            else:
                # Missing output file - mark as missing in raw_data
                for mol_idx in molecules_map:
                    molecules_map[mol_idx].properties[endpoint] = EndpointResult(
                        name=desc.get("name", endpoint),
                        unit=desc.get("unit", "N/A"),
                        description=desc.get("description", ""),
                        application=desc.get("application", ""),
                        value=None,
                        error=None,
                        raw_data={"missing": True},
                    )

        # Build final typed results and convert to dict for compatibility
        ordered_molecules = [molecules_map[k] for k in sorted(molecules_map.keys())]

        final_results = TestResults(
            molecules=ordered_molecules,
            metadata={
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "tool": "T.E.S.T. Runner",
                "endpoint_count": len(commands),
                "workers": self.args.workers,
                "timeout_sec": self.args.timeout,
            },
            diagnostics={
                "tmpdir": tmpdir,
                "uuid": unique_id,
                "input_file": inp_path,
                "input_filename": inp_filename,
                "input_file_exists": os.path.isfile(inp_path),
                "output_dir": output_dir,
                "output_dir_exists": os.path.isdir(output_dir),
                "output_files_count": len(
                    [
                        f
                        for f in os.listdir(output_dir)
                        if os.path.isfile(os.path.join(output_dir, f))
                    ]
                )
                if os.path.isdir(output_dir)
                else 0,
                "note": (
                    f"Temporary files will be kept for debugging. Located in: {tmpdir}"
                    if self.args.keep_tmp
                    else f"Temporary files will be deleted after execution. Located in: {tmpdir}"
                ),
            },
        )

        final = final_results.to_dict()

        # Clean up if not keeping temporary files
        if not self.args.keep_tmp:
            try:
                shutil.rmtree(tmpdir)
            except Exception as e:
                print(
                    f"Warning: Could not clean up temporary files: {e}", file=sys.stderr
                )

        return final
