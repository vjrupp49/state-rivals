# State Rivals

**Which two U.S. states have the greatest sports antagonism?** I built a reproducible, falsifiable measurement of all 1,225 pairs of states, using 2,558 teams and programs, 18 sport families and more than 340,000 Google Trends observations, and I tested my own answer against four independent checks before deciding how much to claim.

I am Vincent Rupp. This repository holds the code, the derived data, the results and the full record of how the answer changed under review.

## The question

Among the 1,225 unordered pairs of the 50 states, which pair has the greatest **current, reciprocal, population-penetrating** sports antagonism?

- **Current.** The evidence window is the five most recent years (2021 to 2026), with a 24-month half-life. History explains rivalries; it earns no points.
- **Reciprocal.** The pair score is the geometric mean of the two directions. A state that despises its neighbor while the neighbor shrugs is penalized: directed scores of .50 and .10 give .224, while balanced .30 and .30 give .300.
- **Population-penetrating.** The model follows what the residents of a state actually pay attention to, not where a stadium sits. Chiefs fandom in Kansas counts for Kansas.

There is no shortlist. Every pair competes under the same rules, and no points are given for sharing a border, a famous game, a championship or a stereotype.

## The result

<!-- STATUS:BEGIN -->
**I am not declaring a winner. The favorite is Illinois–Wisconsin.** It ranks first in **66.9%** of 800 Monte Carlo simulations and in the top three in **94.8%**. The leading tier is Illinois–Wisconsin, Massachusetts–New York, Minnesota–Wisconsin. The favorite clears 8 of my 12 verdict gates and fails 4.

| Rank | Pair | Reciprocal score M | 90% interval | First in | Top 3 in |
|---|---|---|---|---|---|
| 1 | Illinois–Wisconsin | 0.0643 | 0.0338 to 0.0815 | 66.9% | 94.8% |
| 2 | Massachusetts–New York | 0.0496 | 0.0310 to 0.0582 | 16.4% | 76.5% |
| 3 | Minnesota–Wisconsin | 0.0471 | 0.0243 to 0.0610 | 9.2% | 55.8% |
| 4 | Maryland–Pennsylvania | 0.0377 | 0.0202 to 0.0469 | 2.2% | 17.0% |
| 5 | Illinois–Michigan | 0.0351 | 0.0215 to 0.0449 | 1.8% | 17.8% |

Gates the favorite does not clear:

- **Still first under alternative assumptions.** The pair ranks first in at least 80% of the informative robustness variants (those whose ranking correlates below 0.99 with the base).
- **Top 5 when a key sport is removed.** The pair stays in the top 5 in at least 75% of the leave-one-sport-out tests for sports that drive it (5% or more of its score).
- **One-matchup dependence resolved.** The pair keeps a top-10 rank without its strongest matchup, or measured antipathy supports that matchup's share in both directions on the raw and the ambient-corrected measure.
- **A second source agrees, none contradicts.** An independent source (Wikipedia readership) agrees on the dominance of the biggest matchup and no other proxy contradicts it.

The full leaderboard, every gate, the robustness table and the evidence behind each failure are in [`docs/RESULTS.md`](docs/RESULTS.md); what the results do not establish is in [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md).
<!-- STATUS:END -->

## What I found

