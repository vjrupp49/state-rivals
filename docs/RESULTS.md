# Results

Every number on this page is generated from the committed tables by `scripts/build_results_doc.py` (verdict from `output/verdict.json`, scores from `output/leaderboard.csv`, everything else from `data/model/`). Read it together with `docs/LIMITATIONS.md`, which says what these results do not establish.

## The answer

**I am not declaring a winner.** Under my model's own assumptions the pair with the greatest current, reciprocal, population-penetrating sports antagonism is **Illinois–Wisconsin** (reciprocal score M = 0.0643). It ranks first in **66.9%** of 800 Monte Carlo simulations and in the top three in **94.8%**. The leading tier is Illinois–Wisconsin, Massachusetts–New York, Minnesota–Wisconsin.

I set twelve gates in advance that a pair must clear before I would call it the winner. Illinois–Wisconsin clears 8 and fails 4: *still first under alternative assumptions*; *top 5 when a key sport is removed*; *one-matchup dependence resolved*; *a second source agrees, none contradicts*. A favorite that fails four of twelve gates is a favorite, not a verdict, so that is how I report it.

| | |
|---|---|
| State pairs scored | 1,225 (every unordered pair of the 50 states) |
| Teams and programs measured | 2,558 in 18 sport families |
| Directed rivalry edges | 1,596 |
| Google Trends observations | 342,408 (derived; raw payloads not published) |
| Monte Carlo draws | 800 |
| Favorite | Illinois–Wisconsin (M = 0.0643, 90% interval 0.0338 to 0.0815) |
| Rivalry type | marquee-matchup: the pair is carried by one very large matchup |
| Gates passed | 8 of 12 |

## Leaderboard: the top 15 pairs

M is the geometric mean of the two directed hostilities, so one-sided obsession does not score. The interval is the 5th to 95th percentile of 800 simulations that perturb attention, rivalry salience, temperature, identity and the place factor. *Biggest channel* is the single team or school pairing that carries the largest share of that direction's hostility.

| Rank | Pair | M | 90% interval | First in | Top 3 in | Reciprocity | Biggest channel, first state toward second | Biggest channel, second toward first |
|---|---|---|---|---|---|---|---|---|
| 1 | Illinois–Wisconsin | 0.0643 | 0.0338 to 0.0815 | 66.9% | 94.8% | 0.65 | Chicago Bears → Green Bay Packers (68%) | Green Bay Packers → Chicago Bears (66%) |
| 2 | Massachusetts–New York | 0.0496 | 0.0310 to 0.0582 | 16.4% | 76.5% | 0.52 | Boston Red Sox → New York Yankees (33%) | New York Yankees → Boston Red Sox (35%) |
| 3 | Minnesota–Wisconsin | 0.0471 | 0.0243 to 0.0610 | 9.2% | 55.8% | 0.68 | Minnesota Vikings → Green Bay Packers (74%) | Green Bay Packers → Minnesota Vikings (58%) |
| 4 | Maryland–Pennsylvania | 0.0377 | 0.0202 to 0.0469 | 2.2% | 17.0% | 0.45 | Baltimore Ravens → Pittsburgh Steelers (56%) | Pittsburgh Steelers → Baltimore Ravens (73%) |
| 5 | Illinois–Michigan | 0.0351 | 0.0215 to 0.0449 | 1.8% | 17.8% | 0.63 | Chicago Blackhawks → Detroit Red Wings (33%) | Detroit Red Wings → Chicago Blackhawks (39%) |
| 6 | California–Washington | 0.0342 | 0.0159 to 0.0506 | 1.5% | 14.1% | 0.27 | San Francisco 49ers → Seattle Seahawks (88%) | Seattle Seahawks → San Francisco 49ers (58%) |
| 7 | Ohio–Pennsylvania | 0.0335 | 0.0202 to 0.0419 | 0.2% | 7.1% | 0.91 | Cleveland Browns → Pittsburgh Steelers (34%) | Pittsburgh Steelers → Cleveland Browns (48%) |
| 8 | Illinois–Missouri | 0.0301 | 0.0171 to 0.0363 | 0.1% | 4.0% | 0.64 | Chicago Cubs → St. Louis Cardinals (60%) | St. Louis Cardinals → Chicago Cubs (51%) |
| 9 | Massachusetts–Pennsylvania | 0.0292 | 0.0153 to 0.0386 | 0.8% | 5.9% | 0.59 | Boston Celtics → Philadelphia 76ers (78%) | Philadelphia 76ers → Boston Celtics (66%) |
| 10 | Georgia–Louisiana | 0.0270 | 0.0095 to 0.0414 | 0.8% | 4.0% | 0.61 | Atlanta Falcons → New Orleans Saints (93%) | New Orleans Saints → Atlanta Falcons (94%) |
| 11 | Illinois–Minnesota | 0.0266 | 0.0139 to 0.0362 | 0.0% | 1.4% | 0.47 | Chicago Bears → Minnesota Vikings (69%) | Minnesota Vikings → Chicago Bears (45%) |
| 12 | New York–Pennsylvania | 0.0256 | 0.0173 to 0.0310 | 0.0% | 0.1% | 0.71 | New York Mets → Philadelphia Phillies (21%) | Philadelphia Phillies → New York Mets (27%) |
| 13 | Michigan–Ohio | 0.0239 | 0.0131 to 0.0312 | 0.1% | 0.8% | 0.99 | Detroit Tigers → Cleveland Guardians (39%) | Ohio State Buckeyes Football → Michigan Wolverines Football (54%) |
| 14 | Maryland–Ohio | 0.0211 | 0.0102 to 0.0292 | 0.0% | 0.2% | 0.74 | Baltimore Ravens → Cleveland Browns (42%) | Cleveland Browns → Baltimore Ravens (52%) |
| 15 | Pennsylvania–Texas | 0.0202 | 0.0094 to 0.0260 | 0.0% | 0.0% | 0.84 | Philadelphia Eagles → Dallas Cowboys (78%) | Dallas Cowboys → Philadelphia Eagles (62%) |

