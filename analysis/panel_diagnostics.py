"""Section D: panel diagnostics for the KASE one-minute store.

Every result elsewhere in this project is built on the assumption that a KASE
"session" in the one-minute store is a well-behaved object: it runs from the
11:29 opening auction to a close near 17:25/17:30, it exists on every weekday
the exchange was open, and the bars inside it are genuine trades.  That
assumption is not free.  Bars exist only for minutes in which a trade printed,
so a thin instrument's session bounds are an observation of liquidity as much as
of the trading calendar, and the vendor feed carries at least one class of
synthetic print that is not a trade at all.

This script measures the ways the panel departs from that idealisation:

1. Venue-wide early closes.  A date on which essentially every instrument stops
   printing more than an hour earlier than on both neighbouring sessions is an
   exchange event, not an accident of thin trading; a single instrument doing so
   is just a quiet day.  Requiring the behaviour across a broad panel and
   against both neighbours is what separates the two.
2. Market-wide non-trading weekdays over the modern sample, and the longest
   consecutive run of them, which bounds how stale a "previous session" can be
   in any lagged regression.
3. January 2022 in detail.  The Kazakh unrest closed and then truncated the
   market; the shape of that interruption matters for anything estimated across
   it.
4. Carry-over opening prints.  Through 2016-2017 the feed stamps a bar at
   exactly 09:00 Almaty, hours before the session opens.  Whether its close is
   the previous session's close or the coming session's first trade decides
   whether it is a stale carry-over to be discarded or real information.
5. Per-instrument session bounds from 2023, to show how far the *observed*
   close-time varies across the cross-section once the venue calendar is fixed.

Finally, because a venue-wide early close truncates exactly the part of the
session in which foreign information would be impounded, the script re-estimates
the KSPI KASE-versus-NASDAQ transmission regressions with that date removed and
reports how far each coefficient moves.
"""

from __future__ import annotations

import glob
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[0]))
from _store import store as _store_dir, daily as _daily_dir


# Configuration

REPO_ROOT = Path(__file__).resolve().parents[1]

# companion checkouts; both locations are overridable
STORE = _store_dir()
KASE_INTRADAY = STORE / "kase" / "intraday"
NASDAQ_INTRADAY = STORE / "nasdaq" / "intraday"

# the eleven equity lines. FX keeps its own hours and is excluded.
PANEL = ["KSPI", "KZAP", "AIRA", "HSBK", "KCEL", "KZTO", "KEGC", "KZTK",
         "CCBN", "ASBN", "KMGD"]

# minutes past Almaty midnight
AUCTION_MIN = 11 * 60 + 29
SESSION_END_MIN = 17 * 60 + 30
LATE_BAR_MIN = 17 * 60 + 25          # "a bar after 17:25"
CARRY_OVER_MIN = 9 * 60             # the synthetic 09:00 print

# venue-wide needs a broad cross-section; on a few instruments this is thin-
# day noise
EARLY_CLOSE_GAP_MIN = 60
EARLY_CLOSE_MIN_PANEL = 8
EARLY_CLOSE_MIN_SHARE = 0.8

MODERN_START = pd.Timestamp("2024-01-19")
MODERN_END = pd.Timestamp("2026-08-24")

CARRY_START, CARRY_END = pd.Timestamp("2016-06-01"), pd.Timestamp("2017-12-31")
CARRY_TICKERS = ["HSBK", "KZTO", "KEGC", "KCEL", "KZTK", "CCBN"]

BOUNDS_START = pd.Timestamp("2023-01-01")

# Section A's regression window
REG_START = pd.Timestamp("2024-02-01")

HAC_LAGS = 5

PRICE_TOL = 1e-9  # prices are quoted to the tick; equality is exact


# Loading

def _require_store() -> None:
    if not KASE_INTRADAY.is_dir():
        sys.exit(
            f"KASE one-minute store not found at {KASE_INTRADAY}.\n"
            "Set KASE_STORE to the directory containing kase/intraday."
        )


def load_intraday(root: Path, ticker: str, tz_col: str) -> pd.DataFrame:
    """Concatenate a ticker's monthly parquet shards into one sorted frame."""
    files = sorted(glob.glob(str(root / ticker / "*.parquet")))
    if not files:
        raise FileNotFoundError(f"no parquet shards for {ticker} under {root}")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df = df.sort_values("ts_utc").reset_index(drop=True)
    local = df[tz_col]
    df["date"] = local.dt.normalize().dt.tz_localize(None)
    df["tod"] = local.dt.hour * 60 + local.dt.minute
    return df


