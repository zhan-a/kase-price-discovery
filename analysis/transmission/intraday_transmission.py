#!/usr/bin/env python3
"""
How fast does KASE absorb NASDAQ moves in Kaspi (KSPI)?

The premise the project has been stuck on since May: KASE closes at 17:30
Almaty, NASDAQ opens at ~18:30 Almaty, so the two never overlap. Each KASE
session therefore opens ~10.5 hours after a full NASDAQ session has already
repriced the stock. If Freedom (KASE's near-monopoly market maker) prices
that information in instantly at the open, there is nothing to trade. If it
leaks in over the session, the drift is in principle tradeable.

This measures which, minute by minute, using:
  * data/kase/intraday/KSPI.KZ      1-minute KASE bars (KZT)
  * data/kase/intraday/USDKZT_TOM.KZ on-exchange FX, aligned to each bar
  * Yahoo KSPI daily                NASDAQ closes (the efficient reference)

Outputs a transmission profile: how much of the prior NASDAQ move is
reflected in the KASE open, and how much arrives later in the session.
"""

import glob
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _store import store as _store_dir, daily as _daily_dir


REPO = Path(__file__).resolve().parents[2]
STORE = _store_dir() / "kase" / "intraday"

SESSION_OPEN = 11 * 60 + 30
SESSION_CLOSE = 17 * 60 + 30


def load_store(ticker: str) -> pd.DataFrame:
    files = sorted(glob.glob(str(STORE / ticker / "*.parquet")))
    frame = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    frame = frame[frame["close"].notna()].copy()
    frame["ts_utc"] = pd.to_datetime(frame["ts_utc"], utc=True)
    frame["ts_almaty"] = pd.to_datetime(frame["ts_almaty"])
    return frame.sort_values("ts_utc").reset_index(drop=True)


def load_nasdaq() -> pd.DataFrame:
    url = "https://query1.finance.yahoo.com/v8/finance/chart/KSPI?range=5y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    res = json.load(urllib.request.urlopen(req, timeout=30))["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    nas = pd.DataFrame({
        "ts": pd.to_datetime(res["timestamp"], unit="s", utc=True),
        "nas_open": q["open"], "nas_close": q["close"],
    }).dropna()
    nas["nas_day"] = nas["ts"].dt.tz_convert("America/New_York").dt.normalize().dt.tz_localize(None)
    # day D ends ~01:00 Almaty on D+1, reaching the KASE session opening later
    # that day
    nas["available_from"] = nas["ts"].dt.tz_convert("Asia/Almaty").dt.normalize().dt.tz_localize(None) + pd.Timedelta(days=1)
    nas["nas_ret"] = nas["nas_close"].pct_change()
    return nas.dropna().reset_index(drop=True)


def build() -> pd.DataFrame:
    kspi = load_store("KSPI.KZ")
    fx = load_store("USDKZT_TOM.KZ")[["ts_utc", "close"]].rename(columns={"close": "fx"})
    nas = load_nasdaq()

    # align FX to each bar
    merged = pd.merge_asof(kspi, fx, on="ts_utc", direction="backward")
    merged = merged[merged["fx"].notna() & (merged["fx"] > 0)].copy()
    merged["kase_usd"] = merged["close"] / merged["fx"]
    merged["day"] = merged["ts_almaty"].dt.normalize().dt.tz_localize(None)
    merged["minute"] = merged["ts_almaty"].dt.hour * 60 + merged["ts_almaty"].dt.minute
    merged = merged[(merged["minute"] >= SESSION_OPEN - 5) & (merged["minute"] <= SESSION_CLOSE + 5)]

    # attach the most recent NASDAQ close
    nas_sorted = nas.sort_values("available_from")
    merged = pd.merge_asof(
        merged.sort_values("day"), nas_sorted,
        left_on="day", right_on="available_from", direction="backward",
    )
    merged = merged[merged["nas_close"].notna()].copy()
    merged["premium"] = merged["kase_usd"] / merged["nas_close"] - 1
    return merged.sort_values("ts_utc").reset_index(drop=True), nas


