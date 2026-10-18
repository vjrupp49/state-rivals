"""Static visuals (M5): a state tile map of each state's strongest rival, written to output/state_map.html.

Self-contained HTML/SVG (no external libraries, light and dark aware). Each tile is a state coloured by the
reciprocal score M of its strongest partner; hovering shows its top five partners with M and the 5th-95th
percentile band. All values come from data/model/pair_scores.csv and pair_uncertainty.csv.

    python scripts/build_visuals.py
"""
import csv
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from paths import ROOT  # noqa: E402

MODEL = ROOT / "data" / "model"
OUT = ROOT / "output" / "state_map.html"
# (row, col) grid positions of the common 50-state tile map
GRID = {
    "AK": (0, 0), "ME": (0, 10), "VT": (1, 9), "NH": (1, 10),
    "WA": (2, 0), "ID": (2, 1), "MT": (2, 2), "ND": (2, 3), "MN": (2, 4), "IL": (2, 5), "WI": (2, 6), "MI": (2, 7), "NY": (2, 8), "RI": (2, 9), "MA": (2, 10),
    "OR": (3, 0), "NV": (3, 1), "WY": (3, 2), "SD": (3, 3), "IA": (3, 4), "IN": (3, 5), "OH": (3, 6), "PA": (3, 7), "NJ": (3, 8), "CT": (3, 9),
    "CA": (4, 0), "UT": (4, 1), "CO": (4, 2), "NE": (4, 3), "MO": (4, 4), "KY": (4, 5), "WV": (4, 6), "VA": (4, 7), "MD": (4, 8), "DE": (4, 9),
    "AZ": (5, 1), "NM": (5, 2), "KS": (5, 3), "AR": (5, 4), "TN": (5, 5), "NC": (5, 6), "SC": (5, 7),
    "OK": (6, 3), "LA": (6, 4), "MS": (6, 5), "AL": (6, 6), "GA": (6, 7),
    "HI": (7, 0), "TX": (7, 3), "FL": (7, 8),
}


def main():
    pairs = list(csv.DictReader(open(MODEL / "pair_scores.csv", encoding="utf-8")))
    unc = {(r["state_a"], r["state_b"]): r for r in csv.DictReader(open(MODEL / "pair_uncertainty.csv", encoding="utf-8"))}
    partners = {s: [] for s in GRID}
    for p in pairs:
        a, b, m = p["state_a"], p["state_b"], float(p["M"])
        u = unc.get((a, b), {})
        lo, hi = float(u.get("M_p05", 0) or 0), float(u.get("M_p95", 0) or 0)
        partners[a].append((b, m, lo, hi))
        partners[b].append((a, m, lo, hi))
    top = {s: sorted(v, key=lambda x: -x[1])[:5] for s, v in partners.items()}
    vmax = max(t[0][1] for t in top.values())
    data = {s: [{"with": w, "M": round(m, 5), "lo": round(lo, 5), "hi": round(hi, 5)} for w, m, lo, hi in t] for s, t in top.items()}
    ranks = {(p["state_a"], p["state_b"]): int(p["rank"]) for p in pairs}
    tiles = []
    for s, (r, c) in GRID.items():
        best = top[s][0]
        tiles.append(f'<g class="t" data-s="{s}" transform="translate({c * 64 + 8},{r * 64 + 8})" tabindex="0">'
                     f'<rect width="58" height="58" rx="8" style="--v:{best[1] / vmax:.3f}"/><text x="29" y="26" class="a">{s}</text>'
                     f'<text x="29" y="44" class="b">{best[0] if best[1] > 1e-9 else "none"}</text></g>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>State Rivals Map</title><style>
:root{{--bg:#fafaf7;--fg:#1c1c1a;--mut:#6b6b64;--card:#fff;--line:#e3e1d8;--hot:#c2410c;--cool:#e8e6dd}}
@media(prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#151513;--fg:#ecebe5;--mut:#9a988e;--card:#1f1f1c;--line:#34332e;--hot:#fb923c;--cool:#2a2a26}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}
main{{max-width:900px;margin:0 auto;padding:24px 16px}}h1{{font-size:22px;margin:0 0 4px}}.mut{{color:var(--mut)}}
svg{{width:100%;height:auto;display:block;margin:16px 0}}.t rect{{fill:color-mix(in srgb,var(--hot) calc(var(--v)*100%),var(--cool));stroke:var(--line);cursor:pointer}}
.t:hover rect,.t:focus rect,.t.sel rect{{stroke:var(--fg);stroke-width:2}}.t text{{text-anchor:middle;pointer-events:none}}
.a{{font-weight:700;font-size:15px;fill:var(--fg)}}.b{{font-size:11px;fill:var(--mut)}}
#d{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;min-height:130px}}
table{{border-collapse:collapse;width:100%}}td,th{{padding:4px 8px;text-align:left;border-bottom:1px solid var(--line)}}
</style></head><body><main>
<h1>Each state's strongest sports rival</h1>
<p class="mut">Tile colour = reciprocal score M of the state's strongest partner (darker orange is stronger); the small label is that partner. Provisional: rivalry and identity inputs are analyst priors and four sport families are unmeasured. Select a tile for its top five partners.</p>
<svg viewBox="0 0 720 520" role="img" aria-label="Tile map of the 50 states coloured by strongest rival score">{''.join(tiles)}</svg>
<div id="d"><span class="mut">Select a state.</span></div>
<p class="mut">Source: <code>data/model/pair_scores.csv</code>, <code>pair_uncertainty.csv</code>. Intervals are 5th to 95th percentile of the Monte Carlo.</p>
</main><script>
const D={json.dumps(data)};const R={json.dumps({f"{a}-{b}": r for (a, b), r in ranks.items()})};
function show(s){{document.querySelectorAll('.t').forEach(x=>x.classList.toggle('sel',x.dataset.s===s));
const rows=D[s].map(p=>{{const k=R[s+'-'+p.with]||R[p.with+'-'+s];return `<tr><td>${{s}}&ndash;${{p.with}}</td><td>${{p.M.toFixed(4)}}</td><td>${{p.lo.toFixed(4)}} to ${{p.hi.toFixed(4)}}</td><td>#${{k}}</td></tr>`}}).join('');
document.getElementById('d').innerHTML=`<b>${{s}}</b><table><tr><th>Pair</th><th>M</th><th>90% band</th><th>Rank of 1,225</th></tr>${{rows}}</table>`}}
document.querySelectorAll('.t').forEach(g=>{{g.addEventListener('click',()=>show(g.dataset.s));g.addEventListener('keydown',e=>{{if(e.key==='Enter')show(g.dataset.s)}})}});
</script></body></html>"""
    OUT.write_text(page, encoding="utf-8", newline="\n")
    print("wrote", OUT, f"{len(page) // 1024} KB")


if __name__ == "__main__":
    main()
