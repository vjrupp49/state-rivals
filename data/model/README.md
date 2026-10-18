# Model outputs

Computed matrices and validation tables, all built by scripts in `scripts/` (see `docs/DATA_DICTIONARY.md` for every file and column, and `docs/METHODS.md` for the math).

- Core: `attention_sport.csv` (W), `attention_team.csv` and `A_meta.csv` (P and uncertainty), `A_matrix.csv` (A = W x P), `R_matrix.csv` (R = S.T), `E_matrix.csv`, `H_matrix.csv`, `pair_scores.csv` (M, the primary leaderboard), `pair_scores_original.csv` (without the place factor).
- Uncertainty and robustness: `pair_uncertainty.csv`, `removal_tests.csv`, `robustness_variants.csv`, `variance_decomposition.csv`, `channel_ledger.csv`.
- Validation against measured searches and readership: `channel_decomposition.csv`, `measured_hostility.csv`, `corroboration.csv`, `second_proxy.csv`, `gravity_*.csv`, `college_place_replication.csv`, `cosearch_pilot.csv`, `hate_validation.csv`, `embodiment_check.csv`, `topdown_pairs.csv`, `wikipedia_rivalry.csv`.
