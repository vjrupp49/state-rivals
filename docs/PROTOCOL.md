# Study protocol and decision ledger

This is the protocol I locked before computing any result, with the decision ledger (D-001 to D-017) that records every rule. Two revisions were made after I had seen intermediate results (D-016, the place factor, and D-017, the refined single-matchup rule); both are marked as such in the ledger, and `docs/LIMITATIONS.md` discloses the consequence.

The final results are in [`RESULTS.md`](RESULTS.md); how the model works in plain language is in [`METHODS.md`](METHODS.md). The richer original design dossier is [`master-dossier.html`](master-dossier.html); where it and this protocol differ, the dossier is authoritative.

---

## 1. The exact question

> Among the 1,225 unordered pairs of the 50 U.S. states, which pair has the greatest **current, reciprocal, population-penetrating sports antagonism** across meaningful professional and collegiate team sports?

- **Current** — primary empirical window is roughly the five most recent seasons as of September 15, 2026. History explains persistence; it does not earn automatic points.
- **Reciprocal** — a state pair must matter in both directions. One state obsessing over another while receiving indifference back is penalized by the geometric-mean pair score.
- **Population-penetrating** — the model follows *residents'* sports attention. A stadium sitting inside a border does not, by itself, make a franchise the identity of that state.

### What the study explicitly refuses to do

- No preselected finalist list. Every state pair remains eligible until the same rules eliminate it.
- No points merely for sharing a border, geographic closeness, politics, cultural stereotypes, championships, fights, or memorable individual games.
- No equating team location with fan residence, or with the state identity embodied by that team.
- No deleting in-state, D.C., Canadian, or other non-winning rivals when they consume finite rivalry attention.
- No treating missing observations as observed zeroes.
- No manual boost because a rivalry "feels important," or because a favored candidate otherwise looks too weak.
- No declaring a winner until the bottom-up model, structural stress tests, independent top-down validation, and uncertainty analysis are all complete.

---

## 2. The mathematical engine

A resident's finite sports attention flows through a team/program, into a directed rivalry, and finally toward the state identity embodied by the opponent.

```
A ∈ ℝ^(50×I),   Σᵢ A_si = 1                         attention: state s → entity i
S_ij = directed rivalry salience (i → j)
T_ij ∈ [0,1]   = directed emotional temperature (i → j)
R = S ⊙ T,     R_ij = 0 whenever K_ij = 0            effective directed rivalry
E ∈ ℝ^(I×B),   Σ_b E_ib ≤ 1                          entity i → geographic identity b
H = A R E = A(S ⊙ T)E                                directed state-to-state hostility
M_ab = √(H_ab · H_ba)                                reciprocal pair score (PRIMARY metric)
```

| Object | Dimension | Meaning | Normalization / rule |
|---|---|---|---|
| **A** | 50 × I | State-to-entity sports attention | Every state row sums to 1, including residual `OTHER`. |
| **K** | I × I | Competition-compatibility mask | Binary gate; compatibility permits a rivalry but never proves one. |
| **S** | I × I | Directed rivalry salience | Share/strength of rivalry attention from i toward j. |
| **T** | I × I | Directed emotional temperature | Bounded [0,1]; separates rivalry *importance* from actual animus. |
| **R** | I × I | Effective directed rivalry | `R = S⊙T`; zero wherever `K = 0`. |
| **E** | I × B | Entity-to-geographic identity | Row sum ≤ 1; residual permits national/D.C./Canadian/non-state identity. |
| **H** | 50 × B | Directed state hostility | Final contest uses the 50-state block; diagonal `H_aa` is ignored. |
| **M** | 1,225 pairs | Reciprocal pair score | Primary score is the geometric mean of the two directions. |

**Why geometric, not arithmetic:** the sum would reward one-sided obsession. Directed scores of .50 and .10 produce **.224** under geometric mean vs. balanced scores of .30/.30 producing **.300**. Harmonic mean and minimum are robustness alternatives, never the primary rule.

**Why the graph is directed:** `A→B` and `B→A` are separate measurements. Fans routinely allocate very different rivalry attention in opposite directions. Symmetric labels never justify symmetric weights.

**Illustrative only (not real project values):** if Minnesota assigns .32 of its attention to NFL and .82 of NFL attention to the Vikings, `A(MN,Vikings) = .2624`. If Vikings rivalry salience toward Green Bay is .50 and Packers embody Wisconsin identity at ≈1, that single channel contributes ≈.1312 to MN→WI hostility. This is a worked example of the arithmetic, not an observed result.

---

## 3. Decision ledger (locked unless noted)

