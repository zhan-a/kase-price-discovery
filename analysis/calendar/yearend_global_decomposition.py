#!/usr/bin/env python3
"""
Is the KASE 20 Dec -> 10 Jan window local, or December seasonality arriving
through beta?

The same window is run on SPY and EEM over the same entry years as the spliced
construction of yearend_constructions.py, which is the construction this
repository quotes: minute store with its bar floor wherever it prices a window,
the daily companion for the 2015 window only. For each series the mean, sd,
one-sample t and share of positive windows are printed, then the KASE minus
benchmark differences and the correlation across venues. A large difference with
a high correlation would be leveraged beta; a difference with a correlation near
zero is a local seasonal.

SPY and EEM daily closes are fetched from Yahoo Finance at run time; the raw
series is not stored, the per-window returns are written to
data/derived/yearend_windows.csv. The window return is the first close on or
after 20 December to the first close on or after 10 January, with the same
search limit as the KASE legs.

Descriptive, not a strategy: eleven observations, one per year, on names that
are currently listed.
"""

import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from yearend_constructions import (  # noqa: E402
    ENTRY_DAY, ENTRY_MONTH, ENTRY_YEARS, EXIT_DAY, EXIT_MONTH, MIN_BARS,
    constructions, first_price_on_or_after,
)

REPO = Path(__file__).resolve().parents[2]
BENCHMARKS = ["SPY", "EEM"]


def yahoo(ticker: str) -> pd.DataFrame:
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=15y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    res = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    close = res["indicators"]["quote"][0]["close"]
    idx = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_localize(None).normalize()
    s = pd.Series(close, index=idx, dtype=float).dropna()
    return pd.DataFrame({"day_close": s})


def window_return(prices: pd.DataFrame, year: int) -> float:
    entry, _ = first_price_on_or_after(prices, pd.Timestamp(year, ENTRY_MONTH, ENTRY_DAY), "day_close")
    exit_, _ = first_price_on_or_after(prices, pd.Timestamp(year + 1, EXIT_MONTH, EXIT_DAY), "day_close")
    return (exit_ / entry - 1.0) if entry and exit_ else np.nan


def describe(v: np.ndarray) -> tuple[float, float, float, float, int]:
    v = v[np.isfinite(v)]
    n = len(v)
    sd = v.std(ddof=1)
    return v.mean(), sd, (v > 0).mean(), v.mean() / (sd / np.sqrt(n)), n


def main() -> None:
    c = constructions(MIN_BARS)
    spliced = c["spliced"]
    bench = {b: yahoo(b) for b in BENCHMARKS}

    print("IS THE DEC 20 -> JAN 10 WINDOW KASE-SPECIFIC OR GLOBAL DECEMBER BETA?")
    print(f"KASE leg: spliced construction, minute store with a {MIN_BARS}-bar floor, daily for the "
          "window the minute store cannot price")
    print(f"  {'year':>6} {'KASE':>9} {'source':>7} {'SPY':>9} {'EEM':>9} {'KASE-SPY':>10} {'KASE-EEM':>10}")
    rows = []
    for y in ENTRY_YEARS:
        k = spliced.loc[y, "ret"]
        if not np.isfinite(k):
            continue
        sp, ee = window_return(bench["SPY"], y), window_return(bench["EEM"], y)
        rows.append({"year": y, "kase": k, "source": spliced.loc[y, "source"], "spy": sp, "eem": ee,
                     "kase_minus_spy": k - sp, "kase_minus_eem": k - ee})
        print(f"  {y:>6} {k * 100:+8.2f}% {spliced.loc[y, 'source']:>7} {sp * 100:+8.2f}% {ee * 100:+8.2f}% "
              f"{(k - sp) * 100:+9.2f}% {(k - ee) * 100:+9.2f}%")

    d = pd.DataFrame(rows)
    # the per-window returns, so the benchmark legs are on record and a
    # companion repository can read them instead of typing them
    dest = REPO / "data" / "derived" / "yearend_windows.csv"
    d.rename(columns={"year": "entry_year"}).to_csv(dest, index=False, float_format="%.10g")
    print(f"  Wrote data/derived/yearend_windows.csv ({len(d)} windows)")
    print()
    for label, col in [("KASE basket", "kase"), ("SPY", "spy"), ("EEM", "eem"),
                       ("KASE minus SPY", "kase_minus_spy"), ("KASE minus EEM", "kase_minus_eem")]:
        m, sd, win, t, n = describe(d[col].values)
        print(f"  {label:16} mean {m * 100:+6.2f}%  sd {sd * 100:5.2f}%  "
              f"win {win * 100:3.0f}%  t={t:+5.2f}  n={n}")

    print("\nCORRELATION of the window return across venues")
    corr = d[["kase", "spy", "eem"]].rename(columns=str.upper).corr()
    print("  " + corr.round(2).to_string().replace("\n", "\n  "))
    print(f"\n  n={len(d)} windows, descriptive only.")

    # with eleven points one window can carry a correlation, so the same
    # statistics are repeated without the window the daily source priced
    sub = d[d["source"] == "minute"]
    left_out = ", ".join(str(y) for y in d.loc[d["source"] != "minute", "year"])
    print(f"\nWITHOUT THE WINDOW PRICED FROM THE DAILY SOURCE (entry year {left_out})")
    for label, col in [("KASE basket", "kase"), ("SPY", "spy"), ("EEM", "eem"),
                       ("KASE minus SPY", "kase_minus_spy"), ("KASE minus EEM", "kase_minus_eem")]:
        m, sd, win, t, n = describe(sub[col].values)
        print(f"  {label:16} mean {m * 100:+6.2f}%  sd {sd * 100:5.2f}%  "
              f"win {win * 100:3.0f}%  t={t:+5.2f}  n={n}")
    corr_sub = sub[["kase", "spy", "eem"]].rename(columns=str.upper).corr()
    print("  correlation:")
    print("  " + corr_sub.round(2).to_string().replace("\n", "\n  "))


if __name__ == "__main__":
    main()
