"""Run matched trials on one logical CPU, alternating which backend goes first."""
import csv
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
cpu = int(sys.argv[1]) if len(sys.argv) > 1 else min(os.sched_getaffinity(0))
os.sched_setaffinity(0, {cpu})
profiles = ["shake", "streebog"]
destination = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "experiment/samples.csv"
with destination.open("x") as out:
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["backend", "trial", "operation", "ns", "tsc", "core_cycles", "valid"])
    for trial in range(31):
        for profile in profiles:
            binary = root / "build/experiment/lvl1" / profile / "measure"
            data = subprocess.check_output([binary, str(trial)], text=True)
            if trial:
                for row in csv.reader(data.splitlines()):
                    writer.writerow([profile, *row])
                out.flush()
        profiles.reverse()
