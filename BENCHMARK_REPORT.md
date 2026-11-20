# Benchmark results

## Independent replication on the corrected API

The third series used revision `028187e12fda9a984e6ad0a66d491cab2bb04b1d` in a separate clean clone on the same i7-4770HQ. The replication design was committed at `99c8611` and its source pin was updated for the API correction before timing. The three sessions each contain 16 complete paired blocks with four-position rotations. They use new deterministic indices, one discarded warm-up for every profile/set in each session, 576 timed trials and 144 untimed memory snapshots in total. Compilation and verification finished before the first warm-up. The confidence intervals condition on these consecutive sessions on this host. [Prospective plan](results/reviewer-validation/STUDY_PLAN.md) · [Raw observations and telemetry](results/replication-028187e/) · [Build evidence](results/reviewer-validation/)

For p500_27 COMBINED versus BASELINE, mean signing time changed by **-1.48% (pointwise paired 95% interval -8.02% to +5.29%, -3.167 ms)**. The session estimates were +1.58%, +3.54%, -9.15%. Resampling contiguous four-block groups gives -7.54% to +4.52%. The earlier estimates were +15.84% in the historical series and +2.55% in the first controlled series. Each estimate uses its own paired indices. The three series have separate source pins, seeds and operating conditions.

Replication timings below are means of 48 trials per row. RSS is median process VmRSS and HWM is maximum VmHWM in KiB at the post-Verify boundary. FS excludes encoding, stream excludes initialization, and init includes key-domain clear. All 132 metric cells, including sample SDs, medians and paired effects, are archived. [Summary](results/replication-028187e/analysis/summary.csv) · [Memory by phase](results/replication-028187e/analysis/memory_summary.csv) · [Generated table](results/replication-028187e/analysis/results_tables.tex) · [Signing figure](results/replication-028187e/analysis/signing.pdf)

| Set | Profile | KeyGen ms | Sign ms | Verify ms | RSS / HWM KiB | FS µs | Stream ns/B | Init µs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| p324_3 | BASELINE | 20.602 | 58.836 | 8.123 | 2762 / 2808 | 1.319 | 4.562 | 0.097 |
| p324_3 | STREEBOG_HASH | 20.809 | 60.766 | 8.069 | 3128 / 3164 | 4.291 | 4.352 | 0.088 |
| p324_3 | RUSSIAN_PRNG | 21.834 | 61.558 | 8.346 | 3134 / 3160 | 1.338 | 29.051 | 5.590 |
| p324_3 | COMBINED | 21.690 | 61.047 | 8.175 | 3138 / 3156 | 4.323 | 28.766 | 5.532 |
| p500_27 | BASELINE | 80.135 | 214.269 | 24.571 | 2810 / 2856 | 1.935 | 4.401 | 0.101 |
| p500_27 | STREEBOG_HASH | 79.988 | 220.927 | 24.624 | 3184 / 3212 | 4.907 | 4.453 | 0.087 |
| p500_27 | RUSSIAN_PRNG | 81.136 | 208.573 | 24.325 | 3184 / 3220 | 1.943 | 28.443 | 5.404 |
| p500_27 | COMBINED | 80.403 | 211.101 | 24.448 | 3192 / 3212 | 4.857 | 28.843 | 5.547 |
| p664_17 | BASELINE | 134.904 | 411.505 | 46.830 | 2880 / 2924 | 2.084 | 4.484 | 0.097 |
| p664_17 | STREEBOG_HASH | 135.079 | 420.912 | 48.534 | 3248 / 3276 | 5.471 | 4.428 | 0.092 |
| p664_17 | RUSSIAN_PRNG | 132.806 | 416.419 | 48.721 | 3260 / 3288 | 2.168 | 29.789 | 5.644 |
| p664_17 | COMBINED | 131.594 | 406.469 | 46.737 | 3260 / 3280 | 5.497 | 28.421 | 5.611 |

| Session | One-minute load | Sampled logical CPU 2 GHz | SMT sibling 6 busy time |
|---|---:|---:|---:|
| 4 | 2.02–2.83 | 3.283–3.392 | 2.01% |
| 5 | 1.83–1.95 | 3.193–3.392 | 3.22% |
| 6 | 1.59–2.01 | 3.197–3.392 | 5.55% |

