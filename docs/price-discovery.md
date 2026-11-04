# Overnight transmission into a thin venue: dual-listed Kazakh equities on KASE

## Abstract

On the 174 sessions where NASDAQ moved at least 2%, Kaspi.kz (KSPI) on the Kazakhstan Stock
Exchange (KASE) absorbs 81.1% of its full-session drift within thirty minutes of the first traded
print: the return to the close, in the direction of the NASDAQ move, is +0.856% from the first
print, +0.380% from five minutes later and +0.173% from thirty. That is the speed Thorp and
Milunovich (2006) report for New York, up to 30 minutes, on a venue with one 293rd of NASDAQ's
dollar turnover in the stock. The two regular sessions share no clock time, so every KASE session opens after a complete
NASDAQ session has repriced the stock; over 591 sessions from January 2024 to August 2026 the
opening gap carries 0.2019 of the prior NASDAQ close-to-close move and the intraday drift 0.2718
(Newey-West HAC(5) t 10.50 and 12.49), 0.4741 in total. NASDAQ pre-market prints that fall inside
the KASE session do not explain the drift away: conditioning on the last visible print raises the
lagged coefficient. Two co-listings that do overlap their foreign venue, KZAP and AIRA on the LSE
International Order Book, differ sharply from KSPI in how much of the foreign day has arrived by
the KASE close (covariance shares 0.6686 and 0.7183 against 0.0996) but not identifiably in
absorption rate: the pooled contrast on next-day pass-through is +0.0334 with a 95% interval of
[-0.1405, +0.2073], and the two pair-specific contrasts are opposite in sign. The drift is not
capturable without setting the opening print: at a five-minute entry it falls short of a round
trip of 0.41% (Roll) or 0.64% (Corwin-Schultz).

## 1. Introduction

A stock listed on a deep foreign venue and a thin local one must, at some point in the local
session, absorb what the foreign venue decided about it overnight. How long that takes is a
property of the venue. On developed markets the answer is minutes: Patell and Wolfson (1984) see
trading-rule returns around news dissipate within five to ten minutes on the NYSE, Chordia, Roll
and Subrahmanyam (2005) put convergence to efficiency at 5 to 15 minutes for large NYSE names, and
for overnight foreign news Thorp and Milunovich (2006) report that New York takes up to 30 minutes
after the open, Tokyo about 90 and London about 120. Section 4 measures the same quantity on a
venue that turns over one
293rd of the foreign venue's dollar volume in the same stock.

KSPI's two regular sessions never run together: NASDAQ trades 09:30 to 16:00 New York, KASE 11:30
to 17:30 Almaty, and Section 2.1 counts the shared minutes rather than assuming them. The count is
zero on every one of 602 days. What is not zero is information overlap: NASDAQ pre-market prints
fall inside the KASE session on 293 of the 535 sessions the local NASDAQ store covers, and Section
7 conditions on them. Two other KASE listings, Kazatomprom (KZAP) and Air Astana (AIRA), trade
against the LSE International Order Book, which overlaps the KASE session by a median of 314 and
325 minutes. The three pairs share a local venue, a settlement currency and a commission schedule,
which removes most of the cross-country heterogeneity that limits comparisons of this kind.

The regression behind the absorption measurement is not new. Becker, Finnerty and Gupta (1990)
regress the Tokyo session on the prior US move, find partial adjustment at the Tokyo open with
residual drift over the session, and conclude the drift is not tradeable after costs; Sections 5
and 11 reach the same design and the same conclusion. Hamao, Masulis and Ng (1990), Eun and Shim
(1989) and Lin, Engle and Ito (1994) establish the spillover pattern across non-synchronous
venues, Hou and Moskowitz (2005) formalise the split between gap and drift as price delay, Hong and
Stein (1999) supply a mechanism of gradual diffusion, and Rapach, Strauss and Zhou (2013) show
lagged US returns predicting other countries' index returns. What this setting adds is resolution
and a contrast: minute-level trade data on a market that trades KSPI in a median of 124 minutes
of a 370-minute session, and three co-listings that differ in overlap while sharing everything
else local.

The non-overlapping case is the one the cross-listing literature on contemporaneous price
discovery does not cover. Hasbrouck (1995) information shares need the two price series at the
same instants, which the KSPI pair lacks by construction. Gonzalo and Granger (1995) common-factor
weights can be computed for all three pairs; Section 8.5 shows that for the non-overlapping pair
they depend on how the two daily series are aligned, which is the same missing input in another
form. The relevant prior work is therefore the spillover literature on non-synchronous markets
(Engle, Ito and Lin 1990) and the around-the-clock models that treat the foreign leg as unobserved
while the local venue trades (Menkveld, Koopman and Lucas 2007), rather than the overlapping-hours
studies (Werner and Kleidon 1996; Grammig, Melvin and Schlag 2005; Karolyi 2006). Craig, Dravid and
Richardson (1995) bound the whole exercise: apparent partial adjustment to a stale foreign close
can vanish once the regression admits foreign instruments that trade during the local session.
Section 7 runs that test.

A verification of this repository on 2026-10-12 and a later, stricter re-analysis of
the same market (2026-10-16), both unpublished, changed this document: the spread
convention in Section 2.3, the regressor alignment in Section 5.1, the threshold selection in
Section 10, and the year-end construction in Section 9. Where a result of the re-analysis bears on
one here, the text states it in place; neither document is one a reader can open.

## 2. Institutional setting

### 2.1 Session overlap, measured

KASE sessions run 11:30 to 17:30 Almaty with an opening auction that prints at 11:29. Overlap with
the foreign venue is computed from the bar store, date by date through the timezone database,
because Almaty moved from UTC+6 to UTC+5 on 2024-03-01 and both foreign venues observe summer
time.

| pair | days | median shared minutes | days with zero | median KASE-close to foreign-close gap |
|---|---|---|---|---|
| KSPI / NASDAQ | 602 | 0 | 602 | 7.58 h |
| KZAP / LSE-IOB | 607 | 314 | 0 | 3.27 h |
| AIRA / LSE-IOB | 600 | 325 | 0 | 3.08 h |

Produced by `analysis/transmission/overlap_comparison.py`. The IOB overlaps range from 104 to 329
minutes for KZAP and 106 to 329 for AIRA.

0 of 116,225 NASDAQ regular-session bars fall inside a KASE session window. NASDAQ pre-market
trading opens at 04:00 New York, which falls inside the back half of the KASE session for part of
the year: 1,286 of 2,855 pre-market bars fall inside a KASE session, on 293 of the 508 days both
legs trade in the composition sample, and the covariance share of KSPI's foreign daily return
arriving before the KASE close is 0.0996 rather than zero (Section 8.2). Every statement about the
KSPI pair below is about zero continuous-session overlap with a small, measured information
overlap.

### 2.2 Venue thinness, measured against the same stock on NASDAQ

KSPI is the same claim on the same company on both venues, so the comparison needs no matching
and no size adjustment.

| quantity | KASE | NASDAQ | ratio |
|---|---|---|---|
| median minutes with a trade | 124 | 206 | 1.7x |
| median shares traded | 952 | 287,858 | 302x |
| median turnover, USD | 94,688 | 27,789,973 | 293x |

Produced by `analysis/transmission/venue_liquidity.py`, over 517 common sessions from 2024-01-19,
NASDAQ restricted to the regular session, the KASE side converted at the on-exchange `USDKZT_TOM`
rate.

Bars are minutes with at least one trade, so the first row is a lower bound on trade counts, not a
trade count. A KASE session runs 370 minutes and trades in a median of 124 of them, one minute
with a trade per 3.0 minutes of clock. Absence of a bar means no trade, so the series must not be
forward-filled onto a grid. Turnover carries the comparison: the 293-to-1 ratio is what "thin"
means throughout this document.

### 2.3 Costs are estimated from trade prints, not measured from quotes

