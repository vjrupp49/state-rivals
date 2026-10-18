# Methods

Plain-language summary of the locked design in [`PROTOCOL.md`](PROTOCOL.md) plus the protocol revisions made since. Where they differ, `PROTOCOL.md` and `master-dossier.html` win. The story of how the method evolved, including the reviews, is in [`STORY.md`](STORY.md); the results are in [`RESULTS.md`](RESULTS.md); what the method cannot establish is in [`LIMITATIONS.md`](LIMITATIONS.md).

## Question

Which of the 1,225 U.S. state pairs has the greatest **current, reciprocal, population-penetrating** sports antagonism?

## Model

```
A  (50 x I)   each state's attention split across entities (rows sum to 1, includes OTHER)
S  (I x I)    directed rivalry salience          T  directed emotional temperature in [0,1]
E  (I x B)    entity -> the state identity it embodies
F  (50 x I)   place factor: hostility from state s toward entity j shrinks with distance
H = ((A (S . T)) . F) E       directed state-to-state hostility
M_ab = sqrt(H_ab * H_ba)      reciprocal pair score (primary)
```

The geometric mean means one-sided obsession is penalized: .50 and .10 score .224, balanced .30 and .30 score .300. In-state, DC, Canadian and non-winning rivals stay in the denominators, so they absorb attention that would otherwise flow to other states.

## Attention A

`A = W x P`. `W` is a state's share of attention by sport family; `P` splits a family's share among its entities.

- **Signal.** Google Trends `interest_by_region` returns each state's integer percent *share* among up to five terms, so batches are tied together with two anchor terms per batch. Ratios are batch-invariant and are rescaled to units of the first anchor by inverse-variance combination. A reported zero is *below detection* (censored): it enters as a floor with a large variance, never as a true zero and never dropped.
- **W** blends sport-level Trends terms (Google *topic* ids for the college sports, because literal phrases such as "men's college basketball" gave them almost no weight; the phrase-based version is kept as a robustness variant) with national survey priors. Small regional sports sit at the detection floor relative to the NFL anchor, so their weights are upper bounds.
- **P** blends Trends with Vivid Seats county-plurality population shares (`C_si`).
- **Recency.** Windows W0 to W3 (12, 12, 12 and 24 months) with a 24-month half-life; the five-year window is the persistent baseline for families that lack all windows. Every window is a whole number of years ending on the same date, so no sport's season phase biases the comparison.

## Rivalry S, T and the identity layer E

- **Rivalry edges** come from a curated discovery list (`config/rivalry_curated.yaml`), unique per directed pair and family. Each gets a tier that maps to a salience and a temperature (`config/priors.yaml`), scaled by a sport-class factor and capped per row. These are my priors, not survey data.
- **Measured split.** Measured "A vs B" co-search shares redistribute a team's prior salience *among its rivals* (weight set per league from the pilot's agreement with the tiers, capped at 0.4). Row totals and temperatures are untouched, so the measurement changes which rival matters, never how much rivalry there is.
- **E** gives home-state weight 0.95 plus documented exceptions (Chiefs and Sporting KC across Kansas and Missouri, Patriots across New England, DC-area teams, Notre Dame, service academies). It has an exploratory measurement only (`docs/EMBODIMENT_CHECK.md`).
- **Place factor (D-016).** Hostility toward a team shrinks by exp(-0.33 x thousands of miles) beyond what the team-level structure implies, estimated from antipathy searches on pro teams and replicated on college schools (`docs/GRAVITY_DISTANCE.md`, `docs/COLLEGE_PLACE_REPLICATION.md`). The original ranking without it is published beside the final one.

## Uncertainty and robustness

