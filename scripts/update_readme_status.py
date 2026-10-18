"""Regenerates the result section of README.md from output/verdict.json and output/leaderboard.csv, so the README can never contradict the data.

The block between the markers  <!-- STATUS:BEGIN -->  and  <!-- STATUS:END -->  is replaced on every build. Called by build_report.py.
"""
import csv
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gate_labels as GL  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
BEGIN, END = "<!-- STATUS:BEGIN -->", "<!-- STATUS:END -->"
DASH = chr(8211)


def _names():
    with open(ROOT / "data/registries/states.csv", encoding="utf-8") as f:
        return {r["state_id"]: r["state_name"] for r in csv.DictReader(f)}


def _pair(code, names):
    a, b = code.split("-")
    return f"{names[a]}{DASH}{names[b]}"


def render(v):
    nl = chr(10)
    names = _names()
    with open(ROOT / "output/leaderboard.csv", encoding="utf-8") as f:
        lb = list(csv.DictReader(f))
    gates = v.get("gates", {})
    n_pass = sum(1 for ok in gates.values() if ok)
    lead = v.get("favored_pair", v.get("leading_pair"))
    tier = ", ".join(_pair(t, names) for t in v.get("tied_tier", []))
    lines = []
    if v.get("declared_winner"):
        lines.append(f"**Winner: {_pair(v['declared_winner'], names)}.** It clears all {len(gates)} verdict gates; first in {100 * v['leading_P_rank1']:.1f}% of 800 simulations, top three in {100 * v['leading_P_top3']:.1f}%.")
    else:
        lines.append(f"**I am not declaring a winner. The favorite is {_pair(lead, names)}.** It ranks first in **{100 * v['leading_P_rank1']:.1f}%** of 800 Monte Carlo simulations "
                     f"and in the top three in **{100 * v['leading_P_top3']:.1f}%**. The leading tier is {tier}. "
                     f"The favorite clears {n_pass} of my {len(gates)} verdict gates and fails {len(gates) - n_pass}.")
    lines += ["", "| Rank | Pair | Reciprocal score M | 90% interval | First in | Top 3 in |", "|---|---|---|---|---|---|"]
    for r in lb[:5]:
        lines.append(f"| {r['rank']} | {_pair(r['state_a'] + '-' + r['state_b'], names)} | {float(r['M']):.4f} | {float(r['M_p05']):.4f} to {float(r['M_p95']):.4f} | "
                     f"{100 * float(r['P_rank1']):.1f}% | {100 * float(r['P_top3']):.1f}% |")
    failed = v.get("failed_gates", [])
    if failed:
        lines += ["", "Gates the favorite does not clear:", ""]
        for g in failed:
            lines.append(f"- **{GL.label_for(g)}.** {GL.statement_for(g)}")
    lines += ["", "The full leaderboard, every gate, the robustness table and the evidence behind each failure are in [`docs/RESULTS.md`](docs/RESULTS.md); "
              "what the results do not establish is in [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md)."]
    return nl.join(lines)


def update(v):
    p = ROOT / "README.md"
    s = p.read_text(encoding="utf-8")
    if BEGIN not in s or END not in s:
        return False
    a, b = s.index(BEGIN) + len(BEGIN), s.index(END)
    p.write_text(s[:a] + chr(10) + render(v) + chr(10) + s[b:], encoding="utf-8", newline=chr(10))
    return True


if __name__ == "__main__":
    import json
    update(json.loads((ROOT / "output" / "verdict.json").read_text(encoding="utf-8")))
