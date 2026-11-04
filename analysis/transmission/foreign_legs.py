"""Foreign legs of the overlap comparison, written as committed aggregates.

overlap_comparison.py needs, for each pair, the foreign venue's daily closes
and, for the two LSE-IOB pairs, the foreign price at the instant KASE closed.
Both came from Yahoo chart JSON held in data/cache/yahoo/, which is not
redistributed. This script turns that cache into two derived tables:

  data/derived/foreign_daily.csv   one row per foreign trading day and pair,
                                   from 2024-01-01: date, regular-session close
                                   timestamp (UTC) and close
  data/derived/foreign_split.csv   one row per IOB foreign day that also has a
                                   KASE session: the regular-session open, close
                                   and previous close taken from the 60-minute
                                   bars, the bar count, and the price at the
                                   KASE close read off bar boundaries without
                                   looking inside a bar

The KASE close timestamps come from the bar store through the same session
builder overlap_comparison.py uses, so the two scripts cannot disagree about
them. Yahoo serves hourly history as a rolling two-year window, so the bars
behind foreign_split.csv for 2024-08 to 2024-10 can no longer be fetched; the
committed tables are the record, and this script stops with a message when the
cache is absent.

Run:  python analysis/transmission/foreign_legs.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import overlap_comparison as oc  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
CACHE = Path(os.environ.get("YAHOO_CACHE", REPO / "data" / "cache" / "yahoo"))
DERIVED = REPO / "data" / "derived"

DAILY_PARAMS = {"period1": 1_600_000_000, "period2": 2_000_000_000, "interval": "1d", "events": "div"}
HOURLY_PARAMS = {"range": "2y", "interval": "60m"}
HOURLY_WIDTH = pd.Timedelta(hours=1)

# the comparison window opens 2024-02-01; one month of history keeps the first
# in-window return computable
FIRST_DATE = pd.Timestamp("2024-01-01")


def cache_path(symbol: str, params: dict) -> Path:
    key = symbol.replace(".", "_") + "_" + "_".join(f"{k}{v}" for k, v in sorted(params.items()))
    return CACHE / f"{key}.json"


def chart_frame(symbol: str, params: dict) -> pd.DataFrame:
    path = cache_path(symbol, params)
    payload = json.loads(path.read_text())["chart"]
    if payload.get("error"):
        sys.exit(f"Yahoo error recorded in {path}: {payload['error']}")
    res = payload["result"][0]
    quote = res["indicators"]["quote"][0]
    df = pd.DataFrame({
        "ts_utc": pd.to_datetime(res["timestamp"], unit="s", utc=True),
        "open": quote["open"], "high": quote["high"], "low": quote["low"],
        "close": quote["close"], "volume": quote["volume"],
    })
    return df.dropna(subset=["close"]).sort_values("ts_utc").reset_index(drop=True)


def foreign_daily(pair: oc.Pair) -> pd.DataFrame:
    """Unadjusted daily closes with an explicit UTC close timestamp.

    Unadjusted rather than back-adjusted, because the KASE leg is unadjusted
    too; a dividend-adjusted foreign leg would put a deterministic wedge into
    the log-price pair that the cointegration tests would have to absorb.
    """
    df = chart_frame(pair.foreign, DAILY_PARAMS)
    local = df["ts_utc"].dt.tz_convert(pair.tz)
    df["date"] = pd.to_datetime(local.dt.date)
    close_local = pd.to_datetime(df["date"].astype(str) + " " + pair.close_time)
    df["close_ts"] = close_local.dt.tz_localize(pair.tz, nonexistent="shift_forward",
                                                ambiguous=True).dt.tz_convert("UTC")
    df = df[["date", "close_ts", "close"]].drop_duplicates("date")
    df = df[df["date"] >= FIRST_DATE]
    df.insert(0, "symbol", pair.foreign)
    df.insert(0, "pair", pair.kase)
    return df.reset_index(drop=True)


def foreign_hourly(pair: oc.Pair) -> pd.DataFrame:
    """Yahoo 60-minute bars up to the regular-session close."""
    df = chart_frame(pair.foreign, HOURLY_PARAMS)
    df = df[df["ts_utc"].dt.tz_convert(pair.tz).dt.time <= pd.Timestamp(pair.close_time).time()]
    return df.reset_index(drop=True)


def foreign_split(pair: oc.Pair, fx: pd.DataFrame) -> pd.DataFrame:
    """Per foreign day: regular-session open and close, and the price at the KASE close."""
    bars = foreign_hourly(pair)
    rs = oc.foreign_daily_from_intraday(pair, bars)
    sessions = oc.kase_sessions(pair.kase, fx)[["date", "close_ts"]]
    d = rs.merge(sessions, on="date", how="inner")
    path = oc.price_path(bars, HOURLY_WIDTH)
    split = pd.merge_asof(
        d.sort_values("close_ts"),
        path.rename(columns={"ts": "split_ts", "px": "split_px"}).sort_values("split_ts"),
        left_on="close_ts", right_on="split_ts", direction="backward",
    )
    # only counts if the print belongs to the current foreign day, else the
    # split price is the previous close and the pre-close segment is zero
    same_day = split["split_ts"].dt.tz_convert(pair.tz).dt.date == split["date"].dt.date
    split["same_day"] = same_day
    split["split_px"] = np.where(same_day, split["split_px"], split["prev_close_rs"])
    split.insert(0, "pair", pair.kase)
    return split[["pair", "date", "close_ts", "open_rs", "close_rs", "prev_close_rs", "n_bars_rs",
                  "split_ts", "split_px", "same_day"]].sort_values("date").reset_index(drop=True)


def main() -> None:
    needed = [cache_path(p.foreign, DAILY_PARAMS) for p in oc.PAIRS]
    needed += [cache_path(p.foreign, HOURLY_PARAMS) for p in oc.PAIRS if p.overlapping]
    missing = [str(p) for p in needed if not p.exists()]
    if missing:
        sys.exit("The Yahoo cache this script reads is not in the public tree, and the hourly\n"
                 "history it holds is no longer served. The committed tables under data/derived/\n"
                 "are the record. Missing:\n  " + "\n  ".join(missing))

    fx = oc.load_kase_minutes("USDKZT_TOM")
    daily = pd.concat([foreign_daily(p) for p in oc.PAIRS], ignore_index=True)
    split = pd.concat([foreign_split(p, fx) for p in oc.PAIRS if p.overlapping], ignore_index=True)

    DERIVED.mkdir(parents=True, exist_ok=True)
    daily.to_csv(DERIVED / "foreign_daily.csv", index=False)
    split.to_csv(DERIVED / "foreign_split.csv", index=False)

    print("FOREIGN LEGS, from the Yahoo cache to committed aggregates")
    print(f"  cache: {CACHE}")
    for p in oc.PAIRS:
        d = daily[daily["pair"] == p.kase]
        print(f"  {p.kase}/{p.foreign:8s} daily rows {len(d):4d}  {d['date'].min():%Y-%m-%d} .. {d['date'].max():%Y-%m-%d}")
    for p in oc.PAIRS:
        if not p.overlapping:
            continue
        s = split[split["pair"] == p.kase]
        print(f"  {p.kase}/{p.foreign:8s} split rows {len(s):4d}  {s['date'].min():%Y-%m-%d} .. {s['date'].max():%Y-%m-%d}"
              f"  days with a same-day print at the KASE close {int(s['same_day'].sum())}")
    print(f"  Wrote data/derived/foreign_daily.csv ({len(daily)} rows) and "
          f"data/derived/foreign_split.csv ({len(split)} rows)")


if __name__ == "__main__":
    main()
