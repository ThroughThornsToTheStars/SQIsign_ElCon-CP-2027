# Reproducing the experiment

The upstream Git tag nist-v3 resolves to 6d017708db403bf83977fa70770fc4f7f9e9ff21. The measured implementation and drivers are pinned to 7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e. Later commits attach evidence and documentation. Run from the research repository root. Public root seeds in the test binaries make the regression signatures reproducible. OS-backed smoke tests intentionally use fresh roots. Work on v1 at 4953a4d9309f62768db907820d8aaa272dc9784e is a separate tree.

## Checkout and build

The local checkout contains both revisions and the upstream KAT files. For another machine, clone the delivered research repository/branch, or transfer the patch series from nist-v3 onto the official tag. Example using a second machine with filesystem access to a copy of this repository:

```sh
git clone --no-local --branch research/v3 /path/to/sqisign-v3-research review
cd review
git switch --detach 7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e
git rev-parse HEAD nist-v3 'nist-v3^{tree}'
git diff --exit-code nist-v3 -- KAT src/mp src/gf src/ec src/hd src/id2iso src/quaternion src/signature src/precomp
```

Linux x86-64, C11 compiler, CMake, Ninja, pkg-config and Python 3 with the standard library. The three modified profiles require Nettle headers/library; the separate oracle uses libgcrypt. OpenSSL CLI is used by the optional independent AES test-root calculation. Versions, hardware, dynamic library hashes and effective compile commands are under results/. For example the Debian/Ubuntu packages include build-essential, cmake, ninja-build, pkg-config, nettle-dev, libgcrypt20 and openssl.

```bash
for p in BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED; do
  bash research/build.sh "$p" Release
  bash research/verify.sh "$p" Release
done
python3 research/check.py
for p in BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED; do
  bash research/build.sh "$p" San
  UBSAN_OPTIONS=print_stacktrace=1 bash research/verify.sh "$p" San
done
```

The last loop enables combined AddressSanitizer and UndefinedBehaviorSanitizer and stops on a UBSan finding. Linux normally also enables LeakSanitizer. For the restricted local run the command was `ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1 JOBS=2 bash research/verify.sh "$p" San`; see TEST_REPORT.md. The CI workflow uses the default leak detection. To run all upstream tests beyond the targeted suite, build all targets before running unfiltered ctest.

The production CMake entry point is e.g. `cmake -S . -B build-lib -DSQISIGN_PROFILE=COMBINED -DCMAKE_BUILD_TYPE=Release`, followed by `cmake --build build-lib`. The system NIST API target uses OS randomness. Drivers named trial_* deliberately link the deterministic test library. In particular they must never be used to generate real keys.

## Independent inputs and regression data

`python3 research/oracle.py` verifies published Streebog-512 and HMAC examples using libgcrypt. For each modified build invoke `build-COMBINED-Release/research/primitive_test > /tmp/sqi-primitive.txt` and `python3 research/oracle.py /tmp/sqi-primitive.txt COMBINED`, substituting the profile as appropriate. The C output uses Nettle. The Python oracle implements the transcript, HMAC padding and 15-byte little-endian counter serialization independently.

The 18 new scheme records in research/vectors/ have two full pk/sk/signed-message examples for each changed profile and parameter set. Produce a separate comparison tree with `python3 research/check.py --create /tmp/new-sqi-vectors` and compare using `diff -r research/vectors /tmp/new-sqi-vectors`. Creation uses exclusive writes. An extra empty-message case is generated in the matrix tests. The official KATs stay in KAT/. To run just the unmodified upstream checkout:

```sh
git worktree add --detach ../sqi-original nist-v3
cd ../sqi-original
cmake -S . -B build-original -G Ninja -DCMAKE_BUILD_TYPE=Release -DSQISIGN_BUILD_TYPE=ref
cmake --build build-original -j6 --target sqisign_test_kat_p324_3 sqisign_test_kat_p500_27 sqisign_test_kat_p664_17
ctest --test-dir build-original -R '_KAT$' --output-on-failure -j3
```

## Timings

Run after builds and tests have finished. Select one allowed logical CPU. Each run takes a fresh result directory; the postprocessor reads the raw CSV.

```sh
python3 research/benchmark.py /tmp/sqi-run-a --blocks 24 --cpu 2
python3 research/summarize.py /tmp/sqi-run-a/raw.csv > /tmp/sqi-run-a/summary.csv
```

Wall-clock times and process RSS depend on the host. The benchmark pins affinity without changing governor, disabling SMT or changing turbo settings. Linux /proc/self/status supplies the process memory counters. Monte Carlo resampling uses a fixed seed. CI runs functionality and instrumented binaries; performance measurements belong to the named local machine.

## Review history

| Stage | Commit | Check and open question at that stage |
|---|---|---|
| 1. Reconstruction | a1c49694f8c597a0f5c485c4da4bad14a912dec2 | Reconstructed official Git tree and commit, verified blob hashes and audited production callers. External integrations untested. |
| 2. Construction | 7a42f288bbde300d69297b7a428a6bceb0b09d2c | Fixed octet formats, domains, truncation and cap. Proof for domain-derived filling and QROM analysis remain open. |
| 3. Implementation | 2dc377e956af7aaeeccec78143783e91dd515256 | Two typed integration points and four CMake profiles. Follow-up 47e7a93 checks digest length at the helper boundary. |
| 4. Verification | 4cd92bf, 09e3537, 4b8bf84, 47e7a93, 7392c66 | Installed the independent oracle, regression fixtures, negative cases and four-verifier matrix. Executed results and limitations in TEST_REPORT.md. |
| 5. Evaluation | d550d5c, measured at 7392c66 | Paired trials and bootstrap postprocessor. See BENCHMARK_REPORT.md for the data and inference limits. |
| 6. CI and review | 3ef213d, final documentation commits | Matrix covers Release and ASan+UBSan. External Actions execution requires publishing this branch. Machine-code side-channel finding in SECURITY_LIMITATIONS.md. |