| ID | Status | Decision | Consequence |
|---|---|---|---|
| D-001 | Locked | Contest contains the 50 states and all 1,225 unordered pairs. | No candidate shortlist. |
| D-002 | Locked | Residents' attention is the unit; entity location and identity are separate. | Chiefs fandom in Kansas can be large even though the team plays in Missouri. |
| D-003 | Locked | Primary current window is ~5 seasons through 2026. | History is diagnostic, not a bonus. |
| D-004 | Locked | Hostility is directional; reciprocity is imposed only at pair aggregation. | One-sided hate cannot masquerade as mutual hate. |
| D-005 | Locked | `M_ab = √(H_ab · H_ba)`. | Balanced hostility beats a larger but lopsided sum. |
| D-006 | Locked | Core model is `H = A(S⊙T)E`. | Attention, rivalry, temperature, and state identity remain separately auditable. |
| D-007 | Locked | Missing evidence is not zero. | Imputation and uncertainty must be explicit. |
| D-008 | Locked | Active threshold begins at preliminary state attention ≥0.25% or 98% state coverage need. | Small but meaningful regional sports survive. |
| D-009 | Locked | Opponent activation begins around 5% rivalry salience. | An overlooked entity may re-enter because it consumes meaningful rivalry attention. |
| D-010 | Locked | In-state, Canadian, D.C., and non-winning opponents remain in denominators. | Finite rivalry attention is not artificially redirected interstate. |
| D-011 | Locked | Attendance calibrates and flags anomalies; it does not compete raw against search/survey data. | Schedule and venue capacity distortions are contained. |
| D-012 | Resolved (sensitivity analysis) | Exact source ensemble weights β and γ. | Set once in the code and then varied in the robustness table (`beta_equal_0.5`, `beta_no_survey_prior`, `gamma_c_0`, `gamma_c_x2`); none of them changes the lead pair. Not chosen to favor a result. |
| D-013 | Resolved | Numeric A, R, E, H and M values. | Computed for all 1,225 pairs (`data/model/`); the final results are in `docs/RESULTS.md`. |
| D-014 | Locked | Bottom-up and top-down models run independently before comparison. | Validation cannot be engineered to agree with the main model. |
| D-015 | Locked | No manual candidate rescue. | If a surprising result survives uniform rules, it survives. |
| D-016 | Locked (protocol revision, 2026-10-16) | Place factor: hostility toward a team shrinks by exp(-gamma x miles/1000) beyond the team-level rivalry structure; gamma = 0.33 from NFL and MLB estimates (config/priors.yaml). | Applied to every pair alike; the original (no place factor) ranking is published beside it. Rationale and data: docs/RIVALRY_WEIGHT_DESIGN.md, docs/GRAVITY_DISTANCE.md. |
| D-017 | Locked (protocol revision, 2026-10-16) | Verdict refinement (the rule text was written before the channel data were seen, but it was adopted after seeing them and after the original removal gate had failed for the lead pair): a lead pair that leans on one matchup passes the single-edge gate if measured antipathy shows that matchup's share within 15 points in both directions; the lead must also be corroborated by state-level searches, a searches-only pair score and reciprocity. | Both the original and the refined verdict are reported. Tightened after independent review (both directions, raw and ambient-corrected measure on the same units, detected-unit testability, a second proxy with no contradiction). docs/CORROBORATION.md, docs/CHANNEL_DECOMPOSITION.md. |

---

## 4. Phase 1 — Protocol v1.0 (complete)

**Unit of analysis:** state-resident sports attention. A "state" acts through the aggregate fan culture of its residents — not legal ownership, venue address, or a team's mailing address.

