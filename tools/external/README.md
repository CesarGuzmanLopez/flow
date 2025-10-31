# External tools

This directory contains third-party CLI tools used by the project. To keep the repository lean, heavy binaries are not committed; a small, safe-to-commit JAR is whitelisted.

## Layout

- ambit/

  - SyntheticAccessibilityCli.jar (small; allowed in VCS)
  - Source: <http://web.uni-plovdiv.bg/nick/ambit-tools/SyntheticAccessibilityCli.jar>

- test/
  - WebTEST.jar (heavy; not committed)
  - Source: <https://github.com/CesarGuzmanLopez/test-app-epa/releases/download/master/WebTEST.jar>

## Fetch or update

- Use `scripts/download_external_tools.sh` to download missing tools (JARs). The script is idempotent.
- Use `scripts/download_java_runtimes.sh` to download portable JREs (8 and 21) under `tools/java/`.

## Notes

- Do not commit heavy vendor binaries unless explicitly whitelisted in this folder's .gitignore.
- Wrapper scripts:
  - `tools/external/ambit/run_ambit.sh` uses Java 8 (embedded or system) to run AMBIT.
  - `tools/external/test/run_test.sh` uses Java 21 (embedded or system) to run WebTEST.

## Docker usage

### WebTEST server (ports 8100/8101)

- Build & start: `scripts/webtest_up.sh`
- Stop: `scripts/webtest_down.sh`
- Compose file: `tools/external/test/docker-compose.yml`
- Config file: `tools/external/test/config.yml`

The container exposes:

- App: <http://localhost:8100/>
- Admin: <http://localhost:8101/>

### AMBIT CLI (Java 8)

- Run inside container: `scripts/ambit_docker.sh --help` (passes args through)
- Dockerfile: `tools/external/ambit/Dockerfile`
- If the AMBIT jar is already present in the repo, the script will skip downloading it.
