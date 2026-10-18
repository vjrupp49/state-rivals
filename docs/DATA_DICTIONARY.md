# Data dictionary

Every table is a CSV (or JSON) in the repository unless marked *not redistributed*. Required columns of the main tables are enforced by `tests/test_schemas.py`. Zero, missing, below-detection and not-applicable are distinct (decision D-007): see `missingness_type` and `flag`. "Built by" names the script that writes the file. Row counts are as of the final 2026-10-17 build.

## Configuration (`config/`)

| File | Contents |
|---|---|
| `priors.yaml` | Analyst priors: rivalry tier ladder (salience and temperature), sport-class factors, row cap, entity and school identity exceptions (E), the measured co-search blend weights per league, the place-factor gamma. Every value is a judgment unless its comment says it was estimated. |
| `rivalry_curated.yaml` | The curated discovery list of directed rivalry tiers (pro pairs by nickname, college pairs by school with football, basketball and per-sport tiers). |
| `mc_noise.yaml` | Monte Carlo noise magnitudes derived from data by `derive_noise.py` (the per-sport multiplier sd is the one value I chose). |
| `state_centroids.csv` | Approximate geographic centers of the 50 states and DC (latitude, longitude), used for distances. |

## Registries (`data/registries/`)

| File | Rows | Built by | Contents |
|---|---|---|---|
| `states.csv` | 51 | `build_states_registry.py` | 50 contest states plus DC; Census FIPS, region, 2025 population. `is_contest_state` marks the 50. |
| `entities.csv` | 2,558 | `build_*_entities_registry.py`, `build_cfb_full_registry.py`, `build_lax_wrestling_registry.py`, `build_bsb_sfb_completion.py` | One row per professional franchise or college institution x sport x sex. `entity_id` is the key everywhere. Families: nfl, mlb, nba, nhl, mls, wnba, nwsl, pwhl, cfb, cbb_m, cbb_w, hky_m, hky_w, bsb, sfb, vbw (women's volleyball), lax (men's and women's lacrosse), wrs (men's wrestling). |
| `sports.csv` | 29 | hand-built | Sport and competition families with their Phase 3A screening status. |
| `rivalry_edges.csv` | 1,596 | `build_H_M.py` from `config/rivalry_curated.yaml` | Directed edges i to j (unique per directed pair and family). `analyst_tier`, `S_prior`, `T_prior` are my priors. |

## Raw evidence (`data/raw/`)

| File | Contents | Redistributed? |
|---|---|---|
| `county_population.csv` | Census Vintage 2025 county population estimates | yes (public domain) |
| `county_fandom.csv`, `vividseats_*_raw.csv` | Vivid Seats ticket-origin plurality maps joined to entities | no (git-ignored; re-fetch with `build_county_fandom.py`) |
| `trends_raw.csv` | Every OK Google Trends response (about 600,000 rows): percent share among up to 5 terms per state | no (git-ignored; export with `export_trends.py` from the local cache) |
| `google_topics.csv` | Query strings and topic ids per entity (refreshed from the cache by `audit_topics.py`) | yes |
| `survey_priors.csv` | National viewing and attendance priors (S&P Global 2025) | yes, with citation |
| `pair_exposure.csv` | Regular-season meetings per season, 2021 to 2025, for NFL and MLB pairs (nflverse; MLB public stats API) | yes (derived aggregate) |
| `team_success.csv` | Win share 2021 to 2025 for NFL and MLB teams | yes (derived aggregate) |

## Observations (`data/observations/`)

One row per measured quantity with full provenance (source, publisher, window, quality, missingness).

