#!/usr/bin/env python3
"""
Drift by entry time on days NASDAQ moved at least 2%, exit fixed at the close.

Two conventions matter. Entry delays run from the first actual trade, not the
nominal 11:30 open: KASE is thin and the first print is often late, so "+5 min"
means five minutes after trading actually started. Prices are raw KZT with no
FX conversion; the USD series gives materially the same answer (beta 0.270
against 0.265 raw, transmission_robustness.py section 1), so these numbers are
not comparable to the USD betas to the third decimal.

Requires data/derived/transmission_daily.csv.

Originally run inline during the August 2026 research session and quoted
without the script being committed; recovered from the transcript.
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
DAILY = REPO / "data" / "derived" / "transmission_daily.csv"

SESSION_LO = 11 * 60 + 25
SESSION_HI = 17 * 60 + 35
MIN_BARS = 20
BIG_MOVE = 0.02

ENTRIES = [
    ("first trade", 0), ("+5 min", 5), ("+15 min", 15), ("+30 min", 30),
    ("+60 min", 60), ("+120 min", 120), ("13:30 (mid)", None),
]
CUTS = [12 * 60, 13 * 60, 14 * 60, 15 * 60, 16 * 60, 17 * 60, 17 * 60 + 35]


def load_kase() -> pd.DataFrame:
    files = sorted(glob.glob(str(STORE / "KSPI.KZ" / "*.parquet")))
    if not files:
        raise SystemExit(f"No bars under {STORE / 'KSPI.KZ'}. Run src/kase/tradernet_fetch.py first.")
    k = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    k = k[k["close"].notna()].copy()
    k["ts_almaty"] = pd.to_datetime(k["ts_almaty"])
    k["day"] = k["ts_almaty"].dt.normalize().dt.tz_localize(None)
    k["min"] = k["ts_almaty"].dt.hour * 60 + k["ts_almaty"].dt.minute
    return k[(k["min"] >= SESSION_LO) & (k["min"] <= SESSION_HI)]


def main() -> None:
    k = load_kase()
    daily = pd.read_csv(DAILY, parse_dates=["day"]).dropna(subset=["nas_ret"])
    big = set(daily[daily["nas_ret"].abs() >= BIG_MOVE]["day"])
    sign = dict(zip(daily["day"], np.sign(daily["nas_ret"])))

    sessions = [(d, g.sort_values("min")) for d, g in k.groupby("day")
                if d in big and len(g) >= MIN_BARS]

    print(f"ENTRY-TIMING SENSITIVITY (>={BIG_MOVE:.0%} NASDAQ days), exit always at the close")
    print(f"  {'entry':>16} {'trades':>7} {'mean':>9} {'hit':>7}")
    entry_rows = []
    for label, delay in ENTRIES:
        rows = []
        for day, g in sessions:
            ent = g[g["min"] >= 13 * 60 + 30] if delay is None \
                else g[g["min"] >= g["min"].iloc[0] + delay]
            if len(ent) < 2:
                continue
            rows.append(sign[day] * (ent["close"].iloc[-1] / ent["close"].iloc[0] - 1))
        if len(rows) < MIN_BARS:
            continue
        a = np.array(rows)
        print(f"  {label:>16} {len(a):>7} {a.mean() * 100:+8.3f}% {(a > 0).mean() * 100:6.1f}%")
        entry_rows.append({"label": label, "delay_minutes": delay, "n": len(a),
                           "mean_pct": a.mean() * 100, "hit_pct": (a > 0).mean() * 100})

    # written out for the figure
    dest = REPO / "data" / "derived" / "entry_delay.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(entry_rows).to_csv(dest, index=False)
    print(f"\n  Wrote data/derived/entry_delay.csv ({len(entry_rows)} entry points)")

    print("\nWHERE THE DRIFT ACCRUES (cumulative from the first print)")
    prof: dict[int, list[float]] = {}
    for day, g in sessions:
        p0 = g["close"].iloc[0]
        for cut in CUTS:
            sub = g[g["min"] <= cut]
            if len(sub) < 2:
                continue
            prof.setdefault(cut, []).append(sign[day] * (sub["close"].iloc[-1] / p0 - 1))
    full = np.mean(prof[CUTS[-1]]) if CUTS[-1] in prof else np.nan
    for cut, v in sorted(prof.items()):
        a = np.array(v)
        share = f"{a.mean() / full * 100:5.1f}% of full" if np.isfinite(full) and full else ""
        print(f"  by {cut // 60:02d}:{cut % 60:02d}  cum {a.mean() * 100:+6.3f}%  (n={len(a)})  {share}")


if __name__ == "__main__":
    main()
