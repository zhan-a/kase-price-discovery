#!/usr/bin/env python3
"""
Newey-West HAC inference for the transmission estimates, and the
measurement-point curve of Section 6.2.

Daily transmission estimates are serially correlated, so OLS standard errors
are understated, and not uniformly: more so for the opening gap, whose residual
carries the auction's own noise, than for the drift. Lag 5 is one trading week,
the horizon over which a KASE repricing episode plausibly persists; HAC(1) and
HAC(10) print alongside so the choice can be seen rather than trusted.

Requires data/derived/transmission_daily.csv and the 1-minute store.
"""

import glob
import os
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _store import store as _store_dir, daily as _daily_dir


ROOT = Path(__file__).resolve().parents[2]
PANEL = ROOT / "data" / "derived" / "transmission_daily.csv"
ALIGN = ROOT / "data" / "derived" / "regressor_alignment.csv"
STORE = _store_dir() / "kase" / "intraday"

SESSION_LO, SESSION_HI = 11 * 60 + 25, 17 * 60 + 35
LAGS = (1, 5, 10)

# Almaty minutes tabulated in Section 6.2
MEASUREMENT_POINTS = [11 * 60 + 29, 11 * 60 + 30, 11 * 60 + 31, 11 * 60 + 32,
                      11 * 60 + 35, 11 * 60 + 40, 12 * 60]


def hac(y, x, lags=5):
    """Slope, HAC t, R2 and n for y = a + b*x."""
    m = np.isfinite(y) & np.isfinite(x)
    y, x = np.asarray(y)[m], np.asarray(x)[m]
    fit = sm.OLS(y, sm.add_constant(x)).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return fit.params[1], fit.tvalues[1], fit.rsquared, int(fit.nobs)


def row(label, y, x):
    b, t, r2, n = hac(y, x)
    extra = "  ".join(f"HAC({L}) {hac(y, x, L)[1]:+6.2f}" for L in LAGS)
    print(f"  {label:44s} beta {b:+7.4f}  t {t:+6.2f}  R2 {r2:5.3f}  n {n:4d}   {extra}")


def load_store(ticker):
    files = sorted(glob.glob(str(STORE / ticker / "*.parquet")))
    if not files:
        return pd.DataFrame()
    k = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    k = k[k["close"].notna()].copy()
    k["alm"] = pd.to_datetime(k["ts_almaty"])
    k["day"] = k["alm"].dt.normalize().dt.tz_localize(None)
    k["minute"] = k["alm"].dt.hour * 60 + k["alm"].dt.minute
    return k[(k["minute"] >= SESSION_LO) & (k["minute"] <= SESSION_HI)]