Use `git log --reverse --format='%H %s' nist-v3..HEAD` and `git diff --name-status nist-v3..HEAD` to list the full hashes and changed paths.

The executed test archive is commit 0292a2d04764f5eae575b0d84bdc42526e8b8df9. Raw measurements, all 12 executable hashes, build caches, compile commands and the benchmark report are commit 22a77efeb57061a1236e451dcbe9469fd1a77861. The final documentation commit adds the verification of a clean rebuild and this index. Reports and the offline bundle describe a local branch; no remote push is needed for reproduction.

For the clean rebuild check, in a fresh clone at the measured revision configure each profile with the same Release options as research/build.sh, build target trial_p324_3, and run the following, substituting the actual profile name. Compare output with results/tests/clean-rebuild.txt from the evidence branch.

```sh
build-BASELINE-Release/research/trial_p324_3 vector 1 | sha256sum
```

## File inventory relative to the official tag

    .cmake/flags.cmake
    .github/workflows/research-profiles.yml
    .gitignore
    ARCHITECTURE.md
    BENCHMARK_REPORT.md
    CMakeLists.txt
    CRYPTO_PROFILE.md
    REPRODUCIBILITY.md
    SECURITY_LIMITATIONS.md
    TEST_REPORT.md
    research/CMakeLists.txt
    research/benchmark.py
    research/build.sh
    research/check.py
    research/oracle.py
    research/primitive_test.c
    research/summarize.py
    research/trial.c
    research/vectors/COMBINED/PQCsignKAT_270_SQIsign_p324_3.rsp
    research/vectors/COMBINED/PQCsignKAT_417_SQIsign_p500_27.rsp
    research/vectors/COMBINED/PQCsignKAT_549_SQIsign_p664_17.rsp
    research/vectors/RUSSIAN_PRNG/PQCsignKAT_270_SQIsign_p324_3.rsp
    research/vectors/RUSSIAN_PRNG/PQCsignKAT_417_SQIsign_p500_27.rsp
    research/vectors/RUSSIAN_PRNG/PQCsignKAT_549_SQIsign_p664_17.rsp
    research/vectors/STREEBOG_HASH/PQCsignKAT_270_SQIsign_p324_3.rsp
    research/vectors/STREEBOG_HASH/PQCsignKAT_417_SQIsign_p500_27.rsp
    research/vectors/STREEBOG_HASH/PQCsignKAT_549_SQIsign_p664_17.rsp
    research/verify.sh
    results/host.txt
    results/run-7392c66/BASELINE-CMakeCache.txt
    results/run-7392c66/BASELINE-compile_commands.json
    results/run-7392c66/COMBINED-CMakeCache.txt
    results/run-7392c66/COMBINED-compile_commands.json
    results/run-7392c66/RUSSIAN_PRNG-CMakeCache.txt
    results/run-7392c66/RUSSIAN_PRNG-compile_commands.json
    results/run-7392c66/STREEBOG_HASH-CMakeCache.txt
    results/run-7392c66/STREEBOG_HASH-compile_commands.json
    results/run-7392c66/metadata.json
    results/run-7392c66/raw.csv
    results/run-7392c66/summary.csv
    results/security.txt
    results/tests/BASELINE.Release.ctest.txt
    results/tests/BASELINE.Release.log
    results/tests/BASELINE.San.ctest.txt
    results/tests/BASELINE.San.log
    results/tests/BASELINE.prelim
    results/tests/COMBINED.Release.ctest.txt
    results/tests/COMBINED.Release.log
    results/tests/COMBINED.San.ctest.txt
    results/tests/COMBINED.San.log
    results/tests/COMBINED.prelim
    results/tests/RUSSIAN_PRNG.Release.ctest.txt
    results/tests/RUSSIAN_PRNG.Release.log
    results/tests/RUSSIAN_PRNG.San.ctest.txt
    results/tests/RUSSIAN_PRNG.San.log
    results/tests/STREEBOG_HASH.Release.ctest.txt
    results/tests/STREEBOG_HASH.Release.log
    results/tests/STREEBOG_HASH.San.ctest.txt
    results/tests/STREEBOG_HASH.San.log
    results/tests/clean-rebuild.txt
    results/tests/gcc-analyzer.txt
    results/tests/initial-LSan.log
    results/tests/linkage.txt
    results/tests/matrix.log
    results/tests/tree-and-kats.txt
    results/tests/upstream-KAT.log
    src/common/generic/CMakeLists.txt
    src/common/generic/include/prng.h
    src/common/generic/include/research_profile.h
    src/common/generic/prng.c
    src/common/generic/research_profile.c
    src/common/generic/test/CMakeLists.txt
    src/common/generic/test/test_prng.c
    src/common/generic/test/test_prng_kat.c
    src/verification/ref/lvlx/common.c
    test/CMakeLists.txt
    test/test_kat.c
