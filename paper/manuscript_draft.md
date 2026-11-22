# Adaptation of the symmetric components of SQIsign 3.0 using Russian cryptographic standards and evaluation of its efficiency

**Abstract—** Russian research on post-quantum signatures includes the development of hash-based schemes using domestic primitives, exemplified by Hypericum. The compact isogeny-based signature SQIsign offers a different trade-off between transmitted data size, computational cost, and cryptographic assumptions. This work addresses the design and evaluation of a consistent SQIsign 3.0 profile using Streebog and Russian pseudorandom sequence generation mechanisms. The objective is to assess adaptation costs and the conditions under which compact keys and signatures retain practical value. The profile covers Fiat–Shamir challenge hashing and internal pseudorandom streams. These components are considered separately because their purposes, secrecy requirements, streaming semantics, and effects on compatibility differ. The analysis covers input encodings, output truncation, domain separation, entropy requirements, and the limits of applicability of the original scheme’s security arguments. Experimental comparison of the reference implementation, individual substitutions, and their combination covers key generation, signing, and verification times, and memory consumption. Comparison with selected Hypericum parameter sets accounts for signing limits and differences in security estimates. The contribution comprises a consistent specification of the adaptation of public hashing and secret pseudorandom streams, an analysis of its compatibility and security implications, and an assessment of substitution costs.

## I. Introduction

SQIsign 3.0 uses the same function, the SHAKE256 extendable-output function, to derive the public challenge checked by the verifier and to supply secret pseudorandom bytes during key generation and signing [@sqisign3, Sec. 3.3]. Adapting the scheme to use the Russian hash function Streebog-512 therefore raises two questions. Which change can a signer make while retaining interoperability with an existing verifier? How much does each change cost in computation and memory? We study the two uses separately and in combination so that their effects can be distinguished.

Signature size motivates the choice of SQIsign. Its isogeny-based construction uses an 83-byte public key and a 200-byte signature at parameter set p324_3 [@sqisign3, Table 1]. Hypericum, a Russian stateless hash-based design built on Streebog, uses a 64-byte public key and a 9,772-byte signature in its small-signature set M_128_20, which permits up to 2²⁰ signatures per secret key [@hypericumspec, Sec. 6]. When the recipient already has the public key, the signature accounts for the authentication data sent with each message. These sizes illustrate the transmission trade-off for the selected sets. Comparing their security also requires accounting for the distinct assumptions of the two constructions and the signing limit of Hypericum.

The byte lengths alone tell us little about the cost of retaining this compact representation. The public hash receives one structured transcript per challenge. The secret generator must instead supply a variable number of bytes to samplers. Even with an identical initial seed, a different stream can lead the signer through different arithmetic work. A measurement of hash throughput therefore cannot answer how long a signature takes, and a measurement of signing time alone cannot identify the cost of generating the stream.

We vary the challenge hash and secret generator independently while holding the isogeny arithmetic fixed. Cross-profile verification identifies which substitution changes interoperability. Paired trials and separate primitive measurements show whether higher hashing or sampling costs appear in end-to-end signing latency.

## II. Related Work

Kiktenko et al. instantiated SPHINCS+ with Streebog and benchmarked it against a SHA-256 instantiation across parameter sets [@kiktenko]. Sim et al. implemented K-XMSS and K-SPHINCS+ with Korean primitives, including LSH and hash functions based on CHAM and LEA, and investigated implementations using Advanced Vector Extensions 2 (AVX2) [@sim]. Both studies establish precedent for substituting national primitives in post-quantum signatures. In their hash-based constructions, hash evaluation implements the signature structure itself. Neither experiment estimates the cost of changing a signer-local sampler separately from a public Fiat–Shamir challenge in an isogeny protocol.

SQIsign 3.0 supplies the reference protocol, encodings, SHAKE256 instantiation and security model [@sqisign3]. Holding its isogeny arithmetic and parameter sets fixed gives the present comparison a common basis. A verifier can expose an encoding error even when the replacement hash passes its own test vectors. Conversely, a verifier that accepts a signature tells us little about the quality or cost of the secret stream that produced it. These two observations determine the scope of the functional and timing experiments below.

## III. Adaptation Design

### The two roles of SHAKE256 in SQIsign

