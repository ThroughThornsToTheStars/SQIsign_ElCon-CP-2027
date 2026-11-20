"""Byte-oriented, independent oracle using libgcrypt. Uses only public test material."""
import ctypes as ct
import ctypes.util
from pathlib import Path
import subprocess
import sys

gcrypt = ct.CDLL(ctypes.util.find_library("gcrypt"))
gcrypt.gcry_check_version.argtypes = [ct.c_char_p]
gcrypt.gcry_check_version.restype = ct.c_char_p
gcrypt.gcry_check_version(None)
gcrypt.gcry_md_map_name.argtypes = [ct.c_char_p]
algorithm = gcrypt.gcry_md_map_name(b"STRIBOG512")
if not algorithm:
    raise RuntimeError("libgcrypt STRIBOG512 unavailable")
gcrypt.gcry_md_hash_buffer.argtypes = [ct.c_int, ct.c_void_p, ct.c_void_p, ct.c_size_t]


def digest(message):
    out = ct.create_string_buffer(64)
    gcrypt.gcry_md_hash_buffer(algorithm, out, message, len(message))
    return out.raw


def mac(key, message):
    padded = key.ljust(64, b"\0")
    inner = digest(bytes(x ^ 0x36 for x in padded) + message)
    return digest(bytes(x ^ 0x5c for x in padded) + inner)


def stream(root, domain, counter):
    key = mac(root, b"SQIsign3-PRNG-v1" + domain)[:48]
    return digest(counter.to_bytes(15, "little") + key)


def challenge(n, fields, msg):
    return digest(b"SQIsign3-FS-Streebog512-v1" + bytes([n]) + b"SQI" + fields + msg)[:n]


def aes_blocks(key, blocks):
    return subprocess.check_output(["openssl", "enc", "-aes-256-ecb", "-nopad",
                                    "-K", key.hex()], input=blocks)


def test_root():
    # SP 800-90A CTR_DRBG AES-256/no_df instantiate then first Generate.
    seed = bytes(range(48))
    update = aes_blocks(bytes(32), b"".join(i.to_bytes(16, "big") for i in (1, 2, 3)))
    state = bytes(a ^ b for a, b in zip(seed, update))
    v = int.from_bytes(state[32:], "big")
    return aes_blocks(state[:32], b"".join((v+i).to_bytes(16, "big") for i in (1, 2, 3)))


def check_answer(name, actual, expected):
    if actual != expected:
        raise ValueError(f"{name}: known-answer mismatch")


if __name__ == "__main__":
    # RFC 6986 §10.1, API octet order; RFC 7836 Appendix B, example 2.
    check_answer("RFC 6986 M1", digest((b"0123456789"*7)[:63]).hex(),
        "1b54d01a4af5b9d5cc3d86d68d285462b19abc2475222f35c085122be4ba1ffa"
        "00ad30f8767b3a82384c6574f024c311e2a481332b08ef7f41797891c1646f48")
    check_answer("RFC 7836 HMAC", mac(bytes(range(32)), bytes.fromhex("0126bdb87800af214341456563780100")).hex(),
        "a59bab22ecae19c65fbde6e5f4e9f5d8549d31f037f9df9b905500e171923a77"
        "3d5f1530f2ed7e964cb2eedc29e9ad2f3afe93b2814f79f5000ffc0366c251e6")
    m2 = bytes.fromhex(
        "fbe2e5f0eee3c820fbeafaebef20fffbf0e1e0f0f520e0ed20e8ece0ebe5f0f2"
        "f120fff0eeec20f120faf2fee5e2202ce8f6f3ede220e8e6eee1e8f0f2d1202ce8f0f2e5e220e5d1")[::-1]
    check_answer("RFC 6986 M2", digest(m2)[::-1].hex(),
        "28fbc9bada033b1460642bdcddb90c3fb3e56c497ccd0f62b8a2ad4935e85f03"
        "7613966de4ee00531ae60f3b5a47f8dae06915d5f2f194996fcabf2622e6881e")
    print("RFC 6986 and RFC 7836 anchors passed")
    if len(sys.argv) > 1:
        if len(sys.argv) != 3 or sys.argv[2] not in ("STREEBOG_HASH", "RUSSIAN_PRNG", "COMBINED"):
            sys.exit("usage: oracle.py [RECORDS {STREEBOG_HASH,RUSSIAN_PRNG,COMBINED}]")
        records = {}
        for line in Path(sys.argv[1]).read_text().splitlines():
            name, value = line.split()
            if name in records:
                raise ValueError(f"duplicate primitive record: {name}")
            records[name] = bytes.fromhex(value)
        expected = {"rfc6986": digest((b"0123456789"*7)[:63]),
                    "rfc7836": mac(bytes(range(32)), bytes.fromhex("0126bdb87800af214341456563780100"))}
        expected["rfc6986_m2"] = digest(m2)
        for n in (16, 24, 32):
            expected[f"fs{n}"] = challenge(n, bytes(range(80)), b"hello")
        for domain in (b"key", b"com", b"res", b"def"):
            expected[domain.decode()] = b"".join(stream(bytes(range(48)), domain, i) for i in (1, 2, 3))
        expected["final"] = stream(bytes(range(48)), b"key", 2**32-1)
        required = {"rfc6986", "rfc6986_m2", "rfc7836"}
        if sys.argv[2] in ("STREEBOG_HASH", "COMBINED"):
            required.update(("fs16", "fs24", "fs32"))
        if sys.argv[2] in ("RUSSIAN_PRNG", "COMBINED"):
            required.update(("key", "com", "res", "def", "final"))
        if records.keys() != required:
            raise ValueError(f"missing records: {sorted(required - records.keys())}, "
                             f"unexpected records: {sorted(records.keys() - required)}")
        for name, value in records.items():
            check_answer(name, value, expected[name])
        print(f"matched {len(records)} emitted records")
