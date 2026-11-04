#!/usr/bin/env python3
"""
Robustness checks on the KASE-follows-NASDAQ drift.

The headline (85% hit rate, +0.88% per trade on >=2% NASDAQ days) is exactly
the shape of result that every prior pipeline in this repo produced and then
had to retract. aira3 died on look-ahead execution and regime concentration;
strategies/ died on multiple testing; mm/ died on costs. So before believing
anything, run the same executions that killed them:

  1. FX confound: is the "drift" just USDKZT moving? Re-run in raw KZT.
  2. Regime concentration: does one period carry the whole result?
  3. Out-of-sample: fit the threshold on the first half, trade the second.
  4. Executability: is the opening print actually reachable, or is it one
     lot at a stale price?
  5. Beta, not alpha: is this just "buy a stock that went up"?
"""

import glob
from pathlib import Path

import numpy as np
import pandas as pd

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _store import store as _store_dir, daily as _daily_dir


REPO = Path(__file__).resolve().parents[2]
STORE = _store_dir() / "kase" / "intraday"

# the first-half sweep; 0.02 is the rule entry_timing.py applies
THRESHOLDS = [0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03]
MIN_TRADES = 20


def ols(y, x):
    mask = np.isfinite(y) & np.isfinite(x)
    y, x = np.asarray(y)[mask], np.asarray(x)[mask]
    n = len(y)
    if n < 20:
        return np.nan, np.nan, n
    X = np.column_stack([np.ones(n), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    se = np.sqrt((resid @ resid / (n - 2)) * np.linalg.inv(X.T @ X)[1, 1])
    return beta[1], beta[1] / se, n


def main():
    daily = pd.read_csv(REPO / "data" / "derived" / "transmission_daily.csv", parse_dates=["day"])
    daily = daily.dropna(subset=["nas_ret", "kase_intraday"]).sort_values("day").reset_index(drop=True)

    # -- 1. FX confound -------------------------------------------------------
    # intraday return in raw KZT
    files = sorted(glob.glob(str(STORE / "KSPI.KZ" / "*.parquet")))
    k = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    k = k[k["close"].notna()].copy()
    k["ts_almaty"] = pd.to_datetime(k["ts_almaty"])
    k["day"] = k["ts_almaty"].dt.normalize().dt.tz_localize(None)
    m = k["ts_almaty"].dt.hour * 60 + k["ts_almaty"].dt.minute
    k = k[(m >= 11 * 60 + 25) & (m <= 17 * 60 + 35)]
    kzt = k.groupby("day").agg(o=("close", "first"), c=("close", "last"),
                               n=("close", "size"), vol=("volume", "sum"),
                               first_vol=("volume", "first"))
    kzt["kase_intraday_kzt"] = kzt["c"] / kzt["o"] - 1
    daily = daily.merge(kzt[["kase_intraday_kzt", "n", "vol", "first_vol"]],
                        left_on="day", right_index=True, how="left")

    print("1. FX CONFOUND: is the drift just USDKZT moving?")
    for label, col in [("USD-converted", "kase_intraday"), ("raw KZT      ", "kase_intraday_kzt")]:
        b, t, n = ols(daily[col], daily["nas_ret"])
        sel = daily[daily["nas_ret"].abs() >= 0.02]
        pnl = np.sign(sel["nas_ret"]) * sel[col]
        print(f"   {label}: beta={b:+.3f} t={t:+.2f} | >=2% days: "
              f"mean {pnl.mean() * 100:+.3f}%  hit {(pnl > 0).mean() * 100:.1f}%  n={len(sel)}")

    # -- 2. Regime concentration ----------------------------------------------
    print("\n2. REGIME CONCENTRATION: does one period carry it? (>=2% NASDAQ days, KZT)")
    sel = daily[daily["nas_ret"].abs() >= 0.02].copy()
    sel["pnl"] = np.sign(sel["nas_ret"]) * sel["kase_intraday_kzt"]
    sel["half"] = sel["day"].dt.year.astype(str) + "H" + ((sel["day"].dt.month > 6) + 1).astype(str)
    for period, grp in sel.groupby("half"):
        if len(grp) < 5:
            continue
        print(f"   {period}: n={len(grp):>3}  mean {grp['pnl'].mean() * 100:+.3f}%  "
              f"hit {(grp['pnl'] > 0).mean() * 100:5.1f}%  total {grp['pnl'].sum() * 100:+6.1f}%")
    best = sel.loc[sel["pnl"].idxmax()]
    print(f"   Largest single trade: {best['day']:%Y-%m-%d} {best['pnl'] * 100:+.2f}% "
          f"({best['pnl'] / sel['pnl'].sum() * 100:.1f}% of total P&L)")
    trimmed = sel.drop(sel["pnl"].nlargest(3).index)
    print(f"   Without the 3 best trades: mean {trimmed['pnl'].mean() * 100:+.3f}%  "
          f"hit {(trimmed['pnl'] > 0).mean() * 100:.1f}%")

    # -- 3. Out-of-sample -----------------------------------------------------
    # Seven thresholds are tried on the first half of the sample and the one
    # with the highest mean is applied to the second half. The 2% rule used by
    # entry_timing.py is a constant fixed in the code with no pre-registration
    # record, so its own out-of-sample row is printed beside the selected one.
    print("\n3. OUT-OF-SAMPLE: pick the threshold in the first half, trade the second")
    mid = daily["day"].quantile(0.5)
    ins, oos = daily[daily["day"] <= mid], daily[daily["day"] > mid]
    print(f"   in-sample {ins['day'].min():%Y-%m-%d}..{ins['day'].max():%Y-%m-%d} (n={len(ins)}), "
          f"out-of-sample {oos['day'].min():%Y-%m-%d}..{oos['day'].max():%Y-%m-%d} (n={len(oos)}), "
          f"{len(THRESHOLDS)} thresholds tried")
    print(f"   {'threshold':>9} {'IS n':>5} {'IS mean':>9} {'IS hit':>7} {'OOS n':>6} "
          f"{'OOS mean':>9} {'OOS hit':>8} {'OOS/IS':>7}")
    sweep = []
    for thr in THRESHOLDS:
        s = ins[ins["nas_ret"].abs() >= thr]
        if len(s) < MIN_TRADES:
            continue
        o = oos[oos["nas_ret"].abs() >= thr]
        p_is = np.sign(s["nas_ret"]) * s["kase_intraday_kzt"]
        p_oos = np.sign(o["nas_ret"]) * o["kase_intraday_kzt"]
        r = {"thr": thr, "is_n": len(s), "is_mean": p_is.mean(), "is_hit": (p_is > 0).mean(),
             "oos_n": len(o), "oos_mean": p_oos.mean(), "oos_hit": (p_oos > 0).mean()}
        r["ratio"] = r["oos_mean"] / r["is_mean"] if r["is_mean"] else np.nan
        sweep.append(r)
        print(f"   {thr * 100:8.1f}% {r['is_n']:>5} {r['is_mean'] * 100:+8.3f}% {r['is_hit'] * 100:6.1f}% "
              f"{r['oos_n']:>6} {r['oos_mean'] * 100:+8.3f}% {r['oos_hit'] * 100:7.1f}% {r['ratio'] * 100:6.0f}%")
    best = sweep[0]
    for r in sweep[1:]:
        if r["is_mean"] > best["is_mean"]:
            best = r
    print(f"   selected on the first half: {best['thr'] * 100:.1f}% (highest in-sample mean, "
          f"{best['is_mean'] * 100:+.3f}%); out of sample n={best['oos_n']}, "
          f"mean {best['oos_mean'] * 100:+.3f}%, hit {best['oos_hit'] * 100:.1f}%, "
          f"OOS/IS ratio {best['ratio'] * 100:.0f}%")
    two = next(r for r in sweep if r["thr"] == 0.02)
    print(f"   the 2% rule used in entry_timing.py: in-sample mean {two['is_mean'] * 100:+.3f}%; "
          f"out of sample n={two['oos_n']}, mean {two['oos_mean'] * 100:+.3f}%, "
          f"hit {two['oos_hit'] * 100:.1f}%, OOS/IS ratio {two['ratio'] * 100:.0f}%")

    # -- 4. Executability -----------------------------------------------------
    print("\n4. EXECUTABILITY: can you actually get filled at the opening print?")
    sel2 = daily[daily["nas_ret"].abs() >= 0.02]
    print(f"   Median bars in session: {sel2['n'].median():.0f}  "
          f"(a bar exists only when a trade happened)")
    print(f"   Median volume in the FIRST bar: {sel2['first_vol'].median():.0f} shares")
    print(f"   Median volume for the whole day: {sel2['vol'].median():.0f} shares")
    px = 46000
    print(f"   At ~{px:,} KZT/share, the first bar is about "
          f"{sel2['first_vol'].median() * px / 460:,.0f} USD of turnover, "
          f"the whole day about {sel2['vol'].median() * px / 460:,.0f} USD.")

    # -- 5. Beta vs alpha -----------------------------------------------------
    print("\n5. BETA OR ALPHA: is this just 'buy what went up'?")
    daily["kase_prev"] = daily["kase_intraday_kzt"].shift(1)
    b1, t1, _ = ols(daily["kase_intraday_kzt"], daily["nas_ret"])
    b2, t2, _ = ols(daily["kase_intraday_kzt"], daily["kase_prev"])
    print(f"   drift vs prior NASDAQ move : beta={b1:+.3f} t={t1:+.2f}")
    print(f"   drift vs own prior KASE move: beta={b2:+.3f} t={t2:+.2f}")
    print("   (if only the first is significant, KASE is tracking NASDAQ, not just trending)")


if __name__ == "__main__":
    main()