The full table of all 1,225 pairs is `output/leaderboard.csv`; the channel-by-channel decomposition of every top-30 pair is `data/model/channel_ledger.csv`.

## Where the Illinois–Wisconsin score comes from

**Illinois toward Wisconsin**

| Team the fans follow | Rival it points at | Sport | Share of this direction |
|---|---|---|---|
| Chicago Bears | Green Bay Packers | nfl | 68% |
| Chicago Cubs | Milwaukee Brewers | mlb | 19% |
| Chicago Bulls | Milwaukee Bucks | nba | 4% |
| Minnesota Vikings | Green Bay Packers | nfl | 4% |
| St. Louis Cardinals | Milwaukee Brewers | mlb | 2% |

**Wisconsin toward Illinois**

| Team the fans follow | Rival it points at | Sport | Share of this direction |
|---|---|---|---|
| Green Bay Packers | Chicago Bears | nfl | 66% |
| Milwaukee Brewers | Chicago Cubs | mlb | 16% |
| Milwaukee Bucks | Chicago Bulls | nba | 4% |
| Minnesota Vikings | Chicago Bears | nfl | 3% |
| Minnesota Wild | Chicago Blackhawks | nhl | 2% |

Remove the single strongest matchup (Chicago Bears <-> Green Bay Packers) and the pair keeps 33% of its score and falls from first to about 15th. That is what a *marquee-matchup* rivalry looks like: most of its weight sits in one very large, state-owned matchup rather than a web of many. Whether the model's share for that matchup matches reality is the main open question (see the gates below).

## The twelve verdict gates

A pair is named the winner only if every gate passes. The gates were written before the final results and tightened (never loosened) after three independent review passes; the history is in `CHANGELOG.md` and `docs/STORY.md`.

