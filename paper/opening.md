# Adaptation of the symmetric components of SQIsign 3.0 using Russian cryptographic standards and evaluation of its efficiency

## I. Introduction

SQIsign 3.0 uses the same function, SHAKE256, to derive the public challenge checked by the verifier and to supply secret pseudorandom bytes during key generation and signing [1, Sec. 3.3]. Adapting the scheme to use the Russian hash function Streebog-512 therefore raises two questions. Which change can a signer make while retaining interoperability with an existing verifier? How much does each change cost in computation and memory? We study the two uses separately and in combination so that their effects can be distinguished.

Signature size motivates the choice of SQIsign. Its isogeny-based construction uses an 83-byte public key and a 200-byte signature at parameter set p324_3 [1, Table 1]. Hypericum, a Russian stateless hash-based design built on Streebog, uses a 64-byte public key and a 9,772-byte signature in its small-signature set M_128_20, which permits up to 2²⁰ signatures per secret key [2, Sec. 6]. When the recipient already has the public key, the signature accounts for the authentication data sent with each message. These sizes illustrate the transmission trade-off for the selected sets. Comparing their security also requires accounting for the distinct assumptions of the two constructions and the signing limit of Hypericum.

## II. The two roles of SHAKE256 in SQIsign

Public challenge. In the Fiat–Shamir transform, the signer derives a challenge from the public key, the commitment and the message. SQIsign 3.0 absorbs the three ASCII bytes “SQI”, the encoded public key (including its hint), the encoded Montgomery coefficient A of the commitment curve, and the message, in that order. SHAKE256 returns 16, 24 or 32 bytes according to the parameter set [1, Alg. 3.3 and Table 11]. The verifier reconstructs the commitment and recomputes the challenge. A Streebog-512 digest contains 64 bytes [3], so truncation can supply any of these lengths. Interoperability requires agreement on the input encoding, the selected digest bytes and their interpretation.

Secret pseudorandom streams. Key generation and signing also use SHAKE256 to supply bytes to randomized subroutines. Initialization absorbs 48 bytes of secret seed material and a three-byte domain label. The labels key, com, res and def distinguish key sampling, commitment sampling, response sampling and a default stream for internal algorithms [1, Sec. 3.3.1]. Successive reads advance the state. Reading 40 bytes twice must return the same sequence as reading 80 bytes once from the same initial state. A replacement built on a fixed-output hash therefore needs a rule for generating successive blocks as well as separating the domains. The verifier does not replay this stream. A change to the generator can alter sampled keys and signatures while preserving the public verification rule. Its security still depends on the quality of the seed and the pseudorandomness of the derived bytes.

## References

[1] M. A. Aardal et al., “SQIsign: Algorithm specifications and supporting documentation,” ver. 3.0, Sept. 2026. [Source](https://sqisign.org/spec/sqisign-20260901.pdf)

[2] QApp, “Hypericum: A stateless hash-based digital signature scheme,” draft specification (in Russian), Moscow, 2025, §§ 6.2–6.3. [Source](https://info.qapp.tech/КуАпп%20ЭЦП%20Гиперикум.pdf)

[3] V. Dolmatov, Ed., and A. Degtyarev, “GOST R 34.11-2012: Hash Function,” RFC 6986, Aug. 2013. [Source](https://www.rfc-editor.org/rfc/rfc6986)
