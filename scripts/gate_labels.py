"""Plain-language names for the verdict gates, shared by the figure, the README status block and docs/RESULTS.md.

Each entry is (prefix of the gate key in output/verdict.json, plain label, one-line statement of what the gate requires).
"""

GATES = [
    ("all_sport_families_have_data", "Every sport family has data",
     "All 18 sport families have Google Trends data (cells below the detection limit count as data, bounded, never zero)."),
    ("monte_carlo_P_rank1", "First in at least half of the simulations",
     "The pair ranks first in at least 50% of the 800 Monte Carlo draws."),
    ("holds_rank1_in", "Still first under alternative assumptions",
     "The pair ranks first in at least 80% of the informative robustness variants (those whose ranking correlates below 0.99 with the base)."),
    ("top5_in>=75%_of_relevant", "Top 5 when a key sport is removed",
     "The pair stays in the top 5 in at least 75% of the leave-one-sport-out tests for sports that drive it (5% or more of its score)."),
    ("top5_under_flat_tier", "Top 5 if all rivalries are weighted alike",
     "The pair stays in the top 5 when every rivalry edge gets identical salience and temperature."),
    ("detected_trends_coverage", "Detected search data for its main sports",
     "At least 70% of the cells behind the pair's driving sport families are detected, not censored."),
    ("single_matchup_dependence_resolved", "One-matchup dependence resolved",
     "The pair keeps a top-10 rank without its strongest matchup, or measured antipathy supports that matchup's share in both directions on the raw and the ambient-corrected measure."),
    ("second_independent_proxy", "A second source agrees, none contradicts",
     "An independent source (Wikipedia readership) agrees on the dominance of the biggest matchup and no other proxy contradicts it."),
    ("corroborated", "State-level searches agree",
     "The pair is within the top 5% of state-level searches, within the top quarter of the searches-only score (or inconclusive), and has reciprocity of at least 0.4."),
    ("top_down_validation_completed", "Independent top-down check completed",
     "The state-versus-state search ranking exists and was built without the team model."),
    ("lead_pair_within_top50", "Top 50 in the independent ranking",
     "The pair ranks in the top 50 of the independent top-down ranking (a missing rank never passes)."),
    ("qa_no_failures", "Quality checks clean",
     "Every QA check passes: attention rows sum to one, no NaN or negative cells, the worked examples reproduce, residual attention is visible."),
]


def label_for(gate_key):
    for prefix, label, _ in GATES:
        if gate_key.startswith(prefix):
            return label
    return gate_key


def statement_for(gate_key):
    for prefix, _, text in GATES:
        if gate_key.startswith(prefix):
            return text
    return ""
