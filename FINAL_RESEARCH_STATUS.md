# Final research status

**Adaptation of the symmetric components of SQIsign 3.0 using Russian cryptographic standards and evaluation of its efficiency.**

Review date 2026-11-20. First review branch `ieee/v3`. The delivery containing the independent replication is `ieee/reviewer-validation`. The research implementation and experimental exhibits are available for independent review. Concrete security of the keyed construction and side-channel safety remain open.

## Source chain

| Item | Commit |
|---|---|
| Official SQIsign nist-v3 | `6d017708db403bf83977fa70770fc4f7f9e9ff21` |
| Historical experiment, 288 trials | `7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e` |
| Published v3 at review, clean initial tree `4f7231a6f393cf4bd256599700fba273d3a2a134` | `d190b204b3650355c029f2bf2ac6e6191f8526cc` |
| Capture published research CI and initial file inventory | `013413145bf3e47b25a1e5161c3f3a15a27980cd` |
| Add domain initialization measurement and memory sampling | `3970946106de1b9b56be823280bc86eef8ebf772` |
| Add balanced sessions, telemetry and hosted LSan control | `46f9e07b15985091d0550dbd4622e17c858520c9` |
| NIST demo fix, local tested binaries and new measurement revision | `3b0795caf383a67c96839be346f7bd1c464bc2e9` |
| Crypto argument, source-to-binary Nettle review | `3f4c0f408288ff1dadda67dcf7e64aaa9fd2af67` |
| Reviewer guide, comparison, analysis program and references | `a338d8a87763148622fd405a92d9d6b448df6e8d` |
| Targeted empty-message regression and CI error capture | `bd2a9739f66b00f4f6f724e36fc63ae8f1853e14` |
| Eight test configurations and original hosted status | `0f5e881cca291203c5c681f130338f17f1a88dd9` |
| New raw data, statistics and exhibits | `b06811ba5244da61b4e746790bf39af8d2ecc1fb` |

The earlier empty working commit `9fa984d83661dcf8f9f5d321f2920ca76c2f9b18` contains no evidence. The next commit added the evidence files. Final status and any subsequent validation commits can be identified with `git rev-parse HEAD` and `git log d190b20..HEAD`. [Initial published diff against nist-v3](results/ieee-audit/initial-changes.tsv) · [Reviewer-branch file list](results/ieee-audit/changed-files.tsv)

## Work inherited at the start of the validation pass

The published v3 already had four build profiles, local operation-root handling and domain separation, fixed-width Streebog challenges, 18 changed-profile scheme records, a libgcrypt oracle, a targeted CI matrix and a 24-block experiment. The original official KAT files and arithmetic are present. The reviewer work retained those implementations, historical raw numbers, checksums, test logs and pinned sources. Direct Git comparison against nist-v3 covered KAT, mp, gf, ec, hd, id2iso, quaternion, signature, precomp and nistapi. Through baee298 the reviewer work changed no file under src/. The subsequent API correction at 028187e changes only src/sqisign.c within that directory. The change under apps/ fixes the example used in testing.

The inherited README and obsolete checkout path were replaced, test selection was counted explicitly, the published workflow was verified through the GitHub API, and memory and timing measurements now have separate process modes. UBSan reproduced the zero-length VLA in the original example with seed 88. Fixed storage and a check against the original message length also close a false-success path for a recovered-message mismatch. The independent security review identified a concrete table-address dependency on secret state, and distinguishes the counter mechanism from the application-specific HMAC initialization. [Test report](TEST_REPORT.md) · [Security argument](SECURITY_ARGUMENT.md)

## Earlier commands and measurement provenance

