"""
Utility functions for file and system operations.
"""

import os
import shutil
from typing import Optional


def validate_dir(path: str) -> bool:
    """Validate if directory exists and is accessible."""
    return os.path.isdir(path) and os.access(path, os.R_OK | os.W_OK)


def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)


def collect_smiles(smiles_list: list, smiles_files: list) -> list:
    """Collect SMILES from arguments and files."""
    result = list(smiles_list)

    for fp in smiles_files:
        if os.path.isfile(fp):
            with open(fp, "r", encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    ln = ln.strip()
                    if ln:
                        result.append(ln)

    return result


def resolve_executable(name: str) -> Optional[str]:
    """Resolve executable path using which."""
    return shutil.which(name)


def write_smiles_file(smiles_list: list, output_path: str) -> None:
    """Write SMILES to a file."""
    with open(output_path, "w", encoding="utf-8") as fh:
        for smiles in smiles_list:
            fh.write(f"{smiles.strip()}\n")
