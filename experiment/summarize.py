"""Print the article table from the 30 matched trials."""
import csv
import random
import sys
from pathlib import Path
from statistics import median, quantiles

path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("samples.csv")
with path.open() as data:
    rows = list(csv.DictReader(data))
profiles = ("shake", "streebog")
operations = ("KeyGen", "Sign", "Verify")
samples = {(r["backend"], int(r["trial"]), r["operation"]): r for r in rows}
expected = {(p, t, op) for p in profiles for t in range(1, 31) for op in operations}
if len(rows) != len(expected) or samples.keys() != expected or any(r["valid"] != "1" for r in rows):
    sys.exit("Incomplete, duplicated or invalid trials")

def delta(a, b):
    return 100 * (median(b) / median(a) - 1)

def medians(op, field):
    return [[int(samples[p, t, op][field]) for t in range(1, 31)] for p in profiles]

rng = random.Random(6986)
print("| Операция | SHAKE, мс | Стрибог, мс | Δ времени | 95% ДИ для Δ | SHAKE, такты | Стрибог, такты | Δ тактов |")
print("|---|---:|---:|---:|---:|---:|---:|---:|")
for op in operations:
    a, b = medians(op, "ns")
    bootstrap = []
    for _ in range(10000):
        idx = rng.choices(range(len(a)), k=len(a))
        bootstrap.append(delta([a[i] for i in idx], [b[i] for i in idx]))
    q = quantiles(bootstrap, n=1000, method="inclusive")
    cycles = "н/д | н/д | н/д"
    if all(samples[p, t, op]["core_cycles"] for p in profiles for t in range(1, 31)):
        ca, cb = medians(op, "core_cycles")
        cycles = f"{median(ca):,.1f} | {median(cb):,.1f} | {delta(ca,cb):+.2f}%".replace(",", " ")
    print(f"| {op} | {median(a)/1e6:.2f} | {median(b)/1e6:.2f} | {delta(a,b):+.2f}% "
          f"| [{q[24]:+.2f}%, {q[974]:+.2f}%] | {cycles} |")
