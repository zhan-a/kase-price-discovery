"""Conditioning KASE intraday drift on NASDAQ prices visible during the local session.

Craig, Dravid and Richardson (1995) argue that what looks like partial adjustment of a
local market to foreign information is often an artefact of the regression's information
set: the local market is compared against a foreign close that is already stale by the
time the local session opens, while foreign instruments that trade *during* the local
session are omitted. Once those contemporaneously observable foreign prices enter the
regression, the lagged foreign coefficient tends to collapse.

KSPI is the natural test case on KASE. Its NASDAQ regular session (09:30-16:00 ET) never
overlaps the KASE session (11:29-17:30 Almaty), so the only NASDAQ information a KASE
trader can act on intraday is the NASDAQ *pre-market*, which opens at 04:00 ET -- roughly
14:00 Almaty in winter -- and therefore prints inside the back half of the KASE session.

The analysis builds, per KASE session:

  drift    KASE intraday drift, USD-converted: last session bar over first session bar,
           each divided by the on-exchange USDKZT_TOM rate prevailing at that bar.
  lagged   the last NASDAQ regular close-to-close return whose close timestamp strictly
           precedes the KASE session open. This is the stale term.
  live     the last NASDAQ pre-market print inside the KASE session window, over the same
           prior NASDAQ regular close, minus one. Zero when no such print exists. This is
           the term a KASE trader could actually observe before the KASE close.

and estimates three specifications: drift on lagged alone; drift on lagged and live
jointly; and the joint specification restricted to sessions that actually carry a live
pre-market print. The question the exercise answers is whether the lagged coefficient
falls once the live term is admitted, which is what the Craig-Dravid-Richardson critique
predicts, or survives it, which would be evidence of genuine overnight partial adjustment.

Newey-West HAC standard errors at lag 5 are the headline, matching the convention used
elsewhere in this transmission work; plain OLS t-statistics are printed alongside so the
reader can see how much of any inference rests on the HAC correction.
"""

from __future__ import annotations

import datetime as dt
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

# must start at 11:29 or the auction print is silently dropped
KASE_SESSION_START = dt.time(11, 29)
KASE_SESSION_END = dt.time(17, 30)

# regular session; earlier NY prints are pre-market, from 04:00 ET
NASDAQ_OPEN = dt.time(9, 30)
NASDAQ_CLOSE = dt.time(16, 0)

HAC_LAG = 5

# the conditioning close must genuinely be the previous trading day's, not one
# stranded on the far side of a data gap. Five days admits a long weekend plus
# a holiday and excludes the rest.
MAX_STALE_DAYS = 5


def find_store() -> Path:
    """Locate the intraday parquet store, which sits outside this repository."""
    override = os.environ.get("KASE_STORE") or os.environ.get("KASE_DATA_STORE")
    candidates = []
    if override:
        candidates.append(Path(override))
    repo_root = Path(__file__).resolve().parents[2]
    candidates.append(repo_root.parent / "trading desk" / "data")
    candidates.append(repo_root / "data")
    for cand in candidates:
        if (cand / "kase" / "intraday").is_dir() and (cand / "nasdaq" / "intraday").is_dir():
            return cand
    tried = "\n  ".join(str(c) for c in candidates)
    raise SystemExit(
        "Could not find the intraday data store. Expected a directory containing both\n"
        "kase/intraday and nasdaq/intraday. Tried:\n  " + tried + "\n"
        "Set KASE_STORE to point at it."
    )


def load_minute_bars(directory: Path, label: str) -> pd.DataFrame:
    files = sorted(directory.glob("*.parquet"))
    if not files:
        raise SystemExit(f"No parquet files for {label} under {directory}")
    frame = pd.concat((pd.read_parquet(f) for f in files), ignore_index=True)
    frame = frame.sort_values("ts_utc").drop_duplicates("ts_utc", keep="last")
    return frame.reset_index(drop=True)


