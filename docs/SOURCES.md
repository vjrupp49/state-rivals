# Sources, licenses and what is redistributed

I researched these terms on 2026-10-18 from public pages and summarize them below. This is my working policy and a good-faith reading, **not legal advice**. Items marked *to confirm* could not be settled from public text; I accept the stated residual risk and will correct the repository if a rights holder objects.

**Policy:** the repository publishes code, derived aggregates (ratios, shares, counts) and re-fetch scripts. It does not redistribute raw third-party dumps. Raw files are git-ignored and rebuilt by the scripts. The Google Trends cache and the raw Vivid Seats county files stay local.

| Source | Used for | Access | In the repo? | Terms as found, and risk |
|---|---|---|---|---|
| U.S. Census Bureau, county population estimates (Vintage 2025) | Population weights, state populations | Public download | Derived table (`county_population.csv`) | Public domain. No restriction. |
| Google Trends (unofficial `interest_by_region` via `pytrends`) | Team and sport attention by state; antipathy, co-search and top-down searches | Scripted, rate-limited; the worker backs off on every refusal and never evades throttling | Derived ratios only (`observations_trends.csv.gz`); raw responses git-ignored | Google's Trends help page allows use of Trends information subject to the Google Terms of Service, with attribution ("Data source: Google Trends"). It does not address publishing derived datasets; the Terms of Service govern. Automated access through an unofficial endpoint is not sanctioned by Google (the official API is an invitation-only alpha; an application was submitted). **Risk: moderate, to confirm.** Mitigations: aggregates only, attribution, no raw dump, slow polite pulling. |
| Vivid Seats ticket-origin plurality maps (NFL, MLB, NBA, MLS, NHL, WNBA, college football) | County plurality fandom (`C_si`) | Extracted from each published map's embedded dataset | Population-weighted shares only; raw county files git-ignored | Third-party blog data. Terms not located. Attribution given. **To confirm.** The NHL map predates the Utah relocation. |
| Wikipedia (MediaWiki API; Pageviews API) | Program lists by sport (registry), rivalry-article titles, page views | MediaWiki and Wikimedia REST APIs, polite delays and a descriptive User-Agent | Derived registry rows with a source note per row; page-view totals in `wikipedia_rivalry.csv` | Article text is CC BY-SA 4.0 (attribution required if text is reused; I reuse facts and counts, not text). Pageviews data is freely usable. Wikimedia API etiquette followed. **Low risk.** |
| MLB public stats API (`statsapi.mlb.com`) | Regular-season schedule and results, 2021 to 2025 | Public, keyless, undocumented | Derived pair counts and win shares only (`pair_exposure.csv`, `team_success.csv`); raw JSON git-ignored | The notice historically attached to MLB data permits only individual, non-commercial, non-bulk use and requires written permission otherwise. My use is non-commercial research on five seasons of aggregates. **Low to moderate risk, to confirm** against the live notice in an API response. |
| nflverse `games.csv` (github.com/nflverse/nfldata) | NFL schedule and results, 2021 to 2025 | Public file on GitHub | Derived pair counts and win shares only; raw file git-ignored | Data license not confirmed from public text (the nflverse R package is MIT-licensed; that does not settle the data). **To confirm.** Low risk for derived counts. |
| NCAA, school, league and conference pages | Rivalry discovery list and notes | Public pages | Citations only (`docs/PROTOCOL.md` section 10) | Facts only. |
| S&P Global (2025 U.S. sports viewing and live attendance), Nielsen fan insights | National sport-level priors | Published reports | Numeric priors only (`survey_priors.csv`) with citation | Priors, never state-level answers; cited. |
| Know Rivalry | Would supply measured rivalry points | Blocked to scripted access; browser use not completed | No | I used my own rivalry priors, tested against search and readership data instead. |

## Attribution to include in the report and README

Google Trends ("Data source: Google Trends, https://www.google.com/trends"); Vivid Seats; U.S. Census Bureau; Wikipedia contributors (CC BY-SA 4.0) and the Wikimedia Pageviews data; MLB (public stats API); nflverse; S&P Global Market Intelligence; Nielsen.

## What is and is not published

- Published: all code, configuration, registries, derived tables, figures, the story and documentation.
- Not published: raw Google Trends responses (local cache), raw Vivid Seats county files, raw MLB and nflverse downloads.
- Consequence: the results are inspectable and every downstream stage is re-runnable from the derived tables, but the raw Trends pull cannot be regenerated without repeating it (days). See `README.md` and `docs/LIMITATIONS.md` item 10.

## Decisions I made for the release

1. **License:** MIT for code; CC BY 4.0 for derived tables, figures and documents (`LICENSE`, `LICENSE-DATA.md`).
2. **Raw Google Trends payloads:** not published. The derived integer shares are in `data/observations/observations_trends.csv.gz`; raw responses stay in a local cache.
3. **Items marked *to confirm*** (Google Trends automated access and derived-data publication, Vivid Seats terms, the nflverse data license, the MLB notice): I publish aggregates only, with attribution, and accept the stated residual risk.
4. **Author identity:** my name only, with a fresh single-commit history.