There is no quote feed, so the effective spread is estimated from trades with two estimators,
both of which return the full bid-ask width. Roll (1984) gives a median of 0.24% over 748 KSPI
sessions; Corwin and Schultz (2012) give 0.47% on the sessions from 2024. A round trip crosses
the spread once, buying at the ask and selling at the bid, and pays commission of 0.085% per
side, so the round trip is 0.41% under Roll and 0.64% under Corwin-Schultz. An earlier version
of this document read both estimates as half spreads and doubled them while leaving the
commission alone, overstating every round trip; the unpublished verification of 2026-10-12 caught
the error, and every net figure below uses the corrected band. The later re-analysis of
the same market puts the Roll effective spread of eight liquid KASE names at 12 to 27 basis
points, a range the 24 basis points here sit inside.

What each estimator leaves out is printed by `analysis/transmission/transmission_tradeable.py`
rather than assumed. Roll needs at least 51 bars and a negative serial covariance: of 1,263 KSPI
sessions in the store, 748 are estimated, 498 are excluded for fewer than 51 bars and 17 for a
non-negative covariance, so the 0.24% is a median over the liquid sessions; on the 648 sessions
from 2024, where no session is that thin, the median is also 0.24%. Corwin-Schultz as implemented
keeps the positive two-day estimates and takes their median: 327 of 647 two-day estimates
(50.5%) are non-positive, the paper's treatment of setting them to zero and averaging gives
0.31%, and the median with negatives set to zero is 0.00%. The band keeps 0.47%, the largest of
the three treatments, as its upper end; the paper's 0.31% lies inside it, and the 0.00% median
says only that half the two-day estimates are non-positive on this data. The two estimators were
first run on different windows, Roll on every KSPI session in the store and Corwin-Schultz on the
sessions from 2024, which is why Roll is repeated on the 2024 window above.

## 3. Data

