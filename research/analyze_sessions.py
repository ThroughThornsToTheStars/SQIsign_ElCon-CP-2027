"""Summarize complete sessions. Run from the checkout holding the analysis."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from benchmark import METRICS
from check import PROFILES, SIZES


def records(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def read_sessions(root):
    samples = {}
    sessions = {}
    attestations = []
    first_build = None
    for folder in sorted(root.glob("session-*")):
        meta = json.loads((folder / "metadata.json").read_text())
        session, n = meta["session"], meta["blocks"]
        if session in sessions or n < 4 or n % 4:
            raise ValueError(f"invalid session metadata in {folder}")
        build = {k: meta[k] for k in ("revision", "build_files", "binaries", "cc", "nettle", "cpu")}
        if first_build is None:
            first_build = build
        if build != first_build:
            raise ValueError("session binaries or configuration changed")
        indices = range(1000 * session + 1, 1000 * session + n + 1)
        sessions[session] = list(indices)
        rows = records(folder / "raw.csv")
        if len(rows) != len(indices) * len(SIZES) * len(PROFILES):
            raise ValueError(f"wrong row count in {folder}")
        for position, row in enumerate(rows):
            idx, v, p = int(row["index"]), row["variant"], row["profile"]
            key = session, idx, v, p
            if (int(row["session"]) != session or idx != indices[position // 12]
                    or int(row["run_order"]) != position or v not in SIZES
                    or p not in PROFILES or key in samples):
                raise ValueError(f"invalid row {key} in {folder}")
            values = [int(row[m]) for m in METRICS]
            if min(values) <= 0 or tuple(int(row[m]) for m in ("pk_bytes", "sk_bytes", "sig_bytes")) != SIZES[v]:
                raise ValueError(f"invalid values in {key}")
            samples[key] = values
        for v in SIZES:
            seq = [r["profile"] for r in rows if r["variant"] == v]
            for start in range(0, len(seq), 16):
                for slot in range(4):
                    if set(seq[start+slot:start+16:4]) != set(PROFILES):
                        raise ValueError(f"unbalanced positions {folder}, {v}")
        attestations.append({name: hashlib.sha256((folder/name).read_bytes()).hexdigest()
                             for name in ("raw.csv", "metadata.json", "memory.csv")})
    if not sessions:
        raise ValueError("no sessions")
    return samples, sessions, first_build, attestations


def resample(lengths, group):
    rng = np.random.default_rng(616)
    offset = 0
    parts = []
    for n in lengths:
        starts = group * rng.integers(n // group, size=(10000, n // group))
        parts.append((starts[:, :, None] + np.arange(group) + offset).reshape(10000, n))
        offset += n
    return np.concatenate(parts, axis=1)


def interval(values):
    return list(np.percentile(values, [2.5, 97.5]))


def summarize(samples, sessions, output):
    blocks = [(s, i) for s, indices in sessions.items() for i in indices]
    lengths = list(map(len, sessions.values()))
    draws = resample(lengths, 1)
    quartets = resample(lengths, 4)
    results = {}
    with (output / "summary.csv").open("x") as f, (output / "by_session.csv").open("x") as g:
        writer, by_session = csv.writer(f), csv.writer(g)
        writer.writerow(["variant","profile","metric","n","mean","median","sd","min","max",
                         "mean_lo","mean_hi","difference","diff_lo","diff_hi","percent",
                         "pct_lo","pct_hi","quartet_pct_lo","quartet_pct_hi"])
        by_session.writerow(["variant","profile","metric","session","n","mean","baseline_mean","percent"])
        for v in SIZES:
            for p in PROFILES:
                data = np.asarray([samples[s,i,v,p] for s,i in blocks])
                base = np.asarray([samples[s,i,v,"BASELINE"] for s,i in blocks])
                for j, metric in enumerate(METRICS):
                    a, b = data[:,j], base[:,j]
                    boot = a[draws].mean(axis=1)
                    control = b[draws].mean(axis=1)
                    percent = 100 * (a.mean()/b.mean()-1)
                    bounds = interval(100*(boot/control-1))
                    quartet = interval(100*(a[quartets].sum(axis=1)/b[quartets].sum(axis=1)-1))
                    results[v,p,metric] = a.mean(), percent, bounds
                    writer.writerow([v,p,metric,len(a),a.mean(),np.median(a),a.std(ddof=1),
                                     a.min(),a.max(),*interval(boot),a.mean()-b.mean(),
                                     *interval(boot-control),percent,*bounds,*quartet])
                    for s in sessions:
                        selected = [k for k, pair in enumerate(blocks) if pair[0] == s]
                        u, z = a[selected].mean(), b[selected].mean()
                        by_session.writerow([v,p,metric,s,len(selected),u,z,100*(u/z-1)])
    return results


def exhibits(results, output):
    rows = [r"\begin{tabular}{llrrr}", r"Set & Profile & KeyGen & Sign & Verify \\",
            r"\hline"]
    labels, estimates, bounds = [], [], []
    for v in SIZES:
        for profile in PROFILES:
            prefix = [v.replace("_", r"\_"), profile.replace("_", r"\_")]
            times = [results[v,profile,m][0]/1e6 for m in ("keygen_ns","sign_ns","verify_ns")]
            rows.append(" & ".join(prefix + [f"{x:.3f}" for x in times]) + r" \\")
            if profile != "BASELINE":
                _, point, ci = results[v,profile,"sign_ns"]
                labels.append(f"{v}  {profile}")
                estimates.append(point)
                bounds.append(ci)
    rows.append(r"\end{tabular}")
    (output/"results_tables.tex").write_text("% Mean elapsed milliseconds. See summary.csv for uncertainty.\n"
                                             + "\n".join(rows) + "\n")
    fig, ax = plt.subplots(figsize=(6.2, 4.1), layout="constrained")
    for y, (x, (lo, hi)) in enumerate(zip(estimates, bounds)):
        ax.plot([lo,hi],[y,y],color="#294467")
        ax.plot(x,y,"o",color="#294467",markersize=4)
    ax.set_yticks(range(len(labels)),labels,fontsize=8)
    ax.axvline(0, color="0.5", linestyle="--", linewidth=0.8)
    ax.invert_yaxis()
    ax.set_xlabel("Change in mean signing time vs. BASELINE (%)\nPointwise 95% paired bootstrap intervals")
    fig.savefig(output/"signing.pdf",metadata={"CreationDate":None,"ModDate":None})
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    data, sessions, build, hashes = read_sessions(args.root)
    args.output.mkdir(parents=True, exist_ok=False)
    results = summarize(data, sessions, args.output)
    exhibits(results, args.output)
    (args.output/"inputs.json").write_text(json.dumps({"build":build, "sessions":list(sessions),
        "input_sha256":hashes, "numpy": np.__version__, "matplotlib": matplotlib.__version__}, indent=2)+"\n")
