#!/usr/bin/env bash
# Inspect the checked x86-64 distro build. No secret input or cache observations.
set -euo pipefail
driver=build-RUSSIAN_PRNG-Release/research/trial_p324_3
library=$(ldd "$driver" | awk '$1 ~ /^libnettle\.so/ {print $3}')
test -f "$library"
pkg-config --modversion nettle
sha256sum "$library" "$driver"
readelf -d "$driver" | rg 'NEEDED|BIND_NOW|FLAGS'
trace=$(mktemp)
trap 'rm -f "$trace"' EXIT
LD_DEBUG=bindings "$driver" vector 1 >/dev/null 2>"$trace"
rg 'binding file .*trial_p324_3.*nettle.*streebog' "$trace" | sed -E 's/^[[:space:]]*[0-9]+:[[:space:]]*//'
if [[ $(sha256sum "$library" | cut -d' ' -f1) == 5cfa2daa591d62161d2f26aa4b8347e3704da1b830e9aba0a312ed1b5f0c7a38 ]]; then
  for symbol in nettle_streebog512_digest nettle_hmac_streebog512_update nettle_hmac_streebog512_set_key; do
    objdump -d --disassemble="$symbol" "$library"
  done
  objdump -d --start-address=0x27f90 --stop-address=0x27ffa "$library"
fi
