# Benchmark results

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
