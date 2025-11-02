"""
Command-line interface handling for T.E.S.T. runner
"""

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build and return command line argument parser."""
    # Get embedded endpoint descriptions
    from test.config import ENDPOINTS_DESCRIPTION

    all_endpoints = list(ENDPOINTS_DESCRIPTION.keys())
    endpoints_str = ", ".join(sorted(all_endpoints))
    calculate_help = (
        f"Comma-separated list of endpoints to calculate. Available: {endpoints_str}. "
        "If not specified, all endpoints are calculated."
    )

    parser = argparse.ArgumentParser(
        description="Run T.E.S.T. endpoints concurrently with flexible configuration",
        epilog=(
            "Examples:\n"
            "  python3 run_test.py --smiles 'CCO' --smiles 'c1ccccc1' > results.json\n"
            "  python3 run_test.py --smiles-file mols.smi --calculate 'BP,VP,WS' "
            "--output-csv results.csv\n"
            "  python3 run_test.py -s 'CCO' -w 8 --java /usr/bin/java "
            "-o output.json"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--smiles", "-s", action="append", default=[], help="SMILES string (can repeat)"
    )

    parser.add_argument(
        "--smiles-file",
        "-f",
        action="append",
        default=[],
        help="Path to SMILES file (one per line, can repeat)",
    )

    parser.add_argument("--java", help="Path to java binary", default="java")

    parser.add_argument(
        "--workers", "-w", type=int, default=6, help="Number of concurrent workers"
    )

    parser.add_argument(
        "--timeout", type=int, default=None, help="Per-endpoint timeout in seconds"
    )

    parser.add_argument(
        "--output-json",
        "-o",
        help="Write final JSON to file (default stdout)",
        default="-",
    )

    parser.add_argument(
        "--output-csv",
        help="Write results to CSV file (one molecule per row, endpoints as columns)",
        default=None,
    )

    parser.add_argument("--calculate", help=calculate_help, default=None)

    parser.add_argument("--tmp-dir", help="Use existing tmp dir", default=None)

    parser.add_argument(
        "--keep-tmp",
        action="store_true",
        help="Keep temporary files for debugging (default: delete after completion)",
    )

    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=3600,
        help="Maximum time to wait for output files in seconds (default: 3600 = 1 hour)",
    )

    parser.add_argument(
        "--no-xvfb",
        action="store_true",
        help="Disable xvfb-run wrapper (execute Java directly without X virtual framebuffer)",
    )

    return parser


def parse_args():
    """Parse command line arguments and return them as argparse.Namespace."""
    parser = build_parser()
    return parser.parse_args()