Frequency and load samples include the end of warm-up and every completed block. SMT occupancy uses Linux CPU ticks over the timed window. Turbo and shared-host scheduling limit portability of the estimates. Replacing a generator changes the arithmetic sampling workload. The component timings and process memory snapshots therefore support different inferences from whole-signature measurements.

On p500_27 the repeat measured 28.843 ns/B for the COMBINED stream and 4.401 ns/B for BASELINE. Key-domain initialization plus clearing cost 5.547 and 0.101 µs, respectively. The interval for whole-signature latency admits both a reduction and an increase. The reference KeyGen never calls the Fiat–Shamir hash. As a control, toggling only the public hash reproduced the same encoded key pair in all 18 deterministic comparisons at indices 0, 1 and 2. Thus timing differences between these KeyGen conditions can occur even with the same sampled key. The signing comparisons include differences in commitments, challenges and arithmetic work. [Key control](results/reviewer-validation/paired-keys.txt) · [Session estimates](results/replication-028187e/analysis/by_session.csv)

Separate post-Verify snapshots showed 0 KiB of Nettle mappings in BASELINE and 340–368 KiB in the adapted profiles. These pages contribute to the process RSS. End-of-phase snapshots can miss transient peaks. A same-host repetition does not establish portability to other processors or a performance ranking against Hypericum.

## Historical series, 24 blocks

Measured at 7392c66e3e77acd36ee9531e8f965ef0d7bd0c0e on Intel Core i7-4770HQ, Linux x86-64, logical CPU 2. GCC 16.2.1, ref, radix 64, Release with upstream optimization and LTO, Nettle 4.0. A randomized complete block contains all 12 profile/parameter combinations. Each of 24 blocks uses the same trial index for its 12 combinations. Each invocation is a new process; one discarded warm-up per combination preceded the run. Order seed 240319. Total 288 timed KeyGen/Sign/Verify triples. The timed calls use the test AES CTR-DRBG and the normal detached NIST signature API. Tests and compilation finished before timing began. [Raw data](results/run-7392c66/raw.csv) · [Metadata and executable hashes](results/run-7392c66/metadata.json) · [Host](results/host.txt)

Each message contains 64 bytes; its octets and the 48-byte DRBG input are deterministic functions of the trial index. KeyGen, signing and verifying use the generated key and signature in the same process. Changing the PRNG changes sampled keys and commitments even with identical initial conditions. Changing the hash may also change the work needed for the response. The end-to-end comparison includes these effects. Clock is CLOCK_MONOTONIC. RSS and VmHWM are Linux process-wide counters sampled after verify and before the microbenchmarks. They cover the loaded libraries, stack, heap and code together. Sampling resolution is that of the kernel counters; allocation peaks per subroutine were not measured.

## End-to-end measurements

Arithmetic means in milliseconds. Typical memory is median VmRSS and peak is the maximum reported VmHWM across 24 processes, both in KiB. The last column gives pk/sk/detached signature lengths in bytes as observed by the driver.

| Set | Profile | KeyGen ms | Sign ms | Verify ms | Typical / peak KiB | pk/sk/sig bytes |
|---|---|---:|---:|---:|---:|---:|
| p324_3 | BASELINE | 20.839 | 57.001 | 8.266 | 2772 / 2804 | 83/270/200 |
| p324_3 | STREEBOG_HASH | 20.426 | 59.632 | 8.125 | 3124 / 3160 | 83/270/200 |
| p324_3 | RUSSIAN_PRNG | 21.829 | 59.319 | 8.203 | 3140 / 3160 | 83/270/200 |
| p324_3 | COMBINED | 21.425 | 58.651 | 8.101 | 3134 / 3156 | 83/270/200 |
| p500_27 | BASELINE | 81.151 | 208.595 | 24.614 | 2808 / 2852 | 129/417/306 |
| p500_27 | STREEBOG_HASH | 81.097 | 211.554 | 24.706 | 3180 / 3208 | 129/417/306 |
| p500_27 | RUSSIAN_PRNG | 75.177 | 233.930 | 25.016 | 3186 / 3208 | 129/417/306 |
| p500_27 | COMBINED | 75.304 | 241.627 | 24.625 | 3178 / 3212 | 129/417/306 |
| p664_17 | BASELINE | 127.608 | 397.562 | 47.188 | 2876 / 2924 | 169/549/406 |
| p664_17 | STREEBOG_HASH | 127.718 | 411.032 | 46.955 | 3246 / 3280 | 169/549/406 |
| p664_17 | RUSSIAN_PRNG | 131.906 | 413.652 | 47.053 | 3256 / 3280 | 169/549/406 |
| p664_17 | COMBINED | 133.434 | 430.615 | 47.805 | 3258 / 3276 | 169/549/406 |

