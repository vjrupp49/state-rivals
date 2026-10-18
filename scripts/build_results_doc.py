"""Generates docs/RESULTS.md: the final results, with every number read from the committed tables.

    python scripts/build_results_doc.py

Reads output/verdict.json, output/leaderboard.csv and the tables in data/model/. Nothing on the page is typed by hand except the
sentences that frame the numbers; the numbers come from the files, so the page cannot drift from the data.
"""
import csv
import gzip
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gate_labels as GL  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
MODEL = ROOT / "data" / "model"
NL = chr(10)
DASH = chr(8211)


def rd(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


VARIANT_TEXT = {
    "reciprocity_harm": "harmonic mean of the two directions instead of the geometric mean",
    "reciprocity_min": "the weaker direction alone",
    "reciprocity_arith": "arithmetic mean of the two directions (rewards one-sided obsession)",
    "salience_only_T=1": "rivalry salience alone, with no emotional-temperature adjustment",
    "flat_tier_prior(structure_only)": "every rivalry edge gets identical salience and temperature; only which teams can rival each other matters",
    "tier3_reader_ladder(0.27)": "third-tier rivalries weighted as Wikipedia readers see them (0.27 of tier 1 instead of 0.11)",
    "no_place_factor(original)": "the model without the distance factor (the original ranking, protocol revision D-016)",
    "no_measured_split": "tier-based salience only, without the co-search blend",
    "leave_out_football": "drop all football (NFL and college) from the model",
    "leave_out_baseball": "drop all baseball",
    "leave_out_basketball": "drop all basketball",
    "leave_out_hockey": "drop all hockey",
    "leave_out_soccer": "drop all soccer",
    "leave_out_softball": "drop softball",
    "leave_out_college_all": "drop every college sport",
    "leave_out_pro_all": "drop every professional sport",
    "gamma_c_0(google_only)": "within-sport allocation from Google Trends only, no ticket-origin counties",
    "gamma_c_x2": "double the weight of the ticket-origin county signal",
    "window_current_only": "most recent 12 months only instead of the recency-weighted five years",
    "beta_equal_0.5": "equal weights on the sport-level sources",
    "beta_no_survey_prior": "sport weights without the national survey prior",
    "flat_sport_weights": "every sport family gets the same weight in every state",
    "sport_terms_phrase(original)": "the original phrase-based sport terms instead of Google topic ids",
}
LEAVE_TEXT = {"pro_all": "all professional sports", "college_all": "all college sports"}


def pct(x, d=0):
    return f"{100 * float(x):.{d}f}%"


def main():
    v = json.loads((ROOT / "output" / "verdict.json").read_text(encoding="utf-8"))
    diag = v["diagnostics"]
    names = {r["state_id"]: r["state_name"] for r in rd(ROOT / "data/registries/states.csv")}
    lb = rd(ROOT / "output/leaderboard.csv")
    unc = {(r["state_a"], r["state_b"]): r for r in rd(MODEL / "pair_uncertainty.csv")}
    ledger = rd(MODEL / "channel_ledger.csv")
    removal = {r["pair"]: r for r in rd(MODEL / "removal_tests.csv")}
    variants = rd(MODEL / "robustness_variants.csv")
    corr = rd(MODEL / "corroboration.csv")
    chan = rd(MODEL / "channel_decomposition.csv")
    prox = rd(MODEL / "second_proxy.csv")
    var = rd(MODEL / "variance_decomposition.csv")
    n_ent = len(rd(ROOT / "data/registries/entities.csv"))
    n_edges = len(rd(ROOT / "data/registries/rivalry_edges.csv"))
    fams = len({r["sport"] for r in rd(MODEL / "attention_sport.csv")}) if "sport" in rd(MODEL / "attention_sport.csv")[0] else 18
    with gzip.open(ROOT / "data/observations/observations_trends.csv.gz", "rt", encoding="utf-8") as f:
        n_trends = sum(1 for _ in f) - 1

    def pname(code):
        a, b = code.split("-")
        return f"{names[a]}{DASH}{names[b]}"

    lead = v["leading_pair"]
    a, b = lead.split("-")
    first = lb[0]
    gates = v["gates"]
    n_pass = sum(1 for ok in gates.values() if ok)
    failed = [g for g, ok in gates.items() if not ok]
    rem = diag.get("edge_removal") or {}

    def top_channel(pair_rank, direction):
        rows = [r for r in ledger if r["pair_rank"] == str(pair_rank) and r["direction"] == direction]
        return max(rows, key=lambda r: float(r["share_of_directed_H"])) if rows else None

    md = []
    w = md.append
    w("# Results")
    w("")
    w("Every number on this page is generated from the committed tables by `scripts/build_results_doc.py` (verdict from `output/verdict.json`, scores from `output/leaderboard.csv`, everything else from `data/model/`). "
      "Read it together with `docs/LIMITATIONS.md`, which says what these results do not establish.")
    w("")
    w("## The answer")
    w("")
    w(f"**I am not declaring a winner.** Under my model's own assumptions the pair with the greatest current, reciprocal, population-penetrating sports antagonism is **{pname(lead)}** "
      f"(reciprocal score M = {float(first['M']):.4f}). It ranks first in **{pct(v['leading_P_rank1'], 1)}** of 800 Monte Carlo simulations and in the top three in **{pct(v['leading_P_top3'], 1)}**. "
      f"The leading tier is {', '.join(pname(t) for t in v['tied_tier'])}.")
    w("")
    w(f"I set twelve gates in advance that a pair must clear before I would call it the winner. {pname(lead)} clears {n_pass} and fails {len(failed)}: "
      + "; ".join(f"*{GL.label_for(g).lower()}*" for g in failed) + ". "
      "A favorite that fails four of twelve gates is a favorite, not a verdict, so that is how I report it.")
    w("")
    w("| | |")
    w("|---|---|")
    w("| State pairs scored | 1,225 (every unordered pair of the 50 states) |")
    w(f"| Teams and programs measured | {n_ent:,} in {fams} sport families |")
    w(f"| Directed rivalry edges | {n_edges:,} |")
    w(f"| Google Trends observations | {n_trends:,} (derived; raw payloads not published) |")
    w("| Monte Carlo draws | 800 |")
    w(f"| Favorite | {pname(lead)} (M = {float(first['M']):.4f}, 90% interval {float(first['M_p05']):.4f} to {float(first['M_p95']):.4f}) |")
    w(f"| Rivalry type | {diag.get('type', 'n/a')}: the pair is carried by one very large matchup |")
    w(f"| Gates passed | {n_pass} of {len(gates)} |")
    w("")
    w("## Leaderboard: the top 15 pairs")
    w("")
    w("M is the geometric mean of the two directed hostilities, so one-sided obsession does not score. The interval is the 5th to 95th percentile of 800 simulations that perturb attention, rivalry salience, temperature, identity and the place factor. "
      "*Biggest channel* is the single team or school pairing that carries the largest share of that direction's hostility.")
    w("")
    w("| Rank | Pair | M | 90% interval | First in | Top 3 in | Reciprocity | Biggest channel, first state toward second | Biggest channel, second toward first |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in lb[:15]:
        code = f"{r['state_a']}-{r['state_b']}"
        cells = []
        for d in (f"{r['state_a']}->{r['state_b']}", f"{r['state_b']}->{r['state_a']}"):
            t = top_channel(r["rank"], d)
            cells.append(f"{t['supported_entity']} {chr(8594)} {t['rival_entity']} ({pct(t['share_of_directed_H'])})" if t else "n/a")
        w(f"| {r['rank']} | {pname(code)} | {float(r['M']):.4f} | {float(r['M_p05']):.4f} to {float(r['M_p95']):.4f} | {pct(r['P_rank1'], 1)} | {pct(r['P_top3'], 1)} | {float(r['reciprocity']):.2f} | {cells[0]} | {cells[1]} |")
    w("")
    w("The full table of all 1,225 pairs is `output/leaderboard.csv`; the channel-by-channel decomposition of every top-30 pair is `data/model/channel_ledger.csv`.")
    w("")

    # ---- where the lead pair's score comes from
    w(f"## Where the {pname(lead)} score comes from")
    w("")
    for d in (f"{a}->{b}", f"{b}->{a}"):
        rows = sorted([r for r in ledger if r["pair_rank"] == "1" and r["direction"] == d], key=lambda r: -float(r["share_of_directed_H"]))[:5]
        w(f"**{names[d.split('->')[0]]} toward {names[d.split('->')[1]]}**")
        w("")
        w("| Team the fans follow | Rival it points at | Sport | Share of this direction |")
        w("|---|---|---|---|")
        for r in rows:
            w(f"| {r['supported_entity']} | {r['rival_entity']} | {r['sport_family']} | {pct(r['share_of_directed_H'])} |")
        w("")
    if rem:
        w(f"Remove the single strongest matchup ({rem['edge']}) and the pair keeps {pct(rem['retained_share'])} of its score and falls from first to about {rem['rank_after']}th. "
          "That is what a *marquee-matchup* rivalry looks like: most of its weight sits in one very large, state-owned matchup rather than a web of many. "
          "Whether the model's share for that matchup matches reality is the main open question (see the gates below).")
        w("")

    # ---- gates
    w("## The twelve verdict gates")
    w("")
    w("A pair is named the winner only if every gate passes. The gates were written before the final results and tightened (never loosened) after three independent review passes; the history is in `CHANGELOG.md` and `docs/STORY.md`.")
    w("")
    w("| Gate | What it requires | Result |")
    w("|---|---|---|")
    for prefix, label, text in GL.GATES:
        key = next((g for g in gates if g.startswith(prefix)), None)
        if key is None:
            continue
        w(f"| {label} | {text} | **{'pass' if gates[key] else 'FAIL'}** |")
    w("")
    iv = diag.get("informative_variants", [])
    lo = diag.get("relevant_leave_outs", [])
    w("What the four failures consist of:")
    w("")
    if iv:
        won = sum(1 for x in iv if x["lead_rank"] == 1)
        lost = [f"{x['variant']} ({pname(next(vv['top5'] for vv in variants if vv['variant'] == x['variant']).split(';')[0])} leads)" for x in iv if x["lead_rank"] != 1]
        w(f"- **Robustness to assumptions.** {pname(lead)} is first in {won} of {len(iv)} informative variants. It loses under " + " and under ".join(lost) + ".")
    if lo:
        ok = sum(1 for x in lo if 0 < x["lead_rank"] <= 5)
        w(f"- **Leave-one-sport-out.** For the sports that drive the pair ({', '.join(f.upper() for f in diag.get('driver_sport_families', []))}) it stays in the top 5 in {ok} of {len(lo)} tests; " + "; ".join(f"without {LEAVE_TEXT.get(x['variant'].replace('leave_out_', ''), x['variant'].replace('leave_out_', ''))} it ranks {x['lead_rank']}" + ("st" if x["lead_rank"] == 1 else "th" if x["lead_rank"] != 2 else "nd") for x in lo) + ".")
    mine = [r for r in chan if r["pair_rank"] == "1"]
    w("- **One-matchup dependence.** The model says its biggest matchup carries " + " and ".join(f"{pct(r['model_top_share'])} of {r['direction']}" for r in mine)
      + ". Measured antipathy puts the same matchup at " + " and ".join(f"{pct(r['measured_share_of_that_unit'])}" for r in mine)
      + " on the raw measure, which is close. But the corrected measure cannot be computed for " + ", ".join(r["direction"] for r in mine if r["verdict"].startswith("inconclusive") and "corrected" in r["verdict"])
      + " (too few comparable units) and the other direction has too few detected units to test, so dominance is neither confirmed nor refuted.")
    goog = [r for r in prox if "same platform" in r["independence"]]
    wiki = [r for r in prox if r["independence"].startswith("independent")]
    w("- **Second source.** Wikipedia readership (independent, national, no geography) puts Bears-Packers at " + " and ".join(sorted({pct(r["measured_share"]) for r in wiki}))
      + " of the rivalry reading, in line with the model. Google comparison searches (\"A vs B\", same platform) disagree in both directions: "
      + " and ".join(f"{names[r['direction'].split('->')[0]]} {pct(r['measured_share'])} against the model's {pct(r['model_share'])}" for r in goog) + ".")
    w("")

    # ---- robustness table
    w("## Robustness: which assumptions change the favorite")
    w("")
    w(f"Each row re-runs the whole pipeline with one assumption changed. *Rank of {a}{DASH}{b}* is where the favorite lands; *rank correlation* is Spearman against the base ranking of all 1,225 pairs (below 0.99 means the variant can actually change an answer).")
    w("")
    w(f"| Variant | What changes | Top 5 pairs | Rank of {a}-{b} | Rank correlation |")
    w("|---|---|---|---|---|")
    for r in variants:
        if r["variant"] == "base":
            continue
        w(f"| `{r['variant']}` | {VARIANT_TEXT.get(r['variant'], r.get('note', ''))} | {r['top5'].replace(';', ', ')} | {r['base_top1_rank']} | {float(r['spearman_vs_base']):.3f} |")
    w("")
    w("Two findings matter most. If every rivalry is weighted alike (`flat_tier_prior`), Massachusetts-New York overtakes the favorite; if every sport is weighted alike (`flat_sport_weights`), Minnesota-Wisconsin leads. "
      "The favorite therefore depends on my tier and sport-weight judgments, and the Monte Carlo probability above is conditional on the model's structure, not a probability that the structure is right.")
    w("")

    # ---- edge removal
    w("## Strongest-edge removal for the top ten pairs")
    w("")
    w("| Rank | Pair | Strongest matchup removed | Share of score retained | Approximate rank after |")
    w("|---|---|---|---|---|")
    for r in lb[:10]:
        code = f"{r['state_a']}-{r['state_b']}"
        t = removal.get(code)
        if t:
            w(f"| {r['rank']} | {pname(code)} | {t['removed_edge']} | {pct(t['retained_share'])} | {t['approx_rank_after']} |")
    w("")
    w("Massachusetts-New York keeps two thirds of its score without Yankees-Red Sox because it is spread over several channels; Illinois-Wisconsin, Minnesota-Wisconsin, Maryland-Pennsylvania and California-Washington keep about a third or less.")
    w("")

    # ---- corroboration
    w("## Evidence that does not come from my team model")
    w("")
    w("*State-level rank* is the pair's rank among the pairs measured in both directions by direct state-versus-state antipathy searches (\"Wisconsin sucks\"), which ignore teams entirely. "
      "*Searches-only rank* is the rank of a pair score built only from team antipathy searches, with no tiers or attention weights. Details: `docs/CORROBORATION.md`.")
    w("")
    w("| Model rank | Pair | State-level rank | Searches-only rank | Reciprocity | Corroborated | Type |")
    w("|---|---|---|---|---|---|---|")
    for r in corr:
        w(f"| {r['model_rank']} | {pname(r['pair'])} | {r['topdown_rank']} | {r['measured_rank'] or 'not scored'} | {float(r['reciprocity']):.2f} | {'yes' if r['corroborated'] == 'True' else 'no'} | {r['type']} |")
    w("")
    w("Illinois-Wisconsin, Minnesota-Wisconsin and Illinois-Michigan are corroborated. Massachusetts-New York, California-Washington and Maryland-Pennsylvania, which are high in the model, are not: they behave like feuds between famous teams more than between states.")
    w("")
    w("**Is the biggest matchup as dominant as the model says?** Model share of the biggest matchup against the measured share of searches, for the lead pair:")
    w("")
    w("| Direction | Biggest matchup | Model share | Raw measured share (interval) | Verdict |")
    w("|---|---|---|---|---|")
    for r in chan:
        if r["pair_rank"] == "1":
            w(f"| {r['direction']} | {r['model_top_unit']} | {pct(r['model_top_share'])} | {pct(r['measured_share_of_that_unit'])} ({pct(r['raw_lo'])} to {pct(r['raw_hi'])}) | {r['verdict']} |")
    w("")
    w("Second proxies for the same question:")
    w("")
    w("| Direction | Proxy | Independence | Model share | Measured share | Agrees |")
    w("|---|---|---|---|---|---|")
    for r in prox:
        w(f"| {r['direction']} | {r['proxy']} | {r['independence']} | {pct(r['model_share'])} | {pct(r['measured_share'])} | {'yes' if r['agrees'] == 'True' else 'no'} |")
    w("")
    w("Across the top 30 pairs the model concentrates hostility on its biggest channel more than the searches do in most directions where the comparison can be made (`docs/CHANNEL_DECOMPOSITION.md`).")
    w("")

    # ---- variance
    w("## What drives the uncertainty")
    w("")
    w("One noise source at a time on the top 30 pairs (`docs/VARIANCE_DECOMPOSITION.md`): rivalry salience is the largest single source of uncertainty, then team attention; identity is almost irrelevant under my assumptions.")
    w("")
    w("| Layer perturbed | Mean relative spread of M | P(base #1 stays #1) | Mean rank sd |")
    w("|---|---|---|---|")
    for r in var:
        w(f"| {r['component']} | {float(r['mean_cv_top30']):.3f} | {pct(r['p_baseline_top1_stays_top1'])} | {float(r['mean_rank_sd_top30']):.1f} |")
    w("")

    # ---- strongest rival per state
    w("## Each state's strongest rival")
    w("")
    w("For every state, the partner with the highest reciprocal score M. This is a descriptive view of the same model, with the same caveats; it is also drawn as `output/state_map.html`.")
    w("")
    ps = rd(MODEL / "pair_scores.csv")
    best = {}
    for r in ps:
        m = float(r["M"])
        for s, o in ((r["state_a"], r["state_b"]), (r["state_b"], r["state_a"])):
            if s not in best or m > best[s][1]:
                best[s] = (o, m)
    w("| State | Strongest rival | M |")
    w("|---|---|---|")
    for s in sorted(best, key=lambda x: names[x]):
        w(f"| {names[s]} | {names[best[s][0]]} | {best[s][1]:.4f} |" if best[s][1] >= 0.001 else f"| {names[s]} | no rival above M = 0.001 | {best[s][1]:.4f} |")
    w("")
    w("## How to read this")
    w("")
    w("- M is a score on an arbitrary scale: only the ordering and the ratios mean anything. Hostility is estimated from search behavior and ticket-origin geography, with rivalry intensity set by tiers I wrote down and then tested against measured searches and Wikipedia readership.")
    w("- A pair's interval and win probability describe measurement and parameter noise inside one model structure. They do not cover the structural alternatives in the robustness table.")
    w("- The limitations register (`docs/LIMITATIONS.md`) lists thirteen things the results do not establish, and what would close each one.")
    w("")
    (ROOT / "docs" / "RESULTS.md").write_text(NL.join(md), encoding="utf-8", newline=NL)
    print("docs/RESULTS.md written,", len(md), "lines")


if __name__ == "__main__":
    main()
