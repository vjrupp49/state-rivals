# Changelog

All notable changes, in the order they landed. The release history is a single commit; this file keeps the development record. No winner is declared (see `docs/RESULTS.md`).

## v1.0 (released 2026-10-18)

### 2026-10-08
- Repository initialised; pipeline v0 imported (registries, Trends worker, A/S/T/E/H/M model, robustness, top-down check, QA gate, report).
- Rivalry and identity priors moved from code to `config/priors.yaml` and `config/rivalry_curated.yaml` (outputs byte-identical).
- Trends cache location configurable (`SR_WORK_DIR`); Trends data exported into `observations.csv` (traceability).
- Tests added: invariants, schemas, model properties (shared fandom, one-sided rivalry, in-state attention, new leagues, stress cases).
- Registry expanded from 1,765 to 2,558 entities: full FBS+FCS football, D-I women's volleyball, men's and women's lacrosse, men's wrestling, and the deferred Pac-12/UAC baseball and softball programs.
- Worker fix: after a 429 the pace could drop to 15 s (cap bug); it now never goes below the 60 s base.
- Topic audit found four wrong baseball topic matches; matching now requires the school name.
- Docs: METHODS, DATA_DICTIONARY, SOURCES, STRESS_CASES, TOPIC_AUDIT, VARIANCE_DECOMPOSITION, ROADMAP.
- Worker watchdog (`scripts/watchdog.py`) that restarts the Trends pull after a stall without ever speeding it up.

### Findings at that point (superseded by `docs/RESULTS.md`)
- Leading tier: IL-WI, MA-NY, MN-WI, CA-WA. The verdict gate declines to name a winner (four sport families unmeasured; the lead pair depends on one edge).
- Under current assumptions, rivalry salience (S) is the largest single driver of ranking uncertainty, then team attention (A).

### 2026-10-13
- All 18 sport families measured (12-month window); pipeline status COMPLETE.
- Fixed the verdict coverage gate (it ran before its input was loaded and always failed); one gate remains failing: single-edge dependence of the lead pair.
- Measured co-search shares now set how each team's prior rivalry salience is split among its rivals (row totals unchanged); ranking effect negligible.
- Added antipathy-search validation (`scripts/hate_validation.py`): NFL and MLB agree moderately with the model's hostility; NBA does not.

### 2026-10-16
- Protocol revisions D-016 (place factor: hostility shrinks with distance, gamma 0.33 per 1,000 miles) and D-017 (verdict refined: measured dominance supported plus corroboration), both recorded in docs/PROTOCOL.md with the original ranking kept side by side (`data/model/pair_scores_original.csv`).
- New evidence and checks: gravity calibration of the tier ladder, distance decay, exposure (not identified), measured channel decomposition (school-level), searches-only pair score, corroboration and type labels.
- Full 800-draw rebuild: under the original gates a tied tier; under the refined gates Illinois-Wisconsin passes all gates. The verdict remains provisional with five listed open items.
- Distance factor replicated on college schools; Monte Carlo noise derived from data (`config/mc_noise.yaml`, `docs/NOISE_DERIVATION.md`); exploratory embodiment check for the identity layer. Verdict open items updated.
- Independent Wikipedia reading check of the rivalry ladder (`scripts/wikipedia_rivalry.py`, `docs/WIKIPEDIA_RIVALRY.md`); new robustness variant with the readers' tier-3 weight (ranking unchanged). Open item about single-source evidence narrowed to state-level evidence.

### 2026-10-16 (independent review)
- Independent review by a separate agent (report summarized in `docs/STORY.md`). Fixed: dominance gate now needs support on raw and ambient-corrected measures in both directions with testable coverage, plus a second independent proxy; censored cells are bounded in the channel test (never dropped or zeroed); duplicate directed edges removed (1,668 to 1,596); estimator keeps censored candidates; top-down missing stays missing; `finalize.py` exits non-zero on a failed step and the nightly job commits only named paths; place-factor uncertainty added to the Monte Carlo; NHL co-search blend set to 0 under the stated rule; Army West Point identity alias; library-level tests (36 tests); README and METHODS corrected; contradictory generated texts replaced by text derived from `output/verdict.json`.
- Verdict: no winner declared; favored pair Illinois-Wisconsin; open items expanded (college sport-level weights, heavy censoring, post-hoc gate disclosure, missing second proxy, over-concentration, reproducibility, re-review).
- Release hygiene: Trends observations moved to a gzip file (112 MB exceeded the hosting limit); obsolete prompt file with a local path removed; API application text de-identified. Git history still contains old traces and an author identity: publish from a fresh history.
- Sport-level weights re-measured with Google topic terms (`SPORT_TERM_TOPIC` in `scripts/build_W_A.py`; the phrase-based set stays as a robustness variant). Four new SPORT batches pulled. College basketball weight about 17x higher; ranking correlation with the previous run 0.99; top three unchanged; IL-WI first in 67% of Monte Carlo runs.
- Second proxies for dominance (`scripts/second_proxy.py`, `docs/SECOND_PROXY.md`): Wikipedia readership agrees; Google comparison searches agree for Illinois but disagree for Wisconsin. Gate treats any contradicting proxy as failing. (Superseded by the second review below: the claim that Illinois to Wisconsin dominance was supported on the corrected measure rested on a denominator mismatch and was withdrawn.)
- Second independent review (2026-10-17): fixed the excess-share denominator mismatch (the corrected comparison is made over the same units on both sides; Illinois to Wisconsin is untestable on the corrected measure, Wisconsin to Illinois untestable), censored-cell bounds (zero to twice the floor), a testability rule based on detected units only, a missing top-down rank passing the gate, the Wikipedia tolerance (now the same 15 points), gates that passed by construction (only informative variants and relevant leave-outs count), coverage counted on detected cells, and stale or contradicting texts (open items and the README verdict block are now generated from the data; story chapter 12 corrected). Three new tests (39 in all). Verdict: no winner declared; four gates fail; Illinois-Wisconsin remains the favorite under the model's own assumptions (first in about 67% of simulations).
- 2026-10-18: I chose to finish as an honest leading-tier result (no declared winner, Illinois-Wisconsin favored). Added `docs/LIMITATIONS.md` (status of each limitation), story Chapter 13 and epilogue, gate scorecard figure.
- Third independent review (2026-10-18), release candidate: fixed the top-down rank denominator (28 of the 677 pairs measured in both directions, not of 1,225; the corroboration cutoff is now 5% of the ranked pairs, so Ohio-Pennsylvania and Illinois-Missouri are no longer corroborated), the report's stale limitations and coverage cards (detected coverage now shown), the epilogue and Chapter 13 over-claims (reciprocity, state-level rank, embodiment, comparison searches in both states), stale numbers in Chapters 7 to 7e, stage ordering (scorecard now built after the verdict), a README with a reproduction path that works from the repository alone (`--from-derived`), a second-proxy gate that cannot pass when a proxy is absent, a leave-out gate threshold disclosure, and the removal of operational files from the release package. Verdict unchanged: no winner declared, Illinois-Wisconsin favored.
- Presentation pass (2026-10-18): README, results page (`docs/RESULTS.md`, generated), story, timeline, limitations, methods and sources rewritten in my voice with the final numbers; the study protocol published as `docs/PROTOCOL.md`; plain-language gate labels; stale generated texts corrected (stress cases, noise derivation, co-search pilot, corroboration header that printed unrendered code).