## Relative changes

Percent change in the ratio of sample means versus BASELINE, followed by the pointwise 95% paired percentile-bootstrap interval. Each of 10,000 draws resamples complete trial indices with replacement. Standard deviations, medians, extrema and intervals for the other metrics are in [summary.csv](results/run-7392c66/summary.csv). Intervals address trial variation on this run. They do not include between-machine or between-session variation. No multiplicity adjustment. Estimates with intervals spanning zero leave the direction unresolved.

| Set | Profile | KeyGen % [CI] | Sign % [CI] | Verify % [CI] |
|---|---|---:|---:|---:|
| p324_3 | STREEBOG_HASH | -2.0 [-4.3, +0.8] | +4.6 [+0.2, +9.9] | -1.7 [-4.2, +0.8] |
| p324_3 | RUSSIAN_PRNG | +4.7 [-1.1, +10.7] | +4.1 [-0.3, +8.5] | -0.8 [-3.5, +1.9] |
| p324_3 | COMBINED | +2.8 [-2.7, +8.8] | +2.9 [-1.7, +7.7] | -2.0 [-5.7, +1.5] |
| p500_27 | STREEBOG_HASH | -0.1 [-1.2, +1.0] | +1.4 [-5.7, +9.5] | +0.4 [-2.4, +3.5] |
| p500_27 | RUSSIAN_PRNG | -7.4 [-21.3, +10.7] | +12.1 [+1.4, +23.7] | +1.6 [-2.5, +6.8] |
| p500_27 | COMBINED | -7.2 [-21.4, +10.7] | +15.8 [+5.4, +26.5] | +0.0 [-3.1, +3.3] |
| p664_17 | STREEBOG_HASH | +0.1 [-0.6, +0.8] | +3.4 [-3.1, +10.4] | -0.5 [-2.1, +1.2] |
| p664_17 | RUSSIAN_PRNG | +3.4 [-4.5, +12.2] | +4.0 [-4.2, +12.8] | -0.3 [-2.3, +1.8] |
| p664_17 | COMBINED | +4.6 [-3.2, +13.2] | +8.3 [-4.2, +22.0] | +1.3 [-0.4, +3.2] |

Across the nine Verify comparisons, each interval included zero. The p500_27 COMBINED signing mean was 33.032 ms above BASELINE, with a relative interval of +5.4% to +26.5%. The p500_27 RUSSIAN_PRNG signing interval also lay above zero. On p324_3 and p664_17 the COMBINED signing intervals span zero. These are descriptive, pointwise comparisons from a single machine. The larger isolated digest and stream costs cannot by themselves predict signing latency because the sampled arithmetic work varies.

## Isolated component costs

Each trial times 256 challenge hashes of a synthetic fixed-width public prefix and a 64-byte message, and 64 reads of 4096 bytes from a seeded default domain. The first benchmark includes hash initialization/finalization and excludes curve serialization. The second excludes seed/derivation time. Values below are per-call mean microseconds and mean nanoseconds per generated byte. These microbenchmarks use one contiguous stream and do not approximate the distribution of sampler read sizes.

