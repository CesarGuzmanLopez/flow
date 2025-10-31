#!/usr/bin/env bash
set -euo pipefail

# Run WebTEST server using portable Java 21 (or 17+)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Load environment variables from .env if present
ENV_FILE="$ROOT_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

# Default ports if not set in .env
WEBTEST_PORT="${WEBTEST_PORT:-8100}"
WEBTEST_ADMIN_PORT="${WEBTEST_ADMIN_PORT:-8101}"

JAVA_BIN="$ROOT_DIR/tools/java/jre21/bin/java"
JAR_PATH="$ROOT_DIR/tools/external/test/WebTEST.jar"
CONFIG_TEMPLATE="$ROOT_DIR/tools/external/test/config.yml"

# Check if Java portable exists
if [[ ! -x "$JAVA_BIN" ]]; then
  echo "ERROR: Java 21 portable not found at $JAVA_BIN" >&2
  echo "Run: scripts/download_java_runtimes.sh" >&2
  exit 1
fi

# Check if JAR exists
if [[ ! -f "$JAR_PATH" ]]; then
  echo "ERROR: WebTEST.jar not found at $JAR_PATH" >&2
  echo "Run: scripts/download_external_tools.sh" >&2
  exit 1
fi

# Create temporary config with custom ports
TEMP_CONFIG="/tmp/webtest_config_$$.yml"
trap "rm -f $TEMP_CONFIG" EXIT

cat > "$TEMP_CONFIG" <<EOF
server:
  applicationConnectors:
    - type: http
      port: $WEBTEST_PORT
  adminConnectors:
    - type: http
      port: $WEBTEST_ADMIN_PORT
EOF

echo "Starting WebTEST server on ports $WEBTEST_PORT/$WEBTEST_ADMIN_PORT..."
exec "$JAVA_BIN" -jar "$JAR_PATH" predict -i $1 -o $2 -m $3