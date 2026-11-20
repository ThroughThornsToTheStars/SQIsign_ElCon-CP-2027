"""Descriptives and paired percentile-bootstrap intervals. Write CSV to stdout."""
import csv
import random
import sys
from statistics import mean, median, stdev
from check import PROFILES, SIZES
from benchmark import METRICS

with open(sys.argv[1]) as f:
    rows = list(csv.DictReader(f))
writer = csv.writer(sys.stdout)
writer.writerow(["variant","profile","metric","n","mean","median","sd","min","max","delta_pct","ci_low_pct","ci_high_pct"])
for variant in SIZES:
    groups = {p: sorted((r for r in rows if r["variant"] == variant and r["profile"] == p),
                        key=lambda r: int(r["index"])) for p in PROFILES}
    rng = random.Random(616)
    baseline = groups["BASELINE"]
    n = len(baseline)
    indices = [r["index"] for r in baseline]
    if len(set(indices)) != n or n < 2:
        raise ValueError("incomplete blocks")
    draws = [rng.choices(range(n), k=n) for _ in range(10000)]
    for profile, group in groups.items():
        if [r["index"] for r in group] != indices:
            raise ValueError("unpaired data")
        for metric in METRICS[:7]:
            base = [int(r[metric]) for r in baseline]
            data = [int(r[metric]) for r in group]
            delta = 100*(sum(data)/sum(base)-1)
            ci = sorted(100*(sum(data[i] for i in d)/sum(base[i] for i in d)-1) for d in draws)
            stats = [mean(data), median(data), stdev(data), min(data), max(data), delta, ci[249], ci[9749]]
            writer.writerow([variant, profile, metric, n, *(round(x,5) for x in stats)])