def main():
    if not PANEL.exists():
        raise SystemExit(f"{PANEL} not found. Run analysis/transmission/intraday_transmission.py first.")
    d = pd.read_csv(PANEL, parse_dates=["day"]).dropna(subset=["nas_ret"]).sort_values("day")

    print("HAC(5) INFERENCE, with HAC(1) and HAC(10) alongside\n")
    print("Headline, trimmed panel")
    row("opening gap on prior NASDAQ move", d["kase_gap"].values, d["nas_ret"].values)
    row("intraday drift on prior NASDAQ move", d["kase_intraday"].values, d["nas_ret"].values)

    # compounded, not summed: the components are ratios against different
    # denominators
    d["total_ret"] = (1 + d["kase_gap"]) * (1 + d["kase_intraday"]) - 1
    row("prev-close-to-close total on prior move", d["total_ret"].values, d["nas_ret"].values)
    bg = hac(d["kase_gap"].values, d["nas_ret"].values)[0]
    bd = hac(d["kase_intraday"].values, d["nas_ret"].values)[0]
    print(f"  {'(sum of the two component betas, for contrast)':44s} {bg + bd:+7.4f}")

    # The headline keeps the panel as committed. These rows show what the
    # regressor's alignment with the opening gap does to the estimates: first
    # on the sessions whose gap spans exactly one NASDAQ session, then on every
    # session whose gap spans at least one, with the regressor replaced by the
    # NASDAQ return over the span the gap actually covers.
    print("\nRegressor alignment, from data/derived/regressor_alignment.csv")
    if not ALIGN.exists():
        print("  (alignment table absent; run intraday_transmission.py first)")
    else:
        a = pd.read_csv(ALIGN, parse_dates=["day"])
        m = d.merge(a[["day", "nas_sessions_spanned", "nas_interval_ret"]], on="day", how="left")
        k = m["nas_sessions_spanned"]
        print(f"  gap spans 0 NASDAQ sessions (stale regressor): {int((k == 0).sum())}   "
              f"1 session (aligned): {int((k == 1).sum())}   2 or more: {int((k >= 2).sum())}")
        one = m[k == 1]
        row("opening gap, aligned sessions only", one["kase_gap"].values, one["nas_ret"].values)
        row("intraday drift, aligned sessions only", one["kase_intraday"].values, one["nas_ret"].values)
        row("prev-close-to-close total, aligned only", one["total_ret"].values, one["nas_ret"].values)
        span = m[k >= 1]
        row("opening gap on the interval NASDAQ return", span["kase_gap"].values, span["nas_interval_ret"].values)
        row("intraday drift on the interval NASDAQ return", span["kase_intraday"].values, span["nas_interval_ret"].values)
        row("prev-close-to-close total, interval return", span["total_ret"].values, span["nas_interval_ret"].values)

    print("\nLargest-move quartile")
    q = d[d["nas_ret"].abs() > d["nas_ret"].abs().quantile(0.75)]
    row("opening gap, |move| above the 75th pct", q["kase_gap"].values, q["nas_ret"].values)
    row("intraday drift, |move| above the 75th pct", q["kase_intraday"].values, q["nas_ret"].values)

    print("\nPlacebo: the next NASDAQ move, which cannot reach today's KASE session")
    # only meaningful without overlap: tomorrow's NASDAQ session opens after
    # today's KASE close, so anything non-zero is a construction error. On an
    # overlapping pair it is mechanically non-null.
    d["nas_next"] = d["nas_ret"].shift(-1)
    row("opening gap on the NEXT NASDAQ move", d["kase_gap"].values, d["nas_next"].values)
    row("intraday drift on the NEXT NASDAQ move", d["kase_intraday"].values, d["nas_next"].values)

    print("\nPlacebo: is this momentum rather than transmission?")
    d["own_prev"] = d["kase_intraday"].shift(1)
    row("intraday drift on its own prior move", d["kase_intraday"].values, d["own_prev"].values)

    kase = load_store("KSPI.KZ")
    if kase.empty:
        print("\n(1-minute store absent; raw-tenge and opening-convention rows skipped.)")
        return

    print("\nRaw tenge, no FX conversion")
    kzt = kase.sort_values("minute").groupby("day").agg(o=("close", "first"), c=("close", "last"),
                                                       n=("close", "size"))
    kzt = kzt[kzt["n"] >= 20]
    kzt["drift"] = kzt["c"] / kzt["o"] - 1
    j = d.merge(kzt[["drift"]], left_on="day", right_index=True, how="inner")
    row("intraday drift in tenge", j["drift"].values, j["nas_ret"].values)

    print("\nOpening convention: 11:29 auction print against the first continuous trade")
    # The comparison is anchored on the panel, not rebuilt from the store. Only the
    # opening price differs between the two conventions, so the panel's own gap and
    # drift are rescaled by the ratio of the continuous open to the auction open.
    # Rebuilding the day set from the store instead produces a different and smaller
    # sample, and therefore a different estimate, for no substantive reason.
    fx_files = sorted(glob.glob(str(STORE / "USDKZT_TOM.KZ" / "*.parquet")))
    if not fx_files:
        print("  (on-exchange FX absent; skipped)")
        return
    fx = pd.concat([pd.read_parquet(f) for f in fx_files], ignore_index=True)
    fx["ts_utc"] = pd.to_datetime(fx["ts_utc"], utc=True)
    fx = fx[["ts_utc", "close"]].rename(columns={"close": "fx"}).sort_values("ts_utc")

    k = kase.copy()
    k["ts_utc"] = pd.to_datetime(k["ts_utc"], utc=True)
    k = pd.merge_asof(k.sort_values("ts_utc"), fx, on="ts_utc", direction="backward")
    k = k[k["fx"].notna() & (k["fx"] > 0)].copy()
    k["usd"] = k["close"] / k["fx"]
    per = {day: g.sort_values("minute") for day, g in k.groupby("day")}

    recs = []
    for _, r in d.iterrows():
        g = per.get(r["day"])
        if g is None or len(g) < 2:
            continue
        cont = g[g["minute"] >= 11 * 60 + 30]
        if not len(cont):
            continue
        ratio = cont["usd"].iloc[0] / g["usd"].iloc[0]
        recs.append({"nas": r["nas_ret"],
                     "gap29": r["kase_gap"], "drift29": r["kase_intraday"],
                     "gap30": (1 + r["kase_gap"]) * ratio - 1,
                     "drift30": (1 + r["kase_intraday"]) / ratio - 1})
    c = pd.DataFrame(recs)
    row("opening gap, 11:29 auction print", c["gap29"].values, c["nas"].values)
    row("intraday drift, 11:29 auction print", c["drift29"].values, c["nas"].values)
    row("opening gap, 11:30 first continuous", c["gap30"].values, c["nas"].values)
    row("intraday drift, 11:30 first continuous", c["drift30"].values, c["nas"].values)
    bg29 = hac(c["gap29"].values, c["nas"].values)[0]
    bg30 = hac(c["gap30"].values, c["nas"].values)[0]
    print(f"  {'reallocation on the opening gap':44s} {bg30 - bg29:+7.4f}")

    # the same rescale, swept. The rows above are its first two points, kept
    # separately because 6.1 quotes their HAC t. Computed here rather than in
    # the plotting code so the figure and the table are one implementation.
    print("\nMeasurement-point curve: the split against the price called the open")
    print(f"  {'open':>6} {'beta gap':>10} {'t':>7} {'beta drift':>12} {'t':>7} {'n':>5}")
    curve = []
    for pt in MEASUREMENT_POINTS:
        recs = []
        for _, r in d.iterrows():
            g = per.get(r["day"])
            if g is None or len(g) < 2:
                continue
            sub = g[g["minute"] >= pt]
            if not len(sub) or not np.isfinite(r["nas_ret"]):
                continue
            ratio = sub["usd"].iloc[0] / g["usd"].iloc[0]
            recs.append(((1 + r["kase_gap"]) * ratio - 1,
                         (1 + r["kase_intraday"]) / ratio - 1,
                         r["nas_ret"]))
        a = pd.DataFrame(recs, columns=["gap", "drift", "nas"])
        bg, tg, _, n = hac(a["gap"].values, a["nas"].values)
        bd, td, _, _ = hac(a["drift"].values, a["nas"].values)
        label = f"{pt // 60:02d}:{pt % 60:02d}"
        curve.append({"minute": pt, "label": label, "beta_gap": bg, "t_gap": tg,
                      "beta_drift": bd, "t_drift": td, "n": n})
        print(f"  {label:>6} {bg:>10.4f} {tg:>7.2f} {bd:>12.4f} {td:>7.2f} {n:>5d}")
    dest = ROOT / "data" / "derived" / "measurement_point_curve.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # ten digits: a full repr differs between numpy builds and would diff
    # everywhere
    pd.DataFrame(curve).to_csv(dest, index=False, float_format="%.10g")
    print(f"  Wrote data/derived/measurement_point_curve.csv ({len(curve)} points)")

    print("\n  HAC(5) is one trading week. Where the three columns differ, the")
    print("  estimate is sensitive to the assumed persistence.")


if __name__ == "__main__":
    main()
