"""Randomized complete-block, single-CPU end-to-end comparison on Linux."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import subprocess
from check import PROFILES, SIZES, executable

METRICS = ["keygen_ns", "sign_ns", "verify_ns", "rss_kib", "peak_kib",
           "hash_batch256_ns", "stream_256kib_ns", "pk_bytes", "sk_bytes", "sig_bytes", "domain_init_clear_batch256_ns"]


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def main(output, count, cpu):
    if count < 2:
        raise ValueError("at least two complete blocks required")
    output.mkdir(parents=True, exist_ok=False)
    os.sched_setaffinity(0, {cpu})
    order = random.Random(240319)
    revision = command("git", "rev-parse", "HEAD")
    if command("git", "diff", "HEAD", "--name-only"):
        raise RuntimeError("commit tracked changes before measuring")
    meta = {"revision": revision, "upstream": command("git", "rev-parse", "nist-v3"),
            "cpu": cpu, "kernel": platform.release(), "python": platform.python_version(),
            "cpu_model": next(x.split(":", 1)[1].strip() for x in Path("/proc/cpuinfo").read_text().splitlines()
                              if x.startswith("model name")),
            "compiler": command("cc", "--version").splitlines()[0], "cmake": command("cmake", "--version").splitlines()[0],
            "nettle": command("pkg-config", "--modversion", "nettle"), "order_seed": 240319,
            "blocks": count, "warmup_index": 9999, "configuration": "Release ref RADIX=64",
            "executables": {}, "loadavg_before": os.getloadavg()}
    for profile in PROFILES:
        directory = Path(f"build-{profile}-Release")
        for name in ("compile_commands.json", "CMakeCache.txt"):
            (output / f"{profile}-{name}").write_bytes((directory/name).read_bytes())
        for variant in SIZES:
            binary = executable(profile, variant, "Release")
            meta["executables"][f"{profile}/{variant}"] = hashlib.sha256(binary.read_bytes()).hexdigest()
            subprocess.run([binary, "trial", "9999"], stdout=subprocess.DEVNULL, check=True)
    with (output/"raw.csv").open("x") as out:
        writer = csv.writer(out)
        writer.writerow(["variant", "profile", "index", "run_order", *METRICS])
        position = 0
        for index in range(1, count+1):
            cases = [(v, p) for v in SIZES for p in PROFILES]
            order.shuffle(cases)
            for variant, profile in cases:
                row = command(str(executable(profile, variant, "Release")), "trial", str(index)).split(",")
                if len(row) != len(METRICS) or any(int(x) <= 0 for x in row):
                    raise ValueError(row)
                writer.writerow([variant, profile, index, position, *row])
                position += 1
                out.flush()
    meta["loadavg_after"] = os.getloadavg()
    (output/"metadata.json").write_text(json.dumps(meta, indent=2) + "\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("output", type=Path)
    p.add_argument("--blocks", type=int, default=24)
    p.add_argument("--cpu", type=int, default=min(os.sched_getaffinity(0)))
    args = p.parse_args()
    main(args.output, args.blocks, args.cpu)
