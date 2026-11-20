# Verification evidence

Upstream revision 6d017708db403bf83977fa70770fc4f7f9e9ff21. Final local runs used 7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e on x86-64 Linux, ref, 64-bit radix, GCC 16.2.1. Commands in REPRODUCIBILITY.md. The measured reference code, release fixtures and CI script are in the same revision.

## Results

| Profile | Release CTest | Combined ASan+UBSan CTest | Independent primitive records checked per build |
|---|---:|---:|---:|
| BASELINE | 19/19 | 16/16 plus three individual KAT records | Upstream SHAKE/DRBG KAT |
| STREEBOG_HASH | 19/19 | 19/19 | 6 |
| RUSSIAN_PRNG | 19/19 | 19/19 | 8 |
| COMBINED | 19/19 | 19/19 | 11 |

The separate pristine-tag run passed all 100 records for each of three parameter sets. BASELINE Release repeated the full 300-record corpus. For each changed profile the upstream KAT reader compared pk, sk, the complete signed message and recovered message against two committed records per set, 18 new records in total. New scheme vectors were frozen from the implementation and replayed in two build modes. They detect regression; their provenance differs from the independently computed primitive answers. [Original run](results/tests/upstream-KAT.log) · [Git objects and official corpus digests](results/tests/tree-and-kats.txt) · [All test logs](results/tests/)

The targeted suites covered the NIST API, OS-backed KeyGen/Sign/Verify, deterministic test RNG, PRNG errors and reseeding, all three parameter sets and parallel-vs-serial thread-safety checks. research/check.py also compared the fixed records byte-for-byte and exercised an empty message. The unchanged SHAKE checks remained active in all profiles. The research generator checks included zero reads, 13+51+128 bytes versus a cloned partial-block cursor, four domain labels, repeated initialization, the last block, partial final consumption, failed oversize requests with unchanged state/output, and rejection after exhaustion. The public helper rejected length 65 without writing.

Nettle 4.0 and a separately assembled Python/libgcrypt 1.12.4 oracle agreed. The anchors were both 512-bit worked examples of RFC 6986 and the HMAC-Streebog-512 example of RFC 7836. The oracle re-encodes the challenge, derives each domain using manual HMAC padding, and encodes the counter in 15 little-endian octets. The high-counter test checks all 64 bytes independently. This establishes the specified byte behavior; the custom stream has no official SQIsign or TK26 profile vector. [RFC 6986 §10](https://www.rfc-editor.org/rfc/rfc6986.html) · [RFC 7836 Appendix B](https://www.rfc-editor.org/rfc/rfc7836.html)

## Cross-profile verification

Observed results below were the same for all three parameter sets and indices 0, 1, 2. For each signer/verifier pair there were 9 distinct set/index combinations using the published deterministic seed schedule. There were 144 decisions, 72 accept and 72 reject. For the 36 generated signatures, verification also rejected every changed challenge, all-zero signature and different message, 108 additional negative checks. [Cross-profile log](results/tests/matrix.log) · [Exact pass/fail predicates](research/check.py)

| Signing profile ↓ / verifying profile → | BASELINE | STREEBOG_HASH | RUSSIAN_PRNG | COMBINED |
|---|---|---|---|---|
| BASELINE | accept | reject | accept | reject |
| STREEBOG_HASH | reject | accept | reject | accept |
| RUSSIAN_PRNG | accept | reject | accept | reject |
| COMBINED | reject | accept | reject | accept |

## Failures, scope and residual risk

* In the first instrumented COMBINED run, LeakSanitizer could not inspect threads in the restricted runtime. The initial failures are retained. The final ASan/UBSan runs disabled leak detection locally; the global sanitizer flags and fail-fast UBSan remained active. Nettle is a distribution binary outside the compiler instrumentation. [Initial LSan run](results/tests/initial-LSan.log) · [Instrumented library linkage](results/tests/linkage.txt)
* Two preliminary Release harness runs overlapped development of the harness or relinking. One shell invocation lost its script position after a change following CTest; in another, three binaries were temporarily unavailable. The final runs used the pinned scripts and complete binaries. [Preliminary baseline log](results/tests/BASELINE.prelim) · [Preliminary combined log](results/tests/COMBINED.prelim)
* GCC -fanalyzer on the combined research backend completed without a diagnostic. A separate review of the installed binary identified state-dependent table addresses in Streebog. An absence of sanitizer diagnostics cannot establish constant time. Valgrind/ctgrind was unavailable locally. [Analyzer invocation](results/tests/gcc-analyzer.txt) · [Security review](SECURITY_LIMITATIONS.md)
* The targeted suite ran on Linux x86-64 with the reference arithmetic. Exhaustive verification of every malformed encoding, other toolchains, big-endian/32-bit/assembly targets, liboqs, MCU integration and the entire upstream arithmetic test suite were outside the executed matrix. The hosted GitHub Actions jobs have not been executed here. Functional evidence does not establish unforgeability or quantum security.

A fresh non-local Git clone at 7392c66 independently configured each profile with ref, radix 64, Release, Ninja and the research drivers enabled. Building only trial_p324_3 and running vector 1 in each profile reproduced the measured build's complete pk ∥ sk ∥ signature output byte-for-byte. The hashes cover public regression material. [Clean rebuild](results/tests/clean-rebuild.txt)