def alignment(daily: pd.DataFrame, df: pd.DataFrame, nas: pd.DataFrame) -> pd.DataFrame:
    """How many NASDAQ sessions each opening gap spans.

    The regressor is the one-session NASDAQ return ending at the last NASDAQ
    close before the KASE open. The opening gap runs from the previous KASE
    session's close, so it spans every NASDAQ session between the close matched
    to that previous session and the close matched to this one: one when both
    exchanges traded on consecutive days, none when NASDAQ was shut in between
    (the regressor was already public during the previous KASE session), two or
    more across a Kazakh holiday or another weekday on which the store holds no
    KASE bars. The interval return is the NASDAQ move over exactly that span.
    """
    nas_day = df.groupby("day")["nas_day"].first()
    a = pd.DataFrame({"day": daily["day"].values, "nas_close": daily["nas_close"].values})
    a["nas_day"] = a["day"].map(nas_day)
    a["prev_day"] = a["day"].shift(1)
    a["prev_nas_day"] = a["nas_day"].shift(1)
    a["prev_nas_close"] = a["nas_close"].shift(1)
    order = {d: i for i, d in enumerate(sorted(nas["nas_day"].unique()))}
    a["nas_sessions_spanned"] = a["nas_day"].map(order) - a["prev_nas_day"].map(order)
    a["nas_interval_ret"] = a["nas_close"] / a["prev_nas_close"] - 1
    return a[["day", "prev_day", "nas_day", "prev_nas_day", "nas_sessions_spanned", "nas_interval_ret"]]


def ols(y: np.ndarray, x: np.ndarray) -> tuple[float, float, float, int]:
    """Slope, t-stat, R^2, n for y = a + b*x."""
    mask = np.isfinite(y) & np.isfinite(x)
    y, x = y[mask], x[mask]
    n = len(y)
    if n < 30:
        return np.nan, np.nan, np.nan, n
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    s2 = resid @ resid / (n - 2)
    se = np.sqrt(s2 * np.linalg.inv(X.T @ X)[1, 1])
    r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
    return beta[1], beta[1] / se, r2, n