| File | Contents |
|---|---|
| `observations.csv` | County-plurality rows (`county_plurality_pop_share`, the share of a state's residents living in counties where an entity is the plurality ticket-origin team; not a fan share). |
| `observations_trends.csv.gz` | About 340,000 Google Trends-derived rows, metric `trends_ratio_to_anchor`: an entity's or term's regional search interest in units of its family anchor after batch rescaling. `notes` holds the anchor, the log-variance and the flag. Window is `W0` (last 12 months), `W1` to `W3` (older detail) or `W5` (5-year aggregate). Gzip keeps it under hosting limits. |

`quality_class` is High, Moderate or Low. `missingness_type` is `observed` or `below_detection` (a reported zero share, never a true zero).

## Model outputs (`data/model/`)

### Core matrices

| File | Rows | Contents |
|---|---|---|
| `attention_sport.csv` | 900 | `W`: each state's share of attention by sport family, and the `method` used (Google topic terms blended with national priors). |
| `attention_team.csv`, `A_meta.csv` | 127,900 each | `P`, `G_C` (current), `G_P` (persistent), `C_si` (county plurality), `confidence`, `logsd`, `flag` per state-entity cell. `flag` includes `below_detection` (censored, carried as a floor with wide uncertainty). |
| `A_matrix.csv` | 50 | `A = W x P`, one row per state, one column per entity plus `OTHER`; rows sum to 1. |
| `E_matrix.csv` | 2,558 | Entity-to-identity weights over 50 states, DC, Canada, national; rows sum to at most 1. |
| `R_matrix.csv` | 1,596 | Effective directed rivalry `R = S x T` (nonzero entries only, after the measured co-search blend). |
| `H_matrix.csv` | 50 | Directed state-to-state hostility `H = (A R) F E` (F is the place factor). Diagonal ignored. |
| `pair_scores.csv` | 1,225 | `M = sqrt(H_a_to_b x H_b_to_a)` with the place factor, rank, reciprocity ratio. |
| `pair_scores_original.csv` | 1,225 | The same score without the place factor, kept for the side-by-side comparison. |
| `channel_ledger.csv` | 640 | Decomposition of the top pairs: source state, supported entity, rival entity, embodied state, contribution and share. |
| `pair_uncertainty.csv` | 1,225 | Monte Carlo: M percentiles, probability of rank 1, top 3, top 10. |
| `removal_tests.csv`, `robustness_variants.csv` | 30 / 24 | Strongest-edge removal and deterministic variants (reciprocity forms, flat tiers, flat sport weights, leave-one-sport-out, place factor off, measured split off, reader-based tier 3, phrase-based sport terms, window and source variants). |
| `variance_decomposition.csv` | 6 | Which layer drives ranking uncertainty (one noise source at a time). |
| `*.json` | | `A_audit` (coverage: with data, detected, unmeasured), `model_run` (parameters), `robustness`, `topdown` (independent top-down check). |

### Validation and calibration tables

| File | Contents |
|---|---|
| `cosearch_pilot.csv` | Within-team ranking of rivals by "A vs B" searches versus my tier (pro leagues and college). |
| `hate_validation.csv` | Per-team agreement between "<team> suck" searches and model hostility across states (own-state teams excluded). |
| `gravity_calibration.csv` | Estimated tier-2 and tier-3 weights relative to tier 1 (NFL, MLB, NBA). |
| `gravity_distance.csv` | Distance decay of antipathy per 1,000 miles by league, with measurement and model error standard deviations (used for the Monte Carlo noise). |
| `gravity_exposure.csv` | Exposure (meetings per season) elasticity; not identified, kept as a diagnostic. |
| `college_place_replication.csv` | The distance factor re-estimated on college schools (replication). |
| `channel_decomposition.csv` | For each direction of the top pairs: the model's biggest channel and share, the measured raw and ambient-corrected shares with intervals (censored cells bounded), detected units and coverage, testability, verdict. |
| `measured_hostility.csv` | A pair score built from antipathy searches alone, with effective numbers of channels, for the pairs where both directions could be measured. |
| `corroboration.csv` | State-level search rank, searches-only rank, reciprocity, corroboration verdict and rivalry type for the model's top pairs. |
| `second_proxy.csv` | For the lead pair: share of its biggest matchup per direction under Google comparison searches and Wikipedia readership, with the model share and whether they agree. |
| `embodiment_check.csv` | Exploratory embodiment index (does a team stand for its state?) for 40 teams and schools. |
| `topdown_pairs.csv` | Every pair's state-vs-state search score and rank next to the bottom-up rank (rank 0 means not measured in both directions). |
| `wikipedia_rivalry.csv` | Rivalry articles with page views and reader interest by tier (independent check of the tier ladder). |

## Outputs (`output/`)

`verdict.json` (gates, failed gates, favored pair, diagnostics, and the open items generated from the data; a winner is named only if every gate passes), `leaderboard.csv`, `qa_report.json`, `report.html`, `state_map.html`, `MORNING_BRIEFING.md`, `FINAL_STATUS.json`. Figures for the story are in `docs/figures/`.