**Entity definition:** a professional franchise/team, or a college institution × sport × sex/category program. (Ohio State football and Ohio State women's hockey are distinct entities.)

**Eligible competition:** geographically/institutionally anchored team competition with organized fandom, genuine opponent-based rivalry, and enough evidence to estimate its contribution to a state's sports culture.

**Currentness:** main evidence centers on the 5 seasons nearest Sept 15, 2026. Persistent history informs classification/diagnostics, never arbitrary score additions.

### Scope inclusions/exclusions

| Category | Treatment | Reason |
|---|---|---|
| Major professional team sports | Included | Anchored entities, large fandom, rival structures, measurable geography. |
| Division I college varsity sports | Candidate by default | Institutional identity can dominate state culture even outside the biggest sports. |
| Lower-division varsity / NAIA | Conditional | Included when state attention or rivalry evidence clears common thresholds. |
| Minor / alternative pro leagues | Team-by-team conditional | League membership alone doesn't prove statewide relevance. |
| High-school sports | **Excluded** | Too diffuse, localized, inconsistently measurable. |
| Club, intramural, recreational | **Excluded** | Outside the anchored, organized fan-attention unit. |
| International national teams | **Excluded** | Don't map cleanly into state-vs-state identities. |
| Pure individual-athlete sports | Generally excluded | Insufficient stable opponent/state anchoring; exceptions need evidence. |
| Motorsports | Generally excluded | Driver/manufacturer fandom rarely maps to persistent interstate identities. |

### Protocol safeguards

- Rules are frozen before results; revisions must be global and documented.
- Every source has date, scope, provenance, quality, and missingness metadata.
- Observed zero, structural zero, below-detection, missing, and not-applicable are different states.
- Asymmetric rivalry and asymmetric state identity are permitted.
- Shared fandom can *reduce* interstate hostility by consuming/redirecting attention.
- Every final score must decompose into auditable entity-to-entity channels.
- Unexpected winners are accepted if they survive the same evidence and robustness rules.

---

## 5. Phase 2 — Sports and entity universe (complete)

Three geographies are deliberately kept distinct: `G_i` (physical location), `A_si` (state attention), `E_ib` (geographic identity embodiment). **`G ≠ A ≠ E`.**

### Guaranteed professional core (2026 snapshot) — 197 entities

| Competition | Entities |
|---|---|
| NFL | 32 |
| MLB | 30 |
| NBA | 30 |
| NHL | 32 |
| MLS | 30 |
| WNBA | 15 |
| NWSL | 16 |
| PWHL | 12 (young rivalries treated conservatively) |
| **Total** | **197** — before conditional leagues |

**College:** all Division I varsity programs are automatic candidates (football splits FBS/FCS). Lower divisions and NAIA enter conditionally. Every record is institution × sport × sex/category; school brand is a weak prior at most, never a substitute for sport-specific attention.

**Other professional:** league-agnostic screening admits UFL, USL, pro volleyball, and other anchored leagues/teams when common attention/evidence rules are met. Formal existence alone ≠ relevance.

### Active-universe logic

```
Active entity if  max_s A⁽⁰⁾_si ≥ 0.0025
             OR   entity is required to reach ≈98% modeled attention in a state
             OR   a retained rivalry opponent reaches S_ij ≥ 0.05
Unexplained attention remains visible as OTHER.
```
The 0.25% threshold is intentionally high-recall, not a final weight. The 98% rule catches concentrated omissions. Opponent activation prevents a small entity from disappearing when it absorbs meaningful rivalry attention from a large one.

### Geography and lifecycle rules

| Case | Locked treatment |
|---|---|
| D.C. teams | Stay in the network, may receive MD/VA attention via A. D.C. is not a contestant; its teams aren't auto-reassigned to MD or VA. |
| Canadian teams | Remain in rivalry denominators and the extended identity domain. Canada cannot win the U.S.-state contest. |
| Shared cross-border metros | Fan residence measured via A; state embodiment estimated separately in E. Metro geography dictates neither. |
| Team name vs. venue state | Neither alone determines E — evidence must show perceived geographic identity. |
| Relocated / defunct teams | Historical lineage archived; current attention is zero for defunct entities. A relocated entity gets a separate current-market era. |
| Announced future expansion | Registered only when relevant to planning; no invented present rivalry/attention. |
| Neutral-site games | Don't move entity geography; may supply rivalry evidence, not state identity. |
| National brands | May receive attention in many states; E rows may keep national/residual identity rather than forcing all mass into one state. |

### Entity registry schema (`data/registries/entities.csv`)

```
entity_id, organization_id, entity_name, sport, sex_category, level, professional_college,
league, conference, division, home_city, home_state, stadium_or_campus,
active_from, active_to, current_status, source, notes
```

### Compatibility mask K

`K_ij = 1` means two entities could plausibly sustain an opponent-based rivalry under the sport's real competition structure — not that they do. Same-sport regular season, conference, postseason, interleague, cup, historic scheduling, or other genuine competitive paths qualify. Different sports never form a rivalry edge merely because their states overlap. Conference/division membership is opportunity, never automatic rivalry.

---

## 6. Phase 3A — National relevance screen (complete)

High-recall attention screen completed *before* rivalry discovery, so rivalries couldn't decide which sports were allowed to matter.

| Status | Sport / competition families | Rule |
|---|---|---|
| **Core active** | NFL; college football; MLB; NBA; men's/women's college basketball; NHL; MLS; WNBA; NWSL; PWHL | Full systematic screen and candidate coverage. |
| **Regional active** | Men's/women's college hockey; college baseball; softball; volleyball; wrestling; lacrosse | Active where state-level evidence shows meaningful attention. |
| **Team-by-team** | UFL; USL; pro volleyball; other pro leagues; lower-division college | Uniform 0.25% / 98% / opponent-activation rules. |
| **Excluded** | High school; clubs/intramurals; recreation; national teams; most individual sports/motorsports | Outside Protocol v1.0 absent a formally justified exception. |

### Evidence benchmarks that forced regional breadth (do not discard these sports nationally)

| Entity / sport | Benchmark | Implication |
|---|---|---|
| Iowa wrestling | 13,640 avg attendance, 2024–25 | Regional sport can clearly matter statewide. |
| North Dakota men's hockey | 11,614 avg | College hockey retained as a potentially dominant state channel. |
| Wisconsin men's hockey | 10,461 avg | Supports hockey-specific rivalry study. |
| Minnesota men's hockey | 9,233 avg | Supports multi-channel MN rivalry modeling. |
| Nebraska volleyball | 8,713 avg (2024-25); 92,003 stadium match | Football attention can't substitute for volleyball data. |
| LSU baseball | 11,185 avg; 458,606 total, 2025 | Can't be nationally discarded. |
| Oklahoma softball | 3,717/game; 107,813 total, 2025 | Retained where program-specific evidence is strong. |
| Maryland men's lacrosse | 4,011 avg, 2025 | Regional identity/rivalry channel. |
| UConn women's basketball | 11,825 avg, 2025–26 | Core national family, not an appendix. |
| PWHL | 9,304/game, 2025–26 | League-level A justified; rivalry maturity handled separately. |
| Omaha Supernovas (volleyball) | 10,925 avg, 2025; 16,838 match | Pro volleyball gets team-level screening. |
| St. Louis Battlehawks (UFL) | 23,239/home game, 2026 | UFL can't be categorically ignored. |
| NDSU / SDSU football | FCS anchors | FCS remains eligible, potentially central in smaller states. |

> **Screening does not award weight.** Passing Phase 3A means an entity deserves measurement — it doesn't grant a minimum A value, prove a rivalry, or help any state pair.

---

## 7. Phase 3B — National rivalry discovery (complete)

Decided which directed rivalry edges could plausibly be nonzero. Deliberately stopped **before** assigning emotional weights.

```
For survey-covered competitions: S_discovery_ij ≥ 0.05
(≈ 5 of 100 rivalry points in Know Rivalry's fan-allocation framework)
```

### Evidence classes

| Class | Meaning | Typical evidence | Model treatment |
|---|---|---|---|
| R1 | Direct measured | Fans quantitatively allocate rivalry attention | Strongest discovery evidence; still reviewed for currentness. |
| R2 | Explicit contemporary rivalry | League/team labeling, annual trophy, rivalry week | Edge retained; Phase 5 measures direction and heat. |
| R3 | Strong inferred | Multiple independent current sources, repeated scheduling | Retained with greater measurement burden. |
| R4 | Emerging / provisional | New expansion geography, marketing, recent postseason conflict | Conservative prior; no mature hatred assumed. |

Every edge is labeled **current-active**, **current-intermittent**, **dormant**, or **historical** — only the first two generate substantial primary-model R.

**Finite rivalry attention:** if Michigan fans devote major attention to Michigan State, that mass is unavailable to flow toward Ohio. Deleting same-state edges would inflate interstate hostility.

**Discovery is not scoring:** a named/measured rivalry survives into Phase 5 — it gets no emotional-intensity number here.

### Strongly established contemporary examples (do not treat as ranked)

- Minnesota–Wisconsin football: Paul Bunyan's Axe, 2026 meeting is the 136th.
- Kansas–Missouri football: returned after a 14-year gap, 122nd playing in 2026; basketball's Border Showdown continues.
- Texas–Oklahoma: Red River Rivalry (football + softball), other channels to measure.
- Illinois–Missouri: Braggin' Rights (men's basketball) extended through at least 2029; football returned 2026.
- Minnesota–North Dakota men's hockey; Minnesota–Wisconsin men's/women's hockey: explicit contemporary rivalry language.
- Maryland–Johns Hopkins men's lacrosse: "The Rivalry," 120th official-era meeting in 2026.
- WNBA Rivals Week: R2/R4 evidence including Indiana–Chicago and renewed Seattle–Portland.
- NWSL and MLS both flag Seattle–Portland as Cascadia rivalry (also present in college football).
- PWHL: important enough for A, too young for automatic mature rivalry weight — new edges stay R4 without stronger evidence.