def kase_sessions_usd(bars: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    """First and last USD-converted print of each KASE session, with their timestamps.

    The FX line trades on its own schedule, so each equity bar is matched to the most
    recent USDKZT_TOM print at or before it (merge_asof backward). Bars preceding the
    first FX print of the sample have no rate and are dropped.
    """
    tod = bars["ts_almaty"].dt.time
    in_session = (tod >= KASE_SESSION_START) & (tod <= KASE_SESSION_END)
    bars = bars.loc[in_session, ["ts_utc", "ts_almaty", "close"]].copy()

    rate = fx[["ts_utc", "close"]].rename(columns={"close": "usdkzt"})
    bars = pd.merge_asof(
        bars.sort_values("ts_utc"),
        rate.sort_values("ts_utc"),
        on="ts_utc",
        direction="backward",
    )
    bars = bars.dropna(subset=["usdkzt"])
    bars["px_usd"] = bars["close"] / bars["usdkzt"]

    bars["session"] = bars["ts_almaty"].dt.date
    grouped = bars.groupby("session", sort=True)
    sessions = pd.DataFrame(
        {
            "open_ts": grouped["ts_utc"].first(),
            "close_ts": grouped["ts_utc"].last(),
            "open_usd": grouped["px_usd"].first(),
            "close_usd": grouped["px_usd"].last(),
            "n_bars": grouped.size(),
        }
    ).reset_index()
    sessions["drift"] = sessions["close_usd"] / sessions["open_usd"] - 1.0
    return sessions


def nasdaq_regular_closes(bars: pd.DataFrame) -> pd.DataFrame:
    """Last regular-session print of each NASDAQ trading day, with its close-to-close return."""
    tod = bars["ts_ny"].dt.time
    regular = bars.loc[(tod >= NASDAQ_OPEN) & (tod <= NASDAQ_CLOSE)].copy()
    regular["ny_date"] = regular["ts_ny"].dt.date
    grouped = regular.groupby("ny_date", sort=True)
    closes = pd.DataFrame(
        {"close_ts": grouped["ts_utc"].last(), "close_px": grouped["close"].last()}
    ).reset_index()
    closes["cc_ret"] = closes["close_px"].pct_change()
    return closes


def attach_lagged_close(sessions: pd.DataFrame, closes: pd.DataFrame) -> pd.DataFrame:
    """Attach the last NASDAQ close strictly preceding each KASE session open."""
    merged = pd.merge_asof(
        sessions.sort_values("open_ts"),
        closes.rename(
            columns={
                "close_ts": "prior_close_ts",
                "close_px": "prior_close_px",
                "cc_ret": "lagged",
                "ny_date": "prior_close_date",
            }
        ).sort_values("prior_close_ts"),
        left_on="open_ts",
        right_on="prior_close_ts",
        direction="backward",
        allow_exact_matches=False,
    )
    return merged


def attach_live_premarket(
    sessions: pd.DataFrame, nasdaq: pd.DataFrame, close_bound: str
) -> pd.DataFrame:
    """Attach the last NASDAQ pre-market print visible before the KASE close.

    ``close_bound`` selects the upper edge of the window: "last_bar" uses the timestamp of
    the KASE closing print (the price the drift is measured to), "nominal" uses 17:30
    Almaty. The lower edge is the nominal session start; in this sample it never binds,
    because NASDAQ extended hours begin at 04:00 ET, well after 11:29 Almaty.
    """
    tod_ny = nasdaq["ts_ny"].dt.time
    pre = nasdaq.loc[tod_ny < NASDAQ_OPEN, ["ts_utc", "ts_ny", "close"]].copy()

    out = sessions.copy()
    if close_bound == "last_bar":
        upper = out["close_ts"]
    elif close_bound == "nominal":
        almaty_day = pd.to_datetime(out["session"]).dt.tz_localize("Asia/Almaty")
        upper = (
            almaty_day
            + pd.Timedelta(hours=KASE_SESSION_END.hour, minutes=KASE_SESSION_END.minute)
        ).dt.tz_convert("UTC")
    else:
        raise ValueError(close_bound)

    almaty_day = pd.to_datetime(out["session"]).dt.tz_localize("Asia/Almaty")
    lower = (
        almaty_day
        + pd.Timedelta(hours=KASE_SESSION_START.hour, minutes=KASE_SESSION_START.minute)
    ).dt.tz_convert("UTC")

    # one asof merge cannot express a two-sided window: take the last print
    # before the upper edge, then discard it if it precedes the lower
    matched = pd.merge_asof(
        pd.DataFrame({"upper": upper.set_axis(out.index), "_row": out.index}).sort_values(
            "upper"
        ),
        pre.rename(
            columns={"ts_utc": "pre_ts", "ts_ny": "pre_ts_ny", "close": "pre_px"}
        ).sort_values("pre_ts"),
        left_on="upper",
        right_on="pre_ts",
        direction="backward",
    ).set_index("_row")

    out["pre_ts"] = matched["pre_ts"]
    out["pre_ts_ny"] = matched["pre_ts_ny"]
    out["pre_px"] = matched["pre_px"]
    out["_lower"] = lower.set_axis(out.index)
    stale = out["pre_ts"].isna() | (out["pre_ts"] < out["_lower"])
    out.loc[stale, ["pre_ts", "pre_ts_ny", "pre_px"]] = pd.NaT, pd.NaT, np.nan
    out = out.drop(columns="_lower")

    out["has_live"] = out["pre_px"].notna()
    out["live"] = np.where(
        out["has_live"], out["pre_px"] / out["prior_close_px"] - 1.0, 0.0
    )
    return out


def build_panel(store: Path, close_bound: str = "last_bar") -> pd.DataFrame:
    kase = load_minute_bars(store / "kase" / "intraday" / "KSPI.KZ", "KSPI.KZ")
    fx = load_minute_bars(store / "kase" / "intraday" / "USDKZT_TOM.KZ", "USDKZT_TOM.KZ")
    nasdaq = load_minute_bars(store / "nasdaq" / "intraday" / "KSPI.US", "KSPI.US")

    sessions = kase_sessions_usd(kase, fx)
    closes = nasdaq_regular_closes(nasdaq)

    # outside NASDAQ coverage the "prior close" is just the last observation
    # before the store
    cover_lo = closes["ny_date"].min()
    cover_hi = closes["ny_date"].max()
    sessions = sessions[
        (sessions["session"] >= cover_lo) & (sessions["session"] <= cover_hi)
    ].copy()

    panel = attach_lagged_close(sessions, closes)
    panel = attach_live_premarket(panel, nasdaq, close_bound=close_bound)

    panel["stale_days"] = (
        panel["open_ts"] - panel["prior_close_ts"]
    ).dt.total_seconds() / 86400.0
    panel = panel[panel["stale_days"] <= MAX_STALE_DAYS]
    panel = panel.dropna(subset=["drift", "lagged"])
    return panel.reset_index(drop=True)


def run_regression(frame: pd.DataFrame, regressors: list[str]) -> dict:
    y = frame["drift"].to_numpy(float)
    X = sm.add_constant(frame[regressors].to_numpy(float), has_constant="add")
    ols = sm.OLS(y, X).fit()
    hac = ols.get_robustcov_results(cov_type="HAC", maxlags=HAC_LAG, use_correction=True)
    names = ["const"] + regressors
    return {
        "names": names,
        "params": dict(zip(names, ols.params)),
        "t_hac": dict(zip(names, hac.tvalues)),
        "p_hac": dict(zip(names, hac.pvalues)),
        "se_hac": dict(zip(names, hac.bse)),
        "t_ols": dict(zip(names, ols.tvalues)),
        "r2": ols.rsquared,
        "r2_adj": ols.rsquared_adj,
        "n": int(ols.nobs),
    }


def print_spec(title: str, res: dict) -> None:
    print(title)
    print(
        "  {:<8s} {:>12s} {:>12s} {:>9s} {:>9s} {:>9s}".format(
            "term", "coef", "se(HAC5)", "t(HAC5)", "t(OLS)", "p(HAC5)"
        )
    )
    for name in res["names"]:
        print(
            "  {:<8s} {:>12.6f} {:>12.6f} {:>9.3f} {:>9.3f} {:>9.4f}".format(
                name,
                res["params"][name],
                res["se_hac"][name],
                res["t_hac"][name],
                res["t_ols"][name],
                res["p_hac"][name],
            )
        )
    print(
        "  n = {:d}   R^2 = {:.4f}   adj R^2 = {:.4f}".format(
            res["n"], res["r2"], res["r2_adj"]
        )
    )
    print()


def main() -> int:
    store = find_store()
    print("=" * 78)
    print("Section B. Conditioning KASE drift on NASDAQ prices visible in-session")
    print("=" * 78)
    print(f"store: {store}")
    print()

    panel = build_panel(store, close_bound="last_bar")

    live = panel[panel["has_live"]]
    print("-- sample --")
    print(f"  KASE sessions in the estimation panel : {len(panel)}")
    print(f"  first / last session                  : {panel['session'].min()} .. {panel['session'].max()}")
    print(f"  sessions carrying a live pre-market print: {len(live)} "
          f"({100.0 * len(live) / len(panel):.1f}% of panel)")
    if len(live):
        ny_times = live["pre_ts_ny"].dt.time
        print(f"  live print NY time, earliest / latest  : {min(ny_times)} .. {max(ny_times)}")
        print(f"  all live prints strictly pre-09:30 ET  : {bool((ny_times < NASDAQ_OPEN).all())}")
        alm = live["pre_ts"].dt.tz_convert("Asia/Almaty").dt.time
        print(f"  live print Almaty time, earliest/latest: {min(alm)} .. {max(alm)}")
        # pre-market is thin, so a sign tilt would mean a quote-side artefact
        # in the live term
        print(f"  live move on those sessions, median    : {live['live'].median():+.5f}")
        print(f"  share of live moves that are positive  : {(live['live'] > 0).mean():.3f}")
    print()

    print("-- variable summary (decimal returns) --")
    print("  {:<8s} {:>6s} {:>10s} {:>10s} {:>10s} {:>10s}".format(
        "var", "n", "mean", "sd", "min", "max"))
    for var, frame in (("drift", panel), ("lagged", panel), ("live", panel),
                       ("live>0", live)):
        col = "live" if var == "live>0" else var
        s = frame[col]
        print("  {:<8s} {:>6d} {:>10.5f} {:>10.5f} {:>10.5f} {:>10.5f}".format(
            var, len(s), s.mean(), s.std(ddof=1), s.min(), s.max()))
    print()
    corr = panel[["drift", "lagged", "live"]].corr()
    print("-- correlations (full panel) --")
    print(corr.round(4).to_string())
    print()

    spec1 = run_regression(panel, ["lagged"])
    spec2 = run_regression(panel, ["lagged", "live"])
    spec3 = run_regression(live, ["lagged", "live"])

    print("-- specifications: dependent variable is KASE USD intraday drift --")
    print()
    print_spec("(1) drift ~ lagged NASDAQ close-to-close, full panel", spec1)
    print_spec("(2) drift ~ lagged + live pre-market, full panel", spec2)
    print_spec("(3) drift ~ lagged + live pre-market, live-print sessions only", spec3)

    b1 = spec1["params"]["lagged"]
    b2 = spec2["params"]["lagged"]
    b3 = spec3["params"]["lagged"]
    direction = "falls" if b2 < b1 else "rises"
    print("-- effect of admitting the live term --")
    print(f"  lagged coefficient, spec (1)                 : {b1: .6f}")
    print(f"  lagged coefficient, spec (2)                 : {b2: .6f}")
    print(f"  change, (2) - (1)                            : {b2 - b1: .6f}"
          f"   ({100.0 * (b2 - b1) / abs(b1):+.1f}% of the spec-1 coefficient)")
    print(f"  the lagged coefficient {direction} when the live term is added.")
    print(f"  lagged coefficient, spec (3) live sessions   : {b3: .6f}")

    # spec (1) on the live subsample separates regressor from sample
    spec1_live = run_regression(live, ["lagged"])
    print(f"  lagged coefficient, spec (1) on live subsample: {spec1_live['params']['lagged']: .6f}"
          f"  (n = {spec1_live['n']}, R^2 = {spec1_live['r2']:.4f})")
    print()

    print("-- robustness --")
    alt = build_panel(store, close_bound="nominal")
    alt_live = alt[alt["has_live"]]
    a1 = run_regression(alt, ["lagged"])
    a2 = run_regression(alt, ["lagged", "live"])
    a3 = run_regression(alt_live, ["lagged", "live"])
    print("  (a) KASE close bound taken as nominal 17:30 Almaty rather than the last bar")
    print(f"      live-print sessions: {len(alt_live)} of {len(alt)}")
    print(f"      lagged: (1) {a1['params']['lagged']: .6f}  (2) {a2['params']['lagged']: .6f}"
          f"  (3) {a3['params']['lagged']: .6f}")
    print(f"      live  : (2) {a2['params']['live']: .6f}  (3) {a3['params']['live']: .6f}")
    print(f"      R^2   : (1) {a1['r2']:.4f}  (2) {a2['r2']:.4f}  (3) {a3['r2']:.4f}")

    sub = panel[panel["session"] >= dt.date(2024, 2, 1)]
    sub_live = sub[sub["has_live"]]
    s1 = run_regression(sub, ["lagged"])
    s2 = run_regression(sub, ["lagged", "live"])
    s3 = run_regression(sub_live, ["lagged", "live"])
    print("  (b) sample restricted to 2024-02 onward, matching the Section A common window")
    print(f"      n: (1) {s1['n']}  (2) {s2['n']}  (3) {s3['n']}")
    print(f"      lagged: (1) {s1['params']['lagged']: .6f}  (2) {s2['params']['lagged']: .6f}"
          f"  (3) {s3['params']['lagged']: .6f}")
    print(f"      live  : (2) {s2['params']['live']: .6f}  (3) {s3['params']['live']: .6f}")
    print(f"      R^2   : (1) {s1['r2']:.4f}  (2) {s2['r2']:.4f}  (3) {s3['r2']:.4f}")
    print(f"      t(HAC5) lagged: (1) {s1['t_hac']['lagged']: .3f}  (2) {s2['t_hac']['lagged']: .3f}"
          f"  (3) {s3['t_hac']['lagged']: .3f}")
    print(f"      t(HAC5) live  : (2) {s2['t_hac']['live']: .3f}  (3) {s3['t_hac']['live']: .3f}")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