def hhmm(minutes: float) -> str:
    if pd.isna(minutes):
        return "  --  "
    m = int(round(minutes))
    return f"{m // 60:02d}:{m % 60:02d}"


def rule(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# D1, D2, D3, D5 share one summary

def session_summary(bars: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """First-bar, last-bar and bar-count per instrument-date."""
    out = []
    for tkr, df in bars.items():
        g = df.groupby("date")["tod"].agg(first="min", last="max", n="size")
        g = g.reset_index()
        g["ticker"] = tkr
        out.append(g)
    return pd.concat(out, ignore_index=True)


def venue_early_closes(summary: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Dates where the whole panel's last bar is far earlier than on both neighbours.

    Neighbours are the adjacent dates on which the panel traded at all, not the
    adjacent calendar days: a Monday's neighbour to the left is the preceding
    Friday.
    """
    dates = np.sort(summary["date"].unique())
    pos = {d: i for i, d in enumerate(dates)}
    summary = summary.assign(i=summary["date"].map(pos))
    last = summary.pivot(index="i", columns="ticker", values="last")
    last = last.reindex(range(len(dates)))

    prev, nxt = last.shift(1), last.shift(-1)
    flagged = (last < prev - EARLY_CLOSE_GAP_MIN) & (last < nxt - EARLY_CLOSE_GAP_MIN)
    comparable = last.notna() & prev.notna() & nxt.notna()

    tbl = pd.DataFrame({
        "date": dates,
        "n_comparable": comparable.sum(axis=1).to_numpy(),
        "n_early": flagged.sum(axis=1).to_numpy(),
        "med_last": last.median(axis=1).to_numpy(),
        "med_prev": prev.median(axis=1).to_numpy(),
        "med_next": nxt.median(axis=1).to_numpy(),
    })
    tbl["share_early"] = tbl["n_early"] / tbl["n_comparable"].replace(0, np.nan)
    hits = tbl[(tbl["n_comparable"] >= EARLY_CLOSE_MIN_PANEL)
               & (tbl["share_early"] >= EARLY_CLOSE_MIN_SHARE)].copy()
    return hits.sort_values("date"), tbl


def missing_weekdays(summary: pd.DataFrame) -> tuple[list[pd.Timestamp], list[list[pd.Timestamp]]]:
    traded = set(pd.DatetimeIndex(summary["date"].unique()))
    weekdays = pd.bdate_range(MODERN_START, MODERN_END)
    missing = [d for d in weekdays if d not in traded]

    runs, current = [], []
    for d in weekdays:
        if d in traded:
            if current:
                runs.append(current)
                current = []
        else:
            current.append(d)
    if current:
        runs.append(current)
    return missing, runs


# D4: carry-over opening prints

def carry_over_prints(bars: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """For each 09:00 bar, its close against the two candidate sources.

    The comparison is against the previous *session* close and the current
    session's first print, where a session excludes anything before the 11:29
    auction, so that a run of consecutive 09:00 stamps cannot chain onto itself.
    """
    rows = []
    for tkr in CARRY_TICKERS:
        df = bars[tkr]
        sess = df[df["tod"] >= AUCTION_MIN]
        agg = sess.groupby("date").agg(
            sess_close=("close", "last"),
            first_open=("open", "first"),
            first_close=("close", "first"),
        ).reset_index()
        sdates = agg["date"].to_numpy()

        stamps = df[(df["tod"] == CARRY_OVER_MIN)
                    & (df["date"] >= CARRY_START) & (df["date"] <= CARRY_END)]
        for _, bar in stamps.iterrows():
            when = np.datetime64(bar["date"])
            j = np.searchsorted(sdates, when, "left")
            prev_close = agg["sess_close"].iloc[j - 1] if j > 0 else np.nan
            same_day = j < len(sdates) and sdates[j] == when
            rows.append({
                "ticker": tkr,
                "date": bar["date"],
                "stamp_close": bar["close"],
                "prev_sess_close": prev_close,
                "first_open": agg["first_open"].iloc[j] if same_day else np.nan,
                "first_close": agg["first_close"].iloc[j] if same_day else np.nan,
            })

    out = pd.DataFrame(rows)
    eq = lambda a, b: np.isclose(a, b, rtol=0.0, atol=PRICE_TOL)
    out["eq_prev_close"] = eq(out["stamp_close"], out["prev_sess_close"])
    out["eq_first_open"] = eq(out["stamp_close"], out["first_open"])
    out["eq_first_close"] = eq(out["stamp_close"], out["first_close"])
    return out


# transmission regressions, early-close sensitivity

def kase_sessions_usd(kspi: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    """KSPI KASE session open/close in USD, plus gap, drift and session return."""
    px = kspi[(kspi["tod"] >= AUCTION_MIN) & (kspi["tod"] <= SESSION_END_MIN)].copy()
    rate = fx[["ts_utc", "close"]].rename(columns={"close": "usdkzt"})
    px = pd.merge_asof(px.sort_values("ts_utc"), rate.sort_values("ts_utc"),
                       on="ts_utc", direction="backward")
    px = px.dropna(subset=["usdkzt"])
    px["open_usd"] = px["open"] / px["usdkzt"]
    px["close_usd"] = px["close"] / px["usdkzt"]

    s = px.groupby("date").agg(
        open_usd=("open_usd", "first"),
        close_usd=("close_usd", "last"),
        open_ts=("ts_utc", "first"),
        close_ts=("ts_utc", "last"),
    ).reset_index()
    s["prev_close_usd"] = s["close_usd"].shift(1)
    s["gap"] = s["open_usd"] / s["prev_close_usd"] - 1.0
    s["drift"] = s["close_usd"] / s["open_usd"] - 1.0
    s["session_ret"] = s["close_usd"] / s["prev_close_usd"] - 1.0
    return s


def nasdaq_daily(us: pd.DataFrame) -> pd.DataFrame:
    """Regular-session (09:30-16:00 ET) daily close and close-to-close return."""
    ny = us["ts_ny"]
    tod = ny.dt.hour * 60 + ny.dt.minute
    reg = us[(tod >= 9 * 60 + 30) & (tod < 16 * 60)].copy()
    reg["date"] = ny[reg.index].dt.normalize().dt.tz_localize(None)
    d = reg.groupby("date").agg(us_close=("close", "last"),
                                us_close_ts=("ts_utc", "last")).reset_index()
    d["us_ret"] = d["us_close"].pct_change()
    return d


def build_regression_frame() -> pd.DataFrame:
    kspi = load_intraday(KASE_INTRADAY, "KSPI.KZ", "ts_almaty")
    fx = load_intraday(KASE_INTRADAY, "USDKZT_TOM.KZ", "ts_almaty")
    us = load_intraday(NASDAQ_INTRADAY, "KSPI.US", "ts_ny")

    kase = kase_sessions_usd(kspi, fx)
    usd = nasdaq_daily(us).dropna(subset=["us_ret"])

    # last NASDAQ return before the open
    lag = pd.merge_asof(
        kase.sort_values("open_ts"),
        usd[["us_close_ts", "us_ret"]].sort_values("us_close_ts")
            .rename(columns={"us_ret": "us_ret_lag"}),
        left_on="open_ts", right_on="us_close_ts",
        direction="backward", allow_exact_matches=False,
    )
    # same-day NASDAQ return, printed after the close
    frame = lag.merge(usd[["date", "us_ret"]].rename(columns={"us_ret": "us_ret_same"}),
                      on="date", how="left")
    # merge_asof would otherwise carry the last return past the store's end
    window_end = usd["date"].max()
    keep = (frame["date"] >= REG_START) & (frame["date"] <= window_end)
    return frame[keep].reset_index(drop=True)


def fit(frame: pd.DataFrame, y: str, xs: list[str]) -> sm.regression.linear_model.RegressionResults:
    d = frame[[y] + xs].dropna()
    X = sm.add_constant(d[xs], has_constant="add")
    return sm.OLS(d[y], X).fit(cov_type="HAC", cov_kwds={"maxlags": HAC_LAGS})


# Main

def main() -> None:
    _require_store()
    bars = {t: load_intraday(KASE_INTRADAY, f"{t}.KZ", "ts_almaty") for t in PANEL}
    summary = session_summary(bars)

    rule("D0. Panel coverage (one-minute store)")
    print(f"{'ticker':8s} {'bars':>9s}  {'first':>10s}  {'last':>10s}  {'sessions':>8s}")
    for t in PANEL:
        df = bars[t]
        print(f"{t:8s} {len(df):9d}  {df['date'].min():%Y-%m-%d}  "
              f"{df['date'].max():%Y-%m-%d}  {df['date'].nunique():8d}")
    print(f"panel trading dates: {summary['date'].nunique()}  "
          f"({summary['date'].min():%Y-%m-%d} to {summary['date'].max():%Y-%m-%d})")

    # ---- D1 -----------------------------------------------------------------
    rule("D1. Venue-wide early closes")
    print(f"criterion: last bar more than {EARLY_CLOSE_GAP_MIN} minutes earlier than on "
          f"both neighbouring panel sessions,\n"
          f"           for >= {EARLY_CLOSE_MIN_SHARE:.0%} of at least "
          f"{EARLY_CLOSE_MIN_PANEL} instruments comparable on all three dates")
    hits, allrows = venue_early_closes(summary)
    print()
    print(f"{'date':12s} {'n_early':>7s} {'n_cmp':>6s} {'share':>6s} "
          f"{'med_last':>9s} {'med_prev':>9s} {'med_next':>9s}")
    for _, r in hits.iterrows():
        print(f"{r['date']:%Y-%m-%d}   {int(r['n_early']):7d} {int(r['n_comparable']):6d} "
              f"{r['share_early']:6.2f} {hhmm(r['med_last']):>9s} "
              f"{hhmm(r['med_prev']):>9s} {hhmm(r['med_next']):>9s}")
    if hits.empty:
        print("  (none)")

    for _, r in hits.iterrows():
        d = r["date"]
        print(f"\n  per-instrument last bar on {d:%Y-%m-%d}:")
        detail = summary[summary["date"] == d].sort_values("ticker")
        print("   " + "  ".join(f"{row.ticker}={hhmm(row.last)}"
                                for row in detail.itertuples()))

    # FX is on another board; if it stops early too, the event is venue-wide
    if not hits.empty:
        fx_bars = load_intraday(KASE_INTRADAY, "USDKZT_TOM.KZ", "ts_almaty")
        fx_last = fx_bars.groupby("date")["tod"].max()
        print("\n  cross-check on the USDKZT_TOM board (last bar):")
        print(f"    {'date':12s} {'prev':>6s} {'date':>6s} {'next':>6s}")
        fx_dates = fx_last.index
        for _, r in hits.iterrows():
            j = fx_dates.searchsorted(r["date"])
            same = j < len(fx_dates) and fx_dates[j] == r["date"]
            prev = fx_last.iloc[j - 1] if j > 0 else np.nan
            nxt = fx_last.iloc[j + 1] if same and j + 1 < len(fx_dates) else np.nan
            cur = fx_last.iloc[j] if same else np.nan
            print(f"    {r['date']:%Y-%m-%d}   {hhmm(prev):>6s} {hhmm(cur):>6s} {hhmm(nxt):>6s}")

    # so the threshold choice is visible
    print("\n  sensitivity of the panel/share thresholds (dates selected):")
    for min_panel in (6, 8, 10):
        for min_share in (0.7, 0.8, 0.9, 1.0):
            k = ((allrows["n_comparable"] >= min_panel)
                 & (allrows["share_early"] >= min_share)).sum()
            print(f"    n_comparable>={min_panel:2d}, share>={min_share:.2f}: {k:3d} dates")

    # ---- D2 -----------------------------------------------------------------
    rule("D2. Market-wide non-trading weekdays, "
         f"{MODERN_START:%Y-%m-%d} to {MODERN_END:%Y-%m-%d}")
    missing, runs = missing_weekdays(summary)
    weekdays = pd.bdate_range(MODERN_START, MODERN_END)
    print(f"weekdays in window: {len(weekdays)}   non-trading: {len(missing)}   "
          f"trading: {len(weekdays) - len(missing)}")
    for i in range(0, len(missing), 6):
        print("  " + "  ".join(f"{d:%Y-%m-%d}" for d in missing[i:i + 6]))
    runs_sorted = sorted(runs, key=len, reverse=True)
    longest = len(runs_sorted[0]) if runs_sorted else 0
    print(f"\nlongest consecutive run of non-trading weekdays: {longest}")
    for r in runs_sorted:
        if len(r) == longest:
            gap_days = (r[-1] - r[0]).days + 1
            print(f"  {r[0]:%Y-%m-%d} to {r[-1]:%Y-%m-%d} "
                  f"({len(r)} weekdays, {gap_days} calendar days)")
    print(f"runs of length >= 2: {sum(1 for r in runs if len(r) >= 2)}; "
          f"isolated single days: {sum(1 for r in runs if len(r) == 1)}")

    # ---- D3 -----------------------------------------------------------------
    rule("D3. January 2022")
    jan = summary[(summary["date"] >= "2022-01-01") & (summary["date"] <= "2022-01-31")]
    traded = set(pd.DatetimeIndex(jan["date"].unique()))
    cal = pd.date_range("2022-01-01", "2022-01-31")
    dark_all = [d for d in cal if d not in traded]
    dark_wd = [d for d in dark_all if d.weekday() < 5]
    print(f"calendar days with no bars for any panel instrument: {len(dark_all)}")
    print("  " + "  ".join(f"{d:%m-%d}" for d in dark_all))
    print(f"of which weekdays: {len(dark_wd)}")
    print("  " + "  ".join(f"{d:%m-%d}" for d in dark_wd))
    print()
    print(f"{'date':12s} {'instr':>5s} {'first(med)':>10s} {'last(med)':>10s} "
          f"{'last(max)':>10s} {'bars':>6s}")
    for d, g in jan.groupby("date"):
        print(f"{d:%Y-%m-%d}   {len(g):5d} {hhmm(g['first'].median()):>10s} "
              f"{hhmm(g['last'].median()):>10s} {hhmm(g['last'].max()):>10s} "
              f"{int(g['n'].sum()):6d}")
    short = jan[(jan["date"] >= "2022-01-11") & (jan["date"] <= "2022-01-21")]
    normal = summary[(summary["date"] >= "2021-12-01") & (summary["date"] <= "2021-12-31")]
    print(f"\nshortened window 2022-01-11 to 2022-01-21: median last bar "
          f"{hhmm(short['last'].median())}, panel max {hhmm(short['last'].max())}")
    print(f"December 2021 baseline: median last bar {hhmm(normal['last'].median())}, "
          f"panel max {hhmm(normal['last'].max())}")
    after = summary[(summary["date"] >= "2022-01-24") & (summary["date"] <= "2022-01-31")]
    print(f"after 2022-01-24: median last bar {hhmm(after['last'].median())}, "
          f"panel max {hhmm(after['last'].max())}")

    # ---- D4 -----------------------------------------------------------------
    rule(f"D4. Carry-over 09:00 prints, {CARRY_START:%Y-%m} to {CARRY_END:%Y-%m}")
    co = carry_over_prints(bars)
    print(f"bars stamped at exactly 09:00 Almaty: {len(co)} across "
          f"{len(CARRY_TICKERS)} instruments, {co['date'].nunique()} dates")
    print(f"  with a previous session close available : {co['prev_sess_close'].notna().sum()}")
    print(f"  with a same-day session print available : {co['first_open'].notna().sum()}")
    print(f"  09:00 print is the only bar of its date : {co['first_open'].isna().sum()}")
    print()
    print(f"{'ticker':8s} {'n':>5s} {'=prev close':>12s} {'=first open':>12s} {'=first close':>13s}")
    for t in CARRY_TICKERS:
        g = co[co["ticker"] == t]
        print(f"{t:8s} {len(g):5d} {g['eq_prev_close'].mean():12.4f} "
              f"{g['eq_first_open'].mean():12.4f} {g['eq_first_close'].mean():13.4f}")
    print(f"{'ALL':8s} {len(co):5d} {co['eq_prev_close'].mean():12.4f} "
          f"{co['eq_first_open'].mean():12.4f} {co['eq_first_close'].mean():13.4f}")
    both = co[co["prev_sess_close"].notna() & co["first_open"].notna()]
    print(f"{'BOTH*':8s} {len(both):5d} {both['eq_prev_close'].mean():12.4f} "
          f"{both['eq_first_open'].mean():12.4f} {both['eq_first_close'].mean():13.4f}")
    print("  * restricted to stamps where both comparators exist")
    print(f"\nequal to previous close AND to first print: {(co['eq_prev_close'] & co['eq_first_open']).mean():.4f}")
    print(f"equal to neither                          : "
          f"{(~co['eq_prev_close'] & ~co['eq_first_open']).mean():.4f}")

    # ---- D5 -----------------------------------------------------------------
    rule(f"D5. Per-instrument session bounds, {BOUNDS_START:%Y-%m-%d} onward")
    recent = summary[summary["date"] >= BOUNDS_START]
    print(f"{'ticker':8s} {'sessions':>8s} {'med_first':>10s} {'med_last':>9s} "
          f"{'p10_last':>9s} {'p90_last':>9s} {'share>17:25':>12s}")
    for t in PANEL:
        g = recent[recent["ticker"] == t]
        if g.empty:
            continue
        share = (g["last"] > LATE_BAR_MIN).mean()
        print(f"{t:8s} {len(g):8d} {hhmm(g['first'].median()):>10s} "
              f"{hhmm(g['last'].median()):>9s} {hhmm(g['last'].quantile(0.10)):>9s} "
              f"{hhmm(g['last'].quantile(0.90)):>9s} {share:12.4f}")
    print(f"{'PANEL':8s} {len(recent):8d} {hhmm(recent['first'].median()):>10s} "
          f"{hhmm(recent['last'].median()):>9s} {hhmm(recent['last'].quantile(0.10)):>9s} "
          f"{hhmm(recent['last'].quantile(0.90)):>9s} "
          f"{(recent['last'] > LATE_BAR_MIN).mean():12.4f}")

    # ---- D6 -----------------------------------------------------------------
    rule("D6. Does dropping the venue-wide early close move the transmission regression?")
    frame = build_regression_frame()
    print(f"KSPI KASE-vs-NASDAQ frame: {len(frame)} sessions, "
          f"{frame['date'].min():%Y-%m-%d} to {frame['date'].max():%Y-%m-%d}")

    in_window = [d for d in hits["date"] if d >= REG_START and d <= frame["date"].max()]
    print(f"venue-wide early closes inside the regression window: "
          f"{', '.join(f'{d:%Y-%m-%d}' for d in in_window) if in_window else 'none'}")

    specs = [
        ("contemporaneous: session_ret ~ us_ret_same", "session_ret", ["us_ret_same"]),
        ("lagged gap:      gap ~ us_ret_lag", "gap", ["us_ret_lag"]),
        ("lagged drift:    drift ~ us_ret_lag", "drift", ["us_ret_lag"]),
    ]

    # the early-close session, and the next, whose gap is measured against the
    # truncated close
    drop_self = set(in_window)
    order = frame["date"].tolist()
    drop_next = set(drop_self)
    for d in in_window:
        i = order.index(d)
        if i + 1 < len(order):
            drop_next.add(order[i + 1])

    variants = [
        ("full", frame),
        ("drop early-close session", frame[~frame["date"].isin(drop_self)]),
        ("drop early-close + next", frame[~frame["date"].isin(drop_next)]),
    ]

    for label, dep, indep in specs:
        print(f"\n{label}")
        print(f"  {'sample':26s} {'n':>4s} {'beta':>10s} {'t':>7s} {'R2':>7s} "
              f"{'d(beta)':>10s} {'d/se':>7s}")
        base = None
        for vlabel, sub in variants:
            res = fit(sub, dep, indep)
            b = res.params[indep[0]]
            t = res.tvalues[indep[0]]
            se = res.bse[indep[0]]
            if base is None:
                base = b
                dtxt, rtxt = "     --   ", "   --  "
            else:
                dtxt = f"{b - base:10.5f}"
                rtxt = f"{(b - base) / se:7.3f}"
            print(f"  {vlabel:26s} {int(res.nobs):4d} {b:10.5f} {t:7.3f} "
                  f"{res.rsquared:7.4f} {dtxt} {rtxt}")

    # Section A reports the lagged total
    print("\nlagged total (gap beta + drift beta)")
    print(f"  {'sample':26s} {'total':>10s} {'d(total)':>10s}")
    base_total = None
    for vlabel, sub in variants:
        tot = (fit(sub, "gap", ["us_ret_lag"]).params["us_ret_lag"]
               + fit(sub, "drift", ["us_ret_lag"]).params["us_ret_lag"])
        if base_total is None:
            base_total = tot
            dtxt = "     --   "
        else:
            dtxt = f"{tot - base_total:10.5f}"
        print(f"  {vlabel:26s} {tot:10.5f} {dtxt}")

    print()


if __name__ == "__main__":
    main()