| Set | Profile | Challenge µs | Stream ns/byte |
|---|---|---:|---:|
| p324_3 | BASELINE | 1.305 | 4.557 |
| p324_3 | STREEBOG_HASH | 4.216 | 4.404 |
| p324_3 | RUSSIAN_PRNG | 1.343 | 29.089 |
| p324_3 | COMBINED | 4.347 | 28.693 |
| p500_27 | BASELINE | 1.978 | 4.406 |
| p500_27 | STREEBOG_HASH | 4.897 | 4.379 |
| p500_27 | RUSSIAN_PRNG | 1.945 | 28.556 |
| p500_27 | COMBINED | 4.823 | 28.859 |
| p664_17 | BASELINE | 2.103 | 4.549 |
| p664_17 | STREEBOG_HASH | 5.534 | 4.405 |
| p664_17 | RUSSIAN_PRNG | 2.114 | 28.651 |
| p664_17 | COMBINED | 5.587 | 28.510 |

All results apply to this single local run, using the installed table-based Streebog backend. Thermal state, turbo, SMT siblings and desktop activity were not fixed. Replacing this backend to mitigate the side-channel finding will require fresh measurements. The test RNG eliminates OS entropy latency from the comparison. Original v1 samples are excluded.

## Follow-up series, 48 blocks in three sessions

The new binaries and measurement driver are pinned to `3b0795caf383a67c96839be346f7bd1c464bc2e9`. There are 576 timed trials, three fresh session processes and 36 separate memory processes (four snapshots each). Each session discarded one warm-up trial per combination, then used 16 complete blocks. Within each four-block group, all profiles occupy each position once within each set. The set order is randomized separately in each block. The 48 input indices differ from the historical series. The three sessions ran successively on the same machine and day, with distinct order seeds and warm-ups. Their observations do not estimate between-machine or between-day variance. [Raw sessions, memory snapshots and host telemetry](results/controlled/) · [Measurement driver](research/session.py)

The pilot endpoint was p500_27 COMBINED signing. On the historical pairs let r = mean(A)/mean(B) and B denote BASELINE. The sample standard deviation of (A−rB)/mean(B) was 0.27291. A normal planning approximation for an eight-percentage-point half-width gave (1.96 × 0.27291 / 0.08)² = 44.7 blocks. Rounding up to three balanced sessions gave 48. This criterion estimates precision for this endpoint only. There was no significance-based stopping rule or discarded timed trial.

All timed builds used the i7-4770HQ, GCC 16.2.1, ref/radix 64 and Nettle 4.0. CPU 2 was pinned, SMT sibling 6 remained available, governor schedutil, frequency bounds 0.8–3.4 GHz and turbo enabled. Warm-up-end and block-end samples of CPU 2 ranged from 3.193 to 3.392 GHz. Their one-minute system load ranges by session were 1.61–2.41, 1.48–1.73, and 1.27–1.62. CPU 6 busy time over the timed windows was 6.15%, 7.25%, and 6.92%, calculated as one minus the idle and iowait tick fraction (first eight Linux CPU tick fields). Previous one-minute load started at 5.92 and finished at 2.76. No concurrent compilation occurred in these timed windows. One separate empty-message regression ran during session 1 warm-up and completed before the first timed trial. Affinity, position balancing and monitoring reduce some confounding. This shared desktop offers neither fixed frequency nor exclusive use of the physical core.

### Operation and component means

Each row has 48 timed operations. Memory shows median process VmRSS / maximum process VmHWM in KiB after verification. FS is microseconds per synthetic challenge hash excluding field encoding. Stream is ns per byte in 64 sequential reads of 4096 bytes. Init is microseconds per key-domain initialization **and clear** with an already initialized root, over 256 calls. It excludes OS entropy acquisition. Measurement includes the relevant library calls. [All statistics and bounds](results/controlled/analysis/summary.csv) · [Per-session estimates](results/controlled/analysis/by_session.csv)

