"""Figures for the project story (docs/STORY.md). Re-run after any model rebuild:

    python scripts/build_story_figures.py

Writes PNGs to docs/figures/. Every figure reads only committed model outputs.
"""
import csv
import pathlib
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from paths import ROOT  # noqa: E402
import gate_labels as GL  # noqa: E402

MODEL = ROOT / "data" / "model"
FIG = ROOT / "docs" / "figures"
INK, MUTED, HOT, COOL, GOLD = "#1c1c1a", "#6b6b64", "#c2410c", "#2f6f8f", "#b8860b"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 150, "savefig.bbox": "tight", "savefig.facecolor": "white"})


def rd(name):
    with open(MODEL / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fig_leaderboard():
    unc = {(r["state_a"], r["state_b"]): r for r in rd("pair_uncertainty.csv")}
    top = rd("pair_scores.csv")[:15]
    names = [f"{r['state_a']}-{r['state_b']}" for r in top][::-1]
    m = np.array([float(r["M"]) for r in top])[::-1]
    lo = np.array([float(unc[(r["state_a"], r["state_b"])]["M_p05"]) for r in top])[::-1]
    hi = np.array([float(unc[(r["state_a"], r["state_b"])]["M_p95"]) for r in top])[::-1]
    p1 = np.array([float(unc[(r["state_a"], r["state_b"])]["P_rank1"]) for r in top])[::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(names, m, color=[HOT if p > 0.04 else COOL for p in p1], alpha=0.9)
    ax.errorbar(m, names, xerr=[m - lo, hi - m], fmt="none", ecolor=INK, elinewidth=1, capsize=2)
    for y, (mm, p) in enumerate(zip(m, p1)):
        if p >= 0.04:
            ax.text(hi[y] + 0.001, y, f"#1 in {p:.0%} of runs", va="center", fontsize=8, color=HOT)
    ax.set_xlabel("Reciprocal score M (bars: 5th to 95th percentile of 800 simulations)")
    ax.set_title("The leading tier: three pairs, one favored", loc="left", fontsize=12, color=INK)
    fig.savefig(FIG / "fig01_leaderboard.png")
    plt.close(fig)


def fig_channels():
    led = [r for r in rd("channel_ledger.csv") if r["pair_rank"] == "1"]
    fig, axes = plt.subplots(2, 1, figsize=(7, 3.4), sharex=True)
    palette = [HOT, GOLD, COOL, "#8a8a80", "#b9b9ae", "#d7d7ce"]
    for ax, dr in zip(axes, ("IL->WI", "WI->IL")):
        rows = [r for r in led if r["direction"] == dr][:6]
        left = 0.0
        for k, r in enumerate(rows):
            w = float(r["share_of_directed_H"])
            ax.barh([0], [w], left=left, color=palette[k], edgecolor="white")
            if w > 0.06:
                ax.text(left + w / 2, 0, f"{r['supported_entity'].split()[-1]}\nvs {r['rival_entity'].split()[-1]}\n{w:.0%}", ha="center", va="center", fontsize=7.5, color="white")
            left += w
        ax.set_yticks([])
        ax.set_ylabel(dr.replace("->", " → "), rotation=0, ha="right", va="center")
        ax.spines["left"].set_visible(False)
        ax.set_xlim(0, 1)
    axes[-1].set_xlabel("Share of the directed score (each bar sums to about 100%; remainder is many tiny channels)")
    axes[0].set_title("One matchup carries about 70% of the Illinois-Wisconsin score", loc="left", fontsize=12, color=INK)
    fig.savefig(FIG / "fig02_ilwi_channels.png")
    plt.close(fig)


def fig_removal():
    rows = rd("removal_tests.csv")[:12]
    names = [r["pair"] for r in rows][::-1]
    kept = np.array([float(r["retained_share"]) for r in rows])[::-1]
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.barh(names, kept, color=[HOT if k < 0.5 else COOL for k in kept])
    ax.axvline(0.5, color=MUTED, lw=1, ls="--")
    ax.text(0.505, -0.9, "half", color=MUTED, fontsize=8)
    for y, k in enumerate(kept):
        ax.text(k + 0.01, y, f"{k:.0%}", va="center", fontsize=8, color=INK)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Share of the score that remains after deleting the pair's single strongest rivalry")
    ax.set_title("Which leaders are one matchup, and which are a system?", loc="left", fontsize=12, color=INK)
    fig.savefig(FIG / "fig03_edge_removal.png")
    plt.close(fig)


def fig_topdown():
    rows = rd("topdown_pairs.csv")
    bu = np.array([int(r["bottomup_rank"]) for r in rows])
    td = np.array([int(r["topdown_rank"]) for r in rows])
    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    ax.scatter(bu, td, s=6, color="#bdbdb2", alpha=0.6)
    top = [r for r in rows if int(r["bottomup_rank"]) <= 10]
    ax.scatter([int(r["bottomup_rank"]) for r in top], [int(r["topdown_rank"]) for r in top], s=34, color=HOT, zorder=3)
    for r in top:
        ax.annotate(f"{r['state_a']}-{r['state_b']}", (int(r["bottomup_rank"]), int(r["topdown_rank"])), textcoords="offset points", xytext=(5, 3), fontsize=7.5, color=INK)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.invert_yaxis()
    ax.set_xlim(0.8, 1300)
    ax.set_ylim(1300, 0.8)
    ax.set_xlabel("Rank from the team-by-team model (1 = strongest)")
    ax.set_ylabel("Rank from state-vs-state 'X sucks' searches")
    ax.set_title("Two independent views: where they agree and where they don't", loc="left", fontsize=11, color=INK)
    fig.savefig(FIG / "fig04_bottomup_vs_topdown.png")
    plt.close(fig)


def fig_coverage():
    import json
    a = json.loads((MODEL / "A_audit.json").read_text(encoding="utf-8"))["family_trends_coverage"]
    names = list(a)
    vals = np.array([a[k] for k in names])
    order = np.argsort(vals)
    fig, ax = plt.subplots(figsize=(7, 4.4))
    ax.barh([names[i] for i in order], [vals[i] for i in order], color=[HOT if vals[i] < 0.7 else COOL for i in order])
    ax.axvline(0.7, color=MUTED, ls="--", lw=1)
    ax.set_xlim(0, 1.02)
    ax.set_xlabel("Share of team-by-state cells with real Google Trends data")
    ax.set_title("From 11 measured sports to all 18", loc="left", fontsize=12, color=INK)
    fig.savefig(FIG / "fig05_coverage.png")
    plt.close(fig)


def fig_channel_check():
    rows = rd("channel_decomposition.csv")
    x = np.array([float(r["model_top_share"]) for r in rows])
    y = np.array([float(r["measured_share_of_that_unit"]) for r in rows])
    fig, ax = plt.subplots(figsize=(6, 5.6))
    xs = np.linspace(0, 1, 50)
    ax.fill_between(xs, np.clip(xs - 0.15, 0, 1), np.clip(xs + 0.15, 0, 1), color="#e5efe5", label="within 15 points (supported)")
    ax.plot(xs, xs, color=MUTED, lw=1)
    ok = np.abs(x - y) <= 0.15
    ax.scatter(x[~ok], y[~ok], s=26, color=HOT, label="model share too high or too low", zorder=3)
    ax.scatter(x[ok], y[ok], s=26, color=COOL, label="supported", zorder=3)
    for r, xx, yy in zip(rows, x, y):
        if r["pair_rank"] in ("1", "2", "4") and r["direction"] in ("IL->WI", "WI->IL", "NY->MA", "CA->WA", "WA->CA"):
            ax.annotate(r["direction"], (xx, yy), textcoords="offset points", xytext=(5, -9), fontsize=7.5, color=INK)
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("Share the model gives its biggest channel")
    ax.set_ylabel("Share measured from 'X suck' searches")
    ax.set_title("Is the biggest rivalry as big as the model says?", loc="left", fontsize=12, color=INK)
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.savefig(FIG / "fig06_channel_check.png")
    plt.close(fig)


def fig_original_vs_calibrated():
    orig = {(r["state_a"], r["state_b"]): int(r["rank"]) for r in rd("pair_scores_original.csv")}
    cal = {(r["state_a"], r["state_b"]): int(r["rank"]) for r in rd("pair_scores.csv")}
    keys = sorted(set(k for k, v in orig.items() if v <= 12) | set(k for k, v in cal.items() if v <= 12), key=lambda k: orig[k])
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    for k in keys:
        o, c = orig[k], cal[k]
        col = HOT if c - o >= 5 else (COOL if o - c >= 3 else MUTED)
        ax.plot([0, 1], [o, c], color=col, lw=1.6, marker="o", ms=4)
        ax.text(-0.04, o, f"{k[0]}-{k[1]}  {o}", ha="right", va="center", fontsize=8, color=INK)
        ax.text(1.04, c, f"{c}  {k[0]}-{k[1]}", ha="left", va="center", fontsize=8, color=INK)
    ax.set_xlim(-0.45, 1.45)
    ax.invert_yaxis()
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Original model", "With the place factor"])
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_title("Distance changes the middle of the pack, not the top", loc="left", fontsize=12, color=INK)
    fig.savefig(FIG / "fig07_original_vs_calibrated.png")
    plt.close(fig)


def fig_gate_scorecard():
    import json
    v = json.loads((ROOT / "output" / "verdict.json").read_text(encoding="utf-8"))
    plain = [(prefix, label) for prefix, label, _ in GL.GATES]
    rows = []
    for key, label in plain:
        g = next((k for k in v["gates"] if k.startswith(key)), None)
        if g is not None:
            rows.append((label, bool(v["gates"][g])))
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for y, (label, ok) in enumerate(rows[::-1]):
        ax.barh(y, 1, color=COOL if ok else HOT, alpha=0.9, height=0.7)
        ax.text(0.03, y, label, va="center", fontsize=8.5, color="white")
        ax.text(0.97, y, "pass" if ok else "FAIL", va="center", ha="right", fontsize=8.5, color="white", weight="bold")
    ax.set_xlim(0, 1)
    ax.set_yticks([])
    ax.set_xticks([])
    for sp in ("left", "bottom"):
        ax.spines[sp].set_visible(False)
    n_fail = sum(1 for _, ok in rows if not ok)
    ax.set_title(f"Illinois-Wisconsin against the gates: {len(rows) - n_fail} pass, {n_fail} fail", loc="left", fontsize=12, color=INK)
    fig.savefig(FIG / "fig08_gate_scorecard.png")
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    for f in (fig_leaderboard, fig_channels, fig_removal, fig_topdown, fig_coverage, fig_channel_check, fig_original_vs_calibrated, fig_gate_scorecard):
        f()
        print("wrote", f.__name__)


if __name__ == "__main__":
    main()