### Interstate corridors that must survive into quantitative analysis

Deliberately unranked and over-inclusive — "survive" means at least one plausible channel merits measurement, **not** finalist status.

| Corridor | Channels to measure |
|---|---|
| Arizona–California | Suns–Lakers; Dodgers–Diamondbacks-type MLB hostility |
| California–Washington | 49ers–Seahawks + Western pro possibilities |
| Colorado–Nebraska | Football historical/current relevance |
| Connecticut–Tennessee | UConn–Tennessee women's basketball |
| Florida–Georgia | Football; regional pro overlap |
| Illinois–Indiana | Fever–Sky (WNBA) + Big Ten/pro channels |
| Illinois–Minnesota | Bears–Vikings, White Sox–Twins, divisional spillover |
| Illinois–Missouri | Cubs–Cardinals, Blackhawks–Blues, Braggin' Rights, revived football |
| Illinois–Wisconsin | Bears–Packers, Cubs–Brewers, Bulls–Bucks |
| Indiana–Kentucky | Basketball + regional collegiate history |
| Iowa–Minnesota | Football; wrestling + other Big Ten channels |
| Iowa–Nebraska | Football + regional college sports |
| Iowa–Pennsylvania | Iowa–Penn State wrestling + football-era history |
| Kansas–Missouri | KU–Mizzou football/basketball; Sporting KC cross-border identity; shared Chiefs fandom |
| Louisiana–Georgia | Saints–Falcons |
| Massachusetts–California | Celtics–Lakers |
| Massachusetts–New York | Yankees–Red Sox; Patriots–Jets/Bills; Bruins–NY/Sabres; basketball |
| Michigan–Illinois | Lions–Bears, Red Wings–Blackhawks, Great Lakes pro channels |
| Michigan–Indiana | Michigan/Notre Dame and Michigan State/Notre Dame traditions |
| Michigan–Ohio | Michigan–Ohio State football; Detroit/Cleveland pro overlap |
| Minnesota–North Dakota | Men's hockey rivalry; shared Vikings fandom as countervailing evidence |
| Minnesota–Wisconsin | Vikings–Packers; Gophers–Badgers football; men's/women's hockey; baseball/basketball |
| Missouri–Wisconsin | Cardinals–Brewers, Blues-related interactions; uncertain strength |
| Nebraska–Wisconsin | Volleyball + Big Ten football/basketball |
| New York–Pennsylvania | Giants–Eagles, Mets–Phillies, NY hockey–Flyers, basketball |
| Ohio–Pennsylvania | Steelers–Browns/Bengals, Ohio State–Penn State, Pittsburgh/Ohio channels |
| Oklahoma–Texas | Red River football/softball; basketball/baseball possibilities |
| Oregon–Washington | Football; Timbers–Sounders; Thorns–Reign; emerging WNBA |
| Pennsylvania–Maryland | Steelers–Ravens + college/lacrosse |
| Virginia–Maryland | Lacrosse history + regional overlap |
| West Virginia–Pennsylvania | Pitt–West Virginia football/basketball |