The remote branch and workflow were read through the public GitHub connector after the literal HTTPS clone failed DNS resolution. The local `origin/v3` object matched the published SHA and tree. A fresh linked worktree started from that object. The comparison commands and portable build commands appear in [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

- Eight configurations used `bash research/build.sh "$p" "$mode"`. The build helper passes the exact profile, ref arithmetic, 64-bit radix, generator and build flags. Verification used `JOBS=2 bash research/verify.sh "$p" Release` and `ASAN_OPTIONS=detect_leaks=0 UBSAN_OPTIONS=print_stacktrace=1 JOBS=2 bash research/verify.sh "$p" San`. The archived configuration files and logs include the initial target builds and incremental rebuild after the demo change. All eight target builds were checked again after measurement.
- Ran `python3 research/oracle.py`, per-profile C-oracle comparisons, `python3 research/check.py` and `python3 research/check.py --create "$tmp_vectors"` followed by `diff -r research/vectors "$tmp_vectors"`. The regenerated records were byte-identical. COMBINED/San also repeated its updated verification script including seed 88. [Repeat verification](results/ieee-audit/final-combined-san.log) · [Regeneration](results/ieee-audit/regenerate.log)
- Ran `bash research/inspect-nettle.sh` and `bash research/lsan-probe.sh`. The latter produced the recorded local runtime failure. The former used a deterministic public test input and the installed ELF. Nettle 4.0 release tag `nettle_4.0_release_20260205` was resolved to `bf13ee9e5024014cfa6d2fc097923afe087e63ba`. [Binary evidence](results/ieee-audit/nettle-binary.txt) · [Threat model](SECURITY_LIMITATIONS.md)
- In a detached worktree at the measurement SHA, four Release build directories pointed to the tested binaries of that revision. For i = 1,2,3 executed `python3 research/session.py OUTPUT/session-$i --session "$i" --blocks 16 --cpu 2`. Each session fingerprinted all 12 drivers and its configuration files. [New raw sessions](results/controlled/)
- Executed `python3 research/analyze_sessions.py results/controlled FRESH_OUTPUT` and checked the derived files and paper exhibits. An independent standard-library calculation matched all 132 metric cells for means, medians, sample SDs, paired mean differences and ratios and all 12 rounded TeX rows. The executable and configuration hashes in all three sessions matched the actual builds and archived decompressed build files. Re-running `python3 research/summarize.py results/run-7392c66/raw.csv` reproduced the historical summary byte-for-byte.

## Results archived before the validation pass

All four profiles built in both modes. The selected first-pass matrix passed 149 CTests across eight configurations with 47 registrations each. BASELINE Release passed 300 original records. BASELINE/San ran three original records directly. Each changed profile ran six committed custom records per mode. The independent implementation checked the primitive outputs and the Release cross-profile matrix made 144 verifier decisions plus 108 negative tests. The historical public workflow succeeded in nine jobs at the published SHA. The amended workflow has only local validation until it runs on a hosted runner. [Tests and exclusions](TEST_REPORT.md)

The new experiment contains 576 timings from 48 complete blocks, 144 untimed operation-boundary memory snapshots and per-session telemetry. For p500_27, COMBINED vs BASELINE mean signing time changed by +5.414 ms (+2.55%, pointwise paired 95% interval −4.36% to +10.17%). The older +15.84% estimate remains archived. On the same set, generating stream bytes cost 29.291 vs 4.718 ns/B; key-domain init+clear cost 5.750 vs 0.095 µs. The measurements cover the reference C implementation and the specified GNU Nettle build. The literature comparison covers four Hypericum sets and gives their per-key budgets. Its published latency example is identified separately as an earlier prototype. [Benchmark report](BENCHMARK_REPORT.md) · [Hypericum comparison](HYPERICUM_COMPARISON.md)

## Open review items

1. Establish whether the derived secret fillings satisfy the intended model of R 1323565.1.006-2017. Quantify multi-root and related-counter security including use of the same public hash, per-domain budgets and permitted entropy loss. A standards-based primitive and successful KATs do not settle this.
2. Review the concrete oracle instantiation and key/commitment encodings against the assumptions and query bounds of SQIsign theorem 8.1.7, including any separate quantum-model claim. Runtime tests cover representative transcripts and signed messages.
3. Independently assess the keyed backend on the intended deployment CPU. Machine code establishes secret-indexed loads. Leakage magnitude and practical exploitability have no measurement here. Exposure of a domain key allows replay, and artificial exhaustion can leave higher-level retry loops live. A candidate Botan accelerated implementation requires CPU features absent on this system.
4. Obtain hosted LSan evidence with the positive control in the new workflow. Other architectures, liboqs/MCU, and quantitative leakage assessment remain outside the tested platform. An external host replication would establish how far the timing estimates generalize. Process RSS snapshots cannot identify transient per-routine allocation peaks.
5. The [registered abstract](paper/REGISTERED_ABSTRACT.txt) is archived verbatim. Manuscript drafting and its IEEEtran build were deferred at the author's request. The organizer's 2027 page-limit instructions require confirmation before submission.

## Evidence available by planned section (manuscript deferred)

| Section | Material available |
|---|---|
| I | Registered title, study scope, verified upstream identity and rationale for two independent factors |
| II | Audited architecture, fixed-width encodings, integration boundaries and parameter table |
| III | Exact algorithms, implementation, four builds and byte-level evidence |
| IV | Conditional security argument, confirmed binary limitation and measured interoperability; expert review open |
| V | Two distinct timing series, independent recalculation, phase memory, selected Hypericum literature; cross-scheme latency ranking unavailable |
| VI | Evidence permits a limited conclusion on functionality, sizes and measured costs; production and equivalence claims unsupported |

[Claim-to-source map](paper/EVIDENCE_MAP.md) · [Generated TeX table](paper/results_tables.tex) · [Figure](paper/figures/signing.pdf) · [Bibliography](paper/references.bib)

## Clean transfer and broader verification

A bundle of b06811ba5244da61b4e746790bf39af8d2ecc1fb was cloned with the portable command in REPRODUCIBILITY.md into a new temporary checkout. There, building all four Release profiles and running the verification scripts passed 76/76 selected CTests, the matrix, and the independent primitive comparisons. The complete regenerated analysis directory matched via recursive diff. A separate unfiltered COMBINED Release run passed **47/47** registered tests including every arithmetic test for that build. These additional runs overlap the initial counts. The final delivery adds their logs and review notes to the tested tree. [Full suite](results/ieee-audit/full-combined-release.log) · [Clean matrix](results/ieee-audit/clean-matrix.log)
