#!/usr/bin/env python3
import json
import sys

from test.cli import parse_args
from test.core import TESTRunner


def write_csv_results(results: dict, output_path: str) -> None:
    """Write results to CSV file."""
    import csv

    # Get molecules list (can be a list or dict)
    molecules = results.get("molecules", [])
    if isinstance(molecules, dict):
        molecules = list(molecules.values())

    # Get only the requested endpoints
    requested_endpoints = []
    if results.get("metadata", {}).get("calculate"):
        # Use the endpoints that were actually requested
        calc_param = results["metadata"]["calculate"]
        requested_endpoints = [e.strip() for e in calc_param.split(",")]
    else:
        # Fallback to endpoints that exist in the results
        for mol_data in molecules:
            for endpoint in mol_data.get("properties", {}):
                if endpoint not in requested_endpoints:
                    requested_endpoints.append(endpoint)
        requested_endpoints.sort()

    # Build CSV rows
    csv_rows = []
    for mol_data in molecules:
        row = {"SMILES": mol_data.get("smiles", "")}
        for endpoint in requested_endpoints:
            pred_val = "NA"
            if endpoint in mol_data.get("properties", {}):
                prop = mol_data["properties"][endpoint]
                # Try to extract predicted value from raw_data
                if "raw_data" in prop and prop["raw_data"]:
                    row_data = prop["raw_data"]
                    if isinstance(row_data, dict):
                        pred_candidates = [
                            v
                            for k, v in row_data.items()
                            if "Pred_Value" in k and v and str(v).strip()
                        ]
                        if pred_candidates:
                            pred_val = pred_candidates[0]
                        elif "Error" in row_data and row_data["Error"]:
                            pred_val = "ERROR"
                # Also try the value field directly
                elif "value" in prop and prop["value"] is not None:
                    pred_val = str(prop["value"])
            row[endpoint] = pred_val
        csv_rows.append(row)

    # Write CSV file
    fieldnames = ["SMILES"] + requested_endpoints
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)


def main():
    """Main entry point."""
    try:
        # Parse command line arguments
        args = parse_args()

        # Create and run TEST runner
        runner = TESTRunner(args)
        results = runner.run()

        # Store the calculate parameter in metadata
        if args.calculate:
            results["metadata"]["calculate"] = args.calculate

        # Generate CSV if requested
        if args.output_csv:
            write_csv_results(results, args.output_csv)
        else:
            # Only write JSON output if CSV was not requested
            if args.output_json == "-" or args.output_json.lower() == "stdout":
                json.dump(results, sys.stdout, indent=2, ensure_ascii=False)
                sys.stdout.write("\n")
            else:
                with open(args.output_json, "w", encoding="utf-8") as fh:
                    json.dump(results, fh, indent=2, ensure_ascii=False)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
