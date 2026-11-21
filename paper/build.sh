#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
mkdir -p build
exec 9<build
flock -n 9 || { echo 'Сборка уже выполняется.' >&2; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
python3 tools/build.py 2>&1 | tee build/build.log
