#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Paths
JAVA_BIN="$ROOT_DIR/tools/java/jre21/bin/java"
JAR_PATH="$ROOT_DIR/tools/external/test/WebTEST.jar"
WEBTEST_DIR="$ROOT_DIR/tools/external/test"

# Function to display usage
usage() {
    cat <<EOF
Usage: $0 predict [OPTIONS]

WebTEST toxicity prediction wrapper

OPTIONS:
    -i, --input FILE        Input SMILES file (required)
    -o, --output FILE       Output file (default: output.csv)
    -e, --endpoints LIST    Space-separated endpoint codes (default: all)
    -m, --method METHOD     Prediction method (default: Consensus)
                           Options: Consensus, Hierarchical, FDA, Nearest neighbor,
                                   Group contribution, Single model
                           (case-insensitive)
    -r, --report FORMAT     Report format (default: JSON)
                           Options: JSON, PDF, HTML, TXT
    -h, --help             Show this help message

ENDPOINT CODES:
    Note: WebTEST is very strict about endpoint names. If you get "invalid endpoint(s)" 
    errors, try omitting the -e flag to use all available endpoints.

    Known working codes when tested individually:
    MP           Melting point (tested and works)
    
    Codes to try (based on original WebTEST documentation):
    LD50         Oral rat LD50
    Mutagenicity Mutagenicity  
    Viscosity    Viscosity at 25°C
    WS           Water solubility at 25°C
    VP           Vapor pressure at 25°C
    LC50DM       Daphnia magna LC50 (48 hr)
    BCF          Bioconcentration factor
    BP           Boiling point
    FP           Flash point
    ST           Surface tension at 25°C
    TH           Thermal conductivity at 25°C
    DV           Density
    LC50FM       Fathead minnow LC50 (96 hr)
    IGC50        Tetrahymena pyriformis IGC50 (48 hr)
    DevTox       Developmental toxicity

    You can also pass full endpoint names with spaces if known.

EXAMPLES:
    # Recommended: Use all endpoints (no -e flag)
    $0 predict -i hola.smi -o results.csv

    # Single endpoint that works
    $0 predict -i hola.smi -o results.csv -e MP

    # With method and format
    $0 predict -i input.smi -o output.csv -m consensus -r JSON

    # Try multiple (may give "invalid endpoint" error)
    $0 predict -i hola.smi -o results.csv -e LD50 Mutagenicity MP

EOF
    exit "${1:-0}"
}

# Check prerequisites
check_prerequisites() {
    if [[ ! -x "$JAVA_BIN" ]]; then
        echo "ERROR: Java 21 not found at $JAVA_BIN" >&2
        echo "Run: scripts/download_java_runtimes.sh" >&2
        exit 1
    fi

    if [[ ! -f "$JAR_PATH" ]]; then
        echo "ERROR: WebTEST.jar not found at $JAR_PATH" >&2
        echo "Run: scripts/download_external_tools.sh" >&2
        exit 1
    fi
}

