"""Overlap comparison: does a shared trading hour change how foreign news reaches KASE?

Three KASE listings also trade abroad.  KSPI trades on NASDAQ, whose regular
session opens roughly three hours after KASE has closed for the day, so the two
venues never quote at the same instant.  KZAP (as KAP.IL) and AIRA (as AIRA.IL)
trade on the LSE International Order Book, which opens while KASE is still
running and stays open for several hours after KASE closes.  The pairs therefore
differ in one structural respect -- whether a Kazakh trader can watch the foreign
book during his own session -- while sharing issuer, currency exposure and
clientele.  That makes them a natural contrast for the question of how much of
the foreign price signal is already impounded by the time KASE prints its close,
and how much has to wait for the next KASE open.

The script measures, for each pair and on a common 2024-02-onwards window:

  * a contemporaneous beta, KASE session return on the same-calendar-day foreign
    return -- for the overlapping pairs this is partly a genuine simultaneity,
    for KSPI it is an artefact of the calendar-day convention;
  * lagged betas, KASE opening gap and KASE intraday drift each on the most
    recent foreign close-to-close return that was already public before the KASE
    session opened, plus their sum (the "lagged total");
  * the composition of foreign daily return variance -- how much of it arrives
    before the KASE close, which is the mechanism that is supposed to drive any
    difference between the pairs;
  * a conditional test that restricts the foreign signal to the part that
    arrived strictly after the KASE close, so that the overlapping and
    non-overlapping pairs are compared on informationally equivalent news, and
    reports the overlapping-minus-non-overlapping difference in the next-day
    total with a standard error;
  * Johansen cointegration on the daily log price pair and, where a
    cointegrating rank is found, Gonzalo-Granger common-factor weights over a
    grid of lag orders and deterministic terms.

The last item carries a caveat that the script treats as a first-class result
rather than a footnote.  Gonzalo-Granger, like Hasbrouck (1995), decomposes the
innovation in a *contemporaneously observed* price vector.  For KSPI there is no
instant at which both legs are observed: the daily pair is assembled by a
labelling convention, and the script demonstrates that the resulting weight is a
function of that convention rather than of the data, by re-estimating it under
the equally defensible convention that pairs each KASE session with the NASDAQ
close that actually preceded it.

All KASE prices are converted to USD with the on-exchange USDKZT_TOM line,
aligned bar by bar with a backward as-of merge, so both legs of every pair are
quoted in the same numeraire.

The foreign legs are read from two committed tables under data/derived/,
written by foreign_legs.py from Yahoo chart data that this repository does not
redistribute; the NASDAQ 1-minute bars for KSPI come from the local store.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.vector_ar.vecm import VECM, coint_johansen

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _store import store as _store_dir, daily as _daily_dir


# Paths

REPO = Path(__file__).resolve().parents[2]
STORE = _store_dir()
DAILY = _daily_dir()

KASE_INTRADAY = STORE / "kase" / "intraday"
NASDAQ_INTRADAY = STORE / "nasdaq" / "intraday"

# the foreign legs, written by foreign_legs.py from Yahoo chart data that is
# not redistributed: daily closes for all three pairs, and for the two IOB
# pairs the hourly-bar quantities the composition split needs
FOREIGN_DAILY = REPO / "data" / "derived" / "foreign_daily.csv"
FOREIGN_SPLIT = REPO / "data" / "derived" / "foreign_split.csv"

# Conventions

WINDOW_START = pd.Timestamp("2024-02-01")

# KASE trades 11:30-17:30 Almaty, auction at 11:29
SESSION_OPEN = pd.Timestamp("11:29").time()
SESSION_CLOSE = pd.Timestamp("17:30").time()

NW_LAGS = 5

# without a recency bound, a backward as-of merge carries the final observation
# of a truncated foreign series forward across every later KASE session. The
# NASDAQ store stops 2026-03 while KASE runs to 2026-08. Five days spans any
# ordinary weekend plus a holiday on either side.
MAX_STALE = pd.Timedelta(days=5)

# Johansen / VECM grid. det_order follows coint_johansen; 0 restricted
# constant, 1 unrestricted plus trend.
DET_SPECS = [(0, "ci", "restricted constant"), (1, "coli", "restricted trend")]
LAG_ORDERS = [1, 2, 3, 5]


ANSWER_LINES = """
ANSWER TO THE SCOPE QUESTION.

Gonzalo-Granger splits the permanent component of a price VECTOR into weights on
its elements.  The weights are the normalised orthogonal complement of the
error-correction loadings alpha, and alpha is identified from the response of
each leg to the current value of the error-correction term.  The term is only a
disparity between two quotes for one asset if the two quotes are drawn at the
same instant.  Hasbrouck (1995) makes the same requirement explicit and stronger,
since his information shares are read off the contemporaneous innovation
covariance directly.  So the question is not whether the algebra runs -- it
always runs -- but whether the daily observation pair is a snapshot of a
simultaneously observed system.

For KZAP/KAP.IL and AIRA/AIRA.IL it approximately is.  A1 shows the two books are
open together for a median of about five hours every trading day, with no day on
which they share nothing.  The daily close pair is a coarse sample of a system
that really does exist simultaneously, and the sampling error it introduces --
the foreign close is taken some three hours after the KASE close -- is a known
and bounded distortion, not a change of kind.

For KSPI/NASDAQ it is not, and A1 says so without qualification: on every one of
the sample days the two sessions share exactly zero minutes of clock time, and
the NASDAQ close of a given calendar label falls a median of about seven and a
half hours after the KASE close carrying the same label.  There is no instant at
which both legs are observed, so there is no contemporaneous price vector for
Gonzalo-Granger to decompose.  What the calendar-aligned VECM error-corrects on
is quantified in A4 and A8b.  A4 puts the covariance share of the NASDAQ daily
return that has arrived by the KASE close at about one tenth, against roughly two
thirds for each IOB line; A8b regresses the change in the calendar-aligned log
spread on the foreign move that arrived after the KASE close and recovers a slope
near minus one with by far the highest fit of the three pairs.  The
"disparity" is therefore not a mispricing that the KASE book declined to arbitrage
away; it is news the KASE book had not yet been shown.  Alpha then measures how
fast a market updates to information it did not have, which every market does and
which says nothing about which venue discovers price.