1. **Illinois–Wisconsin is the favorite, and the reason is one matchup.** About two thirds of Illinois's measured hostility toward Wisconsin runs through Bears versus Packers, and about two thirds of Wisconsin's toward Illinois runs the other way. Remove that single matchup and the pair keeps a third of its score and falls from first to about 15th. I classify it as a *marquee-matchup* rivalry: one enormous, state-owned game rather than a web of many.
2. **The favorite is not robust to my own judgments, so I do not call it a winner.** If every rivalry is weighted alike, Massachusetts–New York leads. If every sport is weighted alike, Minnesota–Wisconsin leads. Without football the favorite drops to fifth. Four of twelve gates fail, and each failure is documented in [`docs/RESULTS.md`](docs/RESULTS.md).
3. **Illinois–Wisconsin and Minnesota–Wisconsin are real state rivalries; Massachusetts–New York is more a brand feud.** Searches against the *states* themselves rank Minnesota–Wisconsin 7th and Illinois–Wisconsin 28th of the 677 pairs that can be measured in both directions, but Massachusetts–New York only 138th. A score built only from antipathy searches, with none of my rivalry tiers in it, ranks Illinois–Wisconsin first of 73 scorable pairs and Michigan–Ohio second (13th in the model).
4. **Distance matters, and it is measurable.** Holding the model's predictions fixed, antipathy toward a team falls to 0.70 per 1,000 miles for NFL teams (90% interval 0.65 to 0.77), 0.73 for MLB, and 0.77 for college schools (0.71 to 0.83). That is why far-off brand rivalries such as Celtics–Lakers do not carry a state pair. The model applies exp(−0.33 per 1,000 miles) to every pair alike and I publish the ranking without it next to the final one.
5. **My rivalry ladder survived a data test where one was possible.** For the NFL, measured second-tier rivalries come out at 0.41 of a top-tier rivalry (my prior: 0.38) and third-tier at 0.11 (prior: 0.106). Wikipedia readership, an independent source with no Google data, gives 0.36 and 0.27 across 68 rivalries. For baseball and basketball the data cannot pin the ladder down.
6. **The model over-concentrates hostility on its biggest matchup.** Across the 55 directions of the top 30 pairs, 23 could be tested against measured searches. Only 2 were fully supported, 1 on the raw measure, and in 11 the model gave its biggest channel too large a share. Real antipathy is spread across more teams than my tiers assume.
7. **Season length and schedule are not where the story is.** Interest in a team over the last 12 months and the year before correlate at 0.73 to 0.91 (NFL 0.83, MLB 0.91, NBA 0.73, NHL 0.77, college football 0.90), and meetings per season are not identified in the data.
8. **College sports needed a second measurement.** Searching for the phrase "men's college basketball" understated it about 17-fold against the Google topic for the NCAA tournament (about 10% of NFL search volume). After correcting this, the ranking of all 1,225 pairs correlates 0.99 with the old one, and the top three do not move.

The complete write-up, with every table, is [`docs/RESULTS.md`](docs/RESULTS.md). The story of how I got here, including two wrong turns and three review passes that each found real defects, is [`docs/STORY.md`](docs/STORY.md).

## How it works

```
A  (50 x 2,558)   how each state's residents split their sports attention across teams and programs (rows sum to 1, with a residual OTHER)
S, T              how strongly (salience) and how hotly (temperature) the fans of one team rival each other team
E                 which state's identity each team embodies
F                 a place factor: hostility toward a distant team shrinks with distance
H = ((A (S . T)) . F) E        directed hostility from every state toward every other state
M_ab = sqrt(H_ab * H_ba)       reciprocal pair score, the primary metric
```

1. **Attention (A).** Google Trends gives each state's integer percent share among up to five search terms, so I tie batches together with two anchor terms per batch and rescale to one coordinate system. A reported zero is below the detection limit: it enters as a bounded floor, never as a true zero and never dropped. Within-sport allocation blends search with population-weighted county ticket-origin maps (Vivid Seats); sport weights blend sport-level search with national survey priors.
2. **Rivalries (S, T).** 1,596 directed rivalry edges come from a curated discovery list. I assigned each a tier (salience and temperature) and then tested the tiers against measured searches, comparison searches ("A vs B") and Wikipedia readership. The tiers are my priors, not survey data, and the README and report say so.
3. **Identity and place (E, F).** Teams embody their home state at 0.95 with documented exceptions (Chiefs and Sporting KC across Kansas and Missouri, Patriots across New England, Notre Dame, the service academies). The place factor is estimated from the data.
4. **Pair score (M).** The geometric mean of the two directions, for all 1,225 pairs. Every score decomposes into channel rows: source state, team the fans follow, rival team, embodied state, contribution (`data/model/channel_ledger.csv`).
5. **Uncertainty and the verdict.** 800 Monte Carlo draws perturb every layer, with noise levels derived from the model's own misfit to measured antipathy. A winner is declared only if one pair clears twelve gates written in advance. They cover Monte Carlo rank, robustness under informative variants and leave-one-sport-out tests, dependence on a single matchup, a second independent source, corroboration by state-level searches, an independent top-down check and quality checks.

Methods in full: [`docs/METHODS.md`](docs/METHODS.md). The locked protocol and decision ledger (D-001 to D-017): [`docs/PROTOCOL.md`](docs/PROTOCOL.md).

## Where to look