# Parse command line arguments
parse_args() {
    local command="${1:-}"
    shift || true

    if [[ "$command" != "predict" ]]; then
        echo "ERROR: Unknown command '$command'. Only 'predict' is supported." >&2
        usage 1
    fi

    INPUT_FILE=""
    OUTPUT_FILE="output.csv"
    ENDPOINTS=()
    METHOD="Consensus"
    REPORT_FORMAT="JSON"

    while [[ $# -gt 0 ]]; do
        case "$1" in
            -i|--input)
                INPUT_FILE="$2"
                shift 2
                ;;
            -o|--output)
                OUTPUT_FILE="$2"
                shift 2
                ;;
            -e|--endpoints)
                shift
                while [[ $# -gt 0 ]] && [[ ! "$1" =~ ^- ]]; do
                    ENDPOINTS+=("$1")
                    shift
                done
                ;;
            -m|--method)
                METHOD="$2"
                shift 2
                ;;
            -r|--report)
                REPORT_FORMAT="$2"
                shift 2
                ;;
            -h|--help)
                usage 0
                ;;
            *)
                echo "ERROR: Unknown option '$1'" >&2
                usage 1
                ;;
        esac
    done

    # Validate required arguments
    if [[ -z "$INPUT_FILE" ]]; then
        echo "ERROR: Input file (-i) is required" >&2
        usage 1
    fi

    # Convert relative paths to absolute
    if [[ ! "$INPUT_FILE" = /* ]]; then
        INPUT_FILE="$ROOT_DIR/$INPUT_FILE"
    fi
    if [[ ! "$OUTPUT_FILE" = /* ]]; then
        OUTPUT_FILE="$ROOT_DIR/$OUTPUT_FILE"
    fi

    # Check input file exists
    if [[ ! -f "$INPUT_FILE" ]]; then
        echo "ERROR: Input file not found: $INPUT_FILE" >&2
        exit 1
    fi

    # Create output directory if needed
    OUTPUT_DIR="$(dirname "$OUTPUT_FILE")"
    mkdir -p "$OUTPUT_DIR"
}

# Build endpoint arguments
build_endpoint_args() {
    # Map short codes to WebTEST's expected full endpoint names
    # These are the EXACT names from the successful log output
    local endpoint_map=(
        "LD50:Oral rat LD50"
        "Mutagenicity:Mutagenicity"
        "MP:Melting point"
        "Viscosity:Viscosity at 25°C"
        "WS:Water solubility at 25°C"
        "VP:Vapor pressure at 25°C"
        "LC50DM:Daphnia magna LC50 (48 hr)"
        "BCF:Bioconcentration factor"
        "BP:Boiling point"
        "FP:Flash point"
        "ST:Surface tension at 25°C"
        "TH:Thermal conductivity at 25°C"
        "DV:Density"
        "LC50FM:Fathead minnow LC50 (96 hr)"
        "IGC50:Tetrahymena pyriformis IGC50 (48 hr)"
        "DevTox:Developmental toxicity"
    )

    ENDPOINT_ARGS=()
    if [[ ${#ENDPOINTS[@]} -gt 0 ]]; then
        for code in "${ENDPOINTS[@]}"; do
            # If it contains spaces, assume it's already a full name
            if [[ "$code" == *" "* ]]; then
                ENDPOINT_ARGS+=("-e" "$code")
            else
                # Look for mapping
                found=false
                for mapping in "${endpoint_map[@]}"; do
                    if [[ "$mapping" =~ ^$code: ]]; then
                        local full_name="${mapping#*:}"
                        ENDPOINT_ARGS+=("-e" "$full_name")
                        found=true
                        break
                    fi
                done
                if [[ "$found" == "false" ]]; then
                    # Use as-is if not found in map
                    ENDPOINT_ARGS+=("-e" "$code")
                fi
            fi
        done
    fi
}

# Normalize method name to WebTEST format
normalize_method() {
    local method_lower="${METHOD,,}"
    case "$method_lower" in
        consensus)
            METHOD="Consensus"
            ;;
        hierarchical)
            METHOD="Hierarchical"
            ;;
        fda)
            METHOD="FDA"
            ;;
        nearest_neighbor|nearestneighbor)
            METHOD="Nearest neighbor"
            ;;
        group_contribution|groupcontribution)
            METHOD="Group contribution"
            ;;
        single_model|singlemodel)
            METHOD="Single model"
            ;;
        *)
            echo "WARNING: Unknown method '$METHOD', using as-is" >&2
            ;;
    esac
}

# Main execution
main() {
    if [[ $# -eq 0 ]] || [[ "${1:-}" == "-h" ]] || [[ "${1:-}" == "--help" ]]; then
        usage 0
    fi

    check_prerequisites
    parse_args "$@"
    normalize_method
    build_endpoint_args

    echo "WebTEST Toxicity Prediction" >&2
    echo "============================" >&2
    echo "Input:  $INPUT_FILE" >&2
    echo "Output: $OUTPUT_FILE" >&2
    echo "Method: $METHOD" >&2
    echo "Format: $REPORT_FORMAT" >&2
    if [[ ${#ENDPOINTS[@]} -gt 0 ]]; then
        echo "Endpoints: ${ENDPOINTS[*]}" >&2
    else
        echo "Endpoints: All available" >&2
    fi
    echo "" >&2

    # Change to WebTEST directory so it can find databases/ and other resources
    cd "$WEBTEST_DIR"

    # Build command
    CMD=("$JAVA_BIN" "-jar" "$JAR_PATH" "predict" 
         "-i" "$INPUT_FILE" 
         "-o" "$OUTPUT_FILE" 
         "-m" "$METHOD"
         "-r" "$REPORT_FORMAT")

    # Add endpoint arguments if specified
    if [[ ${#ENDPOINT_ARGS[@]} -gt 0 ]]; then
        CMD+=("${ENDPOINT_ARGS[@]}")
    fi

    # Execute
    echo "Running: ${CMD[*]}" >&2
    echo "" >&2
    echo "Full command with proper quoting:" >&2
    printf '%q ' "${CMD[@]}" >&2
    echo "" >&2
    echo "" >&2
    exec "${CMD[@]}"
}

main "$@"