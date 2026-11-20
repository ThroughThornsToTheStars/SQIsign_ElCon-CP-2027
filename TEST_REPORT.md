# Verification evidence

Upstream revision 6d017708db403bf83977fa70770fc4f7f9e9ff21. The historical local runs used 7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e on x86-64 Linux, ref, 64-bit radix, GCC 16.2.1. Commands in REPRODUCIBILITY.md. The measured reference code, release fixtures and CI script are in the same revision.

## API and transcript validation, 028187e

The clean Release clone and the updated ASan+UBSan builds used the same integration source at `028187e12fda9a984e6ad0a66d491cab2bb04b1d`. Against the prior inventory, three added CTest cases inject entropy-provider failure through the public API, one per parameter set. Each case checks that failed KeyGen leaves both output buffers intact, that a subsequent KeyGen can succeed, and that a failed detached Sign on that valid key returns an error and zero length. These cases passed in every profile and mode. The NIST API and the algebraic protocols retain their upstream sources. The early return belongs to the public wrapper in src/sqisign.c.

| Profile | Release registered / selected / passed | San registered / selected / passed | Complete scheme KAT records, Release / San |
|---|---:|---:|---|
| BASELINE | 50 / 22 / 22 | 50 / 19 / 19 | 300 original / 3 original, directly invoked |
| STREEBOG_HASH | 50 / 22 / 22 | 50 / 22 / 22 | 6 custom / 6 custom |
| RUSSIAN_PRNG | 50 / 22 / 22 | 50 / 22 / 22 | 6 custom / 6 custom |
| COMBINED | 50 / 22 / 22 | 50 / 22 / 22 | 6 custom / 6 custom |

The selected matrix passed 173/173 cases from 400 registrations across eight directories. It left 227 registrations unselected. Local sanitizer runs used `ASAN_OPTIONS=detect_leaks=0`; the positive LSan control failed under the local runtime restriction. Rechecking the published research workflow returned nine successful jobs at d190b204. The changed reviewer branch has local evidence only. [Individual test inventory](results/reviewer-validation/ctest-inventory.csv) · [Commands and build evidence](results/reviewer-validation/) · [Hosted job results](results/reviewer-validation/published-actions.json)

The separate unfiltered COMBINED Release run passed **50/50** in 272.05 s. It covers all 28 tests unselected for that build in the targeted matrix. The other seven configurations retain their selected coverage. [Full CTest log](results/reviewer-validation/full-combined-release.txt)

Alongside CTest, the actual typed challenge caller was exercised at all three widths with two ordered pairs of normalized curves drawn from official keys. Empty inputs, embedded zero octets, and lengths immediately before, at, and after the hash-block boundary were included. The independently computed full scalar matched in 288 cases (36 per build). Regression fixtures agreed byte-for-byte after regeneration. The Release matrix made the expected 144 signer/verifier decisions (72 accepted, 72 rejected) and passed all 108 additional negatives. Each modified build also compared respectively 6, 8 or 11 emitted primitive records against libgcrypt. These counts describe separate checks. [Typed adapter](research/transcript_test.c) · [Independent wire encoder](research/check_transcript.py) · [Cross-profile output](results/reviewer-validation/cross-profile.txt)

The former oracle printed success on empty COMBINED output under optimized Python. The corrected oracle accepted all 11 valid records and rejected an empty file, a duplicate label, and a changed digest under both ordinary Python and `python3 -O`. The historical comparisons had been run under ordinary Python. [Oracle regression evidence](results/reviewer-validation/oracle-regression.txt)

## Historical results at 7392c66

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
* The targeted suite ran on Linux x86-64 with the reference arithmetic. Exhaustive verification of every malformed encoding, other toolchains, big-endian/32-bit/assembly targets, liboqs, MCU integration and the entire upstream arithmetic test suite were outside the executed matrix. The hosted status for the later published revision is recorded below. Functional evidence does not establish unforgeability or quantum security.

A fresh non-local Git clone at 7392c66 independently configured each profile with ref, radix 64, Release, Ninja and the research drivers enabled. Building only trial_p324_3 and running vector 1 in each profile reproduced the measured build's complete pk ∥ sk ∥ signature output byte-for-byte. The hashes cover public regression material. [Clean rebuild](results/tests/clean-rebuild.txt)

## Independent reviewer rerun

A clean linked worktree was created from the verified public v3 tree. The binaries used the reference integration and drivers at `3b0795caf383a67c96839be346f7bd1c464bc2e9`; the NIST demo was incrementally rebuilt for that fix before its suite. All eight build configurations and selected verification scripts completed on x86-64, GCC 16.2.1 and Nettle 4.0. Each build registered 47 tests. The table counts CTest cases separately from standalone KAT records, oracle computations and verifier invocations. [Build logs, CMake options, commands and test logs](results/ieee-audit/) · [Every registration with execution outcome](results/ieee-audit/ctest-inventory.csv)

| Profile | Release registered / run / passed | San registered / run / passed | KAT records in Release / San |
|---|---:|---:|---|
| BASELINE | 47 / 19 / 19 | 47 / 16 / 16 | 300 original / 3 original run directly (record 0 per set) |
| STREEBOG_HASH | 47 / 19 / 19 | 47 / 19 / 19 | 6 profile / 6 profile |
| RUSSIAN_PRNG | 47 / 19 / 19 | 47 / 19 / 19 | 6 profile / 6 profile |
| COMBINED | 47 / 19 / 19 | 47 / 19 / 19 | 6 profile / 6 profile |

Thus 149 of 376 CTest registrations across build directories ran and passed. Per directory, 28 were unselected, or 31 for instrumented BASELINE. They include upstream arithmetic and ancillary tests. The direct official KAT subset covers 3/300 instrumented records. The three changed profiles each checked two complete published fixtures per set in both modes. Each mode also checked 6, 8 or 11 primitive records for hash, PRNG or combined, respectively. These include RFC examples and profile-specific comparisons with an independently programmed libgcrypt oracle. The Release cross-profile matrix repeated the 144 pair decisions and 108 additional negative verifications with zero mismatches. [Cross-profile decisions](results/ieee-audit/cross.log) · [Oracle anchors](results/ieee-audit/oracle.log)

The example program had two problems identifiable in source. Its random zero-length message could create a zero-sized VLA in C, and a recovered-message mismatch with a successful API return could propagate success to CTest. The current example uses fixed storage for the 0–99 byte domain, compares the logical length and propagates failure. The deterministic demo seed 88 reproduced the zero-length UBSan error in the older COMBINED binary. The corrected sanitized example signed an empty message, recovered it and rejected the altered signature. This additional check runs outside the CTest count. [Before/after output](results/ieee-audit/empty-regression.log) · [Example](apps/example_nistapi.c)

Published v3 commit `d190b204b3650355c029f2bf2ac6e6191f8526cc` completed eight profile/mode jobs and the compatibility job. The hosted COMBINED/San log shows 19 cases and Ubuntu Nettle 3.9.1. The two other inherited workflow runs were queued at the status check. The nine-job result concerns the published research workflow. The reviewer branch adds an explicit LSan positive control, enables leak detection in hosted San tests and uploads configuration and CTest diagnostics. Its new workflow requires execution on a hosted runner. The historical runner had no positive control, and the local positive control failed due to the ptrace restriction. Local ASan/UBSan results therefore exclude leak detection and the distro library internals. [Published Actions run](https://github.com/handofgod666/SQIsign_ElCon-CP-2027/actions/runs/44710158504) · [Job evidence](results/ieee-audit/github-published.json) · [Local probe](results/ieee-audit/local-lsan.log)

### Additional unfiltered and clean-clone verification

At the data/evidence revision b06811ba5244da61b4e746790bf39af8d2ecc1fb, all targets of COMBINED Release were built, and unfiltered CTest ran **47 registered / 47 executed / 47 passed** in 366.26 s with a 240 s per-test deadline and three workers. This second pass also exercised the 28 registrations omitted from its initial targeted run, including field, quaternion, curve, signature, id2iso and CTR-DRBG concurrency tests. Other profile/mode combinations have the targeted coverage above. The supplementary run overlaps 19 prior tests. [Unfiltered log](results/ieee-audit/full-combined-release.log)

An offline bundle at that revision was cloned into a different temporary directory. In that clean clone all four Release profiles were configured and rebuilt from scratch (JOBS=6), and their verification scripts passed (JOBS=3, 19 CTests each). The complete Release compatibility matrix and independent primitive checks passed again. The statistical CSVs, TeX tabular, PDF and input manifest were regenerated with byte-identical output to the committed analysis directory. [Clean matrix](results/ieee-audit/clean-matrix.log) · [Clean build and verification logs](results/ieee-audit/)