| Gate | What it requires | Result |
|---|---|---|
| Every sport family has data | All 18 sport families have Google Trends data (cells below the detection limit count as data, bounded, never zero). | **pass** |
| First in at least half of the simulations | The pair ranks first in at least 50% of the 800 Monte Carlo draws. | **pass** |
| Still first under alternative assumptions | The pair ranks first in at least 80% of the informative robustness variants (those whose ranking correlates below 0.99 with the base). | **FAIL** |
| Top 5 when a key sport is removed | The pair stays in the top 5 in at least 75% of the leave-one-sport-out tests for sports that drive it (5% or more of its score). | **FAIL** |
| Top 5 if all rivalries are weighted alike | The pair stays in the top 5 when every rivalry edge gets identical salience and temperature. | **pass** |
| Detected search data for its main sports | At least 70% of the cells behind the pair's driving sport families are detected, not censored. | **pass** |
| One-matchup dependence resolved | The pair keeps a top-10 rank without its strongest matchup, or measured antipathy supports that matchup's share in both directions on the raw and the ambient-corrected measure. | **FAIL** |
| A second source agrees, none contradicts | An independent source (Wikipedia readership) agrees on the dominance of the biggest matchup and no other proxy contradicts it. | **FAIL** |
| State-level searches agree | The pair is within the top 5% of state-level searches, within the top quarter of the searches-only score (or inconclusive), and has reciprocity of at least 0.4. | **pass** |
| Independent top-down check completed | The state-versus-state search ranking exists and was built without the team model. | **pass** |
| Top 50 in the independent ranking | The pair ranks in the top 50 of the independent top-down ranking (a missing rank never passes). | **pass** |
| Quality checks clean | Every QA check passes: attention rows sum to one, no NaN or negative cells, the worked examples reproduce, residual attention is visible. | **pass** |

What the four failures consist of:

- **Robustness to assumptions.** Illinois–Wisconsin is first in 3 of 5 informative variants. It loses under flat_tier_prior(structure_only) (Massachusetts–New York leads) and under flat_sport_weights (Minnesota–Wisconsin leads).
- **Leave-one-sport-out.** For the sports that drive the pair (MLB, NFL) it stays in the top 5 in 2 of 3 tests; without football it ranks 5th; without baseball it ranks 1st; without all professional sports it ranks 206th.
- **One-matchup dependence.** The model says its biggest matchup carries 73% of IL->WI and 92% of WI->IL. Measured antipathy puts the same matchup at 77% and 98% on the raw measure, which is close. But the corrected measure cannot be computed for IL->WI (too few comparable units) and the other direction has too few detected units to test, so dominance is neither confirmed nor refuted.
- **Second source.** Wikipedia readership (independent, national, no geography) puts Bears-Packers at 90% of the rivalry reading, in line with the model. Google comparison searches ("A vs B", same platform) disagree in both directions: Illinois 55% against the model's 74% and Wisconsin 37% against the model's 76%.

## Robustness: which assumptions change the favorite

Each row re-runs the whole pipeline with one assumption changed. *Rank of IL–WI* is where the favorite lands; *rank correlation* is Spearman against the base ranking of all 1,225 pairs (below 0.99 means the variant can actually change an answer).

