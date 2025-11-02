"""
Data models for T.E.S.T. results
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass
class EndpointResult:
    """Result from a single endpoint prediction.

    Use `from_row_data` to build an instance from a parsed CSV row.
    """

    name: str
    unit: str
    description: str
    application: str
    value: Optional[float] = None
    error: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        # Produce a JSON-serializable dict and represent missing values as 'NA'
        d = asdict(self)
        # Normalize value and error to 'NA' when missing to make consumption easier
        d["value"] = d.get("value") if d.get("value") is not None else "NA"
        d["error"] = d.get("error") if d.get("error") else "NA"
        return d

    def value_or_na(self) -> Any:
        """Return numeric value or the string 'NA' for convenience.

        Useful for consumers that prefer a single accessor when working with
        the Python objects (not JSON). Keeps original type on the object.
        """
        return self.value if self.value is not None else "NA"

    @classmethod
    def from_row_data(
        cls, row_data: Dict[str, Any], desc: Dict[str, Any]
    ) -> "EndpointResult":
        """Classify a CSV row into an EndpointResult.

        Heuristics:
        - Look for keys containing 'Pred_Value' or starting with 'Pred' for predicted value.
        - If found, try to coerce to float; otherwise keep None and put textual info in error.
        - If an 'Error' key exists and is non-empty, set error to that value.
        """
        val = None
        err = None

        # Detect error message
        if isinstance(row_data, dict) and "Error" in row_data and row_data.get("Error"):
            err = str(row_data.get("Error"))

        # Find predicted value candidates
        if isinstance(row_data, dict):
            for k, v in row_data.items():
                if not v:
                    continue
                key_lower = k.lower()
                if (
                    "pred" in key_lower
                    or "pred_value" in key_lower
                    or "pred value" in key_lower
                ):
                    s = str(v).strip()
                    # try parse float, tolerate comma decimal
                    try:
                        s_norm = s.replace(",", ".")
                        val = float(s_norm)
                        break
                    except Exception:
                        # keep textual error if no numeric value
                        if not err:
                            err = s
                        continue

        return cls(
            name=desc.get("name", ""),
            unit=desc.get("unit", "N/A"),
            description=desc.get("description", ""),
            application=desc.get("application", ""),
            value=val,
            error=err,
            raw_data=row_data,
        )


@dataclass
class MoleculeResult:
    """Results for a single molecule."""

    smiles: Optional[str]
    properties: Dict[str, EndpointResult]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "smiles": self.smiles,
            "properties": {k: v.to_dict() for k, v in self.properties.items()},
        }


@dataclass
class TestResults:
    """Complete results from a T.E.S.T. run."""

    molecules: List[MoleculeResult]
    metadata: Dict[str, Any]
    diagnostics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metadata": self.metadata,
            "diagnostics": self.diagnostics,
            "molecules": [m.to_dict() for m in self.molecules],
        }
