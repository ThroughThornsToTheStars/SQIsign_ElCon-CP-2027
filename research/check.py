"""Check accepted/rejected profile combinations and fixed regressions, or create new fixtures."""
import argparse
from pathlib import Path
import subprocess

PROFILES = ("BASELINE", "STREEBOG_HASH", "RUSSIAN_PRNG", "COMBINED")
SIZES = {"p324_3": (83, 270, 200), "p500_27": (129, 417, 306), "p664_17": (169, 549, 406)}


def executable(profile, variant, mode):
    return Path(f"build-{profile}-{mode}/research/trial_{variant}").resolve()


def seed(index):
    value = bytearray(range(48))
    for j, byte in enumerate(index.to_bytes(4, "little")):
        value[j] ^= byte
    return value.hex()


def record(index, pk, sk, sig):
    msg = bytes((index + 7*i) % 256 for i in range(64)) if index else b""
    return (f"count = {index}\nseed = {seed(index)}\nmlen = {len(msg)}\n"
            f"msg = {msg.hex()}\npk = {pk.hex()}\nsk = {sk.hex()}\n"
            f"smlen = {len(sig)+len(msg)}\nsm = {(sig+msg).hex()}\n\n")


def verify(binary, index, data, accepted):
    p = subprocess.run([binary, "verify", str(index)], input=data)
    if p.returncode != int(not accepted):
        raise RuntimeError(f"{binary} index {index}: expected accept={accepted}, exit={p.returncode}")


def check(mode, create, selected):
    profiles = [selected] if selected else PROFILES
    for variant, (p, s, z) in SIZES.items():
        for profile in profiles:
            binary = executable(profile, variant, mode)
            records = ""
            for index in (0, 1, 2):
                vector = subprocess.check_output([binary, "vector", str(index)])
                if len(vector) != p+s+z:
                    raise ValueError("wrong field lengths")
                pk, sk, sig = vector[:p], vector[p:p+s], vector[p+s:]
                if index:
                    records += record(index, pk, sk, sig)
                for other in profiles:
                    peer = executable(other, variant, mode)
                    same_hash = (PROFILES.index(profile) % 2 == PROFILES.index(other) % 2)
                    verify(peer, index, pk + sig, same_hash)
                damaged = bytearray(sig)
                damaged[-3] ^= 1  # last octet of challenge
                verify(binary, index, pk + damaged, False)
                verify(binary, index, pk + bytes(z), False)
                verify(binary, index+1, pk + sig, False)
            if profile != "BASELINE":
                directory = (create or Path("research/vectors")) / profile
                path = directory / f"PQCsignKAT_{s}_SQIsign_{variant}.rsp"
                if create:
                    directory.mkdir(parents=True, exist_ok=True)
                    with path.open("x") as out:
                        out.write(records)
                elif path.read_text() != records:
                    raise ValueError(f"fixed vector mismatch: {path}")
            print(f"{mode} {profile} {variant}: 3 round trips, {3*len(profiles)} verifier decisions, 9 negatives", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default="Release")
    parser.add_argument("--profile", choices=PROFILES)
    parser.add_argument("--create", type=Path, help="write new fixed vectors in a fresh location")
    args = parser.parse_args()
    check(args.mode, args.create, args.profile)