| Variant | What changes | Top 5 pairs | Rank of IL-WI | Rank correlation |
|---|---|---|---|---|
| `reciprocity_harm` | harmonic mean of the two directions instead of the geometric mean | IL-WI, MA-NY, MN-WI, MD-PA, IL-MI | 1 | 0.966 |
| `reciprocity_min` | the weaker direction alone | IL-WI, MN-WI, MA-NY, OH-PA, IL-MI | 1 | 0.947 |
| `reciprocity_arith` | arithmetic mean of the two directions (rewards one-sided obsession) | IL-WI, MA-NY, MN-WI, CA-WA, MD-PA | 1 | 0.755 |
| `salience_only_T=1` | rivalry salience alone, with no emotional-temperature adjustment | IL-WI, MA-NY, MN-WI, IL-MI, MD-PA | 1 | 0.996 |
| `flat_tier_prior(structure_only)` | every rivalry edge gets identical salience and temperature; only which teams can rival each other matters | MA-NY, IL-WI, IL-MI, MN-WI, OH-PA | 2 | 0.983 |
| `tier3_reader_ladder(0.27)` | third-tier rivalries weighted as Wikipedia readers see them (0.27 of tier 1 instead of 0.11) | IL-WI, MA-NY, MN-WI, IL-MI, MD-PA | 1 | 0.995 |
| `no_place_factor(original)` | the model without the distance factor (the original ranking, protocol revision D-016) | IL-WI, MA-NY, MN-WI, CA-WA, MD-PA | 1 | 0.991 |
| `no_measured_split` | tier-based salience only, without the co-search blend | IL-WI, MA-NY, MN-WI, MD-PA, CA-WA | 1 | 0.999 |
| `leave_out_football` | drop all football (NFL and college) from the model | MA-NY, IL-MO, MA-PA, IL-MI, IL-WI | 5 | 0.934 |
| `leave_out_baseball` | drop all baseball | IL-WI, MN-WI, MD-PA, IL-MI, CA-WA | 1 | 0.996 |
| `leave_out_basketball` | drop all basketball | IL-WI, MN-WI, MD-PA, MA-NY, OH-PA | 1 | 0.979 |
| `leave_out_hockey` | drop all hockey | IL-WI, MN-WI, MA-NY, CA-WA, MD-PA | 1 | 0.996 |
| `leave_out_soccer` | drop all soccer | IL-WI, MA-NY, MN-WI, MD-PA, IL-MI | 1 | 1.000 |
| `leave_out_softball` | drop softball | IL-WI, MA-NY, MN-WI, MD-PA, IL-MI | 1 | 1.000 |
| `leave_out_college_all` | drop every college sport | IL-WI, MA-NY, MN-WI, MD-PA, IL-MI | 1 | 0.715 |
| `leave_out_pro_all` | drop every professional sport | MI-OH, AL-GA, KS-MO, OK-TX, OR-WA | 206 | 0.720 |
| `gamma_c_0(google_only)` | within-sport allocation from Google Trends only, no ticket-origin counties | IL-WI, MA-NY, MN-WI, MD-PA, IL-MI | 1 | 0.998 |
| `gamma_c_x2` | double the weight of the ticket-origin county signal | IL-WI, MA-NY, MN-WI, MD-PA, CA-WA | 1 | 0.996 |
| `window_current_only` | most recent 12 months only instead of the recency-weighted five years | IL-WI, MA-NY, MN-WI, IL-MI, MD-PA | 1 | 0.996 |
| `beta_equal_0.5` | equal weights on the sport-level sources | IL-WI, MA-NY, MN-WI, MD-PA, IL-MI | 1 | 0.999 |
| `beta_no_survey_prior` | sport weights without the national survey prior | IL-WI, MA-NY, MN-WI, MD-PA, CA-WA | 1 | 0.997 |
| `flat_sport_weights` | every sport family gets the same weight in every state | MN-WI, OR-WA, MA-NY, IL-MI, IL-MO | 7 | 0.930 |
| `sport_terms_phrase(original)` | the original phrase-based sport terms instead of Google topic ids | IL-WI, MA-NY, MN-WI, MD-PA, IL-MI | 1 | 0.993 |

Two findings matter most. If every rivalry is weighted alike (`flat_tier_prior`), Massachusetts-New York overtakes the favorite; if every sport is weighted alike (`flat_sport_weights`), Minnesota-Wisconsin leads. The favorite therefore depends on my tier and sport-weight judgments, and the Monte Carlo probability above is conditional on the model's structure, not a probability that the structure is right.

## Strongest-edge removal for the top ten pairs

| Rank | Pair | Strongest matchup removed | Share of score retained | Approximate rank after |
|---|---|---|---|---|
| 1 | Illinois–Wisconsin | Chicago Bears <-> Green Bay Packers | 33% | 15 |
| 2 | Massachusetts–New York | Boston Red Sox <-> New York Yankees | 66% | 8 |
| 3 | Minnesota–Wisconsin | Minnesota Vikings <-> Green Bay Packers | 33% | 25 |
| 4 | Maryland–Pennsylvania | Baltimore Ravens <-> Pittsburgh Steelers | 35% | 39 |
| 5 | Illinois–Michigan | Chicago Blackhawks <-> Detroit Red Wings | 64% | 14 |
| 6 | California–Washington | San Francisco 49ers <-> Seattle Seahawks | 22% | 70 |
| 7 | Ohio–Pennsylvania | Cleveland Browns <-> Pittsburgh Steelers | 59% | 16 |
| 8 | Illinois–Missouri | Chicago Cubs <-> St. Louis Cardinals | 44% | 38 |
| 9 | Massachusetts–Pennsylvania | Boston Celtics <-> Philadelphia 76ers | 27% | 63 |
| 10 | Georgia–Louisiana | Atlanta Falcons <-> New Orleans Saints | 7% | 401 |