- **Monte Carlo** (800 draws): lognormal noise on team attention (per-cell, from the estimator), sport mix, per-sport multipliers (my own choice, not identifiable), edge salience, temperature and identity (the last three derived from the model's error against measured antipathy, `docs/NOISE_DERIVATION.md`), and the place factor's own gamma.
- **Deterministic variants and removal tests:** reciprocity forms, flat tier prior, flat sport weights, leave-one-sport-out, window and source variants, place factor off, measured split off, reader-based tier 3, phrase-based sport terms; strongest-edge removal for the top 30 pairs.
- **Independent top-down check:** state-versus-state "X sucks" searches, compared with the bottom-up ranking only after both are built.

## Validation against measured antipathy and readership

All of these use data the rivalry layer did not use as input; each is a diagnostic or a gate, never an input to M (decision D-014).

| Check | Script | What it tests |
|---|---|---|
| Co-search pilot | `cosearch_pilot.py` | Whether "A vs B" searches rank a team's rivals like the tiers do |
| Antipathy validation | `hate_validation.py` | Whether "<team> suck" searches match the model's hostility by state |
| Gravity calibration | `gravity_calibration.py` | The tier ladder (tier 2 and 3 relative to tier 1) |
| Distance decay and replication | `gravity_distance.py`, `college_place_replication.py` | The place factor |
| Exposure | `gravity_exposure.py` | Whether meetings per season matter (not identified) |
| Measured channel decomposition | `channel_decomposition.py` | The share of one matchup in a direction of hostility, raw and ambient-corrected, with censored cells bounded and the same units on both sides |
| Searches-only pair score | `measured_hostility.py` | The whole pair ranking from antipathy searches alone |
| Corroboration and type | `corroboration.py` | State-level search rank, searches-only rank, reciprocity; marquee-matchup versus system rivalry |
| Second proxies | `second_proxy.py` | Google comparison searches and Wikipedia readership for the dominance of the lead matchup |
| Wikipedia ladder | `wikipedia_rivalry.py` | The tier ladder from readers (independent, national) |
| Embodiment | `embodiment_check.py` | Whether a team stands for its state (exploratory) |

## Verdict gates

A winner is declared only if every gate passes: all sport families have data (censored cells count as data); Monte Carlo rank-1 probability at least 50%; rank 1 in at least 80% of the *informative* variants (those whose ranking correlates below 0.99 with the base); top 5 in at least 75% of the *relevant* leave-one-sport-out tests (sports that drive the lead pair); top 5 under the flat-tier prior; detected (not censored) Trends coverage at least 70% in the lead pair's driving families; top-down check completed and the lead pair within its top 50 (a missing rank never passes); QA clean; **single-matchup dependence resolved** (the lead pair keeps a top-10 rank without its strongest edge, or measured antipathy supports the dominant channel in both directions on both the raw and the ambient-corrected measure, each testable with at least three detected units covering 80% of the model's mass); **a second proxy agrees** (an independent source agrees and no other proxy contradicts); and the pair is **corroborated** (state-level searches within the top 5% of the pairs measured in both directions, a searches-only pair score within the top quarter of scored pairs or inconclusive, reciprocity at least 0.4).

Protocol revisions (`PROTOCOL.md`, D-016 and D-017): the place factor and the refined single-matchup rule. The refined rule's text was written before the channel measurements but it was adopted after seeing them and after the original edge-removal gate had failed for the leading pair; three independent review passes then tightened it. Otherwise the report names a leading tier with a favorite.

## Independent reviews

Three review passes by separate AI agents (2026-10-16, 2026-10-17 and 2026-10-18) examined the code, the statistics, the verdict logic and the repository's publishability. Their findings and my fixes are in `CHANGELOG.md`; the first one changed the verdict from a provisional winner to no declared winner, and the story of all three is in `STORY.md` (Chapters 12 and 15).

## Reproducibility

`scripts/finalize.py` rebuilds every downstream stage from the local Trends cache (a SQLite file outside the repository, location set by `SR_WORK_DIR`). The raw Trends payloads are not published and re-pulling them takes days because Google throttles the unofficial endpoint (the worker backs off and never evades). Derived Trends observations are in `data/observations/observations_trends.csv.gz`. See `README.md`.

## Known limitations

See `docs/LIMITATIONS.md`.