### Three methodological stress cases

- **Kansas–Missouri** — shared fandom / metro ambiguity: unmistakable KU–Mizzou rivalry, broad shared Chiefs identity, Sporting KC physically in Kansas but representing a cross-border metro.
- **Massachusetts–New York** — multi-market states: NY has distinct NYC and Buffalo identities that connect differently to MA teams.
- **Oregon–Washington** — cross-sport reinforcement across college football, MLS, NWSL, potentially WNBA.

### Rivalry-edge schema (`data/registries/rivalry_edges.csv`)

```
entity_i, entity_j, sport, direction, discovery_class, source, source_date,
first_known, last_current_evidence, lifecycle_status, survey_rivalry_points,
sample_quality, notes
```

---

## 8. Phase 4A — State sports-attention model (complete)

```
A_si = W_sk × P_si|k
Σ_k W_sk = 1      Σ_{i∈k} P_si|k = 1
```
i.e., first the share of a state's sports attention going to each *sport*, then the division of that sport's attention among teams/programs.

> Example of interpretation (illustrative, not a real number): if 12% of North Dakota's sports attention goes to hockey and 80% of its NHL attention points to one team, that entity receives 9.6% of the state's *total* modeled attention — not 80%.

Key specification points (see `docs/master-dossier.html` §Phase 4A for full sub-item detail, 4A.1–4A.32):

