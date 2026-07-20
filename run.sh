#!/usr/bin/env bash
# Inicia o Mini Synth. Cria/usa um ambiente virtual em .venv se existir.
set -euo pipefail

cd "$(dirname "$0")"

if [ -d ".venv" ]; then
    # shellcheck disable=SC1091
    source .venv/bin/activate
fi

exec python -m src.main "$@"