The analysis runs on a 1-minute trade store of KASE equities and the on-exchange `USDKZT_TOM`
rate, assembled by the companion `kase-market-data` repository from a chart-data endpoint of a
retail broker (Tradernet, Freedom Finance's platform), together with a 1-minute store for KSPI on
NASDAQ from the same source. Bars exist only for minutes that traded. The stores are not
redistributed, because the endpoint's terms do not clearly address republication; `data/README.md`
states what is committed and how to attach the rest. The daily companion series, used for one
year-end window in Section 9, is the same broker's daily feed. The foreign daily closes of the
three pairs and the hourly-bar quantities behind the IOB composition split were fetched from Yahoo
Finance; what this repository commits is the derived tables `data/derived/foreign_daily.csv` and
`foreign_split.csv`, written by `analysis/transmission/foreign_legs.py`, not the chart data. The
KSPI daily series behind the headline regressor is fetched from Yahoo at run time by
`intraday_transmission.py`.

Panel coverage of the KASE store:

| ticker | bars | first | last | sessions |
|---|---|---|---|---|
| KSPI | 106,898 | 2018-07-23 | 2026-08-24 | 1,263 |
| KZAP | 145,192 | 2018-12-11 | 2026-08-24 | 1,860 |
| AIRA | 143,848 | 2024-02-09 | 2026-08-24 | 621 |
| HSBK | 389,219 | 2015-05-25 | 2026-08-24 | 2,504 |
| KCEL | 104,168 | 2015-05-26 | 2026-08-24 | 2,600 |
| KZTO | 229,727 | 2015-05-25 | 2026-08-24 | 2,608 |
| KEGC | 218,531 | 2015-05-25 | 2026-08-24 | 2,607 |
| KZTK | 43,491 | 2015-05-25 | 2026-08-24 | 2,581 |
| CCBN | 169,598 | 2015-06-01 | 2026-08-24 | 2,559 |
| ASBN | 270,583 | 2016-05-16 | 2026-08-24 | 1,792 |
| KMGD | 145,694 | 2016-12-14 | 2026-08-24 | 1,243 |

Produced by `analysis/panel_diagnostics.py`, which also reports 2,610 panel trading dates from
2015-05-25 to 2026-08-24.

The estimation sample for Sections 5, 6 and 10 is 591 KASE sessions, aligned from 84,526 KASE
minute bars over 2024-01-23 to 2026-08-24. The panel begins with KSPI's NASDAQ listing in January
2024, which is when a prior NASDAQ close first exists. Of the 634 sessions carrying bars, 633 have
a computable opening gap, the first having no prior close, and 42 are removed by a 1%/99% trim
applied in turn to the opening gap, the intraday drift and the NASDAQ move, leaving 591. The trim
drops rows rather than clipping them, and a session lost on any one variable is lost for all, so
the three cuts together remove more than 2%. From 2024-01-19 to 2026-08-24, 43 of 677 weekdays
carry no trading anywhere on the panel.

The regressor is the one-session NASDAQ close-to-close return ending at the last NASDAQ close
before the KASE open. The opening gap runs from the previous KASE session's close, so it spans
every NASDAQ session between the close matched to that session and the close matched to this one;
Section 5.1 counts how many sessions each gap spans and re-estimates the headline on the aligned
ones. The cross-pair sample in Section 8 runs on the common window 2024-02-01 to 2026-08-24, with
626 sessions for KSPI and KZAP and 619 for AIRA; its composition and conditional estimates for the
IOB pairs run on the hourly-bar sample, which begins in late August 2024 (Section 8.2). The
conditioning sample in Section 7 is 535 sessions, 2024-01-23 to 2026-03-31, the span of the local
NASDAQ store, joined to the NASDAQ closes by timestamp rather than by calendar day.

Regression t-statistics are Newey-West HAC (Newey and West 1987) at lag 5 unless a different
estimator is named at the number. They are asymptotic: no small-sample correction and a normal
reference distribution, except in Section 7, whose script applies the small-sample correction.
The year-end statistics in Section 9 are one-sample t-statistics across annual windows. Script
names are given under each table; an entry labelled derived is computed from other entries in the
same table and is printed by no script.

### 3.1 Events inside the panel

Venue-level events inside or near the sample are disclosed as observed facts; no cause is
asserted for any of them. All figures from `analysis/panel_diagnostics.py`.

On 2024-10-14, inside the 591-session panel, 11 of the 11 instruments carrying bars on that date
and on both neighbouring sessions ended early, with a median last bar of 13:47 against 17:12 on
the preceding session and 17:25 on the following one; the on-exchange FX board is truncated the
same day, at 13:50 against 16:59 on both neighbours, so the truncation spans the venue. The
session is retained: dropping it, and dropping it with the following session, moves the gap and
drift betas of a 528-session KSPI frame joined by timestamp (2024-02-01 to 2026-03-31) by 0.00008
at most.

On 2022-12-01, 10 of the 10 equity lines meeting the same neighbour test ended early, with a
median last bar of 12:46; the FX board is not truncated that day. This date is outside the panel.
In January 2022 the store holds no bars for any panel instrument on five weekdays (3, 4, 6, 7 and
10 January); ten instruments trade on the 5th; from the 11th to the 21st the median last bar runs
15:00 to 15:13 against a December 2021 baseline of 16:59, with full hours resuming from the 24th,
median last bar 17:05. This window is outside the panel.

Over 2016-06 to 2017-12 the store's first bar of the day is frequently not a trade: across six
liquid names, 2,054 bars sit at exactly 09:00 on 371 dates, and their close equals the previous
session's close in 99.90% of cases against 13.6% matching the same day's first print. They are
carry-over prints hours before the 11:29 open, outside the panel, and the reason every script here
starts its session at 11:29 or later.

Session bounds are stated per instrument rather than store-wide. From 2023 onward HSBK's median
last bar is 17:28 with 78.41% of sessions carrying a bar after 17:25; the share is 31.32% for
KSPI, 33.22% for KZTO, 32.44% for KZAP, 44.44% for AIRA and 14.32% for KCEL.

## 4. Absorption speed

Daily betas cannot distinguish a venue that reprices over six hours from one that reprices in
five minutes. The KASE session return is therefore decomposed by entry delay from the first actual
trade, exit at the close, on the 174 sessions where NASDAQ moved at least 2%, in raw tenge and in
the direction of the NASDAQ move:

| entry | mean return | hit rate |
|---|---|---|
| first traded print | +0.856% | 83.3% |
| +5 minutes | +0.380% | 63.8% |
| +15 minutes | +0.200% | 57.5% |
| +30 minutes | +0.173% | 54.0% |
| +60 minutes | +0.136% | 50.0% |
| +120 minutes | +0.138% | 52.9% |

Produced by `analysis/transmission/entry_timing.py`.

Cumulated from the first print, 81.1% of the full-session drift has accrued by 12:00, thirty
minutes into the session, and 88.5% by 13:00. Over half of it accrues within five minutes of the
first print. At sixty minutes the hit rate is 50.0%, and the two-hour entry is level with the
one-hour entry rather than below it.

Those numbers sit inside the developed-market benchmarks of Section 1: a venue at the 293-to-1
turnover ratio of Section 2.2 absorbs 81.1% of the transmitted move in about thirty minutes, within
the up to 30 minutes Thorp and Milunovich (2006) report for New York, and halves the capturable
return between the
first print and five minutes later, the decay Patell and Wolfson (1984) describe.

The 2% threshold is a constant in `entry_timing.py` with no pre-registration record. The same
decomposition at the open, exit at the close, on the USD panel, by threshold:

| NASDAQ move at least | sessions | mean return | hit rate |
|---|---|---|---|
| 0% | 591 | +0.401% | 68.2% |
| 1% | 341 | +0.604% | 75.4% |
| 2% | 174 | +0.881% | 85.6% |
| 3% | 67 | +0.833% | 80.6% |

Produced by `analysis/transmission/transmission_tradeable.py`. The 2% row is the same 174 sessions
as the entry-delay table, measured from the auction print in USD rather than from the first print
in tenge, which is why it reads +0.881% against +0.856%. Section 10 reports the first-half
selection of the threshold and the 2% rule out of sample.

Two caveats. The first runs in the same direction as the result: the store records only minutes
in which a trade occurred, one such minute per 3.0 minutes of clock, so absorption measured here
is bounded by the arrival of the next trade rather than the next quote, and a quote-based
measurement would locate the repricing no later. The second bears on Section 11: "exit at the
close" is a last print, not a fill. In the later re-analysis, the final fifteen minutes
of a KASE session carry a median of a few hundred dollars of turnover per name, so a participant
exiting at the close pays for it in price.

Capturing the +0.856% requires setting the first print: resting a limit order that is filled at
the prior day's price on a session when NASDAQ has just moved at least 2%. The premium of KSPI's
KASE line over the prior NASDAQ close is close to flat across the session: across half-hourly
buckets from 11:30 to 17:00 the mean premium runs from +3.03% to +3.16%, a spread of 0.14 points
against a within-bucket standard deviation of about 3.4%, with the widest bucket at 15:00 rather
than at either end (`analysis/transmission/intraday_transmission.py`). The drift is therefore not
a within-session narrowing of the cross-venue price difference. The level of that premium is a
property of the sample period rather than of the venue: the later re-analysis tracks it
from about +3.1% in 2024-25 to near zero by mid-2026 and reads it as a venue and custody premium
rather than a valuation gap. Section 11 sets the entry returns against the cost band.

## 5. Transmission estimates

Regressing KASE returns on the prior NASDAQ close-to-close move over 591 sessions, open defined as
the 11:29 auction print, Newey-West HAC(5):

| component | beta | t | R2 |
|---|---|---|---|
| KASE opening gap (previous close to open) | 0.2019 | 10.50 | 0.284 |
| KASE intraday drift (open to close) | 0.2718 | 12.49 | 0.227 |

Produced by `analysis/transmission/hac_inference.py`.

Total previous-close-to-close transmission is 0.4741 (t 16.73, R2 0.427), under half the NASDAQ
move. It is estimated directly on that return rather than summed from the two rows, because the
components are ratios against different denominators; the sum of the two betas is 0.4737.
Restricting to the largest-move quartile, |NASDAQ move| above the 75th percentile, n 147, gives
0.2136 (t 8.93) and 0.2755 (t 9.89).

This is the Becker, Finnerty and Gupta (1990) result on another venue: partial adjustment at the
local open, a positive coefficient over the local session, total pass-through short of one. The
split between the rows is the kind of quantity the price-delay measure of Hou and Moskowitz (2005)
summarises. Read at daily resolution, more of the move arrives during the KASE session than at its
open; Section 4 locates that arrival in the first half hour, Section 6 shows how the split depends
on the price called the open, and Section 7 asks how much of the drift is lagged adjustment at
all.

### 5.1 The regressor's alignment

The panel is built by calendar day, and the unpublished verification of 2026-10-12 found that the one-session
regressor and the opening gap do not always cover the same NASDAQ sessions. `intraday_transmission.py`
now writes `data/derived/regressor_alignment.csv`, which counts, for each of the 591 sessions, the
NASDAQ sessions between the close matched to the previous KASE session and the close matched to
this one, using the real predecessor before the trim. The headline keeps the committed panel,
which two companion repositories also read; the rows below show what alignment does to it. An
unpublished re-derivation of this version's code, on 2026-10-28, rebuilt the counts and the rows
below from the raw store and matched them.

| sample | n | gap beta | t | drift beta | t | total beta | t |
|---|---|---|---|---|---|---|---|
| all sessions, one-session regressor (headline) | 591 | 0.2019 | 10.50 | 0.2718 | 12.49 | 0.4741 | 16.73 |
| gap spans exactly one NASDAQ session | 541 | 0.2095 | 10.32 | 0.2727 | 12.62 | 0.4827 | 16.71 |
| gap spans at least one session, regressor is the NASDAQ return over the span | 568 | 0.1994 | 9.84 | 0.2693 | 12.79 | 0.4692 | 15.72 |

Produced by `analysis/transmission/hac_inference.py`. Of the 591 sessions, 23 have a gap spanning
no NASDAQ session (a US holiday, or a KASE Saturday session followed by a Monday), 541 span one,
22 span two, 2 span three and 3 span four (a Kazakh holiday, or another weekday on which the store
holds no KASE bars). The stale rows are placebo observations that attenuate the gap beta slightly;
dropping them, or replacing the regressor by the return over the sessions the gap actually covers,
moves the betas in the third decimal and leaves every t above 9. The verification counted
misaligned rows by business-day gaps between consecutive rows of the trimmed panel, which counts a
gap left by the trim as a missing session; the count here is by NASDAQ sessions on the pre-trim
predecessor, and is the smaller of the two.

## 6. The opening auction against continuous trading

### 6.1 Two conventions

Amihud and Mendelson (1987) show open-to-open returns are noisier and more mean-reverting than
close-to-close returns on the NYSE and attribute the difference to the call mechanism; Stoll and
Whaley (1990) isolate a transitory opening component that reverses over the following minutes;
Ibikunle (2015) finds, on the London Stock Exchange, that the opening auction contributes
efficiently to price discovery only for high-volume stocks. KSPI on KASE sits on the thin side of
that split. The first bar of a KASE session is the 11:29 auction. Substituting the first continuous
trade at or after 11:30:

| | auction open (11:29) | first print at or after 11:30 |
|---|---|---|
| opening gap beta | 0.2019 (t 10.50) | 0.2986 (t 12.20) |
| intraday drift beta | 0.2718 (t 12.49) | 0.1751 (t 7.30) |
| gap share of the 0.4741 total (derived) | 43% | 63% |

Measured rows produced by `analysis/transmission/hac_inference.py`. The share row is printed by no
script: it is each column's gap beta over the 0.4741 total of Section 5.

The difference is the beta of the 11:29-to-11:30 price change on the NASDAQ move, +0.0967. The
total beta is 0.4741 under both conventions, because that return does not depend on where the
open is placed, so the change is a reallocation between components rather than additional
transmission. No interval is reported for the +0.0967, so whether the reversal of the gap-drift
ordering between the conventions is separable from a tie is not established.

### 6.2 The measurement-point curve

No breakpoint is privileged, so the full curve is reported:

| measurement point | gap beta | drift beta | n |
|---|---|---|---|
| 11:29 (auction) | 0.2019 | 0.2718 | 591 |
| 11:30 | 0.2986 | 0.1751 | 591 |
| 11:31 | 0.3296 | 0.1441 | 591 |
| 11:32 | 0.3456 | 0.1280 | 591 |
| 11:35 | 0.3920 | 0.0818 | 591 |
| 11:40 | 0.4204 | 0.0534 | 591 |
| 12:00 | 0.4357 | 0.0380 | 591 |

Produced by `analysis/transmission/hac_inference.py`, which writes
`data/derived/measurement_point_curve.csv`; the figure in `figures/paper/` is drawn from that file.
By 12:00 the drift beta is 0.0380 (t 1.98): what the daily regression reads as in-session drift is
almost entirely the first half hour.

### 6.3 What the two conventions measure

Both describe a real transaction. A participant who can submit into the auction faces one number;
one who can only trade continuously from 11:30 faces the other. The auction impounds 0.2019 of the
foreign move against the 0.2986 the continuous market has impounded one minute later, about
two-thirds of it, which is the quantity Ibikunle (2015) estimates for LSE auctions by volume
decile, here for a single thin name. The correction runs toward a smaller in-session drift, so the
choice of convention does not flatter the assessment in Section 11.

## 7. Foreign prices observable during the local session

Craig, Dravid and Richardson (1995) show that apparent cross-market partial adjustment can vanish
once the regression conditions on foreign instruments trading while the local venue is open. The
KSPI pair admits the test because NASDAQ pre-market prints fall inside the KASE session on 293 of
the 535 sessions in this specification, 54.8%, between 04:00 and 08:29 New York, all strictly
before the NASDAQ open.

The lagged term is the last NASDAQ regular close-to-close return whose close strictly precedes the
KASE open, joined by timestamp with a five-day staleness bound. The live term is the last NASDAQ
pre-market print inside the KASE session, measured over the same prior close, and zero where no
such print exists. Newey-West HAC(5) with the small-sample correction:

| specification | lagged beta | live beta | R2 | n |
|---|---|---|---|---|
| drift on the prior NASDAQ move | 0.167861 (t 3.478) | | 0.1005 | 535 |
| drift on the prior move and the live pre-market move | 0.199755 (t 5.782) | 0.377396 (t 4.987) | 0.2129 | 535 |
| sessions carrying a live print only | 0.218799 (t 4.915) | 0.420900 (t 5.299) | 0.2665 | 293 |

Produced by `analysis/transmission/foreign_session_conditioning.py`.

Conditioning does not reduce the lagged coefficient; it raises it by 19.0%, with a higher t, and
the live term enters on its own. The rise is attributable to the added regressor rather than to a
change of sample: the univariate lagged coefficient on the same 293 live-print sessions is
0.168954, indistinguishable from the 0.167861 obtained on all 535. The two channels are additive:
part of what accrues during a KASE session is contemporaneous following of a foreign price visible
at the time, on the 54.8% of sessions where such a price exists, and the overnight channel
survives conditioning on it. The instrument is a pre-market print rather than a continuously
overlapping foreign quote, so this is a partial replication of Craig, Dravid and Richardson on
this sample, not a complete one.

The baseline here is 0.167861 rather than the headline 0.2718 because the two sections differ in
join and sample: this one takes the prior NASDAQ close from the local intraday store by timestamp,
the headline from the daily series by calendar day, and this sample is the 535 sessions the local
store covers. The test concerns the change under conditioning, and these levels are not the
headline estimates. Taking the KASE close as the nominal 17:30 rather than the last bar leaves the
lagged coefficients at 0.167861, 0.197292 and 0.217827 with 303 live-print sessions; restricting
to 2024-02 onward leaves them at 0.168046, 0.199989 and 0.218799.

## 8. Overlap, composition, and what a three-pair contrast identifies

Otsubo (2014) separates the amount of information a local venue must assimilate from the speed at
which it assimilates it, for non-overlapping Tokyo and NYSE sessions; Griffin, Kelly and Nardari
(2010) generalise the warning to cross-country efficiency comparisons; the variance-share argument
below goes back to French and Roll (1986); and Ito, Lyons and Melvin (1998) use the removal of the
Tokyo lunch break as the kind of same-venue experiment that would identify an overlap effect. The
design here is a same-venue overlap contrast: three co-listings on one local venue, one with no
continuous overlap and two with several hours of it, each regressed on the part of the foreign
session that ran while KASE was shut.

### 8.1 The cross-pair comparison

Common window from 2024-02-01, n 626 for KSPI and KZAP and 619 for AIRA, Newey-West HAC(5), the
foreign move measured close-to-close on the foreign venue:

| pair | shared minutes (median) | contemporaneous | lagged gap | lagged drift | lagged total |
|---|---|---|---|---|---|
| KSPI / NASDAQ | 0 | 0.0493 (t 1.1555) | 0.2829 (t 12.32) | 0.1889 (t 4.20) | 0.4718 (t 10.92) |
| KZAP / LSE-IOB | 314 | 0.3541 (t 10.1057) | 0.1801 (t 8.93) | 0.1089 (t 3.85) | 0.2890 (t 7.59) |
| AIRA / LSE-IOB | 325 | 0.2732 (t 4.7914) | 0.0490 (t 3.18) | 0.1222 (t 3.14) | 0.1712 (t 4.03) |

Produced by `analysis/transmission/overlap_comparison.py`. The contemporaneous column is estimated
on 602, 607 and 599 days; the lagged total is the regression of gap plus drift on the same
regressor.

Overlap moves transmission out of the lagged channel and into the contemporaneous one. The
non-overlapping pair carries a contemporaneous coefficient this sample does not separate from zero
and the largest lagged total of the three; both overlapping pairs carry contemporaneous
coefficients several times larger and lagged totals a third to two-thirds the size. The KSPI
lagged rows here differ from Section 5 (0.2829 and 0.1889 against 0.2019 and 0.2718) because the
cross-pair script joins the foreign close by timestamp with a five-day bound, uses the first
session bar at or after 11:29 in USD without the 1%/99% trim, and starts in February.

### 8.2 Composition

How much of the foreign daily return has already arrived by the time KASE closes is the French and
Roll (1986) quantity, and it is what overlap changes mechanically. Measured as the covariance
share of the foreign daily log return attributable to the segment before the KASE close:

| pair | sample | n | covariance share before the KASE close | share after the KASE close | variance-share reading |
|---|---|---|---|---|---|
| KSPI | 2024-02-01 to 2026-03-31 | 508 | 0.0996 | 0.9004 | 0.2225 |
| KZAP | 2024-08-28 to 2026-08-24 | 472 | 0.6686 | 0.3314 | 0.6875 |
| AIRA | 2024-09-02 to 2026-08-24 | 426 | 0.7183 | 0.2817 | 0.9279 |

Produced by `analysis/transmission/overlap_comparison.py`; the share after the close is one minus
the share before it.

The KSPI segment is split on the local 1-minute store, pre-market prints included; the two IOB
legs are split on Yahoo 60-minute bars, which Yahoo serves as a rolling two-year window, so their
sample begins in late August 2024 rather than in February. The price at the KASE close is read off
bar boundaries, never from inside a bar; where a bar's close and the next bar's open share the
boundary, the close is used, as the last trade before that instant. An earlier version left that
choice to the sort order, and the unpublished re-derivation of this version's code found the
committed split mixing the two rules; the rule is now fixed in `price_path` and stated. A print at the KASE close
exists on 293 of the 508 KSPI days, all 472 KZAP days and 363 of the 426 AIRA days; where none
exists the pre-close segment is zero. The KSPI share is 0.0996 and not zero, which is the
pre-market information overlap of Section 2.1 entering the covariance. The covariance and variance
readings agree for KZAP and diverge for AIRA, whose variance share of 0.9279 sits well above its
covariance share. Composition separates the three pairs in the order the session hours imply,
which is a statement about when foreign information arrives, not about how quickly the venue
absorbs it.

### 8.3 Conditioning on news that arrived while KASE was closed

Splitting each foreign session at the KASE close and regressing the next KASE session on the
post-close segment only puts the three pairs on informationally equivalent news. Newey-West HAC(5):

| pair | sample | n | next gap | next drift | next total |
|---|---|---|---|---|---|
| KSPI | 2024-02-02 to 2026-04-03 | 526 | 0.2664 (t 10.58) | 0.1744 (t 3.99) | 0.4408 (t 9.92) |
| KZAP | 2024-08-29 to 2026-08-24 | 482 | 0.2824 (t 9.26) | 0.3439 (t 4.08) | 0.6264 (t 7.48) |
| AIRA | 2024-09-03 to 2026-08-24 | 477 | 0.0102 (t 0.43) | 0.1421 (t 3.46) | 0.1523 (t 3.10) |

Produced by `analysis/transmission/overlap_comparison.py`.

On next-day total pass-through the two overlapping pairs sit on either side of the non-overlapping
one, not together on one side of it. AIRA's next-gap coefficient is not separable from zero, so
essentially all of its conditional pass-through arrives during the following session rather than
at its open.

### 8.4 The pooled contrast and its pair-specific components

Stacking the three pairs on the dates all three trade gives a balanced panel of 381 dates and
1,143 pair-days, 2024-09-03 to 2026-04-03, estimated with Driscoll-Kraay HAC(5) standard errors,
which allow for cross-sectional correlation across the pairs on the same date. The quantity of
interest is the difference in next-day total pass-through between the overlapping pairs and the
non-overlapping one, the interaction coefficient in one pooled model:

| contrast | estimate | se | t | p | 95% interval |
|---|---|---|---|---|---|
| pooled overlapping minus KSPI | +0.0334 | 0.0887 | 0.377 | 0.7063 | [-0.1405, +0.2073] |
| KZAP minus KSPI | +0.2110 | 0.1039 | 2.03 | 0.0423 | [+0.0074, +0.4147] |
| AIRA minus KSPI | -0.2261 | 0.0963 | -2.35 | 0.0189 | [-0.4148, -0.0373] |

Produced by `analysis/transmission/overlap_comparison.py`, which writes
`data/derived/overlap_contrasts.csv`. Pair-specific pass-through in the same panel is 0.4331
(t 7.84) for KSPI, 0.6441 (t 6.94) for KZAP and 0.2070 (t 3.41) for AIRA. Two pair contrasts are
tested; the Holm-adjusted p-values are 0.0423 and 0.0378.

Read alone, the pooled interval is compatible with an overlap effect of either sign up to roughly
a fifth of a unit of pass-through and with no effect at all, and it is reported as that interval
rather than as a decision (Wasserstein, Schirm and Lazar 2019). It is not evidence that overlap
leaves absorption rate unchanged: the two contrasts it averages are each distinguishable from zero
and point in opposite directions, and their near-cancellation is what produces the pooled
+0.0334. With two overlapping units, an overlap effect and a stock effect are not separately
identified: any pair-specific contrast can be assigned to either. AIRA differs from KSPI in overlap
and also in liquidity, free float, listing age, sector and foreign-leg staleness, and so does
KZAP, in the opposite direction on several of those. What survives is the composition result of
Section 8.2. Whether overlap also changes how fast the local venue absorbs foreign information is
not identified by three co-listings; more overlapping pairs, or a within-pair change in overlap
such as a session-hours reform, would be needed.

### 8.5 Common-factor weights

Johansen (1991) rejects no cointegration at the 5% level in all 48 specifications of a grid
crossing the three pairs with two alignment conventions, four lag orders and two deterministic
terms. In 21 of the 48 the trace test also rejects a unit root in each log price separately, so
the system has no common stochastic trend and a common-factor weight is not defined in the usual
sense; for AIRA no specification lands on exactly one cointegrating vector.

Gonzalo and Granger (1995) weights do not require the two series at the same instants, which is
why they are estimable for the KSPI pair where Hasbrouck (1995) shares are not. Two alignments
are defensible: calendar alignment pairs each KASE session with the foreign close bearing the same
date; preceding-close alignment pairs it with the foreign close that strictly preceded its open.
The weight on the KASE leg across the grid:

| pair | alignment | minimum | median | maximum |
|---|---|---|---|---|
| KSPI | calendar | 0.2312 | 0.3005 | 0.3702 |
| KSPI | preceding | 0.4503 | 0.5267 | 0.6059 |
| KZAP | calendar | 0.2724 | 0.3220 | 0.4345 |
| KZAP | preceding | 0.8644 | 0.8834 | 0.9193 |
| AIRA | calendar | 0.4021 | 0.4766 | 0.5182 |
| AIRA | preceding | 0.7059 | 0.7577 | 0.7999 |

Produced by `analysis/transmission/overlap_comparison.py`.

For KSPI the two ranges do not touch, and the shift between their medians, 0.2262, exceeds the
whole within-alignment range, 0.1390 under calendar alignment and 0.1557 under preceding. The data
contain no basis for choosing between the conventions, so no point estimate for KSPI is reported.
The KSPI calendar range also overlaps the KZAP calendar range over most of its length, and the
ordering of the two overlapping pairs reverses between conventions, so the measure delivers no
overlap contrast on this sample.

The missing input is the one that rules out Hasbrouck: both methods decompose innovations in a
jointly observed price vector, and for a pair with no interval in which both venues trade there
is no such vector; the alignment convention supplies by assumption what the data do not contain.
What the calendar-aligned system error-corrects on for KSPI is measurable: regressing the change
in the calendar-aligned log spread on the foreign move arriving after the KASE close gives a slope
of -0.8908 (t -16.65, R2 0.5583, n 506), the highest fit of the three pairs. The disparity is news
the KASE book had not yet been shown, not a mispricing it declined to arbitrage away. The
defensible statistics for that pair are the sequential ones in 8.1 and 8.3.

## 9. The turn-of-the-year window on KASE

The 20 December to 10 January window is the turn-of-the-year effect, documented for the US by
Rozeff and Kinney (1976), located by Roll (1983) on the last December session and the first
January sessions, and concentrated by Keim (1983) and Reinganum (1983) in small capitalisations,
which is the whole of a KASE basket by developed-market standards. The window overlaps the
turn-of-the-month effect of Ariel (1987) and Lakonishok and Smidt (1988), which this design does
not separate, and Schwert (2003) documents attenuation of anomalies of this class after
publication. What is measured below is the size of a named effect on a venue where it had not been
measured.

The trade is mechanical: an equal-weighted basket of nine KASE names (ASBN, CCBN, HSBK, KCEL,
KEGC, KMGD, KZAP, KZTK, KZTO) bought at the first close on or after 20 December and sold at the
first close on or after 10 January, close-to-close to match the literature above, with a search
limit of 10 calendar days and a minimum of 3 legs. The December-January stretch is when a thin
market stops printing, so the construction has to say which prints count as a close. The rule
adopted here is a bar floor: a minute-store day enters only if the store holds at least 5 priced
bars inside the 11:29-17:30 session. A day with one or two prints is not a closing price at which
a basket could have been struck. The unpublished verification of 2026-10-12 found two committed
constructions, one with this floor and one admitting every print, differing by leg admission and
not by pricing convention; the floor is kept, and the construction without it is reported in the
sensitivity table below rather than discarded. The floor's level is a free parameter, so the
result is shown across floors.

The floor changes 12 of the leg prices in the ten minute-priced windows. The largest is ASBN in
the 2020 window: without the floor the entry is a 2.31 print on Sunday 2020-12-20, a transferred
working day with fewer than five priced bars, and the leg returns +29.87% to the 3.00 exit; with
the floor the entry is 3.25 on 2020-12-22 and the same leg returns -7.69%. Every changed leg is
listed by `analysis/calendar/yearend_constructions.py` with both prices.

Per-window basket returns, floor of 5 bars:

| entry year | minute legs | minute | daily legs | daily | spliced | source |
|---|---|---|---|---|---|---|
| 2015 | 0 | | 6 | -3.92% | -3.92% | daily |
| 2016 | 5 | +1.07% | 6 | -0.59% | +1.07% | minute |
| 2017 | 6 | +5.74% | 6 | +5.80% | +5.74% | minute |
| 2018 | 6 | +2.23% | 7 | +1.64% | +2.23% | minute |
| 2019 | 6 | +2.25% | 7 | +1.95% | +2.25% | minute |
| 2020 | 8 | +3.90% | 8 | +8.59% | +3.90% | minute |
| 2021 | 8 | +3.23% | 9 | +3.12% | +3.23% | minute |
| 2022 | 9 | +5.86% | 9 | +5.86% | +5.86% | minute |
| 2023 | 9 | +2.88% | 9 | +2.88% | +2.88% | minute |
| 2024 | 9 | +4.79% | 9 | +4.79% | +4.79% | minute |
| 2025 | 9 | +6.61% | 9 | +6.61% | +6.61% | minute |

Produced by `analysis/calendar/yearend_constructions.py`.

The 1-minute store prices no leg of the 2015 window (enter 20 December 2015, exit 10 January
2016); the companion `kase-market-data` writeup shows this is a collection gap, not a market
closure, since the same endpoint at daily resolution returns the window in full. The daily
companion prices it at -3.92% on six legs, the most adverse window in the sample. The daily series
has no bar count, so no floor applies to that window; the script prints its six legs with their
daily volumes, the thinnest entry being CCBN on 11,020 shares. The spliced series uses the minute
store wherever it prices at least three legs of a window and the daily series otherwise, which in
this sample is 2015 alone; it is the estimate.

| construction | source | n | mean | sd | t | 95% CI | positive |
|---|---|---|---|---|---|---|---|
| 2016 to 2025 | minute, floor 5 | 10 | +3.855% | 1.836% | 6.638 | [+2.541%, +5.169%] | 10 of 10 |
| 2015 to 2025, spliced (the estimate) | minute, daily for 2015 only | 11 | +3.148% | 2.921% | 3.574 | [+1.186%, +5.111%] | 10 of 11 |
| 2015 to 2025 | daily throughout | 11 | +3.338% | 3.551% | 3.118 | [+0.953%, +5.723%] | 9 of 11 |

Produced by `analysis/calendar/yearend_constructions.py`.

Sensitivity to the floor, same script:

| floor (bars) | minute only, n 10: mean, sd, t, positive | spliced, n 11: mean, sd, t, positive |
|---|---|---|
| 1 (every print counts) | +4.082%, 2.797%, 4.615, 9 of 10 | +3.354%, 3.586%, 3.102, 9 of 11 |
| 3 | +3.669%, 2.034%, 5.703, 10 of 10 | +2.979%, 2.994%, 3.300, 10 of 11 |
| 5 | +3.855%, 1.836%, 6.638, 10 of 10 | +3.148%, 2.921%, 3.574, 10 of 11 |
| 10 | +4.101%, 2.195%, 5.910, 10 of 10 | +3.372%, 3.191%, 3.504, 10 of 11 |
| 20 | +4.423%, 1.537%, 9.102, 10 of 10 | +3.665%, 2.908%, 4.180, 10 of 11 |

The mean moves within about three-quarters of a point across floors and the 2015 window is the
one negative window at every floor from 3 upward; the floor of 1 is the construction in which the
2016 window turns negative on the thin prints listed above. The disagreement between the two
sources is also measurable where both price the same leg: 65 of 75 leg-windows agree exactly, the
windows from 2022 to 2025 and 2019 agree exactly at basket level, and the largest basket-level
disagreement is -469.53 bp on the 2020 window, where the daily source carries the same 2.31 ASBN
print the floor rejects. A staleness proxy, the share of flat daily closes in the surrounding 90
days, correlates with the leg-level disagreement at a Spearman rank correlation of 0.3727
(p 0.0010) across the 75 leg-windows. None of that bounds the disagreement in the 2015 window,
which has no leg priced by both sources.

Net of costs, the spliced mean of +3.148% is +2.978% after commission alone, +2.735% after the
Roll round trip and +2.511% after the Corwin-Schultz round trip (same script, reading the spread
table of Section 2.3). The spreads are KSPI's and the basket names are thinner, so the net figures
overstate what a basket would keep.

The benchmark decides whether any of this is local. `analysis/calendar/yearend_global_decomposition.py`
runs the same window on SPY and EEM over the same eleven entry years, on the same spliced series:

| series | mean | sd | positive | t | n |
|---|---|---|---|---|---|
| KASE basket, spliced | +3.15% | 2.92% | 91% | 3.57 | 11 |
| SPY | +1.24% | 2.59% | 82% | 1.58 | 11 |
| EEM | +2.80% | 5.10% | 82% | 1.82 | 11 |
| KASE minus SPY | +1.91% | 2.46% | 91% | 2.57 | 11 |
| KASE minus EEM | +0.35% | 3.46% | 45% | 0.33 | 11 |

Produced by `analysis/calendar/yearend_global_decomposition.py`, which writes
`data/derived/yearend_windows.csv`.

The KASE window sits above the US benchmark and level with the emerging-market one, so the sign
of any local excess depends on the benchmark, which is the standard finding: Gultekin and Gultekin
(1983) document turn-of-the-year seasonality in 12 of 17 countries. On the eleven windows the KASE
series correlates 0.61 with SPY and 0.76 with EEM. That correlation is one window's doing: in the
2015 window all three series fell, and without it the KASE series correlates -0.02 with SPY and
0.37 with EEM on the ten minute-priced windows, while the means become +3.86% (KASE), +1.83% (SPY)
and +3.98% (EEM) and the KASE-minus-EEM difference -0.12%. An earlier version of this document
quoted only the ten-window correlations and read them as evidence that the window does not run
through index beta; with eleven points the reading depends on whether the one adverse window is
in the sample, and it belongs there.

The t of 3.574 is uncorrected for the choice of window. The boundaries were not drawn at random and
no bootstrap over a universe of candidate windows was run, so the figure is an in-sample t on a
selected calendar rule; Sullivan, Timmermann and White (2001) show calendar effects losing their
significance once the universe of rules the researcher could have examined is accounted for.
Eleven observations at one trade per year support a mean and little else: the sample cannot
exclude a true failure rate near one in five, the basket is built from instruments currently
listed, so survivorship bias is not ruled out, the returns are dividend-unadjusted because the
store carries raw traded prices with no corporate-actions file, and the ex-dates of the KZT-only
names could not be verified here. The exit is a last print rather than a fill (Section 4), and
the later re-analysis records that the daily companion's closes from March 2026 do not
always match the intraday last print; the 2015 window, the only one priced from it, predates that.

## 10. Robustness

FX. The drift beta is 0.2660 in raw tenge (HAC t 12.73) against 0.2718 USD-converted
(`analysis/transmission/hac_inference.py`). Under any fixed daily rate FX cancels from an
open-to-close ratio, so the drift beta is the raw-tenge beta by construction. On the sessions with
a NASDAQ move of at least 2%, the sign-adjusted drift is +0.881% in USD and +0.856% in tenge, hit
rates 85.6% and 83.3% (`analysis/transmission/transmission_robustness.py`).

Regimes. Every half-year sub-period is positive on those sessions, in tenge:

| half-year | sessions | mean | hit rate |
|---|---|---|---|
| 2024 H1 | 27 | +0.489% | 77.8% |
| 2024 H2 | 39 | +0.858% | 84.6% |
| 2025 H1 | 29 | +0.774% | 86.2% |
| 2025 H2 | 30 | +1.033% | 93.3% |
| 2026 H1 | 41 | +0.978% | 73.2% |
| 2026 H2 | 8 | +1.087% | 100.0% |

Produced by `analysis/transmission/transmission_robustness.py`. The largest single session
contributes 2.4% of the total, and removing the three largest leaves a mean of +0.812% with an
83.0% hit rate.

Threshold selection. Selecting the threshold on the first half of the sample and applying it to
the second, over seven candidates:

| threshold | in-sample n | in-sample mean | out-of-sample n | out-of-sample mean | out-of-sample hit rate | out-of-sample over in-sample |
|---|---|---|---|---|---|---|
| 0.0% | 296 | +0.305% | 295 | +0.482% | 70.2% | 158% |
| 0.5% | 223 | +0.355% | 233 | +0.596% | 74.7% | 168% |
| 1.0% | 174 | +0.416% | 167 | +0.793% | 82.0% | 190% |
| 1.5% | 127 | +0.519% | 124 | +0.893% | 83.1% | 172% |
| 2.0% | 88 | +0.738% | 86 | +0.976% | 83.7% | 132% |
| 2.5% | 54 | +0.806% | 54 | +0.923% | 81.5% | 115% |
| 3.0% | 37 | +0.814% | 30 | +0.906% | 76.7% | 111% |

Produced by `analysis/transmission/transmission_robustness.py`; the split is at the median
session, 2024-01-24 to 2025-05-28 against 2025-05-29 to 2026-08-24. The first half selects 3.0%,
the candidate with the highest in-sample mean, not 2%; the 111% ratio an earlier version of this
document quoted belongs to that rule. The 2% rule's own second-half mean is +0.976% on 86 sessions.
Every threshold's second-half mean exceeds its first-half mean, so the table says that the second
half was the stronger half, not that any threshold was validated.

Placebos. The regressor is specific to NASDAQ: on the tenge series the drift on KASE's own prior
move has beta +0.015 (OLS t +0.37) against +0.266 (OLS t +14.18) on the NASDAQ move
(`transmission_robustness.py`); on the USD panel the own-move placebo has beta -0.0182 (HAC t -0.41,
`hac_inference.py`). The regressor is also specific in time. Because the sessions do not overlap,
tomorrow's NASDAQ session begins after today's KASE session has closed, so the next NASDAQ move
cannot reach today's KASE prices and is a valid null for this pair:

| dependent variable | on the prior NASDAQ move | on the next NASDAQ move |
|---|---|---|
| opening gap | +0.2019 (t +10.50), n 591 | +0.0141 (t +1.06), n 590 |
| intraday drift | +0.2718 (t +12.49), n 591 | +0.0020 (t +0.08), n 590 |

Produced by `analysis/transmission/hac_inference.py`. The two future-move regressions carry R2 of
0.001 and 0.000. The test is unavailable for an overlapping pair, where part of the next foreign
session falls inside the current local session and the same regression is mechanically non-null,
so no future-move placebo is reported for KZAP or AIRA.

HAC lag. The headline gap beta carries HAC(1) t of 12.14 and HAC(10) t of 9.32 against the HAC(5)
value of 10.50; the drift beta 12.36 and 12.61 against 12.49.

Unconditional drift. The intraday drift of KASE equities is itself positive on the wider sample of
the later re-analysis; the regression carries an intercept, so the betas are unaffected,
but the
sign-adjusted entry returns in Section 4 include whatever unconditional drift the long side
collects and the short side gives back.

## 11. Economic assessment

The portion of the drift a participant can enter against, taking the price once the open is
established rather than setting the opening print, is +0.380% per session at a five-minute delay.
The round trip is 0.41% with Roll and 0.64% with Corwin-Schultz (Section 2.3), so the net is
-0.033% and -0.257% per session (`analysis/transmission/transmission_tradeable.py`). At fifteen
minutes the entry return is +0.200% and the net -0.213% and -0.437%; at sixty minutes +0.136% and
-0.277% and -0.501%. Only the first traded print clears the band, at +0.443% and +0.219%, and it
is available only to whoever sets that print: the median volume in the first bar of a KSPI session
is 25 shares (`transmission_robustness.py`). An outside participant does not set that print; the
order reaches the book through the market maker whose quote it would hit.

This is the pattern threshold-cointegration models describe (Balke and Fomby 1997; Roll, Schwartz
and Subrahmanyam 2007): a transaction-cost band inside which price differences persist without
converging. The cross-venue premium being flat across the session, +3.03% to +3.16% across
half-hourly buckets with no monotone trend (Section 4), is consistent with deviations sitting
inside such a band rather than closing within it.

The later re-analysis reaches the same verdict on its own sample: after NASDAQ moves of
3% or more, the pass-through to KSPI on KASE is real, and every long-only rule loses after a 60
basis point round trip. The cost band and the execution constraints here describe one retail brokerage
agreement, not the market; the estimates measure what the average participant paid rather than
what a participant with queue priority would pay. Whether the drift is exploitable by a
participant able to short, to finance at wholesale, or to set the opening print is a different
question, and this design cannot answer it. The strategies built on these estimates are audited
in the `kase-strategy-audit` repository, whose cost tables were built on the doubled convention
this document has corrected and are being restated to the convention of Section 2.3.

## 12. Limitations

Costs are estimated from trades, not measured from quotes, and the two estimators disagree by a
factor of two, 0.24% against 0.47% for the full spread. Every net figure is reported against both.
Corwin-Schultz is reported as the median of the positive two-day estimates, with the paper's
treatment printed beside it, and Roll on the liquid sessions only; replacing both with a measured
spread requires a quote feed this project did not sample.

Absorption is measured from trades, so a delay of 5 minutes is 5 minutes of clock during which the
venue trades in one minute of every three, and the exit at the close is a last print that the
later re-analysis shows is not a retail fill. The measurement locates repricing no
earlier than a quote-based one would.

The headline regressor is joined by calendar day; 50 of the 591 opening gaps span no NASDAQ
session or more than one. The aligned-only and interval-return rows of Section 5.1 move the betas
in the third decimal, and the headline keeps the committed panel. The conditioning section runs on
a different join and 535 sessions, so its lagged coefficient is not comparable in level to the
headline.

The store carries raw traded prices with no corporate-actions file, so the transmission regressions
run on dividend-unadjusted returns in which ex-dividend dates enter the dependent variable as
mechanical overnight drops: dependent-variable noise uncorrelated with the NASDAQ regressor,
inflating residual variance without biasing the betas.

The composition and conditional estimates for the two IOB pairs are built on 60-minute foreign
bars, so the KASE close falls inside an hourly bar and the foreign price used is the last bar
boundary before it, up to an hour stale; their sample begins in late August 2024 rather than in
February because Yahoo serves hourly history as a rolling two-year window. Those bars have since
rolled off, so the committed tables under `data/derived/` are the record of that input and cannot
be rebuilt from the source.

The overlap dimension carries two units: an overlap effect and a stock effect are not separately
identified, the pooled contrast averages two opposite-signed pair contrasts, and neither reading
is ruled out. Gonzalo-Granger weights for the non-overlapping pair depend on the alignment
convention and no point estimate is reported for KSPI.

The year-end result rests on eleven annual observations under a free admission floor; Section 9
states its limitations.

Robustness checks that no committed script reproduces were removed from this document rather than
restated qualitatively: FX treatment across alternative rate constructions, extended-hours prices
in the opening gap, stale prints at the open and the close, sensitivity to the 1%/99% trim, known
ex-dividend dates, alternative regressor constructions, and a within-pair test of an overlap
change. Their removal is not a report that they passed.

## References

Amihud, Y., and H. Mendelson (1987). Trading mechanisms and stock returns: an empirical
investigation. *Journal of Finance* 42(3), 533-553.

Ariel, R. A. (1987). A monthly effect in stock returns. *Journal of Financial Economics* 18(1),
161-174.

Balke, N. S., and T. B. Fomby (1997). Threshold cointegration. *International Economic Review*
38(3), 627-645.

Becker, K. G., J. E. Finnerty, and M. Gupta (1990). The intertemporal relation between the U.S. and
Japanese stock markets. *Journal of Finance* 45, 1297-1306.

Chordia, T., R. Roll, and A. Subrahmanyam (2005). Evidence on the speed of convergence to market
efficiency. *Journal of Financial Economics* 76(2), 271-292.

Corwin, S. A., and P. Schultz (2012). A simple way to estimate bid-ask spreads from daily high and
low prices. *Journal of Finance* 67(2), 719-760.

Craig, A., A. Dravid, and M. Richardson (1995). Market efficiency around the clock: some supporting
evidence using foreign-based derivatives. *Journal of Financial Economics* 39, 161-180.

Engle, R. F., T. Ito, and W.-L. Lin (1990). Meteor showers or heat waves? Heteroskedastic
intra-daily volatility in the foreign exchange market. *Econometrica* 58(3), 525-542.

Eun, C. S., and S. Shim (1989). International transmission of stock market movements. *Journal of
Financial and Quantitative Analysis* 24(2), 241-256.

French, K. R., and R. Roll (1986). Stock return variances: the arrival of information and the
reaction of traders. *Journal of Financial Economics* 17(1), 5-26.

Gonzalo, J., and C. W. J. Granger (1995). Estimation of common long-memory components in
cointegrated systems. *Journal of Business and Economic Statistics* 13(1), 27-35.

Grammig, J., M. Melvin, and C. Schlag (2005). Internationally cross-listed stock prices during
overlapping trading hours: price discovery and exchange rate effects. *Journal of Empirical
Finance* 12(1), 139-164.

Griffin, J. M., P. J. Kelly, and F. Nardari (2010). Do market efficiency measures yield correct
inferences? A comparison of developed and emerging markets. *Review of Financial Studies* 23(8),
3225-3277.

Gultekin, M. N., and N. B. Gultekin (1983). Stock market seasonality: international evidence.
*Journal of Financial Economics* 12(4), 469-481.

Hamao, Y., R. W. Masulis, and V. Ng (1990). Correlations in price changes and volatility across
international stock markets. *Review of Financial Studies* 3(2), 281-307.

Hasbrouck, J. (1995). One security, many markets: determining the contributions to price
discovery. *Journal of Finance* 50(4), 1175-1199.

Hong, H., and J. C. Stein (1999). A unified theory of underreaction, momentum trading, and
overreaction in asset markets. *Journal of Finance* 54(6), 2143-2184.

Hou, K., and T. J. Moskowitz (2005). Market frictions, price delay, and the cross-section of
expected returns. *Review of Financial Studies* 18(3), 981-1020.

Ibikunle, G. (2015). Opening and closing price efficiency: do financial markets need the call
auction? *Journal of International Financial Markets, Institutions and Money* 34, 208-227.

Ito, T., R. K. Lyons, and M. T. Melvin (1998). Is there private information in the FX market? The
Tokyo experiment. *Journal of Finance* 53, 1111-1130.

Johansen, S. (1991). Estimation and hypothesis testing of cointegration vectors in Gaussian vector
autoregressive models. *Econometrica* 59(6), 1551-1580.

Karolyi, G. A. (2006). The world of cross-listings and cross-listings of the world: challenging
conventional wisdom. *Review of Finance* 10(1), 99-152.

Keim, D. B. (1983). Size-related anomalies and stock return seasonality: further empirical
evidence. *Journal of Financial Economics* 12(1), 13-32.

Lakonishok, J., and S. Smidt (1988). Are seasonal anomalies real? A ninety-year perspective.
*Review of Financial Studies* 1(4), 403-425.

Lin, W.-L., R. F. Engle, and T. Ito (1994). Do bulls and bears move across borders? International
transmission of stock returns and volatility. *Review of Financial Studies* 7(3), 507-538.

Menkveld, A. J., S. J. Koopman, and A. Lucas (2007). Modeling around-the-clock price discovery for
cross-listed stocks using state space methods. *Journal of Business and Economic Statistics* 25(2),
213-225.

Milunovich, G., and S. Thorp (2007). Measuring equity market integration using uncorrelated
information flows: Tokyo, London and New York. *Journal of Multinational Financial Management*
17(4), 275-289.

Newey, W. K., and K. D. West (1987). A simple, positive semi-definite, heteroskedasticity and
autocorrelation consistent covariance matrix. *Econometrica* 55(3), 703-708.

Otsubo, Y. (2014). International cross-listing and price discovery under trading concentration in
the domestic market: evidence from Japanese firms. *Journal of Empirical Finance* 25, 36-51.

Patell, J. M., and M. A. Wolfson (1984). The intraday speed of adjustment of stock prices to
earnings and dividend announcements. *Journal of Financial Economics* 13(2), 223-252.

Rapach, D. E., J. K. Strauss, and G. Zhou (2013). International stock return predictability: what
is the role of the United States? *Journal of Finance* 68(4), 1633-1662.

Reinganum, M. R. (1983). The anomalous stock market behavior of small firms in January: empirical
tests for tax-loss selling effects. *Journal of Financial Economics* 12(1), 89-104.

Roll, R. (1983). Vas ist das? The turn-of-the-year effect and the return premia of small firms.
*Journal of Portfolio Management* 9(2), 18-28.

Roll, R. (1984). A simple implicit measure of the effective bid-ask spread in an efficient market.
*Journal of Finance* 39(4), 1127-1139.

Roll, R., E. Schwartz, and A. Subrahmanyam (2007). Liquidity and the law of one price: the case of
the futures-cash basis. *Journal of Finance* 62(5), 2201-2234.

Rozeff, M. S., and W. R. Kinney (1976). Capital market seasonality: the case of stock returns.
*Journal of Financial Economics* 3, 379-402.

Schwert, G. W. (2003). Anomalies and market efficiency. In G. M. Constantinides, M. Harris, and
R. M. Stulz (eds), *Handbook of the Economics of Finance*, volume 1, 939-974. Elsevier.

Stoll, H. R., and R. E. Whaley (1990). Stock market structure and volatility. *Review of Financial
Studies* 3(1), 37-71.

Sullivan, R., A. Timmermann, and H. White (2001). Dangers of data mining: the case of calendar
effects in stock returns. *Journal of Econometrics* 105(1), 249-286.

Thorp, S., and G. Milunovich (2006). Information processing and measures of integration: New York,
London and Tokyo. Research Paper 177, Quantitative Finance Research Centre, University of
Technology Sydney. Published in revised form as Milunovich and Thorp (2007).

Wasserstein, R. L., A. L. Schirm, and N. A. Lazar (2019). Moving to a world beyond p < 0.05. *The
American Statistician* 73(sup1), 1-19.

Werner, I. M., and A. W. Kleidon (1996). U.K. and U.S. trading of British cross-listed stocks: an
intraday analysis of market integration. *Review of Financial Studies* 9(2), 619-664.

The verification of 2026-10-12 and the later re-analysis of the same market
(2026-10-16), referred to in the text, are unpublished working documents. Where the text draws on
them it states the finding in place; those statements cannot be checked by a reader against a
published source.