def main():
    df, nas = build()
    print(f"Aligned {len(df):,} KASE minute bars over "
          f"{df['day'].min():%Y-%m-%d} .. {df['day'].max():%Y-%m-%d} "
          f"({df['day'].nunique()} sessions)\n")

    # per-session open and close in USD
    daily = df.groupby("day").agg(
        kase_open=("kase_usd", "first"), kase_close=("kase_usd", "last"),
        prem_open=("premium", "first"), prem_close=("premium", "last"),
        nas_ret=("nas_ret", "first"), nas_close=("nas_close", "first"),
        bars=("kase_usd", "size"),
    ).reset_index()
    daily = daily[daily["bars"] >= 20]                      # skip near-untraded days
    align = alignment(daily, df, nas)                       # before the trim, so the
    daily["prev_kase_close"] = daily["kase_close"].shift(1)  # predecessor is the real one
    daily["kase_gap"] = daily["kase_open"] / daily["prev_kase_close"] - 1
    daily["kase_intraday"] = daily["kase_close"] / daily["kase_open"] - 1
    daily = daily.dropna(subset=["kase_gap", "kase_intraday", "nas_ret"])
    aligned = len(daily)
    # Trim the fattest tails (corporate actions, FX jumps). A trim, not a
    # winsorisation: rows leave the sample rather than being clipped, so n
    # falls, and the cut is taken on each of the three variables in turn, so a
    # session lost on one is lost for all and the three remove more than 2%.
    for col in ["kase_gap", "kase_intraday", "nas_ret"]:
        lo, hi = daily[col].quantile([0.01, 0.99])
        daily = daily[daily[col].between(lo, hi)]

    print(f"Sessions aligned: {aligned}")
    print(f"Sessions analysed: {len(daily)}  "
          f"(after 1%/99% trim on kase_gap, kase_intraday and nas_ret; "
          f"{aligned - len(daily)} removed)\n")
    print("TRANSMISSION OF THE PRIOR NASDAQ MOVE")
    for label, col in [("at the KASE open  (gap)     ", "kase_gap"),
                       ("during the session (drift)  ", "kase_intraday")]:
        b, t, r2, n = ols(daily[col].values, daily["nas_ret"].values)
        print(f"  {label} beta={b:+.3f}  t={t:+.2f}  R2={r2:.3f}  n={n}")

    # same test, days NASDAQ actually moved
    big = daily[daily["nas_ret"].abs() > daily["nas_ret"].abs().quantile(0.75)]
    print(f"\n  Restricted to the largest-move quartile (|NASDAQ move| > "
          f"{daily['nas_ret'].abs().quantile(0.75) * 100:.2f}%, n={len(big)}):")
    for label, col in [("open  ", "kase_gap"), ("intraday", "kase_intraday")]:
        b, t, r2, n = ols(big[col].values, big["nas_ret"].values)
        print(f"    {label}: beta={b:+.3f}  t={t:+.2f}  R2={r2:.3f}")

    # premium through the session, by bucket
    print("\nPREMIUM BY TIME OF DAY (KASE price vs prior NASDAQ close)")
    df["bucket"] = (df["minute"] // 30) * 30
    prof = df.groupby("bucket")["premium"].agg(["mean", "median", "std", "size"])
    for b, row in prof.iterrows():
        print(f"  {b // 60:02d}:{b % 60:02d}  mean {row['mean'] * 100:+6.2f}%  "
              f"median {row['median'] * 100:+6.2f}%  sd {row['std'] * 100:5.2f}%  n={int(row['size']):,}")

    # report the range, not three hand-picked buckets. The 11:00 bucket is the
    # auction print and far thinner, so the range is continuous only.
    cont = prof[prof.index >= 11 * 60 + 30]
    lo, hi = cont["mean"].min() * 100, cont["mean"].max() * 100
    print(f"\n  Range across continuous buckets 11:30-17:00: {lo:+.2f}% to {hi:+.2f}%, "
          f"a spread of {hi - lo:.2f} points")
    print(f"  against a within-bucket sd of about {cont['std'].median() * 100:.1f}%. "
          f"Widest bucket at {cont['mean'].idxmax() // 60:02d}:"
          f"{cont['mean'].idxmax() % 60:02d}, narrowest at "
          f"{cont['mean'].idxmin() // 60:02d}:{cont['mean'].idxmin() % 60:02d}.")

    # does the session close the gap?
    daily["gap_to_close"] = daily["prem_open"]
    b, t, r2, n = ols(daily["kase_intraday"].values, daily["prem_open"].values)
    print(f"\nMEAN REVERSION WITHIN THE SESSION")
    print(f"  intraday return vs premium at open: beta={b:+.3f} t={t:+.2f} R2={r2:.3f} n={n}")
    print("  (negative beta = a rich open drifts back down during the session)")

    daily.to_csv(REPO / "data" / "derived" / "transmission_daily.csv", index=False)
    print(f"\nWrote data/derived/transmission_daily.csv ({len(daily)} sessions)")

    align = align[align["day"].isin(daily["day"])].dropna(subset=["nas_sessions_spanned"])
    align["nas_sessions_spanned"] = align["nas_sessions_spanned"].astype(int)
    k = align["nas_sessions_spanned"]
    print("\nREGRESSOR ALIGNMENT: NASDAQ sessions between the closes matched to consecutive KASE sessions")
    print(f"  0 sessions, regressor already public before the previous KASE session closed: {int((k == 0).sum())}")
    print(f"  1 session, aligned: {int((k == 1).sum())}")
    print(f"  2 or more sessions, the gap carries more NASDAQ news than the regressor: {int((k >= 2).sum())}")
    print("  by span: " + ", ".join(f"{int(v)}: {int(c)}" for v, c in k.value_counts().sort_index().items()))
    align.to_csv(REPO / "data" / "derived" / "regressor_alignment.csv", index=False, float_format="%.10g")
    print(f"  Wrote data/derived/regressor_alignment.csv ({len(align)} sessions)")


if __name__ == "__main__":
    main()
