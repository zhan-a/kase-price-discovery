#!/usr/bin/env python3
"""
Is the KASE drift after a NASDAQ move larger than the cost of trading it?

Two trade-print estimators of KSPI's effective spread on KASE, because there is
no quote feed:

  * Roll (1984): s = 2 sqrt(-cov(r_t, r_t-1)) on one-minute log returns, one
    estimate per session, median across sessions. s is the bid-ask spread, the
    full width between bid and ask.
  * Corwin and Schultz (2012): S from the high-low ranges of consecutive
    sessions, S = 2 (e^a - 1) / (1 + e^a). S is the proportional spread, again
    the full width.

A round trip crosses the spread once, buying at the ask and selling at the bid,
so it costs one spread plus commission on both sides. An earlier version of this
script read both estimates as one-way and doubled them; the
verification of 2026-10-12 caught the error. Round trips here are one spread
plus 0.17%.

What each estimator leaves out is printed rather than assumed. Roll returns
nothing for a session with fewer than 51 bars or a non-negative serial
covariance. Corwin-Schultz as implemented keeps the positive two-day estimates
only and takes their median, where the paper sets negative estimates to zero and
averages; both treatments are printed, and the median-of-positives remains the
headline because it is the figure the cost band was built on. The two
estimators were first run on different windows, Roll on every KSPI session in
the store and Corwin-Schultz from 2024, so Roll is also printed on the 2024
window.

Writes data/derived/spread_estimates.csv, read by the year-end cost table.
Requires data/derived/transmission_daily.csv and data/derived/entry_delay.csv.
"""

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _store import store as _store_dir


REPO = Path(__file__).resolve().parents[2]
STORE = _store_dir() / "kase" / "intraday"
PANEL = REPO / "data" / "derived" / "transmission_daily.csv"
ENTRY = REPO / "data" / "derived" / "entry_delay.csv"
DEST = REPO / "data" / "derived" / "spread_estimates.csv"

COMMISSION_PER_SIDE = 0.00085      # Freedom Broker KASE equity tariff, per side
PANEL_ERA = "2024-01-01"           # Corwin-Schultz window; Roll is repeated on it
ROLL_MIN_RETURNS = 50              # 51 bars; fewer give no usable covariance
CS_MIN_DAYS = 30
THRESHOLDS = [0.0, 0.01, 0.02, 0.03, 0.04]
MIN_TRADES = 20


def load_kspi() -> pd.DataFrame:
    files = sorted(glob.glob(str(STORE / "KSPI.KZ" / "*.parquet")))
    if not files:
        raise SystemExit(f"No bars under {STORE / 'KSPI.KZ'}; attach the store as data/README.md describes.")
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    d = d[d["close"].notna()].copy()
    d["ts_almaty"] = pd.to_datetime(d["ts_almaty"])
    d["day"] = d["ts_almaty"].dt.normalize().dt.tz_localize(None)
    return d.sort_values("ts_utc").reset_index(drop=True)


def roll_session(minute_close: pd.Series) -> tuple[float, str]:
    """Roll's spread for one session, or the reason there is none."""
    r = np.log(minute_close).diff().dropna()
    if len(r) < ROLL_MIN_RETURNS:
        return np.nan, "fewer than 51 bars"
    cov = np.cov(r[1:], r[:-1])[0, 1]
    if not cov < 0:
        return np.nan, "serial covariance not negative"
    return 2 * np.sqrt(-cov), "estimated"


