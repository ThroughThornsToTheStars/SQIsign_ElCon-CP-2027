# Experimental profiles, revision 1

All definitions below operate on octets. Text literals are ASCII without NUL. H is the 64-byte Streebog-512 digest in the usual byte-oriented API order (Nettle/libgcrypt). In the RFC 6986 display convention, reverse the printed octets of both the message and hash for its worked examples. [RFC 6986](https://www.rfc-editor.org/rfc/rfc6986.html)

## Public challenge

Let n be 16, 24 or 32 for the three parameter sets. Let T = ASCII("SQI") ∥ encoded_pk ∥ encoded_commitment_A ∥ message, exactly as in algorithm 3.3. The profile outputs the first n bytes of H(ASCII("SQIsign3-FS-Streebog512-v1") ∥ octet(n) ∥ T). Interpret as an unsigned little-endian scalar as upstream. One digest per challenge, no seed, secret state, nonce, counter or repeated squeeze. The fixed prefix separates the use and the length byte binds the parameter set. The fixed-size fields precede the variable-length final message. Input may be absorbed incrementally. Truncation supplies every required length directly. The v1 counter XOF has no role here. [SQIsign §3.3](https://sqisign.org/spec/sqisign-20260901.pdf)

## Internal byte stream

Each KeyGen/Sign requests its own uniform secret 48-byte root S from the upstream entropy interface. The production assumption is a working cryptographic OS RNG with fresh, independent roots; byte count alone gives no measured min-entropy. The deterministic AES test provider is for reproducibility. For d in key, com, res, def derive K = first 48 octets of HMAC-Streebog-512(S, ASCII("SQIsign3-PRNG-v1") ∥ ASCII(d)). The HMAC block length is 64. Label and d have fixed lengths. This application-specific domain derivation is a research choice. HMAC follows the accompanying algorithms for GOST signatures and hashing. The derived-key functions in Р 1323565.1.022-2018 are outside this construction. [Р 50.1.113-2016](https://protect.gost.ru/rst/details/d4318178-cea5-4e8b-b81b-0e36b8951f5d) · [RFC 7836 §4.1.2](https://www.rfc-editor.org/rfc/rfc7836.html) · [Р 1323565.1.022-2018](https://protect.gost.ru/rst/details/a47c68a4-7d4e-4385-a210-fa610983b98d)

Use m=512, h=512, s=384, l=120 in §4 of Р 1323565.1.006-2017. Represent the 504-bit U least-significant octet first, K in API byte order in the high 384 bits. Starting at i=1, block B_i = H(LE32(i) ∥ 11 zero octets ∥ K). U_0 has 15 low zero octets. Concatenate B_1, B_2, ... in API order, and take the requested prefix. In low-octet-first form this realizes the recommendation's prepending of successive blocks to the high end and taking low bits for a partial block. The profile restricts i to 1..2^32−1. Per domain at most 64(2^32−1) bytes, including cached bytes. Reject a read exceeding the remaining capacity before output or state mutation. A zero-length read succeeds on initialized state. No externally supplied nonce, no wrap, no reseed inside a stream. Reinitialization with the same root and domain repeats the stream. Struct copies in the research backend reproduce the cursor for tests; only fresh domains/roots give separated streams. Erase root, K, temporary hash state and cached output at end of use. [Р 1323565.1.006-2017 §4](https://files.stroyinf.ru/Data2/1/4293740/4293740893.pdf)

The standard specifies a secret random initial filling. Here the per-domain filling is derived from a shared root. The composition, cap, labels and octet interface define an experimental profile. No standard conformance or security reduction for the composition is claimed.

| CMake SQISIGN_PROFILE | Fiat–Shamir | Internal domains |
|---|---|---|
| BASELINE | SHAKE256 | SHAKE256 |
| STREEBOG_HASH | truncated H | SHAKE256 |
| RUSSIAN_PRNG | SHAKE256 | HMAC initialization, H counter blocks |
| COMBINED | truncated H | HMAC initialization, H counter blocks |
