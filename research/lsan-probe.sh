#!/usr/bin/env bash
# An intentional leak in a disposable program verifies the detector itself.
set -eu
dir=$(mktemp -d)
trap 'rm -rf "$dir"' EXIT
cat > "$dir/leak.c" <<'C'
#include <stdlib.h>
__attribute__((noinline)) static void leak(void) {
    void *p = malloc(37);
    __asm__ volatile("" : : "r"(p) : "memory");
}
int main(void) { leak(); return 0; }
C
cc -O0 -g -fsanitize=address "$dir/leak.c" -o "$dir/leak"
rc=0
ASAN_OPTIONS=detect_leaks=1 LSAN_OPTIONS=exitcode=23 "$dir/leak" >"$dir/log" 2>&1 || rc=$?
cat "$dir/log"
test "$rc" = 23 && grep -q '37 byte(s) leaked' "$dir/log"
