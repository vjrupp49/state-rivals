# Scripts

Build order (each script is idempotent; `python scripts/finalize.py` runs the model stages in sequence):

| Stage | Script | Output |
|---|---|---|
| Registries | `build_*_entities_registry.py`, `build_states_registry.py` | `data/registries/` |
| Raw evidence | `build_county_population.py`, `build_county_fandom.py`, `build_C_si_observations.py` | `data/raw/`, `data/observations/` |
| Trends pull | `trends_worker.py` (resumable, throttle-aware), `watchdog.py` | local cache (git-ignored) |
| Attention | `build_P_from_trends.py`, `build_W_A.py` | `data/model/A_matrix.csv` |
| Rivalry, identity, score | `lib_model.py`, `build_H_M.py` | `data/model/{R,E,H}_matrix.csv`, `pair_scores.csv` |
| Uncertainty | `robustness.py`, `topdown_validation.py` | `data/model/pair_uncertainty.csv`, `topdown.json` |
| Audit and report | `qa_gate.py`, `build_report.py` | `output/` |

See `docs/METHODS.md` for what each analysis does and `README.md` for the two rebuild modes.