- **Primary signal:** Google Trends, using entity/topic definitions (e.g. "Minnesota Vikings — American football team"), never ambiguous bare strings (Vikings, Wild, Heat, Jazz, Giants, Rangers, etc.). Store `entity_id`, topic/query identifier, query type, ambiguity flag.
- **Window & decay:** ~Sept 2021–Sept 2026, exponential recency weighting with a 24-month half-life: `w(t) = 2^(−t/24)`. Retain `G^P_si` (5-yr recency-weighted persistent baseline) and `G^C_si` (most recent 12-month current signal).
- **Anchored query batching:** every Trends batch uses a common sport anchor so separate comparison groups land on a common coordinate system (Trends has item limits and non-commensurable raw scales).
- **County fandom / geographic penetration:** Vivid Seats county/state ticket-origin maps (NFL, MLB, NBA, MLS, college football, WNBA, an older NHL map), population-weighted with Census Vintage 2025:
  ```
  C_si = [Σ_{c∈s} Pop_c · I(i = plurality team in c)] / Pop_s
  ```
  This is population living in plurality counties, **not** true fan share. Preserve county rows for later statewide/metro/regional/fragmented fandom diagnostics.
- **National survey priors are priors, not state answers.** Captured 2025 priors: viewing ≈ NFL 43%, MLB 29%, NBA 24%, NHL 17% (55% of football fans also watched college football); attendance ≈ NFL 20%, MLB 18%, NBA 14%, NHL 9%. These inform national baselines only — never state-specific allocation directly.
- **Sport-level ensemble W:**
  ```
  log W̃_sk = β_G·log G_sk + β_N·log N_k + β_V·log V_sk
  W_sk = W̃_sk / Σ_l W̃_sl
  ```
  Weighted geometric ensemble. Missing source ⇒ renormalize present sources; never insert zero. β values are **deliberately unfrozen** (D-012) until overlap/held-out validation/sensitivity can estimate reliability.
- **Attendance is calibration, not a raw ingredient** (structurally biased by schedule length, capacity, prices, home-date count):
  ```
  L_si  = avg home attendance / state population
  L*_si = annual unique/estimated attendance exposure / state population
  U_i   = attendance / capacity
  ```
  Never compare raw 81-game MLB totals directly against 7 football dates.
- **Within-sport allocation P:**
  ```
  log P̃_si|k = γ_G·log G_si + γ_C·log C_si + γ_D·log D_si + γ_T·log TKT_si
  P_si|k = P̃_si / Σ_{j∈k} P̃_sj
  ```
  Signals: Google interest, population-weighted county plurality, direct survey/favorite-team evidence, ticket-origin data. Replace numeric zero with a tiny floor `x' = max(x, ε)` to avoid log-zero / false claims of absolute nonexistence.
- **Out-of-state fandom / multi-team states are legitimate A**, e.g. Kansas can assign enormous NFL attention to the Chiefs — E later decides what identity the Chiefs embody. TX (Cowboys/Texans/national spillover), PA (Eagles/Steelers), OH (Browns/Bengals/spillover), CA/NY (multi-market) all need explicit multi-team handling.
- **College/regional sports:** every program × sport measured separately; school brand is only a weak prior when sport-specific evidence is thin.
- **Residual OTHER and audit:** `O_s = 1 − Σ_{i∈Active} A_si`. If `O_s > 0.02`, re-inspect that state. Concentrated identifiable omissions activate missing entities. OTHER generates no baseline rivalry hostility but stays visible as an error bound.
- **Confidence classes per A_si:** High (search + geography + survey/viewership agree), Moderate (two independent signals agree), Low (one weak source or imputation-heavy). Preserve disagreement (e.g. search favors Chiefs, ticket geography favors Vikings, survey favors Bears) as *wider uncertainty*, never "cleaned away."
- **Conditional vs. population-penetrated attention:** primary model uses conditional sports attention `A^sport`. Diagnostics later compute `A^pop_si = C_s · A^sport_si`, where `C_s` is sports-fandom penetration in the state population. W rows double as interpretable "sports fingerprints" per state.
- **No rivalry-driven editing of A.** If Minnesota college hockey looks lower than expected, investigate whether measurement missed evidence — never manually inflate A because a rivalry "should" get credit.

---

## 9. Data architecture and file layout (as designed; the README lists the current layout)

