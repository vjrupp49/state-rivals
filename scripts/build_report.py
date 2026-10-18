"""Phase 10: verdict gate + report package.

Outputs: output/verdict.json, leaderboard.csv, report.html (self-contained), MORNING_BRIEFING.md,
and with --final: FINAL_STATUS.json.

VERDICT RULE (docs/PROTOCOL.md section 11): a named winner is declared ONLY if every gate passes; otherwise the
honest output is a tied tier / probabilistic result. Everything is stamped PROVISIONAL unless all sports
families are measured and the top-down validation has run.
"""
import csv
import datetime as dt
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gate_labels as GL
import qa_gate

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL, OUT = ROOT / "data" / "model", ROOT / "output"
from paths import WORK


def rd(p):
    return list(csv.DictReader(open(p, newline="", encoding="utf-8")))


def jl(p, default=None):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
    except Exception:
        return default


LEDGER = []
# Items that must be closed before the verdict is called final. Remove an item only when it is actually done (and say so in CHANGELOG).
def informative_variants(variants):
    """Variants that can change the answer: not the base, not a leave-out, ranking correlation with the base below 0.99."""
    return [v for v in variants if v["variant"] != "base" and not v["variant"].startswith("leave_out_") and float(v["spearman_vs_base"]) < 0.99]


def relevant_leave_outs(variants, drivers, groups):
    """Leave-one-sport-out variants for sports that drive the lead pair (their family set intersects the driving families)."""
    return [v for v in variants if v["variant"].startswith("leave_out_") and groups.get(v["variant"][len("leave_out_"):], set()) & set(drivers)]


def open_items(diag):
    """Limitations that qualify the verdict; sentences about measured results are built from the data (diag), never hand-typed.
    docs/LIMITATIONS.md is the human-readable register."""
    dom = diag.get("dominance_detail", {})
    dom_txt = "; ".join(k + ": " + v for k, v in dom.items()) or "not computed"
    prox = diag.get("second_proxy_detail", {})
    prox_txt = "; ".join(k + (" agrees" if v else " DISAGREES") for k, v in prox.items()) or "not computed"
    det = diag.get("families_below_50pct_detected_coverage", [])
    lo25 = diag.get("relevant_leave_out_at_2.5pct_share", "n/a")
    return [
        "College sport-level weights were re-measured with topic terms after the first review; the small regional sports (hockey, wrestling, volleyball, lacrosse) still sit at the detection floor relative to the NFL anchor, so their sport-level weights are upper bounds",
        "Families with fewer than half of their team-by-state cells detected (the rest censored, carried as bounded floors): " + (", ".join(det) or "none") + ", so shares for these rest on few detected cells",
        "Dominance of the lead pair biggest matchup, as measured: " + dom_txt + " (a direction is inconclusive without at least three detected units covering 80% of the model mass and, for the corrected measure, comparable units)",
        "Second proxies for that dominance: " + prox_txt + ". A same-platform proxy that contradicts blocks the gate; the independent Wikipedia proxy is national and carries no geography",
        "The refined single-matchup rule: its text was written before the channel measurements but it was adopted after seeing them and after the original edge-removal gate had failed for the lead pair",
        "The model over-concentrates hostility on one marquee matchup in most testable directions (see docs/CHANNEL_DECOMPOSITION.md), and the leading pair changes under the flat-tier prior and under flat sport weights",
        "The Monte Carlo samples measurement and parameter noise but not structural alternatives (tier ladder, sport weights), so the probability of finishing first is conditional on the model structure; the relevant-leave-out gate is threshold-dependent (driver share at least 5%; at 2.5% the result would be: " + str(lo25) + ")",
        "Monte Carlo noise for edges is derived from the model misfit on NFL, MLB and NBA teams (in-sample) and applied to every edge; per-sport systematic multipliers (sd 0.30) are my own choice and not identifiable from team-level data",
        "The identity layer E (which state a team stands for) has only an exploratory measurement (embodiment index for 40 teams and schools; the Bears are +0.46 against +0.80 for the Packers while E gives both 0.95 to their home state)",
        "The corroboration thresholds were fixed before their table was computed but after the lead pairs state-level ranks were already known; the state-level rank is out of the 677 pairs measured in both directions; the searches-only check was inconclusive for most of the top pairs; the place factor was fixed after a first look at the estimates and replicated only on college schools",
        "Raw Google Trends payloads are not published, so a stranger cannot rebuild the results from the repository alone; only stages downstream of the cache are reproducible",
        "Three independent reviews were completed (2026-10-16, 2026-10-17, 2026-10-18) and their findings addressed (see CHANGELOG)",
    ]