| Set | Profile | KeyGen ms | Sign ms | Verify ms | RSS / HWM KiB | FS µs | Stream ns/B | Init µs |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| p324_3 | BASELINE | 21.199 | 58.414 | 8.185 | 2760 / 2804 | 1.331 | 4.530 | 0.096 |
| p324_3 | STREEBOG_HASH | 20.946 | 60.755 | 8.520 | 3132 / 3160 | 4.564 | 4.690 | 0.090 |
| p324_3 | RUSSIAN_PRNG | 21.849 | 60.626 | 8.059 | 3142 / 3160 | 1.366 | 28.989 | 5.594 |
| p324_3 | COMBINED | 21.986 | 59.433 | 8.179 | 3136 / 3160 | 4.249 | 28.810 | 5.685 |
| p500_27 | BASELINE | 85.560 | 212.428 | 24.632 | 2806 / 2852 | 2.025 | 4.718 | 0.095 |
| p500_27 | STREEBOG_HASH | 84.545 | 222.183 | 24.965 | 3180 / 3216 | 5.107 | 4.639 | 0.086 |
| p500_27 | RUSSIAN_PRNG | 81.287 | 215.143 | 24.133 | 3188 / 3212 | 1.992 | 29.248 | 5.694 |
| p500_27 | COMBINED | 81.105 | 217.842 | 24.869 | 3184 / 3212 | 4.885 | 29.291 | 5.750 |
| p664_17 | BASELINE | 143.857 | 408.460 | 47.382 | 2876 / 2916 | 2.142 | 4.450 | 0.098 |
| p664_17 | STREEBOG_HASH | 142.812 | 390.061 | 46.942 | 3248 / 3284 | 5.671 | 4.611 | 0.088 |
| p664_17 | RUSSIAN_PRNG | 132.236 | 403.905 | 47.532 | 3260 / 3280 | 2.084 | 28.864 | 5.530 |
| p664_17 | COMBINED | 131.853 | 401.509 | 47.027 | 3258 / 3284 | 5.584 | 29.036 | 5.584 |

The follow-up ratio of mean signing times for COMBINED vs BASELINE on p500_27 was **+2.55%** (217.842 vs 212.428 ms, +5.414 ms), with a pointwise paired 95% interval of **−4.36% to +10.17%**. Individual sessions gave +5.50%, −2.69% and +4.88%. The historical estimate remains **+15.84%** with an interval of +5.4% to +26.5%. The new data leave the direction unresolved. Neither equivalence nor a persistent 15.8% penalty is established. Changed seeds, shared-host conditions and changed sampled arithmetic workloads preclude assigning this discrepancy to a single cause. The isolated stream and domain initialization costs increased materially under the Nettle generator even when whole-signature effects were uncertain.

The analysis resamples complete paired indices within each session 10,000 times with NumPy seed 616, using the 2.5th and 97.5th percentiles. Each metric has mean, median, sample SD, extrema, interval for its mean, absolute paired difference of means with interval, and change in the ratio of means with interval. As a sensitivity check, contiguous four-block rotation groups were resampled within sessions. For the p500_27 contrast that interval was −4.47% to +9.98%. The intervals condition on these sessions, are pointwise across metrics and use no multiplicity correction. [Analysis](research/analyze_sessions.py) · [Signing figure](paper/figures/signing.pdf)

### Memory interpretation

The timed process counters include executable and shared-library mappings, heap, stack and runtime. A fresh, separately executed driver also read /proc/self/smaps before KeyGen and after each of KeyGen, Sign and Verify. It summed mapping RSS, Nettle-mapping RSS and Private_Clean + Private_Dirty. The scan itself can fault in pages. Endpoints accumulate earlier effects and omit transient allocations released inside an operation. Each profile/set/phase has three snapshots. After Verify, baseline Nettle-mapping RSS was zero. In modified profiles those mappings accounted for 336–368 KiB depending on process. For example, p500_27 median timed VmRSS was 2,806 KiB baseline and 3,184 KiB COMBINED. These process-level differences include loader, code and allocator effects. No isolated allocation-peak claim follows. [Memory endpoint statistics](results/controlled/analysis/memory_summary.csv)

Secret/public key and signature encodings are unchanged across the 576 trials. The observed public/secret/signature lengths in bytes are 83/270/200, 129/417/306 and 169/549/406. Source-fixed byte lengths have no sampling uncertainty here.
