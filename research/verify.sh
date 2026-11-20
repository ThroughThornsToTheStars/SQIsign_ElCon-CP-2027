#!/usr/bin/env bash
set -euo pipefail
profile=${1:?profile}
mode=${2:-Release}
dir="build-$profile-$mode"
ctest --test-dir "$dir" --output-on-failure -j "${JOBS:-2}" \
    -R '(research_system_|_KAT$|_SELFTEST$|test_nistapi_|test_threadsafety_|test_prng$|test_prng_kat$|test_ctrdrbg_kat$|test_shake256$)'
if [[ "$profile" != BASELINE ]]; then
    tmp=$(mktemp)
    trap 'rm -f "$tmp"' EXIT
    "$dir/research/primitive_test" > "$tmp"
    python3 research/oracle.py "$tmp" "$profile"
fi
python3 research/check.py --profile "$profile" --mode "$mode"