```
State Rivals/
├── docs/PROTOCOL.md                      ← this protocol
├── docs/
│   └── master-dossier.html        ← full original project dossier (reference)
├── data/
│   ├── registries/
│   │   ├── states.csv             ← 50 states + DC/territories flag if needed
│   │   ├── sports.csv             ← sport/competition family registry
│   │   ├── entities.csv           ← schema in §5 above
│   │   └── rivalry_edges.csv      ← schema in §7 above
│   ├── raw/                       ← extracted, unmapped evidence
│   │   ├── county_population.csv
│   │   ├── county_fandom.csv
│   │   ├── google_topics.csv
│   │   ├── trends_raw.csv
│   │   ├── survey_priors.csv
│   │   └── attendance_validation.csv
│   ├── observations/
│   │   └── observations.csv       ← schema below
│   └── model/                     ← computed outputs (Phase 4B onward)
│       ├── attention_sport.csv    (W_sk)
│       ├── attention_team.csv     (P_si|k)
│       ├── A_matrix.csv
│       ├── R_matrix.csv           (Phase 5)
│       ├── E_matrix.csv           (Phase 6)
│       ├── H_matrix.csv           (Phase 7)
│       └── pair_scores.csv        (M, Phase 7)
├── scripts/                       ← extraction, model, validation, verdict and report code (see README and docs/METHODS.md)
└── output/                        ← final report/leaderboard (Phase 10)
```

### Minimum observation metadata schema (`data/observations/observations.csv`)

```
observation_id, entity_id, state_id, metric, value, unit, source_url, publisher,
publication_date, measurement_window, geography, sample_size, quality_class,
missingness_type, retrieved_at, notes
```

### Traceability requirement (non-negotiable)

Every final pair score must be reproducible from versioned matrices and decomposable into rows like: **source state → supported entity → rival entity → embodied target state → channel contribution.** Aggregation without channel-level traceability is not an acceptable final output.

---

## 10. Evidence registry

Principal sources used in completed design/discovery work (Phases 1–4A). Extraction scripts should preserve page-level dates, query parameters, and archived values going forward.

- Know Rivalry — research methodology: https://knowrivalry.com/research/ (100-point rivalry allocation, emotional measures, survey history)
- Know Rivalry — NFL: https://knowrivalry.com/league/nfl/ (directional imbalance evidence)
- Minnesota Athletics — 2026 football schedule: https://gophersports.com/news/2026/1/27/football-big-ten-announces-minnesotas-2026-schedule (Paul Bunyan's Axe continuity)
- Kansas Athletics — 122nd Border Showdown: https://kuathletics.com/news/2026/9/7/football-jayhawks-welcome-tigers-for-122nd-playing-of-border-showdown
- Oklahoma Athletics — Red River Rivalry: https://soonersports.com/news/2023/7/17/football-learfield-unveils-new-name-of-tradition-rich-cotton-bowl-meeting-between-oklahoma-and-texas
- Illinois Athletics — Braggin' Rights extension: https://fightingillini.com/news/2023/12/22/mens-basketball-braggin-rights-series-extended-through-2029
- Minnesota Athletics — 2026–27 men's hockey: https://gophersports.com/news/2026/6/18/-u-releases-2026-27-mens-hockey-schedule
- Wisconsin Athletics — women's hockey: https://uwbadgers.com/news/2026/5/27/womens-hockey-wcha-announces-2026-27-conference-schedule
- Maryland Athletics — "The Rivalry": https://umterps.com/news/2026/4/15/mens-lacrosse-no-7-terps-set-for-120th-meeting-in-the-rivalry-vs-no-12-johns-hopkins
- WNBA — 2026 Rivals Week: https://www.wnba.com/news/2026-wnba-rivals-week-faq
- NWSL — Cascadia rivalry: https://www.nwslsoccer.com/news/seattle-reign-vs-portland-thorns-a-classic-cascadia-clash
- MLS — Seattle–Portland rivalry: https://www.mlssoccer.com/news/seattle-sounders-vs-portland-timbers-what-makes-it-an-elite-rivalry
- PWHL — 2026 expansion: https://www.thepwhl.com/en/news/2026/may/27/pwhl-announces-2026-expansion-player-distribution-process
- Google Trends — normalization: https://support.google.com/trends/answer/4365533?hl=en
- Vivid Seats — NFL fandom by county: https://www.vividseats.com/blog/most-popular-nfl-teams-by-state-county
- Vivid Seats — MLB fandom by county: https://www.vividseats.com/blog/most-popular-mlb-teams-by-county
- Vivid Seats — NBA fandom by county: https://www.vividseats.com/blog/most-popular-nba-teams-by-state-county
- Vivid Seats — MLS fandom by county: https://www.vividseats.com/blog/most-popular-mls-teams-by-state-county
- Vivid Seats — college football fandom by county: https://www.vividseats.com/blog/most-popular-ncaa-football-teams-by-state-county
- Vivid Seats — WNBA fandom by state: https://www.vividseats.com/blog/most-popular-wnba-teams-by-state
- Vivid Seats — NHL fandom by county: https://www.vividseats.com/blog/most-popular-nhl-teams-by-state-county
- Vivid Seats — 2025 NFL loyalty report: https://www.vividseats.com/press/2025-nfl-loyalty-report (cross-state territory examples)
- U.S. Census — county population estimates: https://www.census.gov/data/tables/time-series/demo/popest/2020s-counties-total.html
- S&P Global — 2025 U.S. sports viewing: https://www.spglobal.com/market-intelligence/en/news-insights/research/state-of-us-sports-viewing-2025
- S&P Global — live attendance: https://www.spglobal.com/market-intelligence/en/news-insights/research/2025/11/state-live-game-attendance-us-nfl-mlb-nba-nhl-2025
- Nielsen — U.S. Sports Fan Insights: https://www.nielsen.com/report/us-sports-fan-insights-report/