def verdict(pairs, unc, variants, removal, audit, td, qa):
    gates, reasons = {}, []
    top = unc[0] if unc else None
    by_rank1 = sorted(unc, key=lambda u: -float(u["P_rank1"]))[0]
    cand = by_rank1
    key = (cand["state_a"], cand["state_b"])
    unmeasured = audit.get("families_unmeasured_to_OTHER", [])
    gates["all_sport_families_have_data(censored_floor_cells_count_as_data)"] = not unmeasured
    gates["monte_carlo_P_rank1>=0.5"] = float(cand["P_rank1"]) >= 0.5
    base_top = "-".join(key)
    # Only INFORMATIVE variants count: a variant whose ranking correlates at least 0.99 with the base cannot change the answer, so it cannot support or
    # contradict it (padding the denominator with near-null variants would let the gate pass by construction).
    vs = informative_variants(variants)
    rk1 = sum(1 for v in vs if v["top5"].split(";")[0] == base_top)
    gates["holds_rank1_in>=80%_of_informative_variants(spearman<0.99)"] = bool(vs) and rk1 / len(vs) >= 0.8
    # Only leave-outs of sports that actually carry the lead pair count (leaving out softball cannot hurt a football pair).
    import robustness as RB
    cand_rank0 = next((str(p_["rank"]) for p_ in pairs if {p_["state_a"], p_["state_b"]} == set(key)), "1")
    drv0 = {r["sport_family"] for r in LEDGER if r["pair_rank"] == cand_rank0 and float(r["share_of_directed_H"]) >= 0.05}
    lo = relevant_leave_outs(variants, drv0, RB.GROUPS)
    drv25 = {r["sport_family"] for r in LEDGER if r["pair_rank"] == cand_rank0 and float(r["share_of_directed_H"]) >= 0.025}
    lo25 = relevant_leave_outs(variants, drv25, RB.GROUPS)
    lo25_txt = f"{sum(1 for v in lo25 if 0 < int(v['base_top1_rank']) <= 5)} of {len(lo25)} keep it in the top 5"
    gates["top5_in>=75%_of_relevant_leave_one_sport_out(sports_that_drive_the_pair)"] = bool(lo) and sum(1 for v in lo if 0 < int(v["base_top1_rank"]) <= 5) / len(lo) >= 0.75
    rem = next((r for r in removal if r["pair"] == base_top), None)
    survives = bool(rem) and int(rem["approx_rank_after"]) <= 10
    # Refined single-matchup rule (docs/RIVALRY_WEIGHT_DESIGN.md section 7; its text was written before the channel measurements, but it was ADOPTED after seeing them and after
    # the original removal gate had failed for the leading pair; reported as such). A pair that leans on one matchup passes only if MEASURED antipathy supports the
    # dominance in BOTH directions on BOTH the raw and the ambient-corrected measure (testable: >= 3 units, >= 80% of the model mass), and a second
    # independent proxy agrees. Inconclusive directions never count as support.
    a_, b_ = key
    try:
        cd = rd(MODEL / "channel_decomposition.csv")
    except Exception:
        cd = []
    dirs = {f"{a_}->{b_}", f"{b_}->{a_}"}
    mine = [r for r in cd if r["direction"] in dirs]
    dom_detail = {r["direction"]: r.get("verdict", "n/a") for r in mine}
    dom = len(mine) == 2 and all(r.get("verdict") == "supported" for r in mine)
    try:
        p2 = [r for r in rd(MODEL / "second_proxy.csv") if r["pair"] == base_top]
    except Exception:
        p2 = []
    # the second-proxy gate needs an INDEPENDENT proxy that agrees AND no other proxy (including same-platform ones) that contradicts: no cherry-picking
    indep = [r for r in p2 if r["independence"].startswith("independent")]
    goog = [r for r in p2 if "same platform" in r["independence"]]
    proxy2 = bool(indep) and len(goog) >= 2 and all(r["agrees"] == "True" for r in p2)      # an absent proxy can never pass the gate
    proxy_detail = {r["direction"] + " | " + r["proxy"]: (r["agrees"] == "True") for r in p2}
    gates["single_matchup_dependence_resolved(survives_edge_removal_or_dominance_supported_both_directions_raw_and_excess)"] = survives or dom
    gates["second_independent_proxy_agrees_on_dominance"] = survives or proxy2
    try:
        corr = next((r for r in rd(MODEL / "corroboration.csv") if r["pair"] == base_top), None)
    except Exception:
        corr = None
    gates["corroborated(state_level_searches,searches_only_score,reciprocity)"] = bool(corr) and corr["corroborated"] == "True"
    diagnostics = {"relevant_leave_out_at_2.5pct_share": lo25_txt, "families_below_50pct_detected_coverage": sorted(f_ for f_, c_ in audit.get("family_detected_coverage", {}).items() if c_ < 0.5), "survives_strongest_edge_removal_top10": survives, "measured_dominance_supported_both_directions": dom, "dominance_detail": dom_detail, "second_proxy_agrees": proxy2, "second_proxy_detail": proxy_detail,
                   "type": (corr or {}).get("type", "n/a"),
                   "informative_variants": [{"variant": v["variant"], "lead_rank": int(v["base_top1_rank"])} for v in vs],
                   "relevant_leave_outs": [{"variant": v["variant"], "lead_rank": int(v["base_top1_rank"])} for v in lo],
                   "driver_sport_families": sorted(drv0),
                   "edge_removal": {"retained_share": float(rem["retained_share"]), "rank_after": int(rem["approx_rank_after"]), "edge": rem["removed_edge"]} if rem else None}
    flat = next((v for v in variants if v["variant"].startswith("flat_tier")), None)
    gates["top5_under_flat_tier_prior"] = bool(flat) and 0 < int(flat["base_top1_rank"]) <= 5
    trc = audit.get("family_trends_coverage", {})
    cand_rank = next((str(p_["rank"]) for p_ in pairs if {p_["state_a"], p_["state_b"]} == set(key)), "1")
    drv = {r["sport_family"] for r in LEDGER if r["pair_rank"] == cand_rank and float(r["share_of_directed_H"]) >= 0.05}
    detc = audit.get("family_detected_coverage", trc)
    gates["detected_trends_coverage>=70%_in_families_driving_the_lead_pair"] = bool(drv) and all(detc.get(f_, 0) >= 0.7 for f_ in drv)
    gates["top_down_validation_completed"] = bool(td and td.get("completed"))
    lead_td = next((r for p_, r in (td or {}).get("bottomup_top10_with_topdown_rank", []) if p_ == base_top or "-".join(reversed(p_.split("-"))) == base_top), None)
    gates["lead_pair_within_top50_of_independent_top-down_ranking"] = lead_td is not None and 0 < lead_td <= 50     # 0 means not measured in both directions: never a pass
    gates["qa_no_failures"] = not any(c["status"] == "fail" for c in qa)
    declared = all(gates.values())
    tier = [f"{u['state_a']}-{u['state_b']}" for u in unc if float(u["P_top3"]) >= 0.25][:8] or [f"{u['state_a']}-{u['state_b']}" for u in unc[:5]]
    for g, ok in gates.items():
        if not ok:
            reasons.append(g)
    return {"declared_winner": base_top if declared else None, "leading_pair": base_top, "favored_pair": base_top,
            "leading_P_rank1": float(cand["P_rank1"]), "leading_P_top3": float(cand["P_top3"]), "tied_tier": tier,
            "gates": gates, "failed_gates": reasons, "failed_gate_labels": [GL.label_for(g_) for g_ in reasons], "provisional": True, "open_items": open_items(diagnostics), "diagnostics": diagnostics}


