# Timeline

The dated record of what I built, what I found, and what I had to correct. The reasoning behind each step is in [`STORY.md`](STORY.md); the itemized code and data changes are in [`../CHANGELOG.md`](../CHANGELOG.md).

| Date | What happened | Why it mattered |
|---|---|---|
| 2026-10-08 | First end-to-end pipeline: registries, Google Trends worker, attention, rivalry and identity layers, pair scores, Monte Carlo, robustness tests, top-down check, quality gate, report. 11 of 15 sport families measured. | The first complete model. The verdict gate declined to name a winner. |
| 2026-10-08 | Git repository, tests and configuration files added. The registry grew from 1,765 to 2,558 entities (full FBS and FCS football, volleyball, lacrosse, wrestling, more baseball and softball). | Reproducibility, and coverage beyond the big four leagues. |
| 2026-10-08 | Fixed a worker bug: after a Google block it sped up instead of slowing down. | Never make throttling worse. |
| 2026-10-12 | The worker learned to tell my own network drops from Google's blocks. Pilot of "A vs B" comparison searches. | Resilience; the first measured rivalry signal. |
| 2026-10-13 | Fixed a gate that ran before its input was loaded (it always failed). Antipathy ("X suck") searches for 124 pro teams. | A gate that fails for the wrong reason is worse than none. First independent test of the rivalry layer. |
| 2026-10-13 | Removed each state's own teams from the antipathy comparison. | Fans complain about their own teams; the model ignores in-state hostility on purpose. |
| 2026-10-15 | Data pull complete: all 18 sport families, all windows. Gravity regression: the NFL tier ladder matches my hand-set one (0.41 against 0.38 and 0.11 against 0.106). | The first data-based check of the rivalry ladder. |
| 2026-10-16 | Checked whether season timing biases the numbers (it does not: whole-year windows, year-to-year rank correlation 0.73 to 0.91). | My question about off-seasons. |
| 2026-10-16 | Measured channel shares for the top 30 pairs, aggregated by school so college sports are covered. | The key test of the rivalry layer. |
| 2026-10-16 | Searches-only pair score: Illinois–Wisconsin first, Michigan–Ohio second, Minnesota–Wisconsin third of the scorable pairs. | An independent test of the tiers and attention layers. |
| 2026-10-16 | Average-resident gut check turned into a test: antipathy falls to about 70% per 1,000 miles. Protocol revisions D-016 (place factor) and D-017 (refined verdict rule). | Place-anchoring is real and measurable; the revisions are disclosed as written after intermediate results. |
| 2026-10-16 | Distance decay replicated on college schools (0.77 per 1,000 miles); Monte Carlo noise derived from data; exploratory embodiment index; Wikipedia readership check of the tier ladder. | Three open items narrowed, and a source independent of Google. |
| 2026-10-16 | **Review 1** (separate AI agent): dominance gate graded on the favorable number, college sport weights depressed by literal-phrase terms, heavy censoring counted as coverage, duplicate edges, hidden pipeline failures, an unpublishable repository. | The verdict changed from a provisional winner to **no winner declared**. |
| 2026-10-16 | College sport-level weights re-measured with Google topic terms (college basketball about 17 times higher). | Closed the largest review finding; ranking correlation with the old run 0.99. |
| 2026-10-17 | **Review 2:** a denominator mismatch in the corrected dominance test, upside-down intervals for censored cells, gates that passed by construction, documents claiming agreement the data did not show. | With only informative variants and relevant leave-outs counted, Illinois–Wisconsin is first in 3 of 5 variants. Four gates fail. |
| 2026-10-18 | I chose to finish as an honest leading-tier result: favorite Illinois–Wisconsin, no declared winner. Limitations register, conclusion chapter and gate scorecard written. | The finish line. |
| 2026-10-18 | **Review 3** (release candidate): a state-level rank quoted against the wrong denominator, stale numbers and over-claims in the report and story, a reproduction path that needed the private cache, a second-proxy gate that could pass with no proxy. | All fixed. The verdict did not change. |
| 2026-10-18 | Release v1.0 published. | MIT code, CC BY 4.0 derived tables, fresh single-commit history, raw Trends payloads not published. |