**Source hierarchy:** prefer direct fan allocation, official league/team language, primary attendance/schedule records, Census population data, and transparent ticket/search methodology. Secondary narrative sources fill discovery gaps; they never silently override primary measures.

---

## 11. Audit and stress-test plan (Phases 8-9; run: results in the README, docs/ and output/verdict.json)

### Sanity checks a credible model should pass
- Michigan–Ohio and Minnesota–Wisconsin should emerge as strong channels *without being hard-coded*.
- Random state pairs with no shared sporting structure should remain near zero.
- Shared team fandom across a border should dampen, not inflate, hatred.
- Strongly one-sided rivalries should lose ground under reciprocal aggregation.
- Internal (in-state) rivalries should consume attention even though self-state hostility is ignored in the final contest.
- New leagues should not leapfrog durable rivalry systems from one playoff series.

### Structural removal tests
- **Strongest-edge removal** — remove a pair's single largest entity-to-entity channel; test whether the pair still reflects a rivalry *system* or collapses to one matchup.
- **Leave-one-sport-out** — recompute without football, baseball, basketball, hockey, soccer, college sports, and pro sports, in turn.
- **Window and source variants** — 5- vs 10-year windows, persistent vs current signals, alternate survey/map sources, recency assumptions.

### Uncertainty and alternative specifications
- Monte Carlo sample plausible A, R, E distributions rather than treating point estimates as exact.
- Report each pair's win probability, top-three probability, rank distribution, score interval.
- Compare geometric-mean reciprocity with harmonic-mean and minimum variants.
- Compare salience-only S with emotionally adjusted S⊙T.
- Vary E definitions for ambiguous metros, national brands, multi-state identity.
- Preserve source disagreement as uncertainty width.
- Require a winner credible across plausible weights — not dependent on β=.63 vs .58.

### Independent top-down validation (Phase 9)
A separate model works directly at the state level: sports-related negative mentions, search behavior about another state's teams, schadenfreude at losses, explicit state-vs-state language, direct surveys on which sports states are hated — initially ignoring individual team-rivalry structure. Bottom-up and top-down results are compared **only after both are complete**; convergence strengthens confidence, disagreement becomes a research finding in itself.

> **Verdict rule:** the final answer is not merely the largest baseline M value. The declared winner must have traceable evidence, credible reciprocity, and robustness that survives plausible alternate assumptions. If uncertainty prevents a unique winner, the honest output is a probabilistic result or a tied tier — not false certainty.

---

## 12. Roadmap

| Phase | Purpose | Primary output | State |
|---|---|---|---|
| **4B** | Extract state sport/team attention evidence, construct A | `A_matrix.csv` + uncertainty/confidence | **Built** (all 18 families; topic-based sport weights; censored cells bounded) |
| 5 | Measure directed rivalry salience S, temperature T, R=S⊙T | `R_matrix.csv` | **Built** as analyst tiers, tested against measured antipathy, comparison searches and Wikipedia readership (partly confirmed, see docs/LIMITATIONS.md) |
| 6 | Estimate how each entity embodies states/residual geography | `E_matrix.csv` | **Built** as rules; exploratory measurement only |
| 7 | Compute H=ARE and reciprocal M across all 1,225 pairs; decompose channels | Baseline leaderboard + channel ledger | **Built** (with the place factor, D-016) |
| 8 | Structural robustness diagnostics (removal, leave-one-out, geography, penetration) | Structural robustness report | **Run** (informative variants and relevant leave-outs gate the verdict) |
| 9 | Independent top-down validation; Monte Carlo; alternate specs | Win probabilities + validation comparison | **Run** (800 draws; derived noise; top-down check; second proxies) |
| 10 | Audit provenance, reproduce outputs, explain winner + caveats | Final verdict, report, code + data package | **Done as an honest finish**: no winner declared, favorite Illinois-Wisconsin; release package script prepared |

