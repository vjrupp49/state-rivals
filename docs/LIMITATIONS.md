# Limitations register

This is my authoritative list of what the study does not establish. It is the human-readable companion to the `open_items` in `output/verdict.json` (which are generated from the data). Every item has one of three statuses:

- **Disclosed limitation**: will not be closed by this release; the result must be read with it in mind.
- **Resolved before release**: closed by work in this release (listed for the record).
- **Future work**: closable with data or access I do not currently have.

The headline result these limitations qualify: **no winner is declared. Illinois-Wisconsin is the favorite under the model's own assumptions** (first in about two thirds of Monte Carlo runs, a corroborated "marquee-matchup" rivalry carried by Bears-Packers); the leading tier is Illinois-Wisconsin, Massachusetts-New York and Minnesota-Wisconsin.

| # | Limitation | Affects | Status | What would close it |
|---|---|---|---|---|
| 1 | Sport-level weights for the small regional sports (hockey, wrestling, volleyball, lacrosse) sit at the detection floor relative to the NFL anchor, so they are upper bounds, not measurements. (College football and basketball were re-measured with topic terms after review.) | Corridors driven by hockey (MN-ND, MN-WI hockey), wrestling (IA), volleyball (NE), lacrosse (MD) | Disclosed limitation | A chain of small-sport anchors, or the official Trends API's finer resolution |
| 2 | Most college team-by-state cells are below detection (censored). They are carried as bounded floors (zero to twice the floor), never zero and never dropped, but shares for these families rest on few detected cells. | All college channels; small-state results | Disclosed limitation | The official Trends API, or a different attention source |
| 3 | The measured dominance of Bears-Packers is supported on the raw share (model 73%, measured 77%) for Illinois to Wisconsin, but is untestable on the ambient-corrected measure (too few comparable units) and untestable for Wisconsin to Illinois (too few detected Chicago teams in a small state). | The single-matchup gate | Disclosed limitation | More detected units per direction (official API) |
| 4 | Second proxies disagree: Wikipedia readership (independent, national, no geography) agrees that Bears-Packers dominates; Google comparison searches ("A vs B") do not (Illinois about 55% against the model's 74%; Wisconsin about 37% against 76%). | The second-proxy gate | Disclosed limitation | A second independent source that carries geography |
| 5 | The refined single-matchup rule (D-017) had its text written before the channel measurements but was adopted after seeing them and after the original edge-removal gate failed for the lead pair. | Interpretation of the verdict | Disclosed limitation (recorded in docs/PROTOCOL.md, METHODS and the story) | Cannot be undone; replicate on new data |
| 6 | The model over-concentrates hostility on one marquee matchup in most testable directions (measured shares are lower), and the lead pair changes under the flat-tier prior (Massachusetts-New York leads) and under flat sport weights (Minnesota-Wisconsin leads). | Robustness of the favorite | Disclosed limitation (this is a finding, shown in the report) | Measured rivalry tiers and sport weights replacing my priors |
| 7 | Per-sport systematic multipliers in the Monte Carlo (sd 0.30) are my own choice: a team-level fixed effect absorbs any sport-wide scale. Edge noise is derived from the model's in-sample misfit on NFL, MLB and NBA teams and applied to every edge. | Width of the Monte Carlo intervals | Disclosed limitation | A source that measures cross-sport scale directly |
| 8 | The identity layer E (which state a team stands for) has only an exploratory measurement (embodiment index for 40 teams and schools); the model default is 0.95 to the home state with documented exceptions. | State-level credit for every channel | Disclosed limitation | A systematic measurement of team-state identity |
| 9 | Corroboration thresholds were fixed before their table was computed but after the lead pairs' state-level ranks were known; the place factor was fixed after a first look at the estimates and replicated only on college schools. | Corroboration gate; place factor | Disclosed limitation | Replication on new data |
| 10 | Raw Google Trends payloads are not published, so the results cannot be regenerated from the repository alone; only the stages downstream of the local cache are re-runnable. | Reproducibility | Disclosed limitation (see README) | Publishing the payload archive after a terms check, or a repeat of the multi-day pull |
| 11 | Three independent review passes by separate AI agents (2026-10-16, 2026-10-17, 2026-10-18) found real defects and over-claims, all addressed. | Quality | Resolved before release | Nothing further planned; the code has not been re-reviewed after the third round of fixes |
| 12 | The Monte Carlo samples measurement and parameter noise but not structural alternatives (tier ladder, sport weights), which change the favorite; the probability of finishing first (about two thirds) is conditional on the model structure. The relevant-leave-out gate is threshold-dependent (driver share at least 5%; at 2.5% it would pass 3 of 4). | Robustness claims | Disclosed limitation | Sampling structural alternatives, or measured tiers and weights |
| 13 | State-level ranks are out of the 677 pairs measured in both directions (548 pairs are not measured in both directions); the corroboration threshold (top 5%, about 33) is therefore applied to that set; the searches-only check was inconclusive for most of the top pairs; the lead pair is not the most reciprocal (0.65) and the Bears track Chicago more than Illinois in the embodiment check (+0.46 against +0.80 for the Packers). | Corroboration | Disclosed limitation | The official API, to measure more pairs |

## Resolved before release (for the record)

- The first review found the dominance test graded on the favorable number, sport-level weights artificially low for college sports, duplicate edges, an estimator that dropped censored data, hidden pipeline failures, contradictory generated texts, and a repository that could not be published.
- The second review found a denominator mismatch in the corrected dominance test, upside-down intervals for censored cells, gates that passed by construction, a missing top-down rank passing a gate, and write-ups claiming more than the data showed.
- The third review (on the release candidate) found a state-level rank quoted against the wrong denominator, stale numbers and over-claims in the report and the story, a reproduction path that needed the private cache, and a second-proxy gate that could pass with no proxy.
- Fixes and the reasons for each are in `CHANGELOG.md`; the story of the reviews is in `docs/STORY.md` (Chapters 12 and 15).

## What would change the answer

- If measured rivalry tiers replaced my tiers and the favorite stayed first under both flat-tier and flat-sport-weight assumptions, Illinois-Wisconsin could be declared.
- If Wisconsin to Illinois became testable and Bears-Packers' share were far below the model's, Illinois-Wisconsin would fall behind Minnesota-Wisconsin or Massachusetts-New York.
- If a second independent source with geography agreed with Wikipedia and contradicted the comparison searches, the second-proxy gate would pass.
