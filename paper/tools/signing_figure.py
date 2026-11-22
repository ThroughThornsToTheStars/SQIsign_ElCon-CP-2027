"""Render the archived Sign contrasts at their final printed size."""
import csv
import subprocess

import matplotlib
matplotlib.use("Agg")
from matplotlib import font_manager, pyplot as plt

SETS = ("p324_3", "p500_27", "p664_17")
PROFILES = ("STREEBOG_HASH", "RUSSIAN_PRNG", "COMBINED")


def render(paths, output):
    # The DOCX requests 6.8 inches. Keeping the uncropped canvas makes the
    # 8-point labels exactly 8 points after insertion at that width.
    font_path = subprocess.check_output(["fc-match", "-f", "%{file}", "Times New Roman"], text=True)
    font_manager.fontManager.addfont(font_path)
    font_manager.findfont("Times New Roman", fallback_to_default=False)
    with plt.rc_context({"font.family": "Times New Roman", "font.size": 8,
                         "axes.labelsize": 8, "legend.fontsize": 8,
                         "xtick.labelsize": 8, "ytick.labelsize": 8}):
        fig, ax = plt.subplots(figsize=(6.8, 2.8))
        fig.subplots_adjust(left=0.30, right=0.98, bottom=0.19, top=0.88)
        rows = [(variant, profile) for variant in SETS for profile in PROFILES]
        positions = [i + i // 3 * .50 for i in range(len(rows))]
        ax.axvline(0, color="0.48", linewidth=.7, linestyle=":")
        series = [("Controlled (sessions 1–3)", "o", "#214965", -.13),
                  ("Replication (sessions 4–6)", "s", "#76422b", .13)]
        for path, (label, marker, color, shift) in zip(paths, series, strict=True):
            with open(path, newline="") as src:
                values = {(r["variant"], r["profile"]): r for r in csv.DictReader(src)
                          if r["metric"] == "sign_ns" and r["profile"] != "BASELINE"}
            if values.keys() != set(rows):
                raise ValueError(f"Incomplete Sign chart input: {path}")
            for i, key in enumerate(rows):
                row = values[key]
                x, lo, hi = (float(row[k]) for k in ("percent", "pct_lo", "pct_hi"))
                ax.errorbar(x, positions[i] + shift, xerr=[[x-lo], [hi-x]], fmt=marker,
                            color=color, markersize=3.1, markerfacecolor=color if marker == "o" else "white",
                            capsize=1.6, linewidth=.85, label=label if i == 0 else None)
        ax.set_yticks(positions, [f"{v}   {p}" for v, p in rows])
        ax.invert_yaxis()
        ax.tick_params(axis="y", length=0, pad=5)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.set_xlabel("Change in mean signing time relative to baseline (%)")
        ax.legend(loc="lower center", bbox_to_anchor=(.48, 1.01), ncol=2, frameon=False)
        fig.savefig(output, dpi=400)
        plt.close(fig)