Two further symptoms confirm that the KSPI number is a property of the bookkeeping
rather than of the data.  First, pairing KASE session t with the NASDAQ close that
genuinely preceded it is exactly as defensible as pairing it with the same
calendar label -- neither is contemporaneous, both are one-sided -- and A8a shows
the weight moving between the two conventions by enough to change the qualitative
reading of which venue leads.  For the overlapping pairs the calendar alignment is
not a convention at all but a fact about the trading day, so their (larger)
movement under a deliberate one-day mis-alignment is evidence that alignment
matters, not evidence that their own weight is arbitrary.  Second, the KSPI
weight has no fixed point to converge on: the contemporaneous beta in A2 is
statistically indistinguishable from zero, which is the same statement in
regression form -- there is no same-instant co-movement to attribute.

CONCLUSION.  A Gonzalo-Granger weight -- and equally a Hasbrouck information
share -- is NOT meaningful for KSPI/NASDAQ.  The grid above prints the KSPI rows
only to document their instability and must not be read as a price-discovery
share; in particular, no comparison between a KSPI weight and the KZAP or AIRA
weights is admissible.  For that pair the defensible transmission statistics are
the sequential ones -- the lagged gap, drift and total of A3 and A5 -- which are
constructed so that the regressor is strictly in the KASE trader's information
set at the moment the KASE session opens.
""".strip("\n").split("\n")


@dataclass(frozen=True)
class Pair:
    kase: str          # KASE ticker
    foreign: str       # Yahoo symbol
    venue: str
    tz: str            # foreign exchange timezone
    close_time: str    # foreign regular-session close, local time
    overlapping: bool


PAIRS = [
    Pair("KSPI", "KSPI", "NASDAQ", "America/New_York", "16:00", False),
    Pair("KZAP", "KAP.IL", "LSE IOB", "Europe/London", "16:30", True),
    Pair("AIRA", "AIRA.IL", "LSE IOB", "Europe/London", "16:30", True),
]


def require_paths() -> None:
    missing = [p for p in (STORE, KASE_INTRADAY, NASDAQ_INTRADAY) if not p.exists()]
    if missing:
        sys.exit(
            "Required data directories are absent:\n  "
            + "\n  ".join(str(p) for p in missing)
            + "\nSet up the market-data store next to the repository, or edit STORE."
        )
    absent = [p for p in (FOREIGN_DAILY, FOREIGN_SPLIT) if not p.exists()]
    if absent:
        sys.exit("Foreign-leg tables are absent:\n  " + "\n  ".join(str(p) for p in absent)
                 + "\nThey are committed under data/derived/ and written by foreign_legs.py.")
    if not DAILY.exists():
        print(f"note: daily KASE store not found at {DAILY}; section A does not need it")


# KASE side


def load_kase_minutes(ticker: str) -> pd.DataFrame:
    d = KASE_INTRADAY / f"{ticker}.KZ"
    files = sorted(d.glob("*.parquet"))
    if not files:
        sys.exit(f"no parquet files under {d}")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    return df.sort_values("ts_utc").reset_index(drop=True)


def usd_minutes(ticker: str, fx: pd.DataFrame) -> pd.DataFrame:
    """One-minute KASE bars restricted to the session window and priced in USD."""
    df = load_kase_minutes(ticker)
    t = df["ts_almaty"].dt.time
    df = df[(t >= SESSION_OPEN) & (t <= SESSION_CLOSE)].copy()
    # backward as-of, so every rate was visible
    out = pd.merge_asof(
        df[["ts_utc", "ts_almaty", "close"]].sort_values("ts_utc"),
        fx[["ts_utc", "close"]].rename(columns={"close": "usdkzt"}).sort_values("ts_utc"),
        on="ts_utc",
        direction="backward",
    )
    out = out.dropna(subset=["usdkzt"])
    out["px_usd"] = out["close"] / out["usdkzt"]
    return out


def kase_sessions(ticker: str, fx: pd.DataFrame) -> pd.DataFrame:
    """Per-session open/close in USD, plus the opening gap and intraday drift."""
    m = usd_minutes(ticker, fx)
    m["date"] = m["ts_almaty"].dt.date
    g = m.groupby("date", sort=True)
    s = pd.DataFrame(
        {
            "open_ts": g["ts_utc"].first(),
            "close_ts": g["ts_utc"].last(),
            "open_usd": g["px_usd"].first(),
            "close_usd": g["px_usd"].last(),
            "n_bars": g.size(),
        }
    ).reset_index()
    s["date"] = pd.to_datetime(s["date"])
    s["prev_close_usd"] = s["close_usd"].shift(1)
    s["gap"] = s["open_usd"] / s["prev_close_usd"] - 1.0
    s["drift"] = s["close_usd"] / s["open_usd"] - 1.0
    s["session_ret"] = s["close_usd"] / s["prev_close_usd"] - 1.0
    return s


# Foreign side, from the committed tables and the local NASDAQ store


def load_foreign_daily() -> pd.DataFrame:
    df = pd.read_csv(FOREIGN_DAILY, parse_dates=["date"])
    df["close_ts"] = pd.to_datetime(df["close_ts"], utc=True)
    return df


def load_foreign_split() -> pd.DataFrame:
    df = pd.read_csv(FOREIGN_SPLIT, parse_dates=["date"])
    for col in ("close_ts", "split_ts"):
        df[col] = pd.to_datetime(df[col], utc=True)
    return df


def foreign_daily(pair: Pair, table: pd.DataFrame) -> pd.DataFrame:
    """Unadjusted daily closes with an explicit UTC close timestamp.

    Unadjusted rather than back-adjusted, because the KASE leg is unadjusted
    too; a dividend-adjusted foreign leg would put a deterministic wedge into
    the log-price pair that the cointegration tests would have to absorb.
    """
    df = table.loc[table["pair"] == pair.kase, ["date", "close_ts", "close"]]
    df = df.sort_values("date").reset_index(drop=True)
    df["fret"] = df["close"] / df["close"].shift(1) - 1.0
    df["prev_close"] = df["close"].shift(1)
    return df


def foreign_intraday(pair: Pair) -> tuple[pd.DataFrame, pd.Timedelta, str]:
    """The NASDAQ 1-minute bars from the local store, for the non-overlapping pair."""
    files = sorted((NASDAQ_INTRADAY / "KSPI.US").glob("*.parquet"))
    if not files:
        sys.exit(f"no NASDAQ intraday parquet under {NASDAQ_INTRADAY / 'KSPI.US'}")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df = df.sort_values("ts_utc").reset_index(drop=True)
    return df, pd.Timedelta(minutes=1), "local store, 1-minute, incl. pre/post"


def price_path(bars: pd.DataFrame, width: pd.Timedelta) -> pd.DataFrame:
    """Timestamped prices at bar boundaries, for look-ahead-free as-of pricing.

    A bar stamped t traded at t (its open) and at t+width (its close).  Asking
    the path for the price at some instant s therefore returns the last boundary
    weakly before s and never peeks inside a bar.  Where the close of one bar
    and the open of the next share a boundary, the close is kept: it is the
    last trade before that instant, while the next bar's open may have printed
    anywhere inside the bar that follows.  The sort is stable so the rule is the
    same on every platform.
    """
    a = pd.DataFrame({"ts": bars["ts_utc"], "px": bars["open"], "kind": 0})
    b = pd.DataFrame({"ts": bars["ts_utc"] + width, "px": bars["close"], "kind": 1})
    path = pd.concat([a, b]).dropna(subset=["ts", "px"]).sort_values(["ts", "kind"], kind="stable")
    return path.drop_duplicates("ts", keep="last")[["ts", "px"]].reset_index(drop=True)


def foreign_daily_from_intraday(pair: Pair, bars: pd.DataFrame) -> pd.DataFrame:
    """Daily closes taken from the same intraday source used for the split.

    Using the intraday source for both endpoints keeps the intraday split
    additive: the pre-close and post-close segments sum exactly to the day.
    """
    df = bars.copy()
    local = df["ts_utc"].dt.tz_convert(pair.tz)
    if pair.venue == "NASDAQ":
        t = local.dt.time
        df = df[(t >= pd.Timestamp("09:30").time()) & (t <= pd.Timestamp("16:00").time())]
        local = df["ts_utc"].dt.tz_convert(pair.tz)
    df = df.assign(date=pd.to_datetime(local.dt.date))
    g = df.groupby("date", sort=True)
    out = pd.DataFrame({"close_rs": g["close"].last(), "open_rs": g["open"].first(),
                        "n_bars_rs": g.size()}).reset_index()
    out["prev_close_rs"] = out["close_rs"].shift(1)
    return out


def fopen_series(dates, local_time, tz):
    """Foreign regular-session open, as a UTC timestamp series indexed like `dates`."""
    idx = pd.DatetimeIndex(dates)
    naive = pd.to_datetime(pd.Series(idx.strftime("%Y-%m-%d") + " " + local_time))
    return naive.dt.tz_localize(tz, nonexistent="shift_forward", ambiguous=True).dt.tz_convert("UTC")


# Regression helpers


def hac_ols(y: pd.Series, x: pd.Series):
    d = pd.concat([y.rename("y"), x.rename("x")], axis=1).dropna()
    if len(d) < 20:
        return None
    model = sm.OLS(d["y"], sm.add_constant(d["x"]))
    return model.fit(cov_type="HAC", cov_kwds={"maxlags": NW_LAGS})


def coef_row(res) -> dict:
    if res is None:
        return {"beta": np.nan, "se": np.nan, "t": np.nan, "p": np.nan, "r2": np.nan, "n": 0}
    return {
        "beta": res.params["x"],
        "se": res.bse["x"],
        "t": res.tvalues["x"],
        "p": res.pvalues["x"],
        "r2": res.rsquared,
        "n": int(res.nobs),
    }


def fmt(v, nd=4):
    if v is None or (isinstance(v, float) and not np.isfinite(v)):
        return "     .  "
    return f"{v:.{nd}f}"


def table(rows, cols, title, widths=None):
    print()
    print(title)
    print("-" * len(title))
    widths = widths or {}
    header = "  ".join(f"{c:>{widths.get(c, 12)}}" for c in cols)
    print(header)
    print("-" * len(header))
    for r in rows:
        print("  ".join(f"{str(r.get(c, '')):>{widths.get(c, 12)}}" for c in cols))


# Gonzalo-Granger


def gg_weight_kase(logp: pd.DataFrame, k_ar_diff: int, deterministic: str) -> float:
    """Gonzalo-Granger weight on the first column (the KASE leg).

    With alpha = (a1, a2)', the orthogonal complement is proportional to
    (-a2, a1)'; normalising it to sum to one gives the permanent-component
    weights.  A leg that does not error-correct (a_i = 0) takes the whole
    weight, which is the sense in which the weight measures price leadership.
    """
    model = VECM(logp.values, k_ar_diff=k_ar_diff, coint_rank=1, deterministic=deterministic)
    fit = model.fit()
    a1, a2 = float(fit.alpha[0, 0]), float(fit.alpha[1, 0])
    denom = a1 - a2
    if abs(denom) < 1e-12:
        return np.nan
    return -a2 / denom


def johansen_grid(logp: pd.DataFrame, label: str) -> pd.DataFrame:
    rows = []
    for det_order, vecm_det, det_name in DET_SPECS:
        for k in LAG_ORDERS:
            try:
                jres = coint_johansen(logp.values, det_order, k)
                trace0, trace1 = jres.lr1[0], jres.lr1[1]
                cv0, cv1 = jres.cvt[0, 1], jres.cvt[1, 1]  # 95% critical values
                rank = int(trace0 > cv0) + int(trace1 > cv1)
                w = gg_weight_kase(logp, k, vecm_det)
            except Exception as exc:  # pragma: no cover - numerical failure
                rows.append({"pair": label, "det": det_name, "k": k, "trace0": np.nan,
                             "cv0": np.nan, "trace1": np.nan, "cv1": np.nan,
                             "rank": -1, "gg_kase": np.nan, "note": str(exc)[:30]})
                continue
            rows.append({"pair": label, "det": det_name, "k": k, "trace0": trace0,
                         "cv0": cv0, "trace1": trace1, "cv1": cv1, "rank": rank,
                         "gg_kase": w, "note": ""})
    return pd.DataFrame(rows)


# Main


def main() -> None:
    require_paths()
    pd.set_option("display.width", 200)

    fx = load_kase_minutes("USDKZT_TOM")
    daily_table = load_foreign_daily()
    split_table = load_foreign_split()

    sessions, fdaily, fintra, fwidth, fsource, fdaily_rs, fsplit = {}, {}, {}, {}, {}, {}, {}
    for p in PAIRS:
        sessions[p.kase] = kase_sessions(p.kase, fx)
        fdaily[p.kase] = foreign_daily(p, daily_table)
        if p.overlapping:
            fsplit[p.kase] = split_table[split_table["pair"] == p.kase].copy()
            fsource[p.kase] = "Yahoo 60-minute, via foreign_split.csv"
        else:
            bars, width, src = foreign_intraday(p)
            fintra[p.kase], fwidth[p.kase], fsource[p.kase] = bars, width, src
            fdaily_rs[p.kase] = foreign_daily_from_intraday(p, bars)

    # ---- common window ---------------------------------------------------
    ends = []
    for p in PAIRS:
        s = sessions[p.kase]
        f = fdaily[p.kase]
        ends.append(min(s["date"].max(), f["date"].max()))
    window_end = min(ends)
    print("=" * 78)
    print("SECTION A -- OVERLAP COMPARISON")
    print("=" * 78)
    print(f"KASE store        : {KASE_INTRADAY}")
    print(f"NASDAQ store      : {NASDAQ_INTRADAY}")
    print(f"Foreign legs      : {FOREIGN_DAILY.relative_to(REPO)}, {FOREIGN_SPLIT.relative_to(REPO)}")
    print(f"Common window     : {WINDOW_START.date()} to {window_end.date()}")
    print(f"HAC               : Newey-West, {NW_LAGS} lags")
    print(f"KASE session      : {SESSION_OPEN}-{SESSION_CLOSE} Almaty, USD via USDKZT_TOM")

    rows = []
    for p in PAIRS:
        s = sessions[p.kase]
        s = s[(s["date"] >= WINDOW_START) & (s["date"] <= window_end)]
        f = fdaily[p.kase]
        f = f[(f["date"] >= WINDOW_START) & (f["date"] <= window_end)]
        rows.append({
            "pair": f"{p.kase}/{p.foreign}", "venue": p.venue,
            "overlap": "yes" if p.overlapping else "no",
            "kase_n": len(s), "kase_first": str(s["date"].min().date()),
            "kase_last": str(s["date"].max().date()),
            "fgn_n": len(f), "fgn_first": str(f["date"].min().date()),
            "fgn_last": str(f["date"].max().date()),
        })
    table(rows, ["pair", "venue", "overlap", "kase_n", "kase_first", "kase_last",
                 "fgn_n", "fgn_first", "fgn_last"],
          "A0. Sample coverage on the common window",
          {"pair": 12, "venue": 8, "overlap": 7, "kase_n": 7, "fgn_n": 6,
           "kase_first": 10, "kase_last": 10, "fgn_first": 10, "fgn_last": 10})

    # clock time the sessions share
    # The shared interval is [max(kase_open, foreign_open), min(kase_close,
    # foreign_close)].  Almaty moved from UTC+6 to UTC+5 on 2024-03-01 and both
    # foreign venues observe summer time, so this has to be computed date by
    # date through the timezone database rather than from a nominal offset.
    rows = []
    for p in PAIRS:
        s = sessions[p.kase]
        s = s[(s["date"] >= WINDOW_START) & (s["date"] <= window_end)].set_index("date")
        f = fdaily[p.kase].set_index("date")
        open_local = "09:30" if p.venue == "NASDAQ" else "08:00"
        common = s.index.intersection(f.index)
        fopen = fopen_series(common, open_local, p.tz)
        lo = np.maximum(s.loc[common, "open_ts"].values, fopen.values)
        hi = np.minimum(s.loc[common, "close_ts"].values, f.loc[common, "close_ts"].values)
        mins = np.clip((hi - lo) / np.timedelta64(1, "m"), 0, None)
        gap_h = (f.loc[common, "close_ts"].values
                 - s.loc[common, "close_ts"].values) / np.timedelta64(1, "h")
        rows.append({
            "pair": f"{p.kase}/{p.foreign}", "n_days": len(common),
            "median_min": fmt(float(np.median(mins)), 1),
            "min_min": fmt(float(np.min(mins)), 1),
            "max_min": fmt(float(np.max(mins)), 1),
            "days_zero": int((mins <= 0).sum()),
            "median_gap_h": fmt(float(np.median(gap_h)), 2),
        })
    table(rows, ["pair", "n_days", "median_min", "min_min", "max_min", "days_zero",
                 "median_gap_h"],
          "A1. Shared trading time per calendar day (minutes) and KASE-close to foreign-close gap",
          {"pair": 12, "n_days": 7, "median_min": 11, "min_min": 8, "max_min": 9,
           "days_zero": 10, "median_gap_h": 13})

    # ---- 1. contemporaneous, 2. lagged -----------------------------------
    contemp_rows, lagged_rows = [], []
    for p in PAIRS:
        s = sessions[p.kase]
        s = s[(s["date"] >= WINDOW_START) & (s["date"] <= window_end)].copy()
        f = fdaily[p.kase]
        f = f[(f["date"] >= WINDOW_START) & (f["date"] <= window_end)].copy()

        same = s.merge(f[["date", "fret"]], on="date", how="inner").dropna(
            subset=["session_ret", "fret"])
        res = hac_ols(same["session_ret"], same["fret"])
        contemp_rows.append({"pair": f"{p.kase}/{p.foreign}",
                             "overlap": "yes" if p.overlapping else "no",
                             **{k: (fmt(v) if isinstance(v, float) else v)
                                for k, v in coef_row(res).items()}})

        # last foreign close before the open
        lag = pd.merge_asof(
            s.sort_values("open_ts"),
            f[["close_ts", "fret", "date"]].rename(columns={"date": "fgn_date"})
             .dropna(subset=["fret"]).sort_values("close_ts"),
            left_on="open_ts", right_on="close_ts", direction="backward",
            allow_exact_matches=False, tolerance=MAX_STALE, suffixes=("", "_f"))
        lag = lag.dropna(subset=["fret"])
        lag["total"] = lag["gap"] + lag["drift"]

        r_gap = hac_ols(lag["gap"], lag["fret"])
        r_dft = hac_ols(lag["drift"], lag["fret"])
        r_tot = hac_ols(lag["total"], lag["fret"])
        row = {"pair": f"{p.kase}/{p.foreign}", "overlap": "yes" if p.overlapping else "no"}
        for tag, r in (("gap", r_gap), ("drift", r_dft), ("total", r_tot)):
            c = coef_row(r)
            row[f"b_{tag}"] = fmt(c["beta"])
            row[f"t_{tag}"] = fmt(c["t"], 2)
            row[f"r2_{tag}"] = fmt(c["r2"], 3)
        row["n"] = int(r_tot.nobs) if r_tot is not None else 0
        lagged_rows.append(row)

    table(contemp_rows, ["pair", "overlap", "beta", "se", "t", "p", "r2", "n"],
          "A2. Contemporaneous beta: KASE session return on same-calendar-day foreign return",
          {"pair": 12, "overlap": 7, "beta": 8, "se": 8, "t": 7, "p": 8, "r2": 7, "n": 5})

    table(lagged_rows, ["pair", "overlap", "b_gap", "t_gap", "r2_gap", "b_drift", "t_drift",
                        "r2_drift", "b_total", "t_total", "r2_total", "n"],
          "A3. Lagged betas on the last foreign return public before the KASE open "
          "(total = gap + drift)",
          {"pair": 12, "overlap": 7, "b_gap": 7, "t_gap": 6, "r2_gap": 6,
           "b_drift": 8, "t_drift": 8, "r2_drift": 8, "b_total": 8, "t_total": 8,
           "r2_total": 8, "n": 4})

    # 3. composition of foreign daily variance
    comp_rows, post_frames = [], {}
    for p in PAIRS:
        if p.overlapping:
            # the split against the KASE close was taken from the hourly bars by
            # foreign_legs.py, with the same KASE close timestamps
            split = fsplit[p.kase].dropna(subset=["prev_close_rs"])
            split = split[(split["date"] >= WINDOW_START) & (split["date"] <= window_end)]
            split = split.dropna(subset=["split_px", "close_rs", "prev_close_rs"]).copy()
            same_day = split["same_day"].astype(bool)
        else:
            bars = fintra[p.kase]
            width = fwidth[p.kase]
            rs = fdaily_rs[p.kase]
            s = sessions[p.kase][["date", "close_ts", "open_ts"]]
            d = rs.merge(s, on="date", how="inner").dropna(subset=["prev_close_rs"])
            d = d[(d["date"] >= WINDOW_START) & (d["date"] <= window_end)]

            path = price_path(bars, width)
            split = pd.merge_asof(d.sort_values("close_ts"), path.rename(
                columns={"ts": "split_ts", "px": "split_px"}).sort_values("split_ts"),
                left_on="close_ts", right_on="split_ts", direction="backward")
            # only counts if the print belongs to the current foreign day, else
            # the split price is the previous close and the segment is zero
            same_day = split["split_ts"].dt.tz_convert(p.tz).dt.date == split["date"].dt.date
            split["split_px"] = np.where(same_day, split["split_px"], split["prev_close_rs"])
            split = split.dropna(subset=["split_px", "close_rs", "prev_close_rs"])

        r_day = np.log(split["close_rs"] / split["prev_close_rs"])
        r_pre = np.log(split["split_px"] / split["prev_close_rs"])
        r_post = np.log(split["close_rs"] / split["split_px"])
        r_open_split = np.log(split["split_px"] / split["open_rs"])

        var_share = r_pre.var(ddof=1) / r_day.var(ddof=1)
        cov_share = np.cov(r_pre, r_day, ddof=1)[0, 1] / r_day.var(ddof=1)
        var_share_sess = r_open_split.var(ddof=1) / r_day.var(ddof=1)

        comp_rows.append({
            "pair": f"{p.kase}/{p.foreign}", "overlap": "yes" if p.overlapping else "no",
            "source": fsource[p.kase],
            "n": len(split),
            "first": str(split["date"].min().date()), "last": str(split["date"].max().date()),
            "days_prints": int(same_day.sum()),
            "var_share": fmt(var_share, 4),
            "cov_share": fmt(cov_share, 4),
            # one minus the column beside it
            "cov_after": fmt(1.0 - cov_share, 4),
            "sd_pre_bp": fmt(1e4 * r_pre.std(ddof=1), 1),
            "sd_post_bp": fmt(1e4 * r_post.std(ddof=1), 1),
            "sd_day_bp": fmt(1e4 * r_day.std(ddof=1), 1),
            "open2split": fmt(var_share_sess, 4),
        })

        split["r_post_simple"] = split["close_rs"] / split["split_px"] - 1.0
        split["r_day_simple"] = split["close_rs"] / split["prev_close_rs"] - 1.0
        post_frames[p.kase] = split[["date", "close_ts", "r_post_simple", "r_day_simple"]].copy()

    table(comp_rows, ["pair", "overlap", "source", "n", "first", "last", "days_prints",
                      "var_share", "cov_share", "cov_after", "sd_pre_bp", "sd_post_bp", "sd_day_bp",
                      "open2split"],
          "A4. Share of foreign daily log-return variance arriving before the KASE close",
          {"pair": 12, "overlap": 7, "source": 32, "n": 5, "first": 10, "last": 10,
           "days_prints": 11, "var_share": 9, "cov_share": 9, "cov_after": 9, "sd_pre_bp": 10,
           "sd_post_bp": 10, "sd_day_bp": 9, "open2split": 10})

    # non-overlapping pair: how many regular-session prints fall inside a KASE
    # session?
    p = PAIRS[0]
    bars = fintra[p.kase]
    loc = bars["ts_utc"].dt.tz_convert(p.tz)
    reg = bars[(loc.dt.time >= pd.Timestamp("09:30").time())
               & (loc.dt.time <= pd.Timestamp("16:00").time())]
    s = sessions[p.kase]
    s = s[(s["date"] >= WINDOW_START) & (s["date"] <= window_end)]
    iv = pd.IntervalIndex.from_arrays(s["open_ts"], s["close_ts"], closed="both")
    inside_reg = sum(iv.contains(t).any() for t in reg["ts_utc"])
    pre = bars[loc.dt.time < pd.Timestamp("09:30").time()]
    inside_pre = sum(iv.contains(t).any() for t in pre["ts_utc"])
    print()
    print("A4b. Verification that the KSPI pair really is non-overlapping")
    print("-" * 62)
    print(f"NASDAQ regular-session bars inside a KASE session window : {inside_reg}"
          f" of {len(reg)}")
    print(f"NASDAQ pre-market bars inside a KASE session window      : {inside_pre}"
          f" of {len(pre)}")
    print("Regular sessions are disjoint by the clock, so that share is zero by")
    print("construction; the pre-market prints are what make the measure nonzero.")

    # ---- 4. conditional test ---------------------------------------------
    cond_rows, stacked = [], []
    for p in PAIRS:
        s = sessions[p.kase]
        s = s[(s["date"] >= WINDOW_START) & (s["date"] <= window_end)].copy()
        post = post_frames[p.kase].dropna(subset=["r_post_simple"])
        m = pd.merge_asof(s.sort_values("open_ts"),
                          post.rename(columns={"close_ts": "fgn_close_ts",
                                               "date": "fgn_date"}).sort_values("fgn_close_ts"),
                          left_on="open_ts", right_on="fgn_close_ts",
                          direction="backward", allow_exact_matches=False,
                          tolerance=MAX_STALE)
        m = m.dropna(subset=["r_post_simple", "gap", "drift"])
        m["total"] = m["gap"] + m["drift"]
        row = {"pair": f"{p.kase}/{p.foreign}", "overlap": "yes" if p.overlapping else "no"}
        for tag in ("gap", "drift", "total"):
            c = coef_row(hac_ols(m[tag], m["r_post_simple"]))
            row[f"b_{tag}"] = fmt(c["beta"])
            row[f"t_{tag}"] = fmt(c["t"], 2)
        row["n"] = len(m)
        row["first"] = str(m["date"].min().date())
        row["last"] = str(m["date"].max().date())
        cond_rows.append(row)
        st = m[["date", "total", "r_post_simple"]].copy()
        st["pair"] = p.kase
        st["overlap"] = int(p.overlapping)
        stacked.append(st)

    table(cond_rows, ["pair", "overlap", "b_gap", "t_gap", "b_drift", "t_drift",
                      "b_total", "t_total", "n", "first", "last"],
          "A5. Conditional test: next KASE session on foreign news arriving AFTER the KASE close",
          {"pair": 12, "overlap": 7, "b_gap": 7, "t_gap": 6, "b_drift": 8, "t_drift": 8,
           "b_total": 8, "t_total": 8, "n": 4, "first": 10, "last": 10})

    st = pd.concat(stacked, ignore_index=True)
    common_dates = set.intersection(*[set(x["date"]) for x in stacked])
    st = st[st["date"].isin(common_dates)].sort_values(["date", "pair"]).reset_index(drop=True)
    print()
    print(f"A6. Overlapping minus non-overlapping difference in the next-day total")
    print("-" * 70)
    print(f"Balanced panel: {len(common_dates)} dates common to all three pairs, "
          f"{len(st)} pair-days, {min(common_dates).date()} to {max(common_dates).date()}")

    tvar = st["date"].rank(method="dense").astype(int).values
    X = pd.DataFrame({
        "const": 1.0,
        "overlap": st["overlap"].astype(float),
        "x": st["r_post_simple"].values,
        "x_overlap": st["r_post_simple"].values * st["overlap"].values,
    })
    fit = sm.OLS(st["total"].values, X).fit(
        cov_type="hac-groupsum", cov_kwds={"time": tvar, "maxlags": NW_LAGS})
    d = fit.params["x_overlap"]
    se = fit.bse["x_overlap"]
    ci = fit.conf_int().loc["x_overlap"]
    print(f"beta (non-overlapping, KSPI)         : {fit.params['x']:.4f}")
    print(f"difference (overlapping - KSPI)      : {d:.4f}")
    print(f"  standard error (Driscoll-Kraay, {NW_LAGS}) : {se:.4f}")
    print(f"  t-statistic                        : {fit.tvalues['x_overlap']:.3f}")
    print(f"  p-value                            : {fit.pvalues['x_overlap']:.4f}")
    print(f"  95% confidence interval            : [{ci[0]:.4f}, {ci[1]:.4f}]")
    print(f"  implied overlapping beta           : {fit.params['x'] + d:.4f}")

    # per-pair contrasts, fully interacted stack
    dummies = pd.get_dummies(st["pair"]).astype(float)
    Xf = pd.concat([dummies.add_prefix("a_"),
                    dummies.mul(st["r_post_simple"].values, axis=0).add_prefix("b_")], axis=1)
    fit2 = sm.OLS(st["total"].values, Xf).fit(
        cov_type="hac-groupsum", cov_kwds={"time": tvar, "maxlags": NW_LAGS})
    rows = []
    for p in PAIRS:
        rows.append({"pair": p.kase, "beta_total": fmt(fit2.params[f"b_{p.kase}"]),
                     "se": fmt(fit2.bse[f"b_{p.kase}"]),
                     "t": fmt(fit2.tvalues[f"b_{p.kase}"], 2)})
    for k in ("KZAP", "AIRA"):
        r = np.zeros(len(Xf.columns))
        r[list(Xf.columns).index(f"b_{k}")] = 1.0
        r[list(Xf.columns).index("b_KSPI")] = -1.0
        tt = fit2.t_test(r)
        lo, hi = tt.conf_int()[0]
        rows.append({"pair": f"{k} - KSPI",
                     "beta_total": fmt(float(np.ravel(tt.effect)[0])),
                     "se": fmt(float(np.ravel(tt.sd)[0])),
                     "t": fmt(float(np.ravel(tt.tvalue)[0]), 2),
                     "p": fmt(float(np.ravel(tt.pvalue)[0]), 4),
                     "ci_lo": fmt(lo), "ci_hi": fmt(hi)})
    table(rows, ["pair", "beta_total", "se", "t", "p", "ci_lo", "ci_hi"],
          "A6b. Pair-specific next-day totals on post-KASE-close news, and contrasts",
          {"pair": 12, "beta_total": 10, "se": 8, "t": 7, "p": 8, "ci_lo": 8, "ci_hi": 8})
    # two contrasts are tested, so the Holm step-down adjustment is printed
    raw = {r["pair"]: float(r["p"]) for r in rows if " - " in r["pair"]}
    ordered = sorted(raw.items(), key=lambda kv: kv[1])
    holm, running = {}, 0.0
    for i, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, p * (len(ordered) - i)))
        holm[name] = running
    print("Holm-adjusted p for the two pair contrasts: "
          + ", ".join(f"{k} {holm[k]:.4f}" for k, _ in raw.items()))
    print("All HAC and Driscoll-Kraay t-statistics in this script are asymptotic: no small-sample")
    print("correction, normal reference distribution (statsmodels defaults).")

    # written out for the figure; pooled row is the A6 interaction, pair rows
    # the combinations above
    contrasts = [{"contrast": "pooled overlapping - KSPI", "estimate": float(d),
                  "se": float(se), "t": float(fit.tvalues["x_overlap"]),
                  "p": float(fit.pvalues["x_overlap"]),
                  "ci_lo": float(ci[0]), "ci_hi": float(ci[1])}]
    for k in ("KZAP", "AIRA"):
        r = np.zeros(len(Xf.columns))
        r[list(Xf.columns).index(f"b_{k}")] = 1.0
        r[list(Xf.columns).index("b_KSPI")] = -1.0
        tt = fit2.t_test(r)
        lo, hi = tt.conf_int()[0]
        contrasts.append({"contrast": f"{k} - KSPI",
                          "estimate": float(np.ravel(tt.effect)[0]),
                          "se": float(np.ravel(tt.sd)[0]),
                          "t": float(np.ravel(tt.tvalue)[0]),
                          "p": float(np.ravel(tt.pvalue)[0]),
                          "ci_lo": float(lo), "ci_hi": float(hi)})
    dest = REPO / "data" / "derived" / "overlap_contrasts.csv"
    dest.parent.mkdir(parents=True, exist_ok=True)
    # ten digits: a full repr differs between numpy builds and would diff
    # everywhere
    pd.DataFrame(contrasts).to_csv(dest, index=False, float_format="%.10g")
    print(f"\nWrote data/derived/overlap_contrasts.csv ({len(contrasts)} contrasts)")

    # ---- 5. cointegration and Gonzalo-Granger ----------------------------
    print()
    print("=" * 78)
    print("A7. Johansen cointegration and Gonzalo-Granger weights")
    print("=" * 78)
    print("Alignment 'calendar': KASE session date t paired with foreign close of date t.")
    print("Alignment 'preceding': KASE session t paired with the last foreign close that")
    print("strictly preceded its open -- the only alignment under which both legs of a")
    print("non-overlapping pair share an information set.")

    all_grids = []
    for p in PAIRS:
        s = sessions[p.kase]
        s = s[(s["date"] >= WINDOW_START) & (s["date"] <= window_end)].copy()
        f = fdaily[p.kase]
        f = f[(f["date"] >= WINDOW_START) & (f["date"] <= window_end)].copy()

        cal = s.merge(f[["date", "close"]], on="date", how="inner").dropna(
            subset=["close_usd", "close"])
        logp_cal = pd.DataFrame({"kase": np.log(cal["close_usd"].values),
                                 "fgn": np.log(cal["close"].values)})

        pre = pd.merge_asof(s.sort_values("open_ts"),
                            f[["close_ts", "close"]].rename(columns={"close": "fclose"})
                             .sort_values("close_ts"),
                            left_on="open_ts", right_on="close_ts",
                            direction="backward", allow_exact_matches=False,
                            tolerance=MAX_STALE)
        pre = pre.dropna(subset=["close_usd", "fclose"])
        logp_pre = pd.DataFrame({"kase": np.log(pre["close_usd"].values),
                                 "fgn": np.log(pre["fclose"].values)})

        for align, lp in (("calendar", logp_cal), ("preceding", logp_pre)):
            g = johansen_grid(lp, f"{p.kase}/{p.foreign}")
            g["align"] = align
            g["n"] = len(lp)
            g["overlap"] = "yes" if p.overlapping else "no"
            all_grids.append(g)

    grid = pd.concat(all_grids, ignore_index=True)
    rows = []
    for _, r in grid.iterrows():
        rows.append({"pair": r["pair"], "align": r["align"], "det": r["det"], "k": r["k"],
                     "n": r["n"],
                     "trace_r0": fmt(r["trace0"], 2), "cv95_r0": fmt(r["cv0"], 2),
                     "trace_r1": fmt(r["trace1"], 2), "cv95_r1": fmt(r["cv1"], 2),
                     "rank": r["rank"], "gg_kase": fmt(r["gg_kase"], 4)})
    table(rows, ["pair", "align", "det", "k", "n", "trace_r0", "cv95_r0", "trace_r1",
                 "cv95_r1", "rank", "gg_kase"],
          "A7a. Full specification grid (trace test at 5%, GG weight on the KASE leg)",
          {"pair": 12, "align": 10, "det": 20, "k": 3, "n": 5, "trace_r0": 9,
           "cv95_r0": 8, "trace_r1": 9, "cv95_r1": 8, "rank": 5, "gg_kase": 8})

    rows = []
    for (pair, align), g in grid.groupby(["pair", "align"], sort=False):
        coint = g[g["rank"] == 1]
        rows.append({
            "pair": pair, "align": align,
            "specs": len(g), "rank1": len(coint),
            "gg_min_all": fmt(g["gg_kase"].min()), "gg_max_all": fmt(g["gg_kase"].max()),
            "gg_med_all": fmt(g["gg_kase"].median()),
            "gg_min_r1": fmt(coint["gg_kase"].min()) if len(coint) else "     .  ",
            "gg_max_r1": fmt(coint["gg_kase"].max()) if len(coint) else "     .  ",
            "gg_med_r1": fmt(coint["gg_kase"].median()) if len(coint) else "     .  ",
        })
    table(rows, ["pair", "align", "specs", "rank1", "gg_min_all", "gg_max_all", "gg_med_all",
                 "gg_min_r1", "gg_max_r1", "gg_med_r1"],
          "A7b. Specification range of the Gonzalo-Granger weight on the KASE leg",
          {"pair": 12, "align": 10, "specs": 6, "rank1": 6, "gg_min_all": 10,
           "gg_max_all": 10, "gg_med_all": 10, "gg_min_r1": 9, "gg_max_r1": 9,
           "gg_med_r1": 9})
    n_rank2 = int((grid["rank"] == 2).sum())
    n_rank0 = int((grid["rank"] == 0).sum())
    print(f"Specifications with rank 0 (no cointegration): {n_rank0} of {len(grid)}")
    print(f"Specifications with rank 2 (both legs test stationary): {n_rank2} of {len(grid)}")
    print("Rank 2 means the trace test rejects a unit root in each log price separately, so")
    print("the system has no common stochastic trend and a common-factor weight is not")
    print("defined in the usual sense.  The 'r1' columns restrict to specifications where the")
    print("trace test actually lands on exactly one cointegrating vector; the 'all' columns")
    print("impose rank 1 regardless, which is what the GG weight is computed under.")

    # ---- the scope question ---------------------------------------------
    print()
    print("=" * 78)
    print("A8. Is a Gonzalo-Granger weight meaningful for a non-overlapping pair?")
    print("=" * 78)
    swing = []
    for (pair, ), g in grid.groupby(["pair"], sort=False):
        cal = g[g["align"] == "calendar"]["gg_kase"]
        pre = g[g["align"] == "preceding"]["gg_kase"]
        swing.append({"pair": pair,
                      "gg_calendar_med": fmt(cal.median()),
                      "gg_preceding_med": fmt(pre.median()),
                      "abs_shift": fmt(abs(cal.median() - pre.median())),
                      "range_calendar": fmt(cal.max() - cal.min()),
                      "range_preceding": fmt(pre.max() - pre.min())})
    table(swing, ["pair", "gg_calendar_med", "gg_preceding_med", "abs_shift",
                  "range_calendar", "range_preceding"],
          "A8a. Sensitivity of the GG weight to the calendar-alignment convention",
          {"pair": 12, "gg_calendar_med": 15, "gg_preceding_med": 16, "abs_shift": 9,
           "range_calendar": 14, "range_preceding": 15})

    # what the calendar-aligned error-correction term is made of. The VECM
    # corrects s_t = log(KASE_usd_t) - log(foreign_t), so d(s_t) is the KASE
    # session return minus the foreign daily return. Where much of that
    # arrived after the KASE close, d(s_t) is not a mispricing the book left
    # open but news it had not been shown.
    rows = []
    for p in PAIRS:
        s = sessions[p.kase]
        s = s[(s["date"] >= WINDOW_START) & (s["date"] <= window_end)].copy()
        f = fdaily[p.kase][["date", "close"]]
        post = post_frames[p.kase][["date", "r_post_simple"]]
        m = s.merge(f, on="date").merge(post, on="date").dropna(
            subset=["close_usd", "close", "r_post_simple"])
        m["spread"] = np.log(m["close_usd"]) - np.log(m["close"])
        m["dspread"] = m["spread"].diff()
        m["r_post_log"] = np.log1p(m["r_post_simple"])
        res = hac_ols(m["dspread"], m["r_post_log"])
        c = coef_row(res)
        rows.append({"pair": f"{p.kase}/{p.foreign}",
                     "overlap": "yes" if p.overlapping else "no",
                     "beta": fmt(c["beta"]), "t": fmt(c["t"], 2),
                     "r2": fmt(c["r2"], 4), "n": c["n"],
                     "sd_dspread_bp": fmt(1e4 * m["dspread"].std(ddof=1), 1),
                     "sd_rpost_bp": fmt(1e4 * m["r_post_log"].std(ddof=1), 1)})
    table(rows, ["pair", "overlap", "beta", "t", "r2", "n", "sd_dspread_bp", "sd_rpost_bp"],
          "A8b. Change in the calendar-aligned log spread regressed on the foreign return "
          "arriving after the KASE close",
          {"pair": 12, "overlap": 7, "beta": 9, "t": 8, "r2": 8, "n": 5,
           "sd_dspread_bp": 13, "sd_rpost_bp": 11})

    print()
    for line in ANSWER_LINES:
        print(line)


if __name__ == "__main__":
    main()
