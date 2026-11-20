#!/usr/bin/env bash
set -euo pipefail
profile=${1:?profile}
mode=${2:-Release}
dir="build-$profile-$mode"
# The complete official corpus is exercised in Release. Pin one official record
# per set for the instrumented baseline, alongside the full negative tests.
extra=()
if [[ "$mode" = San && "$profile" = BASELINE ]]; then
    extra=(-E '_KAT$')
    for variant in p324_3 p500_27 p664_17; do
        "$dir/test/sqisign_test_kat_$variant" 0
    done
fi
ctest "${extra[@]}" --test-dir "$dir" --output-on-failure -j "${JOBS:-2}" \
    -R '(research_system_|_KAT$|_SELFTEST$|test_nistapi_|test_threadsafety_|test_prng$|test_prng_kat$|test_ctrdrbg_kat$|test_shake256$)'
if [[ "$profile" != BASELINE ]]; then
    tmp=$(mktemp)
    trap 'rm -f "$tmp"' EXIT
    "$dir/research/primitive_test" > "$tmp"
    python3 research/oracle.py "$tmp" "$profile"
fi
python3 research/check_transcript.py "$profile" "$mode"
python3 research/check.py --profile "$profile" --mode "$mode"

# This fixed DRBG seed selects an empty message in the upstream NIST API demo.
if [[ "$profile" = COMBINED && "$mode" = San ]]; then
    "$dir/apps/example_nistapi_p324_3" --seed=88
fi