| If you want | Open |
|---|---|
| The answer, with every table | [`docs/RESULTS.md`](docs/RESULTS.md) |
| The interactive report (leaderboard, pair explorer, robustness, validation) | [`output/report.html`](output/report.html) and [`output/state_map.html`](output/state_map.html) |
| The story of the project, in prose with figures | [`docs/STORY.md`](docs/STORY.md) |
| What the results do not establish | [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md) |
| How the model works | [`docs/METHODS.md`](docs/METHODS.md) and [`docs/PROTOCOL.md`](docs/PROTOCOL.md) |
| Every table and column | [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) |
| Data sources, terms and attribution | [`docs/SOURCES.md`](docs/SOURCES.md) |
| What changed and why | [`CHANGELOG.md`](CHANGELOG.md) and [`docs/TIMELINE.md`](docs/TIMELINE.md) |
| The design note behind the validation, written before I built it | [`docs/RIVALRY_WEIGHT_DESIGN.md`](docs/RIVALRY_WEIGHT_DESIGN.md) |
| The validation write-ups | `docs/CHANNEL_DECOMPOSITION.md`, `SECOND_PROXY.md`, `CORROBORATION.md`, `MEASURED_HOSTILITY.md`, `GRAVITY_CALIBRATION.md`, `GRAVITY_DISTANCE.md`, `COLLEGE_PLACE_REPLICATION.md`, `GRAVITY_EXPOSURE.md`, `HATE_VALIDATION.md`, `COSEARCH_PILOT.md`, `WIKIPEDIA_RIVALRY.md`, `EMBODIMENT_CHECK.md`, `NOISE_DERIVATION.md`, `VARIANCE_DECOMPOSITION.md`, `STRESS_CASES.md`, `TOPIC_AUDIT.md` |

## Reproduce

```bash
pip install -r requirements.txt
python -m pytest -q tests
python scripts/finalize.py --from-derived     # works from this repository alone
```

- **From the repository alone** (`--from-derived`, chosen automatically when no local cache exists) re-runs the model computation from the committed matrices, then the corroboration table, stress cases, charts, report, results page and verdict. It reuses the committed uncertainty and measurement tables (robustness, channel decomposition, second proxy), which only the full rebuild regenerates.
- **Full rebuild** (`python scripts/finalize.py --draws 800 --final`) additionally rebuilds attention, uncertainty and every validation table. It needs a local Google Trends cache (a SQLite file outside the repository, set with `SR_WORK_DIR`). I do not publish the raw Trends payloads, and re-pulling them takes days because Google throttles the unofficial endpoint; `scripts/trends_worker.py` is resumable, backs off on every refusal and never evades throttling. The derived Trends observations are in `data/observations/observations_trends.csv.gz`.
- Third-party raw dumps (Vivid Seats county files, MLB and nflverse downloads) are not redistributed; the scripts re-fetch them.

## Limitations in brief

The full register of thirteen items, each with what would close it, is [`docs/LIMITATIONS.md`](docs/LIMITATIONS.md). The ones that matter most:

- The rivalry tiers and the identity layer are my priors. I tested them where the data allow, but they are not survey measurements, and the favorite changes if the tiers or sport weights are flattened.
- Free Google Trends cannot see small states or small sports. Most college team-by-state cells fall below the detection limit; I carry them as bounded floors, and the shares for the smallest sports are upper bounds.
- Dominance of the leading matchup could be tested in only one direction on one measure, and a same-platform second proxy disagrees with it.
- Two protocol revisions (D-016 and D-017) were written after I had seen intermediate results. I disclose this rather than call them pre-registered.

## How I built it

I designed the question, the rules and every decision in the ledger, and I made every call about what to claim. I wrote the code and the analysis with an AI coding assistant (Claude Code). The three review passes (2026-10-16, 2026-10-17 and 2026-10-18) were run by separate AI agents with no stake in the result; they found real defects and over-claims, each of which I fixed, and the verdict moved from a provisional winner to no winner. That record is in [`CHANGELOG.md`](CHANGELOG.md) and in chapters 10 and 12 of [`docs/STORY.md`](docs/STORY.md).

## Data sources and attribution

Data source: Google Trends (https://www.google.com/trends). Also Vivid Seats county ticket-origin maps, the U.S. Census Bureau (Vintage 2025 county estimates), Wikipedia contributors (CC BY-SA 4.0) and Wikimedia Pageviews, the MLB public stats API, nflverse, and published reports from S&P Global and Nielsen. Terms, risks and what is and is not redistributed are in [`docs/SOURCES.md`](docs/SOURCES.md).

## Citation and license

Cite this work with [`CITATION.cff`](CITATION.cff) (GitHub's "Cite this repository" button reads it). Code: MIT ([`LICENSE`](LICENSE)). Derived tables, figures and documents: CC BY 4.0 ([`LICENSE-DATA.md`](LICENSE-DATA.md)). Third-party material keeps its own terms.
