#!/usr/bin/env python3
"""
Draw the figures into figures/paper/. Computes nothing.

Every plotted series comes from data/derived/; the only numbers here are
styling. analysis/check_figure_literals.py enforces that.

  measurement_point_curve.csv  transmission/hac_inference.py
  entry_delay.csv              transmission/entry_timing.py
  overlap_contrasts.csv        transmission/overlap_comparison.py
  venue_liquidity.csv          transmission/venue_liquidity.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
FIGS = ROOT / "figures" / "paper"

CURVE = DERIVED / "measurement_point_curve.csv"
ENTRY = DERIVED / "entry_delay.csv"
CONTRASTS = DERIVED / "overlap_contrasts.csv"
VENUE = DERIVED / "venue_liquidity.csv"

plt.rcParams.update({
    "figure.dpi": 130, "savefig.dpi": 130, "font.size": 9,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
})
INK, ACCENT, MUTE = "#222222", "#B03A2E", "#8899AA"

# layout numbers, so a number in a plot call is data or a name
SIG_LEVEL = 0.05          # colours a contrast
WHISKER_HALF = 0.08       # interval cap half-height, row units
SPAN_PAD = 1.45           # x-limit as a multiple of the widest bound
RATIO_LABEL_X = 1.02      # annotation column, axes fraction
ROW_LABEL_X = -0.02       # row label column, axes fraction


def need(path, script):
    """Read a derived input, or name the script that writes it."""
    if not path.exists():
        print(f"   {path.relative_to(ROOT)} not found; run {script} first")
        return None
    return pd.read_csv(path)


def fig_venue_liquidity():
    """KASE against NASDAQ in KSPI, over common sessions."""
    v = need(VENUE, "analysis/transmission/venue_liquidity.py")
    if v is None:
        return False
    v = v.set_index("measure")
    turn = v.loc["turnover"]
    sessions = int(turn["sessions"])

    fig, (axl, axr) = plt.subplots(1, 2, figsize=(7.6, 3.2),
                                   gridspec_kw={"width_ratios": [1.0, 1.25]})

    # dumbbell, not bars: on a log axis bar length is set by the floor, so
    # 293-fold can look like threefold
    lo, hi = turn["kase"], turn["nasdaq"]
    axl.plot([lo, hi], [0, 0], color=MUTE, lw=1.4, zorder=1)
    axl.plot([lo], [0], marker="o", ms=9, color=ACCENT, zorder=3)
    axl.plot([hi], [0], marker="o", ms=9, color=INK, zorder=3)
    axl.set_xscale("log")
    axl.set_xlim(lo / 6, hi * 6)
    axl.set_ylim(-1, 1)
    axl.set_yticks([])
    axl.spines["left"].set_visible(False)
    axl.grid(axis="y", visible=False)
    axl.annotate(f"KASE\n${lo:,.0f}", xy=(lo, 0), xytext=(0, -14),
                 textcoords="offset points", ha="center", va="top",
                 fontsize=8, color=ACCENT)
    axl.annotate(f"NASDAQ\n${hi:,.0f}", xy=(hi, 0), xytext=(0, -14),
                 textcoords="offset points", ha="center", va="top",
                 fontsize=8, color=INK)
    axl.annotate(f"{turn['ratio']:.0f}$\\times$",
                 xy=(np.sqrt(lo * hi), 0), xytext=(0, 12),
                 textcoords="offset points", ha="center", fontsize=12, color=INK)
    axl.set_xlabel("median session turnover, USD (log scale)")
    axl.set_title("Turnover in KSPI, same stock", loc="left", fontsize=10)

    rows = ["minutes with a trade", "shares traded", "turnover"]
    ratios = [v.loc[r, "ratio"] for r in rows]
    y = np.arange(len(rows))[::-1]
    # dots, not bars
    axr.axvline(1.0, color=INK, lw=1.0, ls="--", zorder=1)
    for yy, r, col in zip(y, ratios, [MUTE, INK, ACCENT]):
        axr.plot([r], [yy], marker="o", ms=9, color=col, zorder=3)
        axr.annotate(f"{r:.1f}$\\times$" if r < 10 else f"{r:.0f}$\\times$",
                     xy=(r, yy), xytext=(9, 0), textcoords="offset points",
                     va="center", fontsize=8, color=col)
    axr.set_xscale("log")
    axr.set_yticks(y)
    axr.set_yticklabels(rows, fontsize=8)
    axr.set_xlabel("NASDAQ / KASE, median session (log scale)")
    axr.set_xlim(0.7, max(ratios) * 5)
    axr.set_ylim(-0.7, len(rows) - 0.3)
    axr.annotate("parity", xy=(1.0, len(rows) - 0.55), xytext=(4, 0),
                 textcoords="offset points", fontsize=7.5, color=INK)
    axr.set_title("Thin in money, not in minutes", loc="left", fontsize=10)
    axr.grid(axis="y", visible=False)

    fig.suptitle(f"KSPI on both venues, {sessions} common sessions", x=0.01, ha="left",
                 fontsize=9, color=MUTE, y=1.02)
    fig.tight_layout()
    fig.savefig(FIGS / "venue-liquidity.png", bbox_inches="tight")
    plt.close(fig)
    return True


def fig_entry_delay():
    """Return and hit rate against entry delay, exit fixed at the close."""
    e = need(ENTRY, "analysis/transmission/entry_timing.py")
    if e is None:
        return False
    # the 13:30 entry has no delay in minutes, so it is off the axis
    e = e[e["delay_minutes"].notna()].sort_values("delay_minutes")
    n = int(e["n"].iloc[0])

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    x = np.arange(len(e))
    ax.bar(x, e["mean_pct"].values, width=0.55, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels([f"+{int(d)}" if d else "first\nprint" for d in e["delay_minutes"]])
    ax.set_xlabel("minutes after the first traded print")
    ax.set_ylabel("mean return to the close (%)", color=INK)
    ax2 = ax.twinx()
    ax2.plot(x, e["hit_pct"].values, marker="o", ms=4, lw=1.3, color=ACCENT)
    ax2.axhline(50, color=ACCENT, lw=0.8, ls=":")
    ax2.set_ylabel("hit rate (%)", color=ACCENT)
    ax2.set_ylim(40, 90)
    ax2.grid(False)
    ax.set_title(f"Entry delay against captured drift, sessions with a NASDAQ move "
                 f"of at least 2%, n={n}", loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "entry-delay.png")
    plt.close(fig)
    return True


def fig_measurement_point():
    """Gap and drift betas against the price called the session open."""
    c = need(CURVE, "analysis/transmission/hac_inference.py")
    if c is None:
        return False
    c = c.sort_values("minute")
    n = int(c["n"].iloc[0])

    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    x = np.arange(len(c))
    ax.plot(x, c["beta_gap"].values, marker="o", ms=4, lw=1.3, color=INK,
            label="opening gap")
    ax.plot(x, c["beta_drift"].values, marker="s", ms=4, lw=1.3, color=ACCENT,
            label="intraday drift")
    ax.set_xticks(x)
    ax.set_xticklabels(c["label"].tolist())
    ax.axvline(0, color=MUTE, lw=1.0, ls="--")
    ax.annotate("auction print", xy=(0, c["beta_gap"].iloc[0]), xytext=(8, 10),
                textcoords="offset points", fontsize=8, color=MUTE)
    ax.set_xlabel("price used as the session open (Almaty)")
    ax.set_ylabel("beta on the prior NASDAQ move")
    ax.set_ylim(0, c["beta_gap"].max() * 1.15)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title(f"Transmission split against the choice of opening price, n={n}",
                 loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIGS / "measurement-point-curve.png")
    plt.close(fig)
    return True


def fig_overlap_contrasts():
    """Pair-specific and pooled overlap contrasts with 95% intervals.

    The figure this replaced showed the three pairs side by side and read as
    indistinguishable. The pooled contrast sits on zero because KZAP and AIRA
    are individually significant with opposite signs, which is identification
    power across a cross-section of size two, not an absent overlap effect.
    """
    c = need(CONTRASTS, "analysis/transmission/overlap_comparison.py")
    if c is None:
        return False
    c = c.set_index("contrast")
    order = ["KZAP - KSPI", "AIRA - KSPI", "pooled overlapping - KSPI"]
    labels = ["KZAP $-$ KSPI\noverlapping, LSE-IOB",
              "AIRA $-$ KSPI\noverlapping, LSE-IOB",
              "pooled overlapping\n$-$ KSPI"]

    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    for i, (key, lab) in enumerate(zip(order, labels)):
        r = c.loc[key]
        y = len(order) - 1 - i
        col = ACCENT if r["p"] < SIG_LEVEL else MUTE
        ax.plot([r["ci_lo"], r["ci_hi"]], [y, y], color=col, lw=1.6,
                solid_capstyle="butt", zorder=2)
        for b in (r["ci_lo"], r["ci_hi"]):
            ax.plot([b, b], [y - WHISKER_HALF, y + WHISKER_HALF], color=col, lw=1.6, zorder=2)
        ax.plot([r["estimate"]], [y], marker="o", ms=6, color=col,
                markeredgecolor="white", markeredgewidth=0.8, zorder=3)
        # fixed column; at the bound the AIRA label crossed zero
        ax.text(RATIO_LABEL_X, y, f"{r['estimate']:+.4f}   p {r['p']:.3f}",
                transform=ax.get_yaxis_transform(), va="center", fontsize=8, color=col)
        ax.text(ROW_LABEL_X, y, lab, transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=8)

    ax.axvline(0, color=INK, lw=1.0, ls="--", zorder=1)
    ax.set_yticks([])
    ax.set_ylim(-0.6, len(order) - 0.4)
    ax.set_xlabel("difference in next-day pass-through against the non-overlapping pair")
    span = max(c["ci_hi"].abs().max(), c["ci_lo"].abs().max()) * SPAN_PAD
    ax.set_xlim(-span, span)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", visible=False)
    ax.set_title("The pooled null is an average of two significant effects of opposite sign",
                 loc="left", fontsize=10)
    fig.subplots_adjust(left=0.28)
    fig.savefig(FIGS / "overlap-contrasts.png", bbox_inches="tight")
    plt.close(fig)
    return True


def main():
    FIGS.mkdir(parents=True, exist_ok=True)
    figures = [("venue-liquidity", fig_venue_liquidity),
               ("entry-delay", fig_entry_delay),
               ("measurement-point-curve", fig_measurement_point),
               ("overlap-contrasts", fig_overlap_contrasts)]
    drawn = 0
    for name, fn in figures:
        if fn():
            drawn += 1
            print(f"wrote figures/paper/{name}.png")
    print(f"{drawn} of {len(figures)} figures drawn")


if __name__ == "__main__":
    main()
