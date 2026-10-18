# Output

- `report.html` - self-contained interactive report (leaderboard, pair explorer, robustness, validation, limitations).
- `state_map.html` - tile map of each state's strongest rival.
- `leaderboard.csv` - all 1,225 pairs with M, 90% interval, P(rank 1), P(top 3), reciprocity.
- `verdict.json` - the verdict: gates, failed gates, favored pair, diagnostics and the open items, all generated from the data (a winner is named only if every gate passes).
- `qa_report.json`, `FINAL_STATUS.json` - quality checks and build status.

The verdict is qualified by the limitations in `docs/LIMITATIONS.md`. Rebuild with `python scripts/finalize.py` (see the README for the two modes).
