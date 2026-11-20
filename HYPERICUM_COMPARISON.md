# Hypericum and SQIsign 3.0

Hypericum uses a stateless hash-based hypertree, with WOTS+C and FORS+C components. Key generation samples secret seeds, a PRF key and a public seed and computes the root of the top tree. The signing key encoding includes the public key. Signing identifies tree/leaf positions from a message-dependent digest, performs a counter search, constructs a FORS+C signature and authenticates it in the hypertree. Verification recomputes the digest and roots. Bounds on hash-based forgery depend on the hash properties, parameters and query budget. SQIsign instead uses a Fiat–Shamir protocol for an isogeny-based relation. Key generation produces a curve public key with secret algebraic information. Signing constructs a commitment and response using fresh randomness. [QApp specification §§6.1–6.5](https://info.qapp.tech/КуАпп%20ЭЦП%20Гиперикум.pdf) · [Turchenko and Grebnev](https://doi.org/10.1007/s11416-024-00520-6) · [SQIsign specification §§3,8](https://sqisign.org/spec/sqisign-20260901.pdf)

## Size, budget and verification work

QApp §6.2 distinguishes fast (Б) and small (М) signatures, security-estimate labels 128/256 and maximum signatures per secret key. The following selection covers both ends of its listed budgets. Counts of Th are approximate calls to the specification's tweakable hash. They do not represent CPU cycles or elapsed times. The two seed/root components of the public key total 64 bytes. Four 32-byte components of the stored signing key total 128 bytes. [QApp parameter and key definitions, §§6.2–6.3](https://info.qapp.tech/КуАпп%20ЭЦП%20Гиперикум.pdf) · [QApp API and encodings](https://docs.qapp.tech/group__hypericum.html)

| Hypericum set | PK / SK bytes | Signature bytes | Signatures/key | Sign Th calls | Verify Th calls |
|---|---:|---:|---:|---:|---:|
| Б_128_20 | 64 / 128 | 16,376 | 2²⁰ | 99,864 | 2,733 |
| М_128_20 | 64 / 128 | 9,772 | 2²⁰ | 2,154,158 | 1,187 |
| Б_256_64 | 64 / 128 | 59,132 | 2⁶⁴ | 220,309 | 11,663 |
| М_256_64 | 64 / 128 | 18,932 | 2⁶⁴ | 544,997,215 | 2,368 |

| SQIsign set | Upstream target NIST category | PK / SK bytes | Signature bytes |
|---|---:|---:|---:|
| p324_3 | I | 83 / 270 | 200 |
| p500_27 | III | 129 / 417 | 306 |
| p664_17 | V | 169 / 549 | 406 |

All four tested profiles preserve the SQIsign encoding widths. Upstream target categories describe the original parameter sets. No category for the adapted profiles follows from these byte widths. The security-estimate labels in Hypericum use its authors' model, including the per-key usage condition. SQIsign's proof also depends on signing and hash queries, although its parameter names carry no corresponding fixed per-key signature budget. The counter cap in a SQIsign research PRNG domain limits bytes per operation. It does not impose a Hypericum-style signature budget. [SQIsign data](results/run-7392c66/raw.csv) · [Proof assumptions](SECURITY_ARGUMENT.md)

For a concrete bandwidth example, storing a detached signature and one public key costs 283 bytes for p324_3 and 9,836 bytes for М_128_20, before protocol framing. Reusing a cached public key makes the signature alone the marginal transmission cost. Hypericum has smaller keys in the table and much larger signatures. A system using a 2²⁰-budget key must account for signatures across replicas and rotate keys within that budget even though the signing algorithm is stateless. This comparison addresses storage and transmission and supplies no equivalent-security ranking.

## Published latency measurements

The authors' 2023 unoptimized prototype reported 15.98 ms KeyGen, 463 ms Sign and 20.57 ms Verify for **Hypericum-128f** on an i7-7500U at 2.7 GHz under real-time Linux 4.18 with Google Benchmark, Turbo Boost and Hyper-Threading disabled. That prototype's own 128f signature occupies 17,088 bytes, distinguishable from the later Б_128_20 profile above. These numbers have different parameter definitions, implementation and host from the SQIsign trials. There are no local Hypericum timings or cross-scheme speed ratios in this study. A public C reference tree is available for an eventual same-host comparison. [Authors' slides 9 and 12](https://ruscrypto.ru/resource/archive/rc2023/files/02_grebnev.pdf) · [Reference implementation](https://github.com/QAPP-tech/hypericum_tc26/tree/f3f254038e5539132d112e8f97332a2a351131fe)