Public challenge. In the Fiat–Shamir transform, the signer derives a challenge from the public key, the commitment and the message. SQIsign 3.0 absorbs the three American Standard Code for Information Interchange (ASCII) bytes “SQI”, the encoded public key (including its hint), the encoded Montgomery coefficient A of the commitment curve, and the message, in that order. SHAKE256 returns 16, 24 or 32 bytes according to the parameter set [@sqisign3, Alg. 3.3 and Table 11]. The verifier reconstructs the commitment and recomputes the challenge. A Streebog-512 digest contains 64 bytes [@rfc6986], so truncation can supply any of these lengths. Interoperability requires agreement on the input encoding, the selected digest bytes and their interpretation.

Secret pseudorandom streams. Key generation and signing also use SHAKE256 to supply bytes to randomized subroutines. Initialization absorbs 48 bytes of secret seed material and a three-byte domain label. The labels key, com, res and def distinguish key sampling, commitment sampling, response sampling and a default stream for internal algorithms [@sqisign3, Sec. 3.3.1]. Successive reads advance the state. Reading 40 bytes twice must return the same sequence as reading 80 bytes once from the same initial state. A replacement built on a fixed-output hash therefore needs a rule for generating successive blocks as well as separating the domains. The verifier does not replay this stream. A change to the generator can alter sampled keys and signatures while preserving the public verification rule. Its security still depends on the quality of the seed and the pseudorandomness of the derived bytes.

### Octet specification of the experimental profile

Let H denote Streebog-512 in the byte order returned by its application programming interface (API), prefixₖ the first k octets, and the two vertical bars (||) denote octet-string concatenation. All literal strings are ASCII without a terminating zero. For n = 16, 24 or 32, respectively, let T = “SQI” || encoded_pk || encoded_commitment_A || message. Write F and P for the ASCII strings “SQIsign3-FS-Streebog512-v1” and “SQIsign3-PRNG-v1”, respectively. The adapted challenge is

::::: {.wide}

