"""Compare the typed public challenge caller with an independent wire encoder."""
import argparse
import hashlib
import subprocess
from itertools import islice
from pathlib import Path

from check import PROFILES, SIZES


def check(profile, mode):
    for variant, n in (("p324_3", 16), ("p500_27", 24), ("p664_17", 32)):
        fixture = Path("KAT") / f"PQCsignKAT_{SIZES[variant][1]}_SQIsign_{variant}.rsp"
        with fixture.open() as f:
            key, commitment = islice((bytes.fromhex(row[5:]) for row in f if row.startswith("pk = ")), 2)

        # Both curves come from official keys. Only the signing key contributes
        # its hint byte. The commitment contributes its normalized coefficient.
        use_streebog = profile in ("STREEBOG_HASH", "COMBINED")
        prefix = b"SQIsign3-FS-Streebog512-v1" + bytes([n]) if use_streebog else b""
        rate = 64 if use_streebog else 136
        fixed = len(prefix) + 3 + len(key) + len(commitment) - 1
        boundary = rate - fixed % rate
        lengths = sorted({0, 1, boundary - 1, boundary, boundary + 1, 255})
        adapter = Path(f"build-{profile}-{mode}/research/transcript_{variant}")
        count = 0
        for pk, com in ((key, commitment), (commitment, key)):
            for length in lengths:
                message = bytes(range(length))
                wire = prefix + b"SQI" + pk + com[:-1] + message
                if use_streebog:
                    from oracle import digest
                    expected = digest(wire)[:n]
                else:
                    expected = hashlib.shake_256(wire).digest(n)
                limbs = subprocess.check_output([adapter], input=pk + com + message)
                if len(limbs) < n or limbs != expected.ljust(len(limbs), b"\x00"):
                    raise ValueError(f"scalar mismatch for {variant}, {profile}, length {length}")
                count += 1
        print(f"{mode} {profile} {variant}: {count} typed transcript comparisons passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILES)
    parser.add_argument("mode", choices=("San", "Release"))
    args = parser.parse_args()
    check(args.profile, args.mode)
