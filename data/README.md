# Data

This directory holds derived tables only. The bar stores the scripts read are not redistributed
and are not in git, and neither is the Yahoo chart data behind two of the tables. The rule, shared
with the companion KASE repositories: raw vendor feeds (the broker's minute bars, Yahoo chart
data, AIX data) are never published; small derived tables that the published results depend on
may be committed, with their source named.

## Committed: `derived/`

Ten CSV files, each written by one script. Every number in the write-up traces to one of them or
to the standard output of the script named beside it.

| file | rows | written by | what it holds |
|---|---|---|---|
| `transmission_daily.csv` | 591 sessions | `analysis/transmission/intraday_transmission.py` | the session panel: KASE open and close in USD, the opening gap, the intraday drift, the prior NASDAQ move and close, the premium at open and close, bar count |
| `regressor_alignment.csv` | 591 sessions | `analysis/transmission/intraday_transmission.py` | for each session, the previous session, the NASDAQ days matched to both, the number of NASDAQ sessions the opening gap spans, and the NASDAQ return over that span |
| `measurement_point_curve.csv` | 7 points | `analysis/transmission/hac_inference.py` | gap and drift betas with HAC(5) t against the price called the open, 11:29 to 12:00 |
| `venue_liquidity.csv` | 3 measures | `analysis/transmission/venue_liquidity.py` | median minutes with a trade, shares and USD turnover on both venues, with the ratio |
| `entry_delay.csv` | 7 entries | `analysis/transmission/entry_timing.py` | mean return and hit rate by entry delay from the first print |
| `overlap_contrasts.csv` | 3 contrasts | `analysis/transmission/overlap_comparison.py` | pooled and pair-specific next-day pass-through contrasts with standard errors and intervals |
| `foreign_daily.csv` | 1,968 pair-days | `analysis/transmission/foreign_legs.py` | daily closes of KSPI on NASDAQ and of KAP.IL and AIRA.IL on the LSE International Order Book from January 2024, with the regular-session close timestamp in UTC |
| `foreign_split.csv` | 900 pair-days | `analysis/transmission/foreign_legs.py` | for KZAP and AIRA, one row per foreign day with a KASE session: regular-session open, close and previous close from the hourly bars, the bar count, and the foreign price at the KASE close |
| `spread_estimates.csv` | 5 rows | `analysis/transmission/transmission_tradeable.py` | Roll and Corwin-Schultz full-spread estimates under each treatment and window, and the commission per side |
| `yearend_windows.csv` | 11 windows | `analysis/calendar/yearend_global_decomposition.py` | per entry year, the KASE basket return with its source, the SPY and EEM returns, and the differences |

The two foreign-leg tables are the record of an input that can no longer be rebuilt: Yahoo serves
hourly history as a rolling two-year window, so the bars behind `foreign_split.csv` for 2024-08 to
2024-10 are no longer available, and `foreign_legs.py` stops with a message when its cache is
absent. Both tables are daily aggregates, one row per day and pair; they hold no minute or hourly
series.

Every other file regenerates byte-identically from the stores below and two Yahoo series fetched
at run time: `transmission_daily.csv` and `regressor_alignment.csv` carry the KSPI daily closes on
NASDAQ, and `yearend_windows.csv` the SPY and EEM closes.

## Not committed

`kase/intraday/<TICKER>.KZ/<YYYY-MM>.parquet` and `nasdaq/intraday/KSPI.US/<YYYY-MM>.parquet`:
the 1-minute bars, assembled by the fetcher in the `kase-market-data` repository from a retail
broker's chart-data endpoint (Tradernet). That repository documents the acquisition
defects that matter when reading them. The bars are not redistributed because the endpoint's terms
do not clearly address republication.

`kase/daily/<TICKER>.KZ.parquet`: the daily companion series from the same broker, also built and
documented in `kase-market-data`. Section 9 of the write-up uses it for the one year-end window
the minute store cannot price.

`cache/yahoo/*.json`: raw Yahoo chart data, read only by `foreign_legs.py`. Not in the tree,
ignored by `.gitignore`.

All of these paths are in `.gitignore`, including a `kase/daily` symlink.

## Attaching the stores

`analysis/_store.py` resolves both locations for every script. It tries, in order:

1. the environment variables `KASE_STORE` and `KASE_DAILY`;
2. `data/kase/intraday`, `data/nasdaq/intraday` and `data/kase/daily` inside this repository,
   populated or symlinked;
3. sibling checkouts, `../trading desk/data` and `../kase-market-data/data/kase/daily`.

Either of the first two works on its own:

```sh
export KASE_STORE=/path/to/store          # contains kase/intraday and nasdaq/intraday
export KASE_DAILY=/path/to/kase/daily     # contains KSPI.KZ.parquet and siblings
```

or

```sh
ln -s /path/to/store/kase/intraday    data/kase/intraday
ln -s /path/to/store/nasdaq/intraday  data/nasdaq/intraday
ln -s /path/to/kase/daily             data/kase/daily
```

A script that cannot find a store exits with the list of paths it tried and the environment
variable that overrides them. It does not fail later inside a read.

## Running

```sh
pip install -r requirements.txt
python analysis/transmission/intraday_transmission.py   # writes derived/transmission_daily.csv
python analysis/transmission/hac_inference.py
```

`intraday_transmission.py` runs first, because most scripts read the panel it writes. Two further
dependencies: `transmission_tradeable.py` reads `entry_delay.csv`, and `yearend_constructions.py`
reads `spread_estimates.csv`. The README gives the full order and `docs/reproducibility.md` the
regeneration procedure.
