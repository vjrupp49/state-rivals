# How much does each rivalry matter? A design for measuring rivalry weight

**Status: design note written on 2026-10-15, after I reviewed the first complete results and before I built any of the validation described here.** Some of it was implemented (the gravity calibration, the measured channel test, the corroboration conditions, Section 7's decision rules); some was not (the attendance and "fandom moments" proxies). The numbers in this note are the ones I had on that date; `METHODS.md` describes what exists and `RESULTS.md` has the final numbers.

## 1. The problem, restated

The model scores a state pair by adding up channels: one state's fans of team *i*, who rival team *j*, which embodies the other state. Right now **how much each rivalry matters** (salience S and temperature T) and **how much each team stands for its state** (E) are judgments of mine: a three-tier ladder (0.40 / 0.20 / 0.08) and a default that a team stands 95% for its home state.

That choice decides the headline result. In the leading pair, Illinois-Wisconsin:

- Bears vs Packers carries **69%** of Illinois's hostility toward Wisconsin and **67%** of Wisconsin's toward Illinois.
- Delete that one matchup and the pair keeps **32%** of its score and falls from 1st to about 20th.
- By contrast Massachusetts-New York keeps 66% (falls to 8th). That 66% belongs to MA-NY, not IL-WI.

The structural test fails, but my point is exactly right: **failing it is only a problem if the model's 69% is wrong.** If most of the real rivalry between those two states's sports fans is Bears-Packers, a single dominant channel is simply the truth. So the task is to measure the real proportion and compare it to the model's.

## 2. My ideas, expanded

### Idea A: check the proportion, not the level

*Compare the share of the rivalry that one matchup carries in reality with the share it carries in the model.*

**Why this is strong.** Proportions are unit-free. I never have to say what a "unit of rivalry" is, or compare football with basketball directly. I only ask: of everything that makes Illinois and Wisconsin sports fans antagonistic, what fraction is the Bears-Packers game? It also turns an untestable prior into a testable claim, because the model already publishes its shares (the channel ledger).

**What can go wrong.**
- *No natural denominator.* "All fandom moments" has no census. The share of one channel depends on which channels you counted. If the measured list omits the Brewers or the Badgers, Bears-Packers looks bigger than it is. The curated rivalry list has this flaw built in. The fix is to measure **all entities that embody either state**, not only listed rivalries.
- *Every proxy has its own bias* (see Section 5). One proxy cannot settle it; agreement between several can.
- *Pre-commitment.* If I decide after looking that "keep it if it matches," I can fool myself. Section 7 fixes the rule before any data is seen.

### Idea B: use attendance, but carefully

**Right to worry.** Football has seven home dates and basketball forty, stadiums have different capacities, prices ration seats, and, as I noted, many of the most passionate fans are in bars and living rooms, not seats. I already treat attendance as **calibration only** (decision D-011).

**What survives.** *Ratios within the same team*, which cancel the sport effects:
- **Rivalry premium** = attendance (or average ticket price, or TV audience) at the rivalry game divided by the same team's average. Bears-Packers vs a typical Bears home game is the same kind of quantity as Cubs-Cardinals vs a typical Cubs game, even though football and baseball are different sports.
- **Away-fan travel**: how many visiting fans show up. Revealed passion that costs real money.
- **TV audience premium**, which captures the people who are not in the stadium.

**What it still misses.** Casual national audiences (a Packers-Bears game draws viewers who care about neither state), and it says nothing about identity. Treat it as a cross-check on *which games* are big, not on *which state* feels it.

### Idea C: "it isn't state vs. state; it's team vs. team" (Massachusetts-California)

**This is the most important point of the design.** A Celtics fan in Massachusetts may dislike the Lakers, but that is a rivalry between two *brands* with national fan bases, not Massachusetts against California. The model currently turns team hostility into state hostility through E (the Lakers "stand for" California at 95%), which is an assumption, and it silently converts brand rivalries into state rivalries. Our own independent check agrees with you:

| Pair | Rank in the team-by-team model | Rank in state-vs-state "X sucks" searches |
|---|---|---|
| MN-WI | 3 | 7 |
| IL-WI | 1 | 28 |
| IL-MI | 6 | 32 |
| OH-PA | 7 | 40 |
| MA-NY | 2 | 138 |
| CA-WA | 4 | 189 |
| PA-TX | 10 | 203 |
| MD-PA | 5 | 304 |
| MA-PA | 9 | 536 |

(Figure: `docs/figures/fig04_bottomup_vs_topdown.png`.) The pairs that hold up when people search about *states* are the Midwestern ones. The pairs that collapse are exactly the ones built on teams from famous brands in distant or non-adjacent states. This is a real finding, not noise.

**How to turn it into numbers.** My own protocol already says "neither location nor name alone determines E; evidence must show perceived geographic identity." My default broke that rule. Candidate measurements for how place-like a rivalry is:

1. **Fan locality**: the share of a team's fan attention that actually lives in its home state or region (already in A). A Packers-style team scores high; a global brand like the Lakers scores low.
2. **State-level framing**: the independent top-down data directly says whether people frame the pair as state vs state. Use it as a *validation target*, not an input (decision D-014 keeps the two independent).
3. **Distance decay**: whether hostility per fan falls with distance, estimated from the antipathy searches (Section 4). Neighbors rivalry; strangers have brands.
4. **Team naming**: teams named for a state or region (Minnesota Vikings, New England Patriots, Tennessee Titans) versus a city (Chicago Bears) are cheap, objective evidence of intended identity.
5. **Media framing**: how often rivalry coverage uses state or regional names versus team or city names (free news counts, Section 5).
6. **Flagship universities**: University of Wisconsin is the state's identity in a way the Chicago Bulls are not Illinois's. My data already treat college and pro entities differently.

The right place for this is **E and a place-framing factor**, which is a documented, global protocol change (allowed, per the "revisions must be global and documented" safeguard), not a manual edit for any favorite pair.

### Idea D: "fandom moments"

The picture is: count the moments when fans of the two states feel the rivalry, and ask what fraction come from one matchup. Operationally, a moment can be:

- a **game** between teams embodying the two states, weighted by audience (contact intensity);
- a **search**, a hostile or comparative one, by someone living in a state, aimed at an entity of the other;
- a **headline** or **article** about the matchup;
- a **page read** of a rivalry article on Wikipedia.

Each source is an imperfect census of moments; none is the truth. The principle is the one I already use for attention: **triangulate and keep disagreement as uncertainty** (Section 6).

## 3. What is bad or risky about the approach as a whole

- **Search is not passion.** "Packers suck" includes sarcasm, losing-streak griping, and (my own check found) fans complaining about their own team. I now exclude own-state teams, but nationally hated teams (Cowboys, Patriots, Yankees) still carry an ambient level that is not rivalry.
- **Sampling.** Trends data are rounded integer shares. Small states return zeros that mean "below detection," not "no hate." Small-state results will be noisy whatever I do.
- **Geography confound.** A neighboring state searches about a team for many reasons besides rivalry: shared media markets, migration, cable packages.
- **A measured number is only as good as its definition.** The proportion test could come out against my intuition for good reasons (I might have the Bears-Packers share right and everything else wrong), or for bad ones (proxy bias). I need to know which, so I ask more than one proxy.
- **Circularity trap.** If the curated rivalry list decides what gets measured, the measurement cannot find a rivalry I forgot. The discovery step must be wide (every entity embodying either state).
- **Directional data are thin.** Reciprocity is a core principle, so each direction needs its own measurement; the weaker direction limits the score.

## 3b. Seasons, timing and exposure (my question, 2026-10-16)

*"What if a big rivalry looks small only because its season is in the off-season, while Bears-Packers was played last week?"*

**What is already protected.** Every Trends window is a whole number of years ending on the same calendar date (W0 = Oct 2025 to Oct 2026; W1, W2 the two years before; the five-year window is five full cycles). Every sport's full season, including its off-season, sits inside every window, so the *phase* of the season at pull time does not favor the NFL over the NBA. Direct check (2026-10-16): the last 12 months versus the year before agree closely cell by cell (rank correlation: NFL 0.83, MLB 0.91, NBA 0.73, NHL 0.77, college football 0.90). The model's "current only" variant changes the ranking by a rank correlation of 0.998. The antipathy and co-search pulls use the full five-year window, so one quiet or noisy week cannot move them.

**What is *not* protected, and what to do about it.**
1. **Exposure (how often the teams actually meet).** A rivalry with 13 games a year (many MLB and NHL divisional matchups) generates more search than one with 2 (the NFL), and a rivalry that is *paused* (Kansas-Missouri football, 2012 to 2025) or *rotates* (NFL out-of-division opponents, NBA and NHL conferences) shows different volume for scheduling reasons. Fix: pull game counts for each matchup from free public schedules (nflverse, Retrosheet, the league APIs) and add log(games per year) as a regressor in the gravity model, so measured antipathy is read *net of how often they play*.
2. **Game-day spikes versus year-round feeling.** Search is bursty. A five-year total is dominated by game days. That is acceptable for a quantity defined as accumulated annual attention (how the model's A is defined), but it should be reported as such, and the time-series version (search before, during and after games) is a second proxy for intensity per meeting.
3. **Winning.** Teams that win a lot are hated for winning (Patriots, Yankees, Warriors), and a playoff run inside the window inflates one team's numbers. Fix: add a free team-success index (win percentage and playoff rounds in the window) as a regressor.
4. **Very recent events** (a game last week, a trade, a scandal). The windows exclude them by construction (the most recent unit is 12 months), at the cost of not seeing a genuinely fresh rivalry. A fresh rivalry shows up in W0 versus W1-W3 drift and can be examined as a diagnostic, never as a bonus (decision D-003).

These three controls (exposure, success, window length) are added to the plan as part of step 2 below.

### Exposure can push either way (my observation, 2026-10-16)

More games means more chances to look things up, but also fatigue: a baseball season can wash out and a 162-game rivalry can lose its edge by August. So the *sign* of the exposure effect is unknown, and the plan is to **estimate it instead of assuming it**:
- **Regression:** add log(games per year) to the gravity model; the coefficient says whether more meetings raise or lower antipathy per fan, and by how much. A coefficient near zero would itself be a finding: that scheduling does not drive these numbers, and season length can be ignored.
- **Natural experiments:** rivalries that were paused and then resumed (Kansas-Missouri football, Texas-Texas A&M, Pitt-West Virginia) let me compare antipathy before and after the games came back, with the recency windows.
- **Within-season fatigue:** monthly search for the same rivalry terms across a season (national time series) shows whether interest per game decays by late season, especially in baseball.

**Result (2026-10-16, `docs/GRAVITY_EXPOSURE.md`): exposure is not reliably identified, so it is not adopted.** With meetings per season (2021 to 2025) in the model, the NFL elasticity comes out positive and the MLB elasticity negative, which at least fits the "can go either way" intuition, but both are implausibly large (NFL +4.2, MLB -2.3, the latter with an interval from -12 to -0.5). The reason is collinearity: how often two teams meet is almost the same thing as whether they are division rivals, which is what the rivalry tiers already encode, so the data cannot separate the two. Exposure therefore stays a *diagnostic*, not a correction. Team success needs no separate control: it is a constant for each team across states and is absorbed by the team effect. The distance decay is stable across these specifications (NFL about 0.70 per 1,000 miles). In plain terms: season length and meeting frequency do not add a correction I can defend, which is itself a finding.

### Is one great rivalry enough? Three separate questions

1. **Is the weight right?** (Measured: yes for Illinois-Wisconsin. See `docs/CHANNEL_DECOMPOSITION.md`.)
2. **Is it a state rivalry or a team rivalry?** This is a question about identity, and the evidence for it is independent of the team data: state-level framing (the "X sucks" searches about states, where Illinois-Wisconsin ranks 28th of 1,225), a pair score rebuilt only from searches (below), and whether the two states' hostility is reciprocal.
3. **Does the definition require breadth?** My question is the greatest current, reciprocal, population-penetrating antagonism. A single matchup that occupies a large share of both states' sports attention *is* antagonism by that definition, because the score already equals the share of fans' attention that is engaged times how hot it burns. Breadth is not a requirement of the definition; it is **evidence that a rivalry belongs to the states and not just to two teams.**

**Proposed resolution (to be fixed before the final calibration):** keep M as the primary score (decisions D-005 and D-006), and add pre-registered *corroboration* conditions to the verdict, using evidence that is independent of the model's rivalry tiers: (a) the pair ranks in the top few percent of the state-level searches, (b) the pair ranks near the top of the searches-only pair score, (c) both directions are measured as hostile (reciprocity). Label each leading pair by **type**, using the effective number of channels: *marquee-matchup rivalry* (about one channel carries a direction) or *system rivalry* (several do). Publish both labels. A marquee-matchup pair can win if it is corroborated; a pair that fails corroboration is reported as a team rivalry between two states, not a state rivalry.

## 3c. Standing gut check: the average resident, not the most passionate fan

I measure *population-penetrating* antagonism. The sanity test for any number, any channel and any pair is: **would the average resident of the state, including someone who barely follows sports, plausibly feel this about the other state?**
- A typical Californian, even a big Lakers fan, does not feel animosity toward *Massachusetts* because of Celtics-Lakers. It is a brand feud between two teams with fans everywhere.
- A typical Madison resident who barely follows football does feel animosity toward *Minnesota* (Gophers-Badgers, Paul Bunyan's Axe, a shared border). That is a place rivalry that has diffused into the culture beyond fans.

What this implies for the design:
1. **Distance and place matter, and I can measure them.** First result (2026-10-16, `docs/GRAVITY_DISTANCE.md`): holding the model's predicted rivalry hostility fixed, antipathy shrinks to about 70% per 1,000 miles in the NFL (90% interval 63% to 78%) and about 73% in MLB (65% to 87%), and to about 89% in the NBA. Far-away brand rivalries are weaker than the team-level structure implies, as I expected. What-if (not adopted): damping the model by that factor leaves the top three unchanged (Illinois-Wisconsin, Massachusetts-New York, Minnesota-Wisconsin) and moves the brand pairs most (California-Massachusetts 13th to 36th, Pennsylvania-Texas 10th to 15th; Michigan-Ohio 17th to 13th). Distance alone does not rescue or sink the leaders: the top pairs are mostly neighbors already.
2. **Non-fans are only visible in state-level evidence.** Team-based data measure fans. The state-vs-state searches ("Minnesota sucks" from Wisconsin) come from the whole population. They are therefore the right instrument for diffusion beyond fans, and the verdict's corroboration conditions should lean on them (decision D-014 keeps them out of the score itself).
3. **Fandom penetration.** The attention matrix says how fans split their attention; it does not say what share of residents are fans at all. A population-weighted variant (attention times the share of residents who follow each sport) is a robustness check to add once sport-level penetration data for college sports is in hand.

**Pre-registered rule for the place factor** (written after the first estimate, so disclosed as such): a distance-decay factor exp(-gamma times distance) is adopted into the calibrated model if its 90% interval excludes zero for at least two leagues, using the pooled NFL and MLB estimate, applied identically to every pair. Today: NFL and MLB both exclude zero, so it qualifies.

## 4. The centerpiece: a gravity-style calibration of S, T and E from antipathy searches

I already collected "team X suck" searches by state for the 124 NFL, MLB, NBA and NHL teams. The model predicts a specific quantity for each state-team cell: the hostility state *s* feels toward team *j*, which is `Hm[s, j] = sum_i A[s,i] * R[i,j]`. The measured value for the same cell should be proportional to it, up to two nuisance factors:

- a **state factor** κ_s (how much this state searches at all), and
- a **team factor** ψ_j (how widely disliked this team is regardless of who is asking).

That is the structure of a standard "gravity" regression:

```
log v[s,j] = κ_s + ψ_j + β · log Hm[s,j] + error          (fit with Poisson pseudo-maximum likelihood to handle zeros)
```

- κ_s and ψ_j absorb the nuisances, so what remains identifies **how well the model's pattern of rivalry explains the pattern of hostility beyond what each state and each team would show anyway.**
- **β near 1 means the model's scale is right; β well below 1 means the model's rivalry weights are too steep, and above 1 too flat.**
- Replace the single `Hm` term by one term per rivalry tier (and per sport class) and the regression estimates **the actual ratio between tier 1, 2 and 3 salience**: today's arbitrary 0.40 / 0.20 / 0.08 becomes a fitted ladder with confidence intervals.
- Add distance, same-region, and own-brand-locality regressors and the data say how much of the hostility is place-based. That is the Massachusetts-California question in numbers.
- Residuals name the cells where the model is most wrong, which tells me where the priors are weakest.

**Targeted measurement for the dominance question.** For each of the top ~30 pairs, measure "suck" interest in each direction for *every* entity that embodies the target state (all pro teams plus the flagship college programs, ~10 to 20 terms per state). A bridge batch with anchors from two leagues puts football, baseball, basketball and hockey on one scale within a state. The result is a **measured channel decomposition**: of Illinois's antipathy toward Wisconsin entities, what fraction is aimed at the Packers? Compare to the model's 69%. Cost: roughly 100 to 150 terms, about 50 batches, comparable to what the worker already does in a day or two.

## 5. Free data: what exists, what it measures, and what to watch for

| Source | What it gives | Cost and access | Main weakness |
|---|---|---|---|
| Google Trends (have it) | State-level antipathy and co-search; single-term geographic shape; time series with spikes around games | Free, unofficial, rate-limited | Integer shares, zeros, one platform |
| Wikipedia Pageviews API | Daily views of rivalry articles vs team articles (share of team attention that goes to the rivalry) | Free, no key | National only; reading is not rooting |
| Wikipedia Clickstream | From a team's page, which rival pages readers click next: a *measured* split among rivals, national | Free monthly dump, several hundred MB (not downloaded) | National; reading behavior |
| GDELT DOC API | Counts of news articles mentioning both teams or both states; framing language | Free, no key, rate-limited | Media supply, not fan demand |
| Retrosheet game logs (MLB) | Per-game attendance since 1871, so rivalry premiums | Free, attribution requested | Baseball only |
| MLB, NHL public stats APIs | Schedules and attendance | Free, undocumented; check terms | Terms, stability |
| nflverse open data (NFL) | Schedules and results (clean, free) | Free, open | Little attendance |
| Wikipedia season pages | College football attendance by game, scores | Free | Manual or scraped |
| TV audience press coverage (Sports Media Watch, league press) | Rivalry game audience vs average | Free, manual | Sparse |
| Published fan polls (YouGov, Morning Consult, Harris/Axios, Seton Hall) | A few external anchor numbers | Free | Too sparse for a matrix |
| Census migration (ACS) | Who moved from where: explains transplant fans | Free | Indirect |
| Vivid Seats county maps (have it) | Where each team's fans live, a locality check for fan base | Have it | Single snapshot |

**Things to avoid:** anything needing an account, an API key, or a payment; scraping sites that forbid it; any attempt to get around rate limits.

## 6. How to combine several proxies without fooling myself

1. For each pair and direction, build a **channel-share vector** from each source (shares sum to 1 over the same set of entities).
2. Compare vectors with a distance that respects proportions (log-ratio or Jensen-Shannon).
3. Pool with a weighted geometric mean, weights set by each source's estimated reliability, **not** by which result I like.
4. Treat between-source disagreement as uncertainty: it widens the Monte Carlo, replacing today's fixed noise values with data-derived ones. (This closes milestone M4's "derive the noise from data.")
5. Report the verdict both ways: with the original priors and with the measured-and-calibrated weights.

## 7. Decision rules, written down before looking at any result

These are the pre-commitments. Changing them after seeing data would have to be disclosed as a change.

1. **Dominance test.** Let *m* be the measured share of the largest channel for a direction and *c* the model's. The dominance is **supported** if *m* is within 15 percentage points of *c* or if *c* lies inside the 90% interval of *m*, using at least two independent proxies that agree in direction. Otherwise it is **not supported** and the channel is rescaled toward *m* by an empirical-Bayes shrinkage factor.
2. **Gate redesign.** The single-edge removal gate stays as a diagnostic. The *gating* question becomes: after calibration, does the lead pair still lead, and is its dominance supported by data? A pair whose score rests on one matchup can still win **if** the data show that matchup is that large a share of the real rivalry.
3. **Place-framing.** A rivalry is credited to a state pair only to the extent that measured framing and fan locality support a state-level reading. The factor is estimated, not assigned, and applied to every pair by the same formula.
4. **No manual rescue** (decision D-015): no pair is adjusted by hand; every change goes through the estimated, global rule, and is logged in the changelog and the story.
5. **Report both.** Whatever the outcome, the original (prior-based) and calibrated rankings are published side by side.

## 8. Proposed order of work

0. **School-level measurement closes the college gap.** Terms like "Michigan sucks" are school-level, so the measured side is aggregated by school and compared with the model summed over that school's sports. Only six schools outside major-college football carry meaningful attention (Marquette, Brown, Dartmouth, Denver, Yale, Cornell); they are added with two small batches.

1. **Targeted channel decomposition** for the top 30 pairs (Section 4): about 50 batches, fastest route to the dominance question.
2. **Gravity regression** on the existing 124-team antipathy data: fits β and the tier ladder immediately, no new pulls needed.
3. **Place-framing** measures: fan locality (have it), naming (free), top-down framing (have it), GDELT counts (free).
4. **Rivalry premium** from Retrosheet and public APIs for MLB, NHL, NFL.
5. **Wikipedia pageview shares** for rivalry articles (the clickstream was not downloaded).
6. **Pool, calibrate, rerun** the full model and the Monte Carlo with data-derived noise; publish both rankings.

Estimated Google load for steps 1 and 3: under 100 batches. Everything else is free public data fetched with scripts.

## 9. What would change the conclusion

- If the measured Bears-Packers share is near 69%: dominance is supported, the gate fails for a defensible reason, and the headline becomes "a one-matchup rivalry can still win, and here is the evidence."
- If the measured share is much lower (say 40%): the model overweights it, calibrated Illinois-Wisconsin drops, and the leading tier may reorder toward systems like Minnesota-Wisconsin.
- If place-framing is weak for the brand-driven pairs: Massachusetts-New York, California-Washington and Maryland-Pennsylvania lose ground relative to Midwestern pairs, which is what the top-down check already hints at.
- If the proxies disagree sharply: the honest verdict stays a tied tier and the report says exactly which measurement I could not pin down.
