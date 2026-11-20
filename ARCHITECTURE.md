# Adaptation of the symmetric components of SQIsign 3.0 using Russian cryptographic standards and evaluation of its efficiency.

## Integration map

Upstream tag nist-v3, commit 6d017708db403bf83977fa70770fc4f7f9e9ff21, tree 13f3daf6796fdd8a2eeb3679d82b8495b27acfe7. Compared algorithms 3.1–3.4 to the ref C paths for all parameter sets. The root CMake project still says VERSION 2.0. The Git tag and tree identify the submission. [Specification](https://sqisign.org/spec/sqisign-20260901.pdf) · [Source](https://github.com/SQISign/the-sqisign/tree/6d017708db403bf83977fa70770fc4f7f9e9ff21)

| Entry → dependency | Upstream input, output, lifetime | Experiment boundary |
|---|---|---|
| NIST API → protocols_sign and protocols_verify → verification/ref/lvlx/common.c, hash_to_challenge | SHAKE256 incremental init, absorb ASCII SQI (3), pk bytes and commitment A, then entire message, finalize once, squeeze once, release. Scalar zero-extended and converted for big-endian limbs. | Public digest only |
| public_key_to_bytes → ec_curve_to_bytes, fp2_encode | pk encodes normalized A/C followed by hint. Commitment encodes A supplied by caller. Fp2 encodes real then imaginary, little-endian fixed-width. The source comment mentioning j is misleading. | Preserve encoding and hint |
| protocols_keygen → prng_seed → randombytes | One fresh 48-byte root per operation, stored in thread-local memory. Seed def, then derive local key domain. No explicit nonce. | Keep entropy boundary |
| protocols_sign → prng_seed → prng_domain_seed | Fresh root, def stream for helper algorithms, separate com and res states for commitment and response. Clear local contexts after use and root/default at operation exit. | Replace only domain-state derivation and byte generation |
| mp/ref/lvlx/mp.c → prng_random_bytes | Integer sampler consumes variable byte counts and can reject/retry. Domain passed down through quaternion arithmetic or chosen by helper. Each read advances the same context. | Preserve sampler, retries and call order |
| common/generic/prng.c and include/prng.h | SHAKE256(root ∥ 3-byte domain); no terminating NUL, explicit nonce or exposed counter. Same root/domain restarts same stream. No public clone entry point. | Per-domain buffered cursor |
| common/generic/randombytes_system.c and common/ref/{randombytes_ctrdrbg,aes_c}.c | Platform RNG in system library, deterministic AES-256 CTR-DRBG in test library (including seed and message generation in KAT driver). | Keep both |
| common/generic/fips202.c, tests and utilities | FIPS202 primitive implementations including SHAKE128/256, SHA3 entry points, SHAKE KAT and concurrency-test transcript digest. | Keep every unrelated call |

Parameter order p324_3 / p500_27 / p664_17. Challenge bytes 16 / 24 / 32. Encoded commitment bytes 82 / 128 / 168. Encoded pk bytes 83 / 129 / 169. No public XOF stream is required. Verification reconstructs the commitment before hashing. The verifier needs only the public-hash profile. Neither the wire signature nor the key carries a profile identifier.

Reproduce the inventory from the tag with `git grep -nE 'shake(128|256)|sha3_[0-9]+|aes[0-9]+|randombytes|prng_(seed|domain_seed|random_bytes)|hash_to_challenge' nist-v3 -- src apps include integration test`. Production math, challenge-to-kernel conversion, key/signature codecs, OS entropy, external adapters and the test DRBG are outside the replacement. The Linux CMake build is the evaluation target; external liboqs and MCU builds need separate integration review.
