"""Recompute exhibit values directly from session CSVs, independently of the analyzer."""
import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

import numpy as np


def rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def require_close(actual, expected, label):
    if not math.isclose(float(actual), expected, rel_tol=1e-12, abs_tol=1e-8):
        raise ValueError(f"{label}: found {actual}, expected {expected}")


def check(root):
    analysis = root / "analysis"
    manifest = json.loads((analysis / "inputs.json").read_text())
    samples = defaultdict(dict)
    sessions = manifest["sessions"]
    metrics = None
    for session, hashes in zip(sessions, manifest["input_sha256"], strict=True):
        folder = root / f"session-{session}"
        for name in ("raw.csv", "metadata.json", "memory.csv"):
            if hashlib.sha256((folder / name).read_bytes()).hexdigest() != hashes[name]:
                raise ValueError(f"input digest mismatch: {folder / name}")
        for row in rows(folder / "raw.csv"):
            key = (row["variant"], row["profile"])
            block = (int(row["session"]), int(row["index"]))
            if block[0] != session or block in samples[key]:
                raise ValueError(f"misplaced or duplicate trial: {key}, {block}")
            values = {k: int(v) for k, v in row.items() if k not in
                      ("variant", "profile", "session", "index", "run_order")}
            if metrics is None:
                metrics = set(values)
            if values.keys() != metrics:
                raise ValueError("inconsistent measurements")
            samples[key][block] = values

    expected_cells = {(v, p, m) for v, p in samples for m in metrics}
    displayed_means = {}
    for row in rows(analysis / "summary.csv"):
        v, p, m = row["variant"], row["profile"], row["metric"]
        expected_cells.remove((v, p, m))
        pair = samples[v, p]
        base = samples[v, "BASELINE"]
        if pair.keys() != base.keys():
            raise ValueError(f"unmatched blocks: {v}, {p}")
        a = [x[m] for x in pair.values()]
        b = [base[i][m] for i in pair]
        estimates = dict(n=len(a), mean=mean(a), median=median(a), sd=stdev(a),
                         min=min(a), max=max(a), difference=mean(x-y for x,y in zip(a,b)),
                         percent=100*(mean(a)/mean(b)-1))
        for column, value in estimates.items():
            require_close(row[column], value, (v, p, m, column))
        if m in ("keygen_ns", "sign_ns", "verify_ns"):
            displayed_means[v, p, m] = f"{mean(a) / 1e6:.3f}"
        if (v, p, m) == ("p500_27", "COMBINED", "sign_ns"):
            check_primary_interval(pair, base, sessions, row)
    if expected_cells:
        raise ValueError(f"missing summary cells: {expected_cells}")

    unseen = set(samples)
    for line in (analysis / "results_tables.tex").read_text().splitlines():
        if line.startswith("p"):
            v, p, *times = line.removesuffix(r"\\").strip().replace(r"\_", "_").split(" & ")
            unseen.remove((v, p))
            expected = [displayed_means[v,p,m] for m in ("keygen_ns", "sign_ns", "verify_ns")]
            if times != expected:
                raise ValueError(f"wrong TeX times: {v}, {p}")
    if unseen:
        raise ValueError(f"missing TeX rows: {unseen}")
    print(f"{len(samples)*len(metrics)} metric cells, {len(samples)} TeX rows and "
          "the primary paired 95% interval agree with the raw observations")


def check_primary_interval(pair, base, sessions, row):
    # Draw the same stratified pairs as specified in the study. Accumulate each
    # arm's totals separately to check the ratio of means and percentile bounds.
    rng = np.random.default_rng(616)
    treated = np.zeros(10000, dtype=np.int64)
    control = np.zeros_like(treated)
    for session in sessions:
        ids = sorted(k for k in base if k[0] == session)
        draws = rng.integers(len(ids), size=(len(treated), len(ids)))
        a = np.array([pair[i]["sign_ns"] for i in ids])
        b = np.array([base[i]["sign_ns"] for i in ids])
        for column in draws.T:
            treated += a[column]
            control += b[column]
    bounds = np.percentile(100*(treated/control-1), [2.5, 97.5])
    for name, expected in zip(("pct_lo", "pct_hi"), bounds):
        require_close(row[name], expected, name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("series", type=Path)
    check(parser.parse_args().series)