def roll_census(kspi: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Per-session Roll estimates and the status of every session."""
    out = kspi.groupby("day")["close"].apply(lambda s: pd.Series(roll_session(s), index=["s", "status"]))
    out = out.unstack()
    return out["s"].astype(float), out["status"]


def corwin_schultz_pairs(frame: pd.DataFrame) -> np.ndarray:
    """Two-day Corwin-Schultz estimates, one per consecutive pair of sessions.

    Returned raw: negative and non-finite values included, so the caller
    chooses the treatment and reports what it dropped.
    """
    d = frame.groupby("day").agg(hi=("high", "max"), lo=("low", "min")).dropna()
    d = d[(d["hi"] > 0) & (d["lo"] > 0) & (d["hi"] >= d["lo"])]
    hi, lo = d["hi"].values, d["lo"].values
    if len(hi) < CS_MIN_DAYS:
        return np.array([])
    beta = (np.log(hi[1:] / lo[1:]) ** 2) + (np.log(hi[:-1] / lo[:-1]) ** 2)
    hi2 = np.maximum(hi[1:], hi[:-1])
    lo2 = np.minimum(lo[1:], lo[:-1])
    gamma = np.log(hi2 / lo2) ** 2
    k = 3 - 2 * np.sqrt(2)
    alpha = (np.sqrt(2 * beta) - np.sqrt(beta)) / k - np.sqrt(gamma / k)
    return 2 * (np.exp(alpha) - 1) / (1 + np.exp(alpha))


def round_trip(spread: float) -> float:
    """One spread crossed once, plus commission on both sides."""
    return spread + 2 * COMMISSION_PER_SIDE


def main():
    kspi = load_kspi()
    daily = pd.read_csv(PANEL, parse_dates=["day"])

    print("EFFECTIVE SPREAD OF KSPI ON KASE, ESTIMATED FROM TRADE PRINTS")
    print("  Both estimators return the full bid-ask spread. A round trip pays it once,")
    print(f"  plus commission of {COMMISSION_PER_SIDE * 100:.3f}% per side, {2 * COMMISSION_PER_SIDE * 100:.2f}% both ways.\n")

    roll_all, status_all = roll_census(kspi)
    era = kspi[kspi["day"] >= PANEL_ERA]
    roll_era, status_era = roll_census(era)
    rows = []
    for label, s, st, headline in [("all KSPI sessions in the store", roll_all, status_all, True),
                                   (f"sessions from {PANEL_ERA}", roll_era, status_era, False)]:
        est = s.dropna()
        print(f"  Roll, {label}: median {est.median() * 100:.2f}%  mean {est.mean() * 100:.2f}%")
        print(f"    sessions {len(s)}: estimated {int((st == 'estimated').sum())}, "
              f"excluded for fewer than 51 bars {int((st == 'fewer than 51 bars').sum())}, "
              f"excluded for a non-negative serial covariance "
              f"{int((st == 'serial covariance not negative').sum())}")
        rows.append({"estimator": "roll", "window": label, "treatment": "median of per-session estimates",
                     "n": int(len(est)), "spread": float(est.median()), "headline": headline})

    s = corwin_schultz_pairs(era)
    finite = s[np.isfinite(s)]
    positive = finite[finite > 0]
    floored = np.where(finite > 0, finite, 0.0)
    print(f"\n  Corwin-Schultz, sessions from {PANEL_ERA}: {len(finite)} two-day estimates, "
          f"{int((finite <= 0).sum())} non-positive ({(finite <= 0).mean() * 100:.1f}%)")
    print(f"    median of the positive estimates (as implemented) : {np.median(positive) * 100:.2f}%")
    print(f"    mean with negatives set to zero (the paper)       : {floored.mean() * 100:.2f}%")
    print(f"    median with negatives set to zero                 : {np.median(floored) * 100:.2f}%")
    rows.append({"estimator": "corwin_schultz", "window": f"sessions from {PANEL_ERA}",
                 "treatment": "median of positive two-day estimates", "n": int(len(positive)),
                 "spread": float(np.median(positive)), "headline": True})
    rows.append({"estimator": "corwin_schultz", "window": f"sessions from {PANEL_ERA}",
                 "treatment": "mean, negatives set to zero", "n": int(len(finite)),
                 "spread": float(floored.mean()), "headline": False})
    rows.append({"estimator": "commission", "window": "tariff", "treatment": "per side",
                 "n": 0, "spread": COMMISSION_PER_SIDE, "headline": True})
    out = pd.DataFrame(rows)
    DEST.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(DEST, index=False, float_format="%.10g")

    roll = out[(out["estimator"] == "roll") & out["headline"]]["spread"].iloc[0]
    cs = out[(out["estimator"] == "corwin_schultz") & out["headline"]]["spread"].iloc[0]
    costs = {"Roll": round_trip(roll), "Corwin-Schultz": round_trip(cs)}
    print("\n  ROUND TRIP, one spread plus commission both ways")
    for name, rt in costs.items():
        print(f"    {name:15s} {rt * 100:.2f}%")
    print(f"  Wrote data/derived/spread_estimates.csv ({len(out)} rows)")

    # the drift against the costs
    print("\nTHE TRADE: enter at the KASE open in the direction of the prior NASDAQ move, exit at the close")
    daily = daily.dropna(subset=["nas_ret", "kase_intraday"])
    years = daily["day"].nunique() / 252
    print(f"\n  {'threshold':>12} {'trades':>7} {'gross/trade':>12} {'hit rate':>9} "
          f"{'gross/yr':>10}   net/yr at each round-trip cost")
    for thr in THRESHOLDS:
        sel = daily[daily["nas_ret"].abs() >= thr].copy()
        if len(sel) < MIN_TRADES:
            continue
        # long if NASDAQ rose, short if it fell; the short leg is hypothetical
        sel["pnl"] = np.sign(sel["nas_ret"]) * sel["kase_intraday"]
        gross = sel["pnl"].mean()
        hit = (sel["pnl"] > 0).mean()
        per_year = len(sel) / years
        nets = "  ".join(f"{name}: {(gross - rt) * per_year * 100:+7.1f}%" for name, rt in costs.items())
        print(f"  |move|>={thr * 100:4.1f}% {len(sel):>7} {gross * 100:+11.3f}% "
              f"{hit * 100:8.1f}% {gross * per_year * 100:+9.1f}%   {nets}")

    print("\n  LONG-ONLY (KASE has no short selling)")
    print(f"  {'threshold':>12} {'trades':>7} {'gross/trade':>12} {'hit rate':>9} {'gross/yr':>10}")
    for thr in THRESHOLDS:
        sel = daily[daily["nas_ret"] >= thr].copy()
        if len(sel) < MIN_TRADES:
            continue
        per_year = len(sel) / years
        print(f"  NASDAQ>=+{thr * 100:4.1f}% {len(sel):>7} {sel['kase_intraday'].mean() * 100:+11.3f}% "
              f"{(sel['kase_intraday'] > 0).mean() * 100:8.1f}% "
              f"{sel['kase_intraday'].mean() * per_year * 100:+9.1f}%")

    big = daily[daily["nas_ret"].abs() >= 0.02]
    print(f"\n  On the {len(big)} days NASDAQ moved >=2%, the average |move| was "
          f"{big['nas_ret'].abs().mean() * 100:.2f}% and the average KASE drift in "
          f"that direction was {(np.sign(big['nas_ret']) * big['kase_intraday']).mean() * 100:.3f}%.")

    # the entry-delay returns of entry_timing.py against the same costs
    print("\nNET OF COSTS BY ENTRY DELAY (entry_timing.py returns, raw KZT, sessions with a NASDAQ move of at least 2%)")
    if not ENTRY.exists():
        print("  (data/derived/entry_delay.csv absent; run entry_timing.py first)")
        return
    e = pd.read_csv(ENTRY)
    print(f"  {'entry':>16} {'gross':>8} " + " ".join(f"{'net, ' + n:>22s}" for n in costs))
    for _, r in e.iterrows():
        nets = " ".join(f"{r['mean_pct'] - rt * 100:+21.3f}%" for rt in costs.values())
        print(f"  {r['label']:>16} {r['mean_pct']:+7.3f}% {nets}")
    print("  A negative net means the round trip exceeds the mean return captured from that entry.")


if __name__ == "__main__":
    main()
