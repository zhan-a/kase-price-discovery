"""Year-end calendar window on KASE equities: one construction and its sensitivity.

The trade is mechanical: an equal-weighted basket of nine KASE names bought at
the first close on or after 20 December and sold at the first close on or after
10 January. The December-January stretch is when a thin market stops printing,
so the construction has to say which prints count as a close.

Admission rule. A session day enters the minute-store series only if the store
holds at least MIN_BARS priced bars inside the 11:29-17:30 window. A day with
one or two prints is not a closing price at which a basket could have been
struck; the "legs the floor changes" table below lists every leg whose price
the floor moves, with both prices. The floor is a free parameter, so the summary
statistics are repeated at floors of 1 (every print counts), 3, 5, 10 and 20
bars. The daily companion series, used only for the one window the minute store
cannot price, has one row per day with a trade and no bar count to floor.

Sources. The minute store wherever it prices at least MIN_LEGS legs of a window;
the daily companion where it prices fewer. In this sample that is the 2015
window alone, where the minute store holds no bar for any leg (a collection gap
documented in kase-market-data). The daily series has no bar count, so no floor
applies to that window; its legs are printed with their daily volume instead.
Where both sources price the same leg they are compared leg by leg, and the
disagreement is set against a staleness proxy.

Costs. The net-of-cost table reads data/derived/spread_estimates.csv, written by
transmission_tradeable.py, so the round trips are the same one spread plus
commission on both sides used in the transmission sections. The spreads are
KSPI's; the basket names are thinner, so the table understates their cost.

yearend_global_decomposition.py imports constructions() and runs the same window
on SPY and EEM.

Run:  python analysis/calendar/yearend_constructions.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _store import store as _store_dir, daily as _daily_dir


# --- Configuration -----------------------------------------------------------

REPO = Path(__file__).resolve().parents[2]
SPREADS = REPO / "data" / "derived" / "spread_estimates.csv"

BASKET = ["ASBN", "CCBN", "HSBK", "KCEL", "KEGC", "KMGD", "KZAP", "KZTK", "KZTO"]

ENTRY_MONTH, ENTRY_DAY = 12, 20
EXIT_MONTH, EXIT_DAY = 1, 10
SEARCH_LIMIT_DAYS = 10          # calendar days a leg may drift past its target date
MIN_LEGS = 3                    # a window is computed only with at least this many legs
ENTRY_YEARS = range(2015, 2026)  # entry years 2015 .. 2025 inclusive

# the store also carries pre-session carry-over stamps and late-evening
# artifacts, not tradeable prices
SESSION_START = pd.Timestamp("11:29").time()
SESSION_END = pd.Timestamp("17:30").time()

MIN_BARS = 5                    # the admission floor for a minute-store day
FLOORS = (1, 3, 5, 10, 20)      # sensitivity of the result to the floor

STALENESS_HALF_WINDOW = 45      # +/- 45 calendar days == "surrounding 90 days"


def resolve_paths() -> tuple[Path, Path]:
    """Locate the two data stores, which sit outside this repository."""
    store = _store_dir()
    daily = _daily_dir()
    intraday = store / "kase" / "intraday"
    missing = [str(p) for p in (intraday, daily) if not p.is_dir()]
    if missing:
        sys.exit(
            "Data store not found. Expected these directories to exist:\n  "
            + "\n  ".join(missing)
            + "\nSet KASE_STORE and/or KASE_DAILY to override the default locations."
        )
    return intraday, daily


# --- Loading -----------------------------------------------------------------


def _empty_days() -> pd.DataFrame:
    return pd.DataFrame(columns=["first_print", "day_close", "n_bars"],
                        index=pd.DatetimeIndex([], name="date"))


def load_minute_days(intraday: Path, ticker: str, months: set[str]) -> pd.DataFrame:
    """First print, last print and priced-bar count per session day, unfloored.

    Only the month files the calendar trade touches are read; the store spans a
    decade and the trade touches two months a year.
    """
    frames = []
    for month in sorted(months):
        path = intraday / f"{ticker}.KZ" / f"{month}.parquet"
        if path.exists():
            frames.append(pd.read_parquet(path, columns=["ts_almaty", "open", "close"]))
    if not frames:
        return _empty_days()
    bars = pd.concat(frames, ignore_index=True)
    bars = bars[bars["close"].notna()]
    if bars.empty:
        return _empty_days()
    local_time = bars["ts_almaty"].dt.time
    bars = bars.loc[(local_time >= SESSION_START) & (local_time <= SESSION_END)]
    if bars.empty:
        return _empty_days()
    bars = bars.sort_values("ts_almaty")
    bars["date"] = bars["ts_almaty"].dt.normalize().dt.tz_localize(None)
    grouped = bars.groupby("date")
    return pd.DataFrame({
        "first_print": grouped["open"].first(),
        "day_close": grouped["close"].last(),
        "n_bars": grouped["close"].size(),
    })


def admit(days: pd.DataFrame, min_bars: int) -> pd.DataFrame:
    """The session days that clear the bar floor."""
    return days[days["n_bars"] >= min_bars]


def load_daily(daily_dir: Path, ticker: str) -> pd.DataFrame:
    path = daily_dir / f"{ticker}.KZ.parquet"
    if not path.exists():
        return pd.DataFrame(columns=["first_print", "day_close", "volume"])
    d = pd.read_parquet(path, columns=["date", "open", "close", "volume"])
    d = d.dropna(subset=["date"]).sort_values("date").drop_duplicates("date", keep="last")
    d = d.set_index("date")
    return pd.DataFrame({"first_print": d["open"], "day_close": d["close"], "volume": d["volume"]})


# --- Trade construction ------------------------------------------------------


def first_price_on_or_after(prices: pd.DataFrame, target: pd.Timestamp, field: str):
    """The first price at or after `target`, provided it lands inside the limit."""
    if prices.empty:
        return None, None
    deadline = target + pd.Timedelta(days=SEARCH_LIMIT_DAYS)
    window = prices.loc[(prices.index >= target) & (prices.index <= deadline), field]
    window = window.dropna()
    window = window[window > 0]
    if window.empty:
        return None, None
    return float(window.iloc[0]), window.index[0]


def leg_returns(prices_by_ticker: dict[str, pd.DataFrame], year: int, field: str) -> dict[str, dict]:
    """Per-leg return and prices for one window; legs that cannot be priced drop out."""
    entry_target = pd.Timestamp(year=year, month=ENTRY_MONTH, day=ENTRY_DAY)
    exit_target = pd.Timestamp(year=year + 1, month=EXIT_MONTH, day=EXIT_DAY)
    legs = {}
    for ticker, prices in prices_by_ticker.items():
        p_in, d_in = first_price_on_or_after(prices, entry_target, field)
        p_out, d_out = first_price_on_or_after(prices, exit_target, field)
        if p_in is None or p_out is None:
            continue
        legs[ticker] = {"ret": p_out / p_in - 1.0, "entry_date": d_in, "entry_px": p_in,
                        "exit_date": d_out, "exit_px": p_out}
    return legs


def build_series(prices_by_ticker: dict[str, pd.DataFrame], field: str = "day_close") -> pd.DataFrame:
    """One row per entry year: basket return and the legs that supported it."""
    rows = []
    for year in ENTRY_YEARS:
        legs = leg_returns(prices_by_ticker, year, field)
        rets = [v["ret"] for v in legs.values()]
        rows.append({
            "entry_year": year,
            "n_legs": len(legs),
            "ret": float(np.mean(rets)) if len(legs) >= MIN_LEGS else np.nan,
            "legs": legs,
        })
    return pd.DataFrame(rows).set_index("entry_year")


def splice(minute: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    """Minute tape wherever it prices the window; daily only where it cannot."""
    out = minute.copy()
    out["source"] = np.where(out["ret"].notna(), "minute", "daily")
    fallback = out["ret"].isna()
    out.loc[fallback, "ret"] = daily.loc[fallback, "ret"]
    out.loc[fallback, "n_legs"] = daily.loc[fallback, "n_legs"]
    out.loc[out["ret"].isna(), "source"] = "none"
    return out


def constructions(min_bars: int = MIN_BARS) -> dict:
    """Load both sources and build the three series at one admission floor.

    Returns the unfloored minute days and the daily prices too, so a caller can
    rebuild at another floor without reading the store again.
    """
    intraday, daily_dir = resolve_paths()
    months = set()
    for year in ENTRY_YEARS:
        months.add(f"{year}-12")
        months.add(f"{year + 1}-01")
    minute_days = {t: load_minute_days(intraday, t, months) for t in BASKET}
    daily_prices = {t: load_daily(daily_dir, t) for t in BASKET}
    return rebuild(minute_days, daily_prices, min_bars)


def rebuild(minute_days: dict, daily_prices: dict, min_bars: int) -> dict:
    minute = build_series({t: admit(d, min_bars) for t, d in minute_days.items()})
    daily = build_series(daily_prices)
    return {"min_bars": min_bars, "minute_days": minute_days, "daily_prices": daily_prices,
            "minute": minute, "daily": daily, "spliced": splice(minute, daily)}


# --- Summary statistics ------------------------------------------------------


def summarise(name: str, series: pd.Series) -> dict:
    x = series.dropna().to_numpy(dtype=float)
    n = x.size
    if n == 0:
        return {"construction": name, "n": 0}
    mean = x.mean()
    sd = x.std(ddof=1) if n > 1 else np.nan
    se = sd / np.sqrt(n) if n > 1 else np.nan
    tstat = mean / se if n > 1 else np.nan
    if n > 1:
        crit = stats.t.ppf(0.975, n - 1)
        lo, hi = mean - crit * se, mean + crit * se
    else:
        lo = hi = np.nan
    return {"construction": name, "n": n, "mean": mean, "sd": sd, "t": tstat,
            "ci_lo": lo, "ci_hi": hi, "n_pos": int((x > 0).sum())}


def print_summary_header() -> None:
    print(f"{'construction':<28} {'n':>3} {'mean':>9} {'sd':>9} {'t':>7} "
          f"{'ci_lo':>9} {'ci_hi':>9} {'n_pos':>6}")


def print_summary(s: dict) -> None:
    if s["n"] == 0:
        print(f"{s['construction']:<28} {0:>3}   (no computable windows)")
        return
    print(f"{s['construction']:<28} {s['n']:>3} {100 * s['mean']:>8.3f}% "
          f"{100 * s['sd']:>8.3f}% {s['t']:>7.3f} {100 * s['ci_lo']:>8.3f}% "
          f"{100 * s['ci_hi']:>8.3f}% {s['n_pos']:>6}")


# --- Staleness proxy ---------------------------------------------------------


def flat_close_share(daily_prices: pd.DataFrame, centre: pd.Timestamp) -> float:
    """Share of daily closes in the surrounding 90 days that repeat the prior close.

    A thinly traded KASE line prints the same close day after day; that repeat
    rate is a cheap read on how stale any single price in the window is likely
    to be.
    """
    lo = centre - pd.Timedelta(days=STALENESS_HALF_WINDOW)
    hi = centre + pd.Timedelta(days=STALENESS_HALF_WINDOW)
    closes = daily_prices.loc[(daily_prices.index >= lo) & (daily_prices.index <= hi), "day_close"]
    closes = closes.dropna()
    if len(closes) < 2:
        return np.nan
    changes = closes.diff().iloc[1:]
    return float((changes == 0).mean())


# --- Costs -------------------------------------------------------------------


def round_trips() -> list[tuple[str, float]]:
    """Round-trip costs from the spread table transmission_tradeable.py writes."""
    if not SPREADS.exists():
        return []
    s = pd.read_csv(SPREADS)
    commission = float(s.loc[s["estimator"] == "commission", "spread"].iloc[0])
    roll = float(s[(s["estimator"] == "roll") & s["headline"]]["spread"].iloc[0])
    cs = float(s[(s["estimator"] == "corwin_schultz") & s["headline"]]["spread"].iloc[0])
    return [("commission only", 2 * commission),
            ("Roll spread + commission", roll + 2 * commission),
            ("Corwin-Schultz spread + commission", cs + 2 * commission)]


# --- Reporting ---------------------------------------------------------------


def rule(title: str) -> None:
    print()
    print(title)
    print("-" * max(len(title), 60))


def pct(v) -> str:
    return "      --" if pd.isna(v) else f"{100 * v:7.2f}%"


def main() -> None:
    c = constructions(MIN_BARS)
    minute_series, daily_series, spliced_series = c["minute"], c["daily"], c["spliced"]

    print("KASE year-end calendar window: buy 20 Dec, sell 10 Jan, close to close")
    print(f"Basket: {', '.join(BASKET)}")
    print(f"Entry years {min(ENTRY_YEARS)}-{max(ENTRY_YEARS)}; search limit {SEARCH_LIMIT_DAYS} calendar days; "
          f"minimum {MIN_LEGS} legs")
    print(f"Minute-store day admitted with at least {MIN_BARS} priced bars in "
          f"{SESSION_START:%H:%M}-{SESSION_END:%H:%M} Almaty; daily source used where the "
          f"minute store prices fewer than {MIN_LEGS} legs")

    rule(f"Per-window basket returns by construction, floor {MIN_BARS} bars")
    print(f"{'entry':>6} {'minute_n':>9} {'minute_ret':>11} {'daily_n':>8} {'daily_ret':>10} "
          f"{'spliced_ret':>12} {'source':>8}")
    for year in ENTRY_YEARS:
        m, d, s = minute_series.loc[year], daily_series.loc[year], spliced_series.loc[year]
        print(f"{year:>6} {int(m['n_legs']):>9} {pct(m['ret']):>11} {int(d['n_legs']):>8} "
              f"{pct(d['ret']):>10} {pct(s['ret']):>12} {s['source']:>8}")

    daily_windows = [y for y in ENTRY_YEARS if spliced_series.loc[y, "source"] == "daily"]
    if daily_windows:
        rule("Legs of the windows priced from the daily source: no bar floor applies, daily volume shown")
        print(f"{'entry':>6} {'ticker':>7} {'entry date':>11} {'price':>10} {'volume':>12} "
              f"{'exit date':>11} {'price':>10} {'volume':>12} {'ret':>8}")
        for y in daily_windows:
            for t, leg in sorted(daily_series.loc[y, "legs"].items()):
                dp = c["daily_prices"][t]
                print(f"{y:>6} {t:>7} {leg['entry_date']:%Y-%m-%d} {leg['entry_px']:>10.2f} "
                      f"{dp.loc[leg['entry_date'], 'volume']:>12,.0f} {leg['exit_date']:%Y-%m-%d} "
                      f"{leg['exit_px']:>10.2f} {dp.loc[leg['exit_date'], 'volume']:>12,.0f} "
                      f"{100 * leg['ret']:>+7.2f}%")

    rule(f"Summary statistics by construction, floor {MIN_BARS} bars")
    print_summary_header()
    for s in [summarise("1. minute only", minute_series["ret"]),
              summarise("2. spliced (the estimate)", spliced_series["ret"]),
              summarise("3. daily only", daily_series["ret"])]:
        print_summary(s)

    rule("Sensitivity to the admission floor (minute-only and spliced series)")
    print_summary_header()
    by_floor = {}
    for floor in FLOORS:
        r = rebuild(c["minute_days"], c["daily_prices"], floor)
        by_floor[floor] = r
        print_summary(summarise(f"floor {floor:>2}: minute only", r["minute"]["ret"]))
        print_summary(summarise(f"floor {floor:>2}: spliced", r["spliced"]["ret"]))

    rule(f"Legs the floor changes: every print, against the floor of {MIN_BARS} bars")
    base = by_floor[1]["minute"] if 1 in by_floor else rebuild(c["minute_days"], c["daily_prices"], 1)["minute"]
    print(f"{'entry':>6} {'ticker':>7} {'floor 1 entry':>22} {'floor 1 exit':>22} {'ret':>8}  "
          f"{'floor ' + str(MIN_BARS) + ' entry':>22} {'floor ' + str(MIN_BARS) + ' exit':>22} {'ret':>8}")
    changed = 0
    for year in ENTRY_YEARS:
        lb, la = base.loc[year, "legs"], minute_series.loc[year, "legs"]
        for t in BASKET:
            b, a = lb.get(t), la.get(t)
            if b is None and a is None:
                continue
            same = (b is not None and a is not None and b["entry_date"] == a["entry_date"]
                    and b["exit_date"] == a["exit_date"])
            if same:
                continue
            changed += 1
            fmt = lambda leg, k: (f"{leg[k + '_date']:%Y-%m-%d} @{leg[k + '_px']:.2f}" if leg else "dropped")
            fr = lambda leg: (f"{100 * leg['ret']:+7.2f}%" if leg else "")
            print(f"{year:>6} {t:>7} {fmt(b, 'entry'):>22} {fmt(b, 'exit'):>22} {fr(b):>8}  "
                  f"{fmt(a, 'entry'):>22} {fmt(a, 'exit'):>22} {fr(a):>8}")
    print(f"legs changed by the floor: {changed}")

    # --- splice diagnostics: common-leg comparison ---
    rule("Splice diagnostic: minute vs daily on commonly covered legs")
    common_rows, leg_rows = [], []
    for year in ENTRY_YEARS:
        m_legs, d_legs = minute_series.loc[year, "legs"], daily_series.loc[year, "legs"]
        shared = sorted(set(m_legs) & set(d_legs))
        if not shared:
            common_rows.append({"entry_year": year, "n_common": 0})
            continue
        m_basket = float(np.mean([m_legs[t]["ret"] for t in shared]))
        d_basket = float(np.mean([d_legs[t]["ret"] for t in shared]))
        common_rows.append({"entry_year": year, "n_common": len(shared), "minute": m_basket,
                            "daily": d_basket, "diff": m_basket - d_basket, "legs": shared})
        for t in shared:
            leg_rows.append({"entry_year": year, "ticker": t, "minute": m_legs[t]["ret"],
                             "daily": d_legs[t]["ret"], "diff": m_legs[t]["ret"] - d_legs[t]["ret"]})
    common = pd.DataFrame(common_rows).set_index("entry_year")
    legs_df = pd.DataFrame(leg_rows)

    print(f"{'entry':>6} {'n_common':>9} {'minute':>10} {'daily':>10} {'diff(bp)':>10}")
    for year, row in common.iterrows():
        if row["n_common"] == 0:
            print(f"{year:>6} {0:>9}   (no legs priced by both sources)")
            continue
        print(f"{year:>6} {int(row['n_common']):>9} {100 * row['minute']:>9.3f}% "
              f"{100 * row['daily']:>9.3f}% {1e4 * row['diff']:>10.2f}")

    priced = common.dropna(subset=["diff"])
    if not priced.empty:
        worst = priced["diff"].abs().idxmax()
        print()
        print(f"Largest basket disagreement: entry year {worst}, "
              f"{1e4 * priced.loc[worst, 'diff']:.2f} bp "
              f"(minute {100 * priced.loc[worst, 'minute']:.3f}% vs "
              f"daily {100 * priced.loc[worst, 'daily']:.3f}%, "
              f"{int(priced.loc[worst, 'n_common'])} common legs)")
        exact = priced.index[priced["diff"] == 0].tolist()
        print(f"Windows agreeing exactly: {exact if exact else 'none'}")
        exact_legs = legs_df.loc[legs_df["diff"] == 0]
        print(f"Leg-windows agreeing exactly: {len(exact_legs)} of {len(legs_df)}")

    rule("Staleness vs disagreement (leg-window level)")
    if legs_df.empty:
        print("No leg-windows covered by both sources.")
    else:
        legs_df["staleness"] = [
            flat_close_share(c["daily_prices"][r.ticker],
                             pd.Timestamp(year=r.entry_year, month=ENTRY_MONTH, day=ENTRY_DAY))
            for r in legs_df.itertuples()
        ]
        legs_df["abs_diff"] = legs_df["diff"].abs()
        usable = legs_df.dropna(subset=["staleness", "abs_diff"])
        rho, pval = stats.spearmanr(usable["staleness"], usable["abs_diff"])
        print(f"n leg-windows = {len(usable)}")
        print(f"Spearman rank correlation (staleness, |disagreement|) = {rho:.4f}  (p = {pval:.4f})")
        top = legs_df.sort_values("abs_diff", ascending=False).head(6)
        print()
        print(f"{'entry':>6} {'ticker':>7} {'minute':>10} {'daily':>10} {'diff(bp)':>10} {'staleness':>10}")
        for r in top.itertuples():
            print(f"{r.entry_year:>6} {r.ticker:>7} {100 * r.minute:>9.3f}% {100 * r.daily:>9.3f}% "
                  f"{1e4 * r.diff:>10.2f} {r.staleness:>10.3f}")

    rule("Net of costs: the spliced mean against one spread plus commission both ways")
    trips = round_trips()
    if not trips:
        print("data/derived/spread_estimates.csv absent; run transmission_tradeable.py first")
        return
    gross = summarise("spliced", spliced_series["ret"])["mean"]
    print(f"gross mean, spliced series: {100 * gross:+.3f}%  (KSPI spread estimates applied to a thinner basket)")
    print(f"{'round trip':<36} {'cost':>7} {'net':>9}")
    for label, rt in trips:
        print(f"{label:<36} {100 * rt:>6.2f}% {100 * (gross - rt):>+8.3f}%")


if __name__ == "__main__":
    main()
