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

- Use `scripts/download_external_tools.sh` to download missing files. The script is idempotent.

## Notes

- Do not commit heavy vendor binaries unless explicitly whitelisted in this folder's .gitignore.
- If the AMBIT jar is already present in the repo, the script will skip downloading it.