HTML = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>State Rivals Report</title><style>
:root{--bg:#fbfaf7;--fg:#1d2330;--mut:#5c6578;--card:#fff;--bd:#dcd8cf;--ac:#0b6b66;--warn:#a4570a;--bad:#a02323}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#13161d;--fg:#e9ecf3;--mut:#9aa3b5;--card:#1b2029;--bd:#2c3340;--ac:#4fc1b9;--warn:#e0a458;--bad:#ef7a7a}}
:root[data-theme=dark]{--bg:#13161d;--fg:#e9ecf3;--mut:#9aa3b5;--card:#1b2029;--bd:#2c3340;--ac:#4fc1b9;--warn:#e0a458;--bad:#ef7a7a}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.55 system-ui,Segoe UI,sans-serif}
main{max-width:1100px;margin:0 auto;padding:20px 16px 80px}h1{font-size:1.9rem;margin:.2em 0}h2{margin-top:2.2em;border-bottom:1px solid var(--bd);padding-bottom:.3em}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px 16px;margin:12px 0}.mut{color:var(--mut)}.pill{display:inline-block;padding:2px 10px;border-radius:99px;font-size:.8rem;border:1px solid var(--bd)}
.prov{color:var(--warn);border-color:var(--warn)}.ok{color:var(--ac);border-color:var(--ac)}table{border-collapse:collapse;width:100%;font-size:.9rem}th,td{padding:6px 8px;border-bottom:1px solid var(--bd);text-align:left;vertical-align:top}
th{position:sticky;top:0;background:var(--card)}.num{text-align:right;font-variant-numeric:tabular-nums}.scroll{overflow-x:auto}canvas{max-width:100%;border:1px solid var(--bd);border-radius:6px}
select,button,input{font:inherit;padding:4px 8px;background:var(--card);color:var(--fg);border:1px solid var(--bd);border-radius:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
.bar{height:8px;background:var(--ac);border-radius:4px}.kpi{font-size:1.5rem;font-weight:650}
</style></head><body><main>
<h1>Which pair of U.S. states has the greatest sports antagonism?</h1>
<p class="mut">Current, reciprocal, population-penetrating hostility across all 1,225 state pairs &middot; generated __GEN__</p>
<div class="card" id="verdict"></div>
<h2>Leaderboard</h2><p class="mut">M = geometric mean of the two directed hostility scores (D-005). Intervals and probabilities come from __NMC__ Monte Carlo draws over attention, rivalry and identity uncertainty.</p>
<div class="scroll"><table id="lb"></table></div><p><button id="more">Show all 1,225</button> <span class=mut>(full table also saved as output/leaderboard.csv)</span></p>
<h2>Pair map</h2><p class="mut">Each cell is M for a state pair (log scale). Click a cell to inspect it.</p><canvas id="hm" width="760" height="760"></canvas>
<div id="tip" class="mut"></div>
<h2>Pair explorer</h2><div class="card"><select id="sa"></select> vs <select id="sb"></select><div id="ex"></div></div>
<h2>State profile: who does each state follow?</h2><div class="card"><select id="sp"></select><div id="spx"></div></div>
<h2>How robust is the ranking?</h2><div class="scroll"><table id="rob"></table></div><h3>Strongest-edge removal (top 30 pairs)</h3><div class="scroll"><table id="rem"></table></div>
<h2>Independent top-down validation</h2><div class="card" id="td"></div>
<h2>Data coverage and provenance</h2><div class="grid" id="cov"></div><div class="card" id="prog"></div>
<h2>Method in brief</h2><div class="card">__METHOD__</div>
<h2>Limitations and what is not done</h2><div class="card">__LIMITS__</div>
<h2>Reproduce</h2><div class="card">See <code>README.md</code>. <code>python scripts/finalize.py</code> rebuilds everything from the local Google Trends cache; <code>python scripts/finalize.py --from-derived</code> re-runs the model, charts and verdict from the committed derived tables (it reuses the committed uncertainty outputs). Raw Trends payloads are not published.</div>
</main><script>
const D=__DATA__;const S=D.states,n=S.length,idx=Object.fromEntries(S.map((s,i)=>[s,i]));
const f=(x,d=3)=>x==null?'':(+x).toPrecision(d);const key=(a,b)=>a<b?a+'-'+b:b+'-'+a;
const vd=D.verdict;document.getElementById('verdict').innerHTML=
 `<span class="pill ${vd.declared_winner?'ok':'prov'}">${vd.declared_winner?'ALL GATES PASSED':'NO WINNER DECLARED'}</span>
 <p class="kpi">${vd.declared_winner?('Declared winner: '+vd.declared_winner):('Favorite: '+vd.leading_pair)}</p>
 <p>${vd.declared_winner?'The leading pair passed every robustness and validation gate.':'I am not declaring a winner: under my verdict rule the honest output is a leading tier and a favorite. The favorite is <b>'+vd.leading_pair+'</b> (first in '+(100*vd.leading_P_rank1).toFixed(1)+'% of 800 simulations, top three in '+(100*vd.leading_P_top3).toFixed(1)+'%). Leading tier: <b>'+vd.tied_tier.join(', ')+'</b>.'}</p>
 ${vd.failed_gates.length?'<p class="mut">Gates not passed: '+(vd.failed_gate_labels||vd.failed_gates).join('; ')+'</p>':''}`;
const rows=D.pairs;let shown=25;
function lb(){const t=document.getElementById('lb');t.innerHTML='<tr><th>#</th><th>Pair</th><th class=num>M</th><th class=num>90% interval</th><th class=num>P(rank 1)</th><th class=num>P(top 3)</th><th class=num>Reciprocity</th><th>Lead channel</th></tr>'+
 rows.slice(0,shown).map(r=>`<tr><td>${r.rank}</td><td><b>${r.a}&ndash;${r.b}</b></td><td class=num>${f(r.M)}</td><td class=num>${f(r.p05,2)}&ndash;${f(r.p95,2)}</td><td class=num>${(100*r.p1).toFixed(0)}%</td><td class=num>${(100*r.p3).toFixed(0)}%</td><td class=num>${f(r.rec,2)}</td><td>${r.ch||''}</td></tr>`).join('')}
lb();document.getElementById('more').onclick=e=>{shown=shown==25?rows.length:25;e.target.textContent=shown==25?'Show all 1,225':'Show top 25';lb()};
const cv=document.getElementById('hm'),cx=cv.getContext('2d'),cs=cv.width/n,flat=D.M.flat().filter(x=>x>0).sort((a,b)=>a-b);
const lo=Math.log10(flat[Math.floor(flat.length*.05)]||1e-9),hi=Math.log10(flat[flat.length-1]||1);
function colr(v){if(v<=0)return'#eee';const t=Math.max(0,Math.min(1,(Math.log10(v)-lo)/(hi-lo)));return`rgb(${Math.round(245-215*t)},${Math.round(247-120*t)},${Math.round(240-130*t)})`}
S.forEach((a,i)=>S.forEach((b,j)=>{cx.fillStyle=i==j?'#ccc':colr(D.M[i][j]);cx.fillRect(j*cs,i*cs,cs-.5,cs-.5)}));
cx.fillStyle='#333';cx.font='9px sans-serif';S.forEach((s,i)=>{cx.fillText(s,0,i*cs+cs*.8)});
cv.onmousemove=e=>{const r=cv.getBoundingClientRect(),j=Math.floor((e.clientX-r.left)/r.width*n),i=Math.floor((e.clientY-r.top)/r.height*n);if(i>=0&&j>=0&&i<n&&j<n)document.getElementById('tip').textContent=S[i]+' & '+S[j]+': M='+f(D.M[i][j])};
cv.onclick=e=>{const r=cv.getBoundingClientRect(),j=Math.floor((e.clientX-r.left)/r.width*n),i=Math.floor((e.clientY-r.top)/r.height*n);if(i!=j){sa.value=S[i];sb.value=S[j];ex();location.hash='#ex'}};
const sa=document.getElementById('sa'),sb=document.getElementById('sb'),sp=document.getElementById('sp');
[sa,sb,sp].forEach(s=>s.innerHTML=S.map(x=>`<option>${x}</option>`).join(''));sa.value=rows[0].a;sb.value=rows[0].b;
function ex(){const a=sa.value,b=sb.value,i=idx[a],j=idx[b];if(a==b){document.getElementById('ex').innerHTML='Pick two different states.';return}
 const k=key(a,b),ch=(D.ledger[k]||[]),p=D.pairmap[k]||{};
 document.getElementById('ex').innerHTML=`<p>M = <b>${f(D.M[i][j])}</b> &middot; ${a}&rarr;${b} H=${f(D.H[i][j])} &middot; ${b}&rarr;${a} H=${f(D.H[j][i])} &middot; rank ${p.rank||'?'} &middot; P(top 3) ${p.p3!=null?(100*p.p3).toFixed(0)+'%':'?'}</p>`+
 (ch.length?'<div class=scroll><table><tr><th>Direction</th><th>Supported entity</th><th>Rival entity</th><th>Embodies</th><th class=num>Share of direction</th></tr>'+ch.map(c=>`<tr><td>${c[0]}</td><td>${c[1]}</td><td>${c[2]}</td><td>${c[3]}</td><td class=num>${(100*c[4]).toFixed(1)}%</td></tr>`).join('')+'</table></div>':'<p class="mut">Channel ledger is stored for the top pairs only.</p>')}
sa.onchange=sb.onchange=ex;ex();
function spf(){const s=sp.value;document.getElementById('spx').innerHTML='<table><tr><th>Entity</th><th class=num>A (share of state attention)</th><th>Confidence</th></tr>'+(D.prof[s]||[]).map(r=>`<tr><td>${r[0]}</td><td class=num>${(100*r[1]).toFixed(1)}%</td><td>${r[2]}</td></tr>`).join('')+'</table><p class=mut>OTHER (unmeasured / unregistered sports): '+(100*D.other[s]).toFixed(1)+'%</p>'}
sp.onchange=spf;spf();
document.getElementById('rob').innerHTML='<tr><th>Variant</th><th>Top 5 pairs</th><th class=num>Rank of base #1</th><th class=num>Spearman vs base</th></tr>'+D.variants.map(v=>`<tr><td>${v.variant}</td><td>${v.top5.replace(/;/g,', ')}</td><td class=num>${v.base_top1_rank}</td><td class=num>${v.spearman_vs_base}</td></tr>`).join('');
document.getElementById('rem').innerHTML='<tr><th>Pair</th><th>Removed edge</th><th class=num>Share of M kept</th><th class=num>Approx. rank after</th></tr>'+D.removal.map(v=>`<tr><td>${v.pair}</td><td>${v.removed_edge}</td><td class=num>${(100*v.retained_share).toFixed(0)}%</td><td class=num>${v.approx_rank_after}</td></tr>`).join('');
document.getElementById('cov').innerHTML=Object.entries(D.coverage).map(([k,v])=>{const t=D.trends_coverage[k]||0;const d=(D.detected_coverage||{})[k]||0;return `<div class=card><b>${k}</b><div class=bar style="width:${Math.round(100*d)}%"></div><span class=mut>Detected (not censored) cells: ${(100*d).toFixed(0)}% &middot; with any Trends value incl. below-detection floors: ${(100*t).toFixed(0)}% &middot; any signal incl. county map: ${(100*v).toFixed(0)}%${d<.5?' &mdash; most cells are below detection (carried as bounded floors)':''}</span></div>`}).join('');
document.getElementById('prog').innerHTML=D.progress+'<br>'+D.qa;
(function(){const t=D.topdown,el=document.getElementById('td');if(!t||!t.completed){el.innerHTML='<p class=mut>Top-down pulls not complete; no validation claimed.</p>';return}
 el.innerHTML=`<p>A separate, team-agnostic signal: how often residents of one state search "&lt;other state&gt; sucks" (Google Trends, 5 years). Reciprocal score vs. my bottom-up M across the ${t.pairs_measured_both_directions||'measured'} pairs measured in both directions (of 1,225): <b>Spearman &rho; = ${t.spearman_topdown_vs_bottomup}</b>; top-20 overlap: <b>${t.top20_overlap} of 20</b>. This signal mixes sports and non-sports hostility, so treat it as a cross-check, never an input.</p>
 <div class=grid><div><b>Top-down top 15</b> (bottom-up rank)<table>${t.topdown_top15_with_bottomup_rank.map(r=>`<tr><td>${r[0]}</td><td class=num>#${r[1]}</td></tr>`).join('')}</table></div>
 <div><b>Bottom-up top 10</b> (top-down rank)<table>${t.bottomup_top10_with_topdown_rank.map(r=>`<tr><td>${r[0]}</td><td class=num>#${r[1]}</td></tr>`).join('')}</table></div></div>
 <p class=mut>Reading: where the two lists disagree is a finding, not noise to clean away. The top-down list leans toward college-football rivalry states, which the team-by-team model tends to under-weight.</p>`})();
</script></body></html>"""

METHOD = """<p>Resident sports attention A flows through teams, into directed rivalries R = S&#8857;T, and lands on the state identity each rival embodies (E): <b>H = A(S&#8857;T)E</b>; pair score <b>M = &radic;(H<sub>ab</sub>H<sub>ba</sub>)</b>. Attention A = W &times; P: W is each state's sport mix (Google Trends topic terms, blended with national survey priors), P splits a sport among teams (anchored Google Trends regional shares, blended with population-weighted county-plurality maps). Trends data are integer percent shares among 5 terms per state; two anchor terms per batch put batches on one scale; zeros are treated as below detection, never as true zero.</p>"""
LIMITS = """<ul><li><b>No winner is declared.</b> Illinois-Wisconsin is the favorite under the model&#39;s own assumptions, but four gates fail (robustness under alternative tier and sport-weight assumptions, dominance of its biggest matchup untestable on the corrected measure, and a contradicting second proxy). The full register is in <code>docs/LIMITATIONS.md</code>.</li><li><b>The rivalry layer (S, T) is my prior</b> (tiers .40/.20/.08 and .85/.65/.45), tested against measured antipathy searches and Wikipedia readership; the flat-tier and flat-sport-weight variants show how much the answer depends on those judgments.</li><li><b>Entity-to-state identity (E) is rule-based</b> (home state 95% with documented exceptions) with only an exploratory measurement.</li><li><b>Most college team-by-state cells are below detection</b> (censored; carried as bounded floors, never zero), and the small regional sports sit at the detection floor, so their sport-level weights are upper bounds.</li><li>County-plurality maps measure population living in plurality counties, not fan share; the NHL map predates the Utah relocation.</li><li>Google Trends via an unofficial endpoint: relative, rounded, rate-limited; raw payloads are not published, so only stages downstream of the local cache are re-runnable.</li><li>The Monte Carlo samples measurement and parameter noise but not structural alternatives (tier ladder, sport weights), which change the favorite; &quot;first in about two thirds of runs&quot; is conditional on the model&#39;s structure.</li></ul>"""


def main(final=False):
    OUT.mkdir(exist_ok=True)
    qa = qa_gate.run()
    ps = rd(MODEL / "pair_scores.csv")
    unc = rd(MODEL / "pair_uncertainty.csv") if (MODEL / "pair_uncertainty.csv").exists() else []
    variants = rd(MODEL / "robustness_variants.csv") if (MODEL / "robustness_variants.csv").exists() else []
    removal = rd(MODEL / "removal_tests.csv") if (MODEL / "removal_tests.csv").exists() else []
    audit = jl(MODEL / "A_audit.json", {})
    td = jl(MODEL / "topdown.json", {})
    rob = jl(MODEL / "robustness.json", {})
    st = jl(WORK / "STATE.json", {})
    LEDGER[:] = rd(MODEL / "channel_ledger.csv")   # the coverage gate reads the lead pair's channels, so load them BEFORE verdict()
    v = verdict(ps, unc, variants, removal, audit, td, qa) if unc else {"declared_winner": None, "leading_pair": ps[0]["state_a"] + "-" + ps[0]["state_b"],
        "leading_P_rank1": 0, "leading_P_top3": 0, "tied_tier": [], "gates": {}, "failed_gates": ["monte_carlo_not_run"], "provisional": True}
    (OUT / "verdict.json").write_text(json.dumps(v, indent=1), encoding="utf-8")
    try:
        import update_readme_status as URS
        URS.update(v)
    except Exception as ex:      # the README block is a convenience; never fail the build for it
        print("README status block not updated:", ex)
    states = [r["state_id"] for r in rd(ROOT / "data" / "registries" / "states.csv") if r["is_contest_state"] == "TRUE"]
    n = len(states); ix = {s: i for i, s in enumerate(states)}
    uk = {frozenset((u["state_a"], u["state_b"])): u for u in unc}
    M = [[0.0] * n for _ in range(n)]; H = [[0.0] * n for _ in range(n)]
    pairs, pairmap = [], {}
    led = rd(MODEL / "channel_ledger.csv")
    LEDGER[:] = led
    top_ch = {}
    ledger = {}
    for r in led:
        k_ = r["source_state"]; dst = r["embodied_target_state"]
        a, b = sorted([k_, dst]); kk = a + "-" + b
        ledger.setdefault(kk, []).append([r["direction"], r["supported_entity"], r["rival_entity"], r["embodied_target_state"], float(r["share_of_directed_H"])])
        top_ch.setdefault(r["pair_rank"], f"{r['supported_entity']} vs {r['rival_entity']}")
    for r in ps:
        a, b = r["state_a"], r["state_b"]
        m = float(r["M"]); M[ix[a]][ix[b]] = M[ix[b]][ix[a]] = m
        H[ix[a]][ix[b]] = float(r["H_a_to_b"]); H[ix[b]][ix[a]] = float(r["H_b_to_a"])
        u = uk.get(frozenset((a, b)), {})
        row = {"rank": int(r["rank"]), "a": a, "b": b, "M": m, "rec": float(r["reciprocity_ratio"]),
               "p05": float(u.get("M_p05", 0)), "p95": float(u.get("M_p95", 0)), "p1": float(u.get("P_rank1", 0)),
               "p3": float(u.get("P_top3", 0)), "ch": top_ch.get(r["rank"], "")}
        pairs.append(row); pairmap[a + "-" + b] = row
    prof, other = {}, {}
    meta = rd(MODEL / "A_meta.csv")
    for r in meta:
        prof.setdefault(r["state_id"], []).append((r["entity_id"], float(r["A"]), r["confidence"]))
    names = {e["entity_id"]: e["entity_name"] for e in rd(ROOT / "data" / "registries" / "entities.csv")}
    for s in prof:
        prof[s] = [[names[e], round(a, 5), c] for e, a, c in sorted(prof[s], key=lambda x: -x[1])[:10]]
    arow = list(csv.reader(open(MODEL / "A_matrix.csv", encoding="utf-8")))
    for r in arow[1:]:
        other[r[0]] = float(r[-1])
    cov = audit.get("family_coverage", {})
    nmc = rob.get("n_mc", 0)
    prog = f"Google Trends requests completed: {st.get('jobs_ok', '?')} of {st.get('jobs_planned', '?')} planned (worker phase: {st.get('phase', '?')}). Qa: " + \
           ", ".join(f"{s}={sum(1 for c in qa if c['status'] == s)}" for s in ("pass", "warn", "fail"))
    data = {"states": states, "M": [[round(x, 7) for x in r] for r in M], "H": [[round(x, 7) for x in r] for r in H], "pairs": pairs,
            "pairmap": pairmap, "ledger": ledger, "prof": prof, "other": other, "verdict": v, "variants": variants, "removal": removal,
            "topdown": td, "coverage": cov, "trends_coverage": audit.get("family_trends_coverage", {}), "detected_coverage": audit.get("family_detected_coverage", {}), "progress": prog, "qa": ""}
    html = HTML.replace("__DATA__", json.dumps(data)).replace("__GEN__", dt.datetime.now().strftime("%Y-%m-%d %H:%M")) \
        .replace("__NMC__", str(nmc)).replace("__METHOD__", METHOD).replace("__LIMITS__", LIMITS)
    (OUT / "report.html").write_text(html, encoding="utf-8")
    lb_path = OUT / "leaderboard.csv"
    try:
        open(lb_path, "a").close()
    except PermissionError:   # e.g. open in Excel: write beside it instead of aborting the whole build
        lb_path = OUT / "leaderboard.pending.csv"
        print(f"WARNING: leaderboard.csv is locked; wrote {lb_path.name} instead")
    with open(lb_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["rank", "state_a", "state_b", "M", "M_p05", "M_p95", "P_rank1", "P_top3", "reciprocity"])
        for p in pairs:
            w.writerow([p["rank"], p["a"], p["b"], p["M"], p["p05"], p["p95"], p["p1"], p["p3"], p["rec"]])
    unm = audit.get("families_unmeasured_to_OTHER", [])
    status = "COMPLETE" if (not unm and td.get("completed") and not any(c["status"] == "fail" for c in qa)) else \
             ("BLOCKED" if any(c["status"] == "fail" for c in qa) else "EXHAUSTED_BUDGET")
    fl = []
    if td and td.get("completed"):
        fl.append(f"- Independent top-down check (state-vs-state 'X sucks' searches): Spearman {td['spearman_topdown_vs_bottomup']} vs bottom-up M over the {td.get('pairs_measured_both_directions', '?')} pairs measured in both directions (of 1,225), but only {td['top20_overlap']}/20 top-20 overlap. Top-down top 5: " + ", ".join(p for p, _ in td["topdown_top15_with_bottomup_rank"][:5]) + ". The top-down list is dominated by college-football rivalry pairs; the bottom-up top is dominated by pro corridors. The disagreement is a finding, not noise: the top-down measure covers the whole population, not only fans.")
    if removal:
        r0 = removal[0]
        fl.append(f"- Fragility: the leading pair {r0['pair']} keeps only {100*float(r0['retained_share']):.0f}% of its score once its single strongest edge ({r0['removed_edge']}) is removed (approx. rank {r0['approx_rank_after']}). It behaves like one matchup, not a rivalry system.")
    fl.append("- Reading: leading tier by simulation: " + ", ".join(v["tied_tier"]) + "; favored pair: " + v["leading_pair"] + "; " +
              ("a winner is declared (every gate passed)." if v["declared_winner"] else "no winner is declared because these gates were not passed: " + "; ".join(v["failed_gates"]) + "."))
    fl.append("- Dominance check (measured channel shares): " + json.dumps(v.get("diagnostics", {}).get("dominance_detail", {})) + "; second independent proxy: " + str(v.get("diagnostics", {}).get("second_proxy_agrees")))
    fl.append("- Open before the verdict can be final: " + "; ".join(v["open_items"]))
    findings = chr(10).join(fl)
    brief = f"""# Morning briefing ({dt.datetime.now().strftime('%Y-%m-%d %H:%M')})

**Status: {status}{' (PROVISIONAL)' if v['provisional'] else ''}**

- Verdict: {('winner ' + v['declared_winner']) if v['declared_winner'] else 'NO winner declared (verdict rule not satisfied)'}; leading pair {v['leading_pair']} (rank-1 in {100*v['leading_P_rank1']:.0f}% of Monte Carlo draws); tier: {', '.join(v['tied_tier'])}.
- Gates not passed: {', '.join(v['failed_gates']) or 'none'}.
- Trends coverage by sport (share of entity-state cells with real signal): {json.dumps(cov)}.
- Unmeasured sports (mass sent to OTHER, not guessed): {unm or 'none'}.
- Google Trends: {st.get('jobs_ok', '?')}/{st.get('jobs_planned', '?')} planned requests done; worker phase {st.get('phase', '?')}.
- QA: {sum(1 for c in qa if c['status']=='pass')} pass, {sum(1 for c in qa if c['status']=='warn')} warn, {sum(1 for c in qa if c['status']=='fail')} fail (see output/qa_report.json).

**What the night actually found:**
{findings}

**Biggest caveat:** the rivalry (S, T) and identity (E) layers are my priors, not survey data. The 'flat tier' variant in the report shows how sensitive the ranking is to them.

**Open in the morning:** open `output/report.html`; resume with "Continue Phase 4B" (worker is resumable); delete the scheduled task `state-rivals-overnight-rescue` if it still exists (it fires daily).
"""
    (OUT / "MORNING_BRIEFING.md").write_text(brief, encoding="utf-8")
    if final:
        (OUT / "FINAL_STATUS.json").write_text(json.dumps({"status": status, "ts": dt.datetime.now().isoformat(timespec="seconds"),
            "provisional": v["provisional"], "declared_winner": v["declared_winner"], "unmeasured_families": unm}, indent=1), encoding="utf-8")
    print(json.dumps({"status": status, "verdict": v["declared_winner"], "leading": v["leading_pair"], "failed_gates": v["failed_gates"]}))


if __name__ == "__main__":
    main(final="--final" in sys.argv)