Massachusetts-New York keeps two thirds of its score without Yankees-Red Sox because it is spread over several channels; Illinois-Wisconsin, Minnesota-Wisconsin, Maryland-Pennsylvania and California-Washington keep about a third or less.

## Evidence that does not come from my team model

*State-level rank* is the pair's rank among the pairs measured in both directions by direct state-versus-state antipathy searches ("Wisconsin sucks"), which ignore teams entirely. *Searches-only rank* is the rank of a pair score built only from team antipathy searches, with no tiers or attention weights. Details: `docs/CORROBORATION.md`.

| Model rank | Pair | State-level rank | Searches-only rank | Reciprocity | Corroborated | Type |
|---|---|---|---|---|---|---|
| 1 | Illinois–Wisconsin | 28 | 1 | 0.65 | yes | marquee-matchup |
| 2 | Massachusetts–New York | 138 | 12 | 0.52 | no | system |
| 3 | Minnesota–Wisconsin | 7 | 3 | 0.68 | yes | marquee-matchup |
| 4 | Maryland–Pennsylvania | 304 | 38 | 0.45 | no | system |
| 5 | Illinois–Michigan | 32 | not scored | 0.63 | yes | n/a (not scored) |
| 6 | California–Washington | 189 | 20 | 0.27 | no | system |
| 7 | Ohio–Pennsylvania | 40 | 13 | 0.91 | no | system |
| 8 | Illinois–Missouri | 57 | not scored | 0.64 | no | n/a (not scored) |
| 9 | Massachusetts–Pennsylvania | 536 | not scored | 0.59 | no | n/a (not scored) |
| 10 | Georgia–Louisiana | 167 | not scored | 0.61 | no | n/a (not scored) |
| 11 | Illinois–Minnesota | 306 | 7 | 0.47 | no | marquee-matchup |
| 12 | New York–Pennsylvania | 79 | not scored | 0.71 | no | n/a (not scored) |

Illinois-Wisconsin, Minnesota-Wisconsin and Illinois-Michigan are corroborated. Massachusetts-New York, California-Washington and Maryland-Pennsylvania, which are high in the model, are not: they behave like feuds between famous teams more than between states.

**Is the biggest matchup as dominant as the model says?** Model share of the biggest matchup against the measured share of searches, for the lead pair:

| Direction | Biggest matchup | Model share | Raw measured share (interval) | Verdict |
|---|---|---|---|---|
| IL->WI | Green Bay Packers | 73% | 77% (74% to 80%) | inconclusive (corrected measure lacks comparable units) |
| WI->IL | Chicago Bears | 92% | 98% (97% to 98%) | inconclusive (too few detected units or low detected coverage) |

Second proxies for the same question:

| Direction | Proxy | Independence | Model share | Measured share | Agrees |
|---|---|---|---|---|---|
| IL->WI | Google comparison searches ('A vs B') | same platform, different query type (not counted as independent) | 74% | 55% | no |
| IL->WI (national readership) | Wikipedia rivalry-article readership, 2021 to 2025 | independent source (national, no geography) | 78% | 90% | yes |
| WI->IL | Google comparison searches ('A vs B') | same platform, different query type (not counted as independent) | 76% | 37% | no |
| WI->IL (national readership) | Wikipedia rivalry-article readership, 2021 to 2025 | independent source (national, no geography) | 80% | 90% | yes |

