# Adaptation of the symmetric components of SQIsign 3.0 using Russian cryptographic standards and evaluation of its efficiency.

**Experimental research implementation, not a certified cryptographic product.**

This branch studies how two changes affect signatures made with the reference SQIsign implementation. It tracks the official `nist-v3` submission at `6d017708db403bf83977fa70770fc4f7f9e9ff21`. The published research branch is `v3`. The historical `main` tree uses SQIsign v1. [Official source](https://github.com/SQISign/the-sqisign/tree/6d017708db403bf83977fa70770fc4f7f9e9ff21) · [Official specification](https://sqisign.org/spec/sqisign-20260901.pdf)

| CMake profile | Public Fiat–Shamir challenge | Private operation streams | Compatible verifiers |
|---|---|---|---|
| BASELINE | SHAKE256 | upstream SHAKE256 | BASELINE, RUSSIAN_PRNG |
| STREEBOG_HASH | truncated Streebog-512 | upstream SHAKE256 | STREEBOG_HASH, COMBINED |
| RUSSIAN_PRNG | SHAKE256 | HMAC initialization and Streebog-512 counter blocks | BASELINE, RUSSIAN_PRNG |
| COMBINED | truncated Streebog-512 | HMAC initialization and Streebog-512 counter blocks | STREEBOG_HASH, COMBINED |

The public hash binds a fixed domain label, the requested length, the upstream tag, encoded public key, commitment coefficient and message. The first 16, 24 or 32 digest octets supply the little-endian challenge. The private generator takes a fresh 48-byte operation root, uses HMAC-Streebog-512 to derive 48 bytes per three-byte domain, then hashes consecutive counter inputs with that secret suffix. The field arithmetic, isogenies, rejection sampling, key/signature encodings and OS entropy provider retain the upstream implementation. The validation branch also returns before serializing a key pair when entropy acquisition fails. No profile identifier is carried on the wire. [Architecture](ARCHITECTURE.md) · [Byte-level profile](CRYPTO_PROFILE.md)

Streebog and HMAC have independent specifications. The counter step follows the parameterized generator in R 1323565.1.006-2017 §4. Transcript framing, the domain key schedule, a 32-bit counter cap and their composition with SQIsign are research decisions. The application-specific HMAC transcript differs from the KDFs of R 1323565.1.022-2018. [RFC 6986](https://www.rfc-editor.org/rfc/rfc6986) · [Counter recommendation at Rosstandart](https://protect.gost.ru/rst/details/817595f3-d46b-4bb1-b6aa-eaee1a3c9ec9) · [HMAC recommendation](https://protect.gost.ru/rst/details/d4318178-cea5-4e8b-b81b-0e36b8951f5d) · [KDF recommendation](https://protect.gost.ru/rst/details/a47c68a4-7d4e-4385-a210-fa610983b98d)

## Build and check

Run from the repository root on Linux x86-64 with GCC, CMake, Ninja, pkg-config, Bash and Python 3. Install Nettle development files and the libgcrypt runtime for the oracle. Measurements use reference arithmetic and radix 64. The optional study analysis needs NumPy and Matplotlib. Each trial binary deliberately uses a public deterministic seed. System smoke tests use OS entropy.

```sh
for p in BASELINE STREEBOG_HASH RUSSIAN_PRNG COMBINED; do
  bash research/build.sh "$p" Release && bash research/verify.sh "$p" Release || exit 1
done
python3 research/check.py
```

The profile switch is `-DSQISIGN_PROFILE=<name>`. The script sets the arithmetic build options and enables the research targets. For sanitizers, clean-checkout instructions, fresh measurements and offline transfer see [REPRODUCIBILITY.md](REPRODUCIBILITY.md).

## Read the results

The [registered abstract](paper/REGISTERED_ABSTRACT.txt) sets the study scope. The [latest replication](results/replication-028187e/) contains 576 new observations at `028187e`. For p500_27 signing the COMBINED change versus BASELINE was −1.48% (paired 95% interval −8.02% to +5.29%). The [historical series](results/run-7392c66/) preserves 288 paired-design observations. The [benchmark report](BENCHMARK_REPORT.md) identifies each measured revision, the raw inputs, memory definition and pointwise confidence intervals. The [test report](TEST_REPORT.md) distinguishes selected CTests, KAT records, cross-profile checks and hosted CI. [Hypericum comparison](HYPERICUM_COMPARISON.md) gives size, signature-budget and cost data from the scheme authors.

The installed Nettle 4.0 implementation uses secret-dependent table addresses in the private generator. Exposure of a domain key allows replay of past and future bytes in its stream. Passing the oracle and signature tests establishes functional behavior on the tested platform. Security of the concrete hash/PRNG composition, side-channel exposure and the largest parameter set require separate review. [Security argument](SECURITY_ARGUMENT.md) · [Security limitations](SECURITY_LIMITATIONS.md) · [Final research status](FINAL_RESEARCH_STATUS.md)
