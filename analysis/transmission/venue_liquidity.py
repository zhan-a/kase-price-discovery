#!/usr/bin/env python3
"""
KASE against NASDAQ liquidity in KSPI, over common sessions.

Bars are counted, not trades: a bar exists when at least one trade occurred in
that minute, so the count is a lower bound on trades and the two are not
interchangeable. Turnover carries the comparison and is computed in USD on both
sides, converting the KASE leg at the on-exchange USDKZT_TOM rate. The NASDAQ
side is the regular session only, so pre-market prints do not inflate it.
"""

import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _store import store as _store_dir, daily as _daily_dir


ROOT = Path(__file__).resolve().parents[2]
STORE = _store_dir()

SESSION_LO, SESSION_HI = 11 * 60 + 25, 17 * 60 + 35
PANEL_START = "2024-01-19"


def load(pattern: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(pattern)))
    if not files:
        return pd.DataFrame()
    return pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)


def main() -> None:
    kase = load(STORE / "kase" / "intraday" / "KSPI.KZ" / "*.parquet")
    nas = load(STORE / "nasdaq" / "intraday" / "KSPI.US" / "*.parquet")
    fxr = load(STORE / "kase" / "intraday" / "USDKZT_TOM.KZ" / "*.parquet")
    if kase.empty or nas.empty or fxr.empty:
        raise SystemExit(
            f"Store not found under {STORE}. Set KASE_STORE, or attach the bar store as "
            "data/README.md describes."
        )

    kase = kase[kase["close"].notna()].copy()
    kase["alm"] = pd.to_datetime(kase["ts_almaty"])
    kase["day"] = kase["alm"].dt.normalize().dt.tz_localize(None)
    minute = kase["alm"].dt.hour * 60 + kase["alm"].dt.minute
    kase = kase[(minute >= SESSION_LO) & (minute <= SESSION_HI)]
    kase = kase[kase["day"] >= PANEL_START]

    nas = nas.drop_duplicates("ts_utc").copy()
    nas["ny"] = pd.to_datetime(nas["ts_ny"])
    hour = nas["ny"].dt.hour + nas["ny"].dt.minute / 60
    nas["day"] = nas["ny"].dt.normalize().dt.tz_localize(None)
    nas = nas[(hour >= 9.5) & (hour <= 16.0)]

    fxr["day"] = pd.to_datetime(fxr["ts_almaty"]).dt.normalize().dt.tz_localize(None)
    fx = fxr.groupby("day")["close"].median()

    k = kase.groupby("day").agg(bars=("close", "size"), vol=("volume", "sum"),
                                px=("close", "median"))
    n = nas.groupby("day").agg(bars=("close", "size"), vol=("volume", "sum"),
                               px=("close", "median"))
    both = k.index.intersection(n.index)
    k, n = k.loc[both], n.loc[both]
    k_usd = k["vol"] * k["px"] / fx.reindex(k.index)
    n_usd = n["vol"] * n["px"]

    print("VENUE LIQUIDITY, KSPI ON BOTH VENUES")
    print(f"  common sessions from {PANEL_START}: {len(both)}\n")
    print(f"  {'':30s} {'KASE':>14s} {'NASDAQ':>14s} {'ratio':>9s}")
    rows = [
        ("median minutes with a trade", k["bars"].median(), n["bars"].median(), "{:.1f}x"),
        ("median shares traded", k["vol"].median(), n["vol"].median(), "{:.0f}x"),
        ("median turnover, USD", k_usd.median(), n_usd.median(), "{:.0f}x"),
    ]
    for label, a, b, fmt in rows:
        print(f"  {label:30s} {a:14,.0f} {b:14,.0f} {fmt.format(b / a):>9s}")

    span = SESSION_HI - SESSION_LO
    print(f"\n  {span}-minute session, a trade in a median of {k['bars'].median():.0f} "
          f"minutes, one per {span / k['bars'].median():.1f} minutes of clock.")
    print("\n  Bars are minutes with at least one trade, not trade counts.")

    # written out for the figure
    out = pd.DataFrame([
        {"measure": "minutes with a trade", "unit": "minutes",
         "kase": float(k["bars"].median()), "nasdaq": float(n["bars"].median())},
        {"measure": "shares traded", "unit": "shares",
         "kase": float(k["vol"].median()), "nasdaq": float(n["vol"].median())},
        {"measure": "turnover", "unit": "USD",
         "kase": float(k_usd.median()), "nasdaq": float(n_usd.median())},
    ])
    out["ratio"] = out["nasdaq"] / out["kase"]
    out["sessions"] = len(both)
    out["session_minutes"] = SESSION_HI - SESSION_LO
    dest = ROOT / "data" / "derived" / "venue_liquidity.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    print(f"\n  Wrote data/derived/venue_liquidity.csv ({len(out)} measures)")


if __name__ == "__main__":
    main()