:::: {#eq:challenge .equation}

c = int~LE~(prefix~n~(H(F || octet(n) || T))).

::::

:::::

The prefix binds the use and the length byte identifies the width. For each set, the key and commitment have fixed widths, so the remaining bytes unambiguously encode the message, including an empty message. The signer and verifier use the same interpretation of the digest.

The profile retains the reference seed interface: each KeyGen or Sign operation requests a fresh 48-byte secret root S. For d in {key, com, res, def}, let Z be eleven zero octets and LE32(i) the four-octet little-endian encoding of i. Using a hash-based message authentication code (HMAC), the generator computes

::::: {.wide}

:::: {#eq:domain .equation}

K~d~ = prefix~48~(HMAC-Streebog-512(S, P || ASCII(d))).

::::

:::: {#eq:block .equation}

B~i~ = H(LE32(i) || Z || K~d~),   1 ≤ i ≤ 2^32^ − 1.

::::

:::::

It serves consecutive octets of B₁ || B₂ || …, retaining unused octets between reads. A zero-length read preserves the cursor. A request exceeding the remaining capacity of 64(2³² − 1) bytes per domain fails before output. The counter mechanism instantiates §4 of R 1323565.1.006-2017 with m = h = 512, s = 384 and l = 120 [@tc26stream]. Incrementing the 504-bit state before hashing affects only its low four octets over the admitted range. This supplies a reproducible stream from a fixed-output primitive while retaining the original four domain interfaces. The cap, labels and derivation from a shared root are profile choices. The 384-bit HMAC key falls within the range of R 50.1.113-2016 §4.1.2, which recommends 512 bits [@tc26hmac]. Deriving four domain keys from this root is our design choice.

BASELINE retains both SHAKE256 interfaces. STREEBOG_HASH changes only the public challenge, RUSSIAN_PRNG changes only the secret generator, and COMBINED applies both substitutions.

## IV. Experimental Methodology

The integration uses the Linux x86-64 reference backend, radix 64, for p324_3, p500_27 and p664_17. The upstream reference is the nist-v3 tag (6d017708). The frozen archive contains the source, raw observations and analysis scripts [@artifact]. Its implementation (6d55a8f) and the replication build (028187e) have identical src trees. Functional evidence includes official baseline known-answer tests, independent reconstruction of challenge bytes and cross-profile verification. For the published p324_3 count-0 vector, upstream arithmetic recovered the commitment coefficient. A separate Python calculation assembled the 201-byte transcript and reproduced the embedded challenge. Modified scheme vectors serve as regression tests. Independent SHAKE and libgcrypt calculations check the corresponding primitive and transcript outputs.

Timing used an Intel Core i7-4770HQ, logical CPU 2, the GNU Compiler Collection (GCC) 16.2.1 and GNU Nettle 4.0. A fresh process timed KeyGen, detached Sign and Verify in sequence with a monotonic clock. Each trial index fixed the 64-byte message and the input to the deterministic test entropy provider. Matching indices across profiles controls the input conditions while allowing random sampling paths to diverge. Discarded warm-ups preceded timing. Separate batches measured 256 challenge hashes with synthetic fields of the encoded widths (encoding time excluded), 256 KiB of stream output after initialization, and, in the controlled series, 256 key-domain initializations with clearing. Process resident set size (RSS) after verification includes resident library pages. We also record its high-water mark (HWM). Separate untimed phase snapshots describe memory composition.

The historical series (7392c66) comprised 24 randomized complete blocks of 12 profile/set combinations. The first controlled series (3b0795c, sessions 1–3) and replication (028187e, sessions 4–6) each comprised three sessions of 16 complete blocks with balanced profile order. The replication used fresh indices and a fixed stopping rule. Its prespecified endpoint was 100 × (mean COMBINED Sign time / mean BASELINE Sign time − 1) at p500_27. Each series has its own baseline. Pointwise 95% percentile intervals use 10,000 bootstrap draws of paired indices, stratified by session in the two controlled series. The intervals quantify trial variation conditional on the recorded sessions. The many other contrasts are descriptive, without multiplicity adjustment.

## V. Results and Discussion

### Verification and encodings

BASELINE passed all 300 official Release records across the three sets. In Release, all 144 signer/verifier decisions (16 ordered pairs × 3 sets × 3 inputs) agreed with the predicted compatibility matrix. BASELINE and RUSSIAN_PRNG accepted each other's signatures, as did STREEBOG_HASH and COMBINED. Cross-family checks rejected the tested signatures. An additional 108 mutation cases gave the expected rejections. With identical seeds, all 18 key-pair comparisons between configurations using the same generator matched. These observations confirm the architectural prediction at the implemented byte interface. The wire encoding carries no profile identifier, so a protocol using both challenges must associate the expected rule with the key or protocol context.

### Latency across series

The three series yield different estimates of the p500_27 signing contrast (Table I). The historical positive estimate weakened in the first controlled series and changed sign in replication. Within replication, session estimates were +1.58%, +3.54% and −9.15%. Resampling four consecutive blocks together gave a sensitivity interval of [−7.54%, +4.52%]. Both analyses admit an increase or a decrease. The trials resolve neither a stable speed advantage nor equivalence. Differences in revision, sampled inputs and host conditions preclude attributing the shift to any one cause.

The replication covers both whole operations and symmetric primitives (Table II).

The two controlled series provide separate estimates of the signing contrast for each profile and parameter set (Fig. 1). In the replication, changing only the public hash changed mean signing time at p500_27 by +3.11% [−3.50%, +10.83%]. Changing only the generator gave −2.66% [−9.26%, +4.19%]. These intervals illustrate the limited precision of either individual whole-signature contrast.

The isolated measurements distinguish the two substitutions. At p500_27, changing only the challenge moved the mean per-hash time from 1.935 to 4.907 µs. Changing only the generator moved its mean byte cost from 4.401 to 28.443 ns. In COMBINED, batch durations increased by 150.98% for challenge hashing, 555.43% for stream generation and 5410.16% for domain initialization and clearing. At this set the last percentage corresponds to about 5.55 µs per initialization against 0.10 µs at baseline. These batch counts measure different units of work. Whole-operation times also include arithmetic on the sampled key, commitment and response. Adding the three percentages would have no interpretation as signing overhead.

For p500_27 COMBINED, the replication estimated a +0.33% change in mean KeyGen time [−10.38%, +12.18%] and −0.50% in Verify [−2.16%, +1.29%]. In COMBINED, KeyGen uses the adapted secret generator and Verify uses the adapted public challenge. Neither operation directly uses both substitutions. Both intervals include zero. Mean process RSS on the same comparison increased by 13.34% [12.77%, 13.91%]. Separate post-Verify snapshots attributed 340–368 KiB to Nettle mappings across adapted profiles, against zero in BASELINE. Resident process memory includes shared code and runtime state. The experiment cannot resolve the peak live allocation of a single signing operation.

:::: {.wide}

::: {#tbl:latency}

| Series | Triples | Baseline | Combined | Change | Interval |
|---|---:|---:|---:|---:|---:|
| Historical | 288 | 208.595 | 241.627 | +15.84% | [+5.35%, +26.46%] |
| Controlled | 576 | 212.428 | 217.842 | +2.55% | [−4.35%, +10.17%] |
| Replication | 576 | 214.269 | 211.101 | −1.48% | [−8.02%, +5.29%] |

: Mean p500_27 signing latency in milliseconds. Triples count all timed KeyGen/Sign/Verify trials across the 12 configurations. The interval is for the percentage change relative to the same-series baseline.

:::

::: {#tbl:replication}

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

: Replication, sessions 4–6. Times are arithmetic means over 48 trials per row. RSS is median post-Verify resident set size and HWM is the largest reported high-water mark in KiB. FS is time per Fiat–Shamir challenge hash, Stream is time per output byte and Init is time per key-domain initialization and clear.

:::

::: {.newpage}

![Change in mean signing time relative to the corresponding baseline, with pointwise paired 95% intervals for each substitution and set. Circles represent the first controlled series and squares the replication.](build/signing-panels.png){#fig:signing width=6.8in}

:::

::::

### Transmission context

The four profiles used public keys of 83, 129 and 169 bytes and detached signatures of 200, 306 and 406 bytes, respectively, in order of increasing parameter size. For context, the selected Hypericum fast/small sets have 64-byte public keys and signatures of 16,376/9,772 bytes at a budget of 2²⁰ signatures per key, or 59,132/18,932 bytes at 2⁶⁴ [@hypericumspec]. When transmitting the key once with one signature, p324_3 requires 283 bytes and M_128_20 requires 9,836 before framing. The interpretation depends on key reuse, per-key signing budgets and the distinct forgery models. Published Hypericum prototype timings use another parameterization and host [@hypericum2023]. The comparison therefore quantifies transmission cost under the stated key-use conditions. It leaves relative latency and equivalent-security parameter selection unresolved.

## VI. Security Assumptions and Limitations

The classical SQIsign theorem uses a programmable random oracle, hint-assisted OneEnd hardness, hint indistinguishability and assumptions on sampler distributions [@sqisign3, Thm. 8.1.7]. Its discussion of quantum queries introduces further algebraic-model restrictions [@sqisign3, Rem. 8.1.8]. Truncation gives the adapted scalar the required width. Applying the original argument would also require suitable challenge behavior on adversarial transcripts. Collision resistance alone supplies no oracle-programming argument, and a birthday estimate for arbitrary digest collisions is insufficient to price a forgery.

Kiryukhin gives single-key pseudorandom function (PRF) and message authentication code (MAC) bounds for HMAC-Streebog under assumptions on related-key attacks against its compression function [@kiryukhin2023, Thm. 2; @kiryukhin2024, Thm. 2]. Extending those results to our generator would require a composition argument. For the secret streams, one would first need to justify treating the truncated HMAC outputs under a fresh root as independent domain keys, then treating their bounded counter outputs as pseudorandom to the sampler. COMBINED also requires that these assumptions hold alongside public queries to the same hash. Labels distinguish inputs but provide no quantitative joint bound. The operating system entropy source must supply fresh, secret roots. A request for 48 bytes gives no measurement of their min-entropy. Reusing a root and label repeats the stream. Disclosure of a domain key exposes past and subsequent blocks in that domain. The profile has no within-operation recovery. The tested public API propagates initial entropy failure for KeyGen and detached Sign. Termination of high-level rejection sampling under artificial stream exhaustion remains open.

The measured GNU Nettle 4.0 keyed path uses secret-dependent table addresses, and upstream arithmetic can take variable time. A black-box pseudorandomness argument would omit these observations by a local adversary. Functional tests give no bound on leakage or forgery probability. The upstream security categories describe the original sets. Security levels and certification of the adapted profiles remain unestablished.

The timing intervals also have a limited scope. The replication tests another set of inputs on the same shared machine with active frequency scaling. It cannot estimate variation between processors or backends. The fixed message size limits extrapolation of challenge costs to longer messages. Whether compact signatures justify the observed computation depends on the application's transmission, latency and memory budgets.

## VII. Conclusion

Replacing the public challenge requires agreement at both ends on the transcript, digest prefix and scalar encoding. Replacing the secret generator requires a bounded, domain-separated byte stream at the signer. On three reference parameter sets the four configurations retained their encoded sizes and exhibited the predicted division into two verification families. The controlled trials distinguish a measurable increase in primitive cost and process RSS from a whole-signature effect whose direction varied across series. This gives a concrete account of what is required to retain compact encodings under substitution, what that choice cost on one platform, and which security assumptions still need justification.