Across the top 30 pairs the model concentrates hostility on its biggest channel more than the searches do in most directions where the comparison can be made (`docs/CHANNEL_DECOMPOSITION.md`).

## What drives the uncertainty

One noise source at a time on the top 30 pairs (`docs/VARIANCE_DECOMPOSITION.md`): rivalry salience is the largest single source of uncertainty, then team attention; identity is almost irrelevant under my assumptions.

| Layer perturbed | Mean relative spread of M | P(base #1 stays #1) | Mean rank sd |
|---|---|---|---|
| A (team attention) | 0.173 | 95% | 5.4 |
| W (sport mix) | 0.083 | 99% | 2.9 |
| S (salience, incl. per-sport) | 0.204 | 79% | 5.5 |
| T (temperature) | 0.092 | 96% | 3.0 |
| E (identity) | 0.017 | 100% | 0.9 |
| all combined | 0.276 | 69% | 8.5 |

## Each state's strongest rival

For every state, the partner with the highest reciprocal score M. This is a descriptive view of the same model, with the same caveats; it is also drawn as `output/state_map.html`.

| State | Strongest rival | M |
|---|---|---|
| Alabama | Georgia | 0.0132 |
| Alaska | no rival above M = 0.001 | 0.0000 |
| Arizona | California | 0.0190 |
| Arkansas | Louisiana | 0.0063 |
| California | Washington | 0.0342 |
| Colorado | Missouri | 0.0156 |
| Connecticut | New York | 0.0138 |
| Delaware | no rival above M = 0.001 | 0.0000 |
| Florida | New York | 0.0175 |
| Georgia | Louisiana | 0.0270 |
| Hawaii | no rival above M = 0.001 | 0.0000 |
| Idaho | Washington | 0.0015 |
| Illinois | Wisconsin | 0.0643 |
| Indiana | Illinois | 0.0153 |
| Iowa | Wisconsin | 0.0137 |
| Kansas | Missouri | 0.0172 |
| Kentucky | Indiana | 0.0082 |
| Louisiana | Georgia | 0.0270 |
| Maine | New York | 0.0152 |
| Maryland | Pennsylvania | 0.0377 |
| Massachusetts | New York | 0.0496 |
| Michigan | Illinois | 0.0351 |
| Minnesota | Wisconsin | 0.0471 |
| Mississippi | Louisiana | 0.0054 |
| Missouri | Illinois | 0.0301 |
| Montana | Washington | 0.0014 |
| Nebraska | Iowa | 0.0070 |
| Nevada | California | 0.0193 |
| New Hampshire | New York | 0.0162 |
| New Jersey | New York | 0.0169 |
| New Mexico | no rival above M = 0.001 | 0.0000 |
| New York | Massachusetts | 0.0496 |
| North Carolina | Pennsylvania | 0.0056 |
| North Dakota | South Dakota | 0.0051 |
| Ohio | Pennsylvania | 0.0335 |
| Oklahoma | Texas | 0.0157 |
| Oregon | Washington | 0.0150 |
| Pennsylvania | Maryland | 0.0377 |
| Rhode Island | New York | 0.0151 |
| South Carolina | Georgia | 0.0058 |
| South Dakota | North Dakota | 0.0051 |
| Tennessee | Texas | 0.0091 |
| Texas | Pennsylvania | 0.0202 |
| Utah | Colorado | 0.0075 |
| Vermont | New York | 0.0059 |
| Virginia | Pennsylvania | 0.0121 |
| Washington | California | 0.0342 |
| West Virginia | Pennsylvania | 0.0076 |
| Wisconsin | Illinois | 0.0643 |
| Wyoming | no rival above M = 0.001 | 0.0000 |

## How to read this

- M is a score on an arbitrary scale: only the ordering and the ratios mean anything. Hostility is estimated from search behavior and ticket-origin geography, with rivalry intensity set by tiers I wrote down and then tested against measured searches and Wikipedia readership.
- A pair's interval and win probability describe measurement and parameter noise inside one model structure. They do not cover the structural alternatives in the robustness table.
- The limitations register (`docs/LIMITATIONS.md`) lists thirteen things the results do not establish, and what would close each one.
