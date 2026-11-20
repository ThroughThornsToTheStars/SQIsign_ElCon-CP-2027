# Final research validation

**Scope.** Linux x86-64 reference arithmetic, radix 64; four symmetric configurations and p324_3, p500_27, p664_17. The implementation freeze candidate is `6d55a8fd75adc47abc8a2b266a3adfd8f4d8a20c` (ieee/reviewer-validation). Its src tree is `79b80994b4f95b92ac58632269ada2a139c7f2d5`, identical to the API-fix revision. The stabilization changes are documentation. The [registered abstract](paper/REGISTERED_ABSTRACT.txt) is preserved.

## Project and evidence map

| Revision | Role |
|---|---|
| [6d017708](https://github.com/SQISign/the-sqisign/tree/6d017708db403bf83977fa70770fc4f7f9e9ff21) | Official nist-v3 tag, checked against the authors' remote. The original KAT corpus, signature arithmetic, curves, quaternion, fields, isogeny translation and precomputation directories match. |
| 7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e | Historical series, 24 randomized blocks, 288 triples; [raw data and build metadata](results/run-7392c66/). |
| 3b0795caf383a67c96839be346f7bd1c464bc2e9 | First controlled series, three sessions of 16 blocks with 12 cases each; [controlled](results/controlled/). |
| 028187e12fda9a984e6ad0a66d491cab2bb04b1d | Key-generation API fix and entropy-failure regression. Second controlled series on the same native machine; [replication](results/replication-028187e/). |
| d190b204b3650355c029f2bf2ac6e6191f8526cc | v3 integration base at review. [PR 1](https://github.com/handofgod666/SQIsign_ElCon-CP-2027/pull/1) at 2af15cd contains separate manuscript and public-vector work. A local git merge-tree simulation with the reviewed candidate preserved all five PR 1 blobs; neither branch was merged. Recheck if either head changes. |

Two build switches select the public hash and the local byte generator. The shared challenge helper preserves the encoded key with hint and the commitment's Montgomery A. The modified branch hashes the application label, one byte of output length, SQI, key, commitment and message, then takes the first 16/24/32 digest bytes in API order. Its scalar interpretation is little-endian. KeyGen and Sign seed the operation root from a 48-byte entropy request. The keyed stream uses truncated HMAC-Streebog-512 derivation and successive Streebog-512 blocks for each label. Baseline retains SHAKE256 in both roles. [Definitions](CRYPTO_PROFILE.md), [implementation](src/common/generic/research_profile.c), [call sites](ARCHITECTURE.md).

At the public API, failed KeyGen returns before either key encoder runs. Failed detached Sign sets the length to zero before returning; the entropy-failure test checks sentinel bytes. The attached signing wrapper stages the message before calling detached Sign, so a zero output length on failure is the contract; a blanket unchanged-buffer guarantee would be inaccurate. The stream capacity check precedes any writes or cursor change. See [error tests](research/entropy_failure.c) and [boundary tests](research/primitive_test.c).

## Local and hosted verification

Fresh clone inside Ubuntu 26.04.1 WSL2, kernel 6.18.58.1-microsoft-standard-WSL2, AMD Ryzen 5 5500U, GCC 15.2.0, CMake 4.2.3, Ninja 1.13.2, GNU Nettle 3.10.2, libgcrypt 1.12.0. Local leak positive control detected exactly 37 bytes, exit 23 as required by the probe. An earlier ptrace-restricted result in [the archive](results/reviewer-validation/lsan-control.txt) pertains to a different run. No WSL timing observations were added to the scientific datasets.

Local clean builds and verification finished successfully in all eight profile/mode combinations. Release passed 22/22 selected CTests per profile (88 executions). Instrumented builds passed 19/19 for BASELINE and 22/22 each for the other three (85 executions). Baseline Release processed 300 official records. Baseline San separately passed count 0 for each set. Every configuration passed 12 typed-transcript comparisons per set. The six modified-profile/mode checks used libgcrypt. The combined sanitizer run also exercised the empty-message API regression. A separate unfiltered COMBINED Release run passed 50/50 registered tests, overlapping the selected suite. The Release compatibility run passed all 144 decisions and 108 negative cases. With identical test seeds, all 18 public/secret key comparisons between same-generator profiles matched. Repeated coverage across modes and suites is reported separately.

GitHub: [run 44812445821](https://github.com/handofgod666/SQIsign_ElCon-CP-2027/actions/runs/44812445821) is a successful push run for the exact implementation commit. Nine completed jobs: eight profile/mode combinations and cross-profile compatibility. All eight evidence archives carried the expected SHA and executed CTest logs. All four San archives contain the 37-byte positive control. Runner ubuntu-24.04, GCC 13.3, CMake 3.31.6, Nettle 3.9.1. Release executed 22 selected CTests per profile, San 22 per modified profile and 19 for baseline plus one official record per set. Official baseline Release KAT exercises 100 records per set. Registered inventory is broader than selected execution. Other workflows (Formatting, CMake and Pedantic) were separately queued when queried; the profile result does not establish their outcome.

Release compatibility expects agreement within the two public-hash families. All 16 profile pairs, three sets and three inputs yield 144 decisions; the 108 mutations are additional checks. Oracle comparisons use libgcrypt for the new primitives and Python SHAKE for the original challenge. Typed transcript tests cover length zero, hash-block boundaries and scalar padding. Scheme-level modified KATs are regression vectors generated by the implementation. The public upstream record from PR 1 independently reproduced its embedded challenge using Python; reconstruction of its commitment used upstream arithmetic.

## Recalculation and interpretation

Endpoint: percentage change in mean Sign latency on p500_27 for COMBINED relative to BASELINE. Times below are arithmetic means in ms, intervals are pointwise 95%. The standalone recalculation grouped raw rows by parameter, profile, session and index and resampled paired indices. No additional benchmarks.

| Series | Triples | Baseline | Combined | Change | Interval |
|---|---:|---:|---:|---:|---:|
| Historical | 288 | 208.595 | 241.627 | +15.84% | [+5.35%, +26.46%] |
| Controlled | 576 | 212.428 | 217.842 | +2.55% | [−4.35%, +10.17%] |
| Replication | 576 | 214.269 | 211.101 | −1.48% | [−8.02%, +5.29%] |

The latter runs used 10,000 paired bootstrap draws stratified by session and recorded quartet sensitivity estimates. Blocks within each session preserve the common index and balanced ordering. Replication session effects were +1.58%, +3.54%, and −9.15%. Neither pooling the three series nor interpreting an interval spanning zero as equivalence is warranted. Historical and controlled outputs differ in design, revision and run conditions. All native measurements used the i7-4770HQ. Durations cover the sampled arithmetic work as well as the primitive calls.

Both controlled analyses regenerated summary/by-session/memory CSVs and TeX tables byte-for-byte; the independent exhibit checker matched 132 metric cells, 12 table rows and the primary interval per series. The historical summary also matched after normalizing line endings. Session input hashes and build manifests agree with the regenerated attestations. Figures regenerated on WSL with different NumPy/Matplotlib versions; the plotting data reproduce, PDF bytes differ. The exhibits in paper/ illustrate the first controlled series. Use the separate replication exhibits when describing sessions 4–6.

## Reproduction

Start from a complete clone containing the pinned upstream history. Check out the implementation by its full SHA shown above. From the repo root on Ubuntu, with GCC, CMake, Ninja, nettle-dev, libgcrypt20, Python, NumPy and Matplotlib available:

~~~sh
set -eu
export ASAN_OPTIONS=detect_leaks=1
bash research/lsan-probe.sh
for mode in Release San; do
  for profile in BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED; do
    bash research/build.sh "$profile" "$mode"
    bash research/verify.sh "$profile" "$mode"
  done
done
python3 research/check.py
cmake --build build-COMBINED-Release -j 3
ctest --test-dir build-COMBINED-Release --output-on-failure -j 3
out=$(mktemp -d)
python3 research/summarize.py results/run-7392c66/raw.csv > "$out/historical.csv"
for s in controlled replication-028187e; do
  python3 research/analyze_sessions.py "results/$s" "$out/$s"
  python3 research/check_exhibits.py "results/$s"
  for f in summary.csv by_session.csv memory_summary.csv results_tables.tex; do
    cmp "results/$s/analysis/$f" "$out/$s/$f"
  done
done
~~~

See [scientific claim boundaries](SCIENTIFIC_CLAIMS.md) and the [freeze decision](RESEARCH_FREEZE_CHECKLIST.md).

**READY FOR MANUSCRIPT.** Within the stated reference-platform, functional and statistical scope, this pass found no outstanding correction required for publication of the experimental findings. Use the tested implementation SHA above and the original data-generating SHA for each timing series.
