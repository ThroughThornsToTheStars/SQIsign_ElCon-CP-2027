# Reproducing the v3 experiment

## Acquire the source

```sh
git clone -b v3 https://github.com/handofgod666/SQIsign_ElCon-CP-2027.git
cd SQIsign_ElCon-CP-2027
git rev-parse HEAD
```

The published tree reviewed here is `d190b204b3650355c029f2bf2ac6e6191f8526cc`. The new work is delivered on branch `ieee/v3` in the review bundle. To acquire it offline, from the directory containing the supplied bundle, use a fresh destination:

```sh
git clone -b ieee/v3 sqisign-ieee-review.bundle review
cd review
git rev-parse HEAD
git diff --exit-code 6d017708db403bf83977fa70770fc4f7f9e9ff21 HEAD -- KAT src/mp src/gf src/ec src/hd src/id2iso src/quaternion src/signature src/precomp src/nistapi
```

Alternatively fetch the named review branch into the published clone and switch to it. All commands below assume the repository root. The source tag is also available from the [official repository](https://github.com/SQISign/the-sqisign/tree/6d017708db403bf83977fa70770fc4f7f9e9ff21). The executed DNS-limited checkout and clean-clone checks are recorded in [final status](FINAL_RESEARCH_STATUS.md).

## Toolchain and tests

On Debian/Ubuntu the packages include build-essential, cmake, ninja-build, pkg-config, nettle-dev, libgcrypt20, openssl and python3. The reference build on the measurement host uses GCC 16.2.1, Nettle 4.0 and Linux x86-64. Python/ctypes calls libgcrypt for the oracle. The benchmark analysis additionally uses python3-numpy and python3-matplotlib. The optional binary inspection script uses GNU binutils, ldd and ripgrep.

```bash
set -e
for p in BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED; do
  bash research/build.sh "$p" Release
  bash research/verify.sh "$p" Release
done
python3 research/oracle.py
python3 research/check.py
for p in BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED; do
  bash research/build.sh "$p" San
  ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=print_stacktrace=1 bash research/verify.sh "$p" San
done
bash research/lsan-probe.sh
bash research/inspect-nettle.sh
```

The LSan positive control intentionally leaks a small allocation. The script checks that LSan reports it and returns the configured error code. In the local sandbox this probe failed at runtime. The locally executed San runs used `ASAN_OPTIONS=detect_leaks=0` and fail-fast UBSan. The independent oracle also runs inside each modified-profile verification. To inventory the broader upstream suite use `ctest --test-dir build-COMBINED-San --show-only=json-v1`; the build helper selects targets for the documented test suite. Full registration and execution counts are in TEST_REPORT.md.

To test fixture generation without touching the repository files:

```sh
tmp_vectors=$(mktemp -d)
python3 research/check.py --create "$tmp_vectors"
diff -r research/vectors "$tmp_vectors"
```

## Timing revisions

The 288 historical measurements used `7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e`. Read them from the current results tree. To rerun the historical driver, check out that SHA in a clean worktree, build the four Release profiles there, then run `python3 research/benchmark.py /tmp/sqi-historical-new --blocks 24 --cpu 2` and `python3 research/summarize.py /tmp/sqi-historical-new/raw.csv`. Create a fresh output directory name each time. The committed old raw data, hashes, CMake caches and compile commands remain in [the historical archive](results/run-7392c66/).

The follow-up timing revision is `3b0795caf383a67c96839be346f7bd1c464bc2e9`. Choose a logical CPU allowed by `python3 -c 'import os; print(sorted(os.sched_getaffinity(0)))'`. CPU 2 was selected on the reference host. Use a new output parent outside the source checkout and finish compilation and tests before the timed sessions.

```sh
git worktree add --detach ../sqi-study-src 3b0795caf383a67c96839be346f7bd1c464bc2e9
(
  set -e
  cd ../sqi-study-src
  for p in BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED; do bash research/build.sh "$p" Release; done
  for i in 1 2 3; do
    python3 research/session.py "../sqi-repeat/session-$i" --session "$i" --blocks 16 --cpu 2
  done
)
python3 research/analyze_sessions.py ../sqi-repeat ../sqi-repeat-analysis
```

To recompute the supplied controlled-session tables and figure, use `python3 research/analyze_sessions.py results/controlled /tmp/sqi-derived-new` in the review checkout. The output directory must be fresh. The analysis uses raw observations and metadata, and checks complete profile blocks and executable identity before estimating effects. Use [the benchmark report](BENCHMARK_REPORT.md) to compare units and populations.

## Audit trail

```sh
git log --reverse --format='%H %s' 6d017708db403bf83977fa70770fc4f7f9e9ff21..HEAD
git diff --name-status d190b204b3650355c029f2bf2ac6e6191f8526cc HEAD
git diff --exit-code d190b204b3650355c029f2bf2ac6e6191f8526cc HEAD -- results/run-7392c66 results/tests KAT
```
