#!/usr/bin/env bash
set -euo pipefail
profile=${1:?profile}
mode=${2:-Release}
dir="build-${profile}-${mode}"
flags=()
if [[ "$mode" = San ]]; then
    flags+=("-DCMAKE_C_FLAGS=-fsanitize=address,undefined -fno-sanitize-recover=all -fno-omit-frame-pointer -g -DNDEBUG")
fi
cmake -S . -B "$dir" -G Ninja -DSQISIGN_BUILD_TYPE=ref -DGF_RADIX=64 \
    "-DCMAKE_BUILD_TYPE=$mode" "-DSQISIGN_PROFILE=$profile" \
    -DSQISIGN_RESEARCH_TOOLS=ON -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "${flags[@]}"
targets=(sqisign_test_prng sqisign_test_prng_kat sqisign_test_ctrdrbg_kat sqisign_test_shake256)
for variant in p324_3 p500_27 p664_17; do
    targets+=("entropy_failure_$variant" "transcript_$variant" "trial_$variant" "sqisign_test_kat_$variant" "sqisign_test_scheme_$variant" "sqisign_test_threadsafety_$variant" "example_nistapi_$variant" "system_smoke_$variant")
done
if [[ "$profile" != BASELINE ]]; then targets+=(primitive_test); fi
cmake --build "$dir" -j "${JOBS:-4}" --target "${targets[@]}"
