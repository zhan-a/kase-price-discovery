# Reproducibility policy

This file is a commitment made in advance, not a description written afterwards.
It applies to all three repositories in this project: `kase-market-data`,
`kase-price-discovery` and `kase-strategy-audit`.

## 1. Every published number comes from committed code

No number, table or figure enters a writeup unless a script in the repository
produces it. A figure that plots stored constants is an assertion, not a figure,
and does not satisfy this rule.

The rule exists because this project has repeatedly failed it. Numbers computed
in a working session and pasted into a document cannot be audited later, because
the session that produced them is gone. When such a number is wrong there is no
way to find out, and when it is right there is no way to show it.

## 2. Clean-clone regeneration before any release

Before a repository is made public, or a version is tagged, or a writeup is
submitted anywhere:

1. Clone the repository fresh into an empty directory.
2. Install from `requirements.txt` only.
3. Rebuild or attach the data store as `data/README.md` describes.
4. Run every analysis script.
5. Compare every number in every writeup against the output.
6. Run `analysis/check_figure_literals.py`. It greps the plotting code for
   numeric literals and fails on any that is not a styling parameter. Step 5
   cannot see this class of defect, because a constant typed into plotting
   source appears in neither the writeup nor any script's output.
7. Scan for invisible characters: zero-width spaces and joiners, non-breaking
   spaces, byte-order marks and soft hyphens. None of them shows in an editor or
   a diff, all of them survive a copy-paste out of a browser or a PDF, and a soft
   hyphen inside an identifier breaks a search that looks correct on screen. All
   four repositories were clean on 2026-08-27; the check exists to keep them that
   way, so a hit means something was pasted rather than typed.

   ```sh
   grep -rnP '[\x{200b}-\x{200d}\x{2060}\x{feff}\x{00a0}\x{00ad}]' \
     --include='*.py' --include='*.md' --include='*.cff' .
   ```

Any number the committed code does not produce is a defect. Either the script is
written or the number comes out of the writeup. There is no third option.

## 3. Replication is blind, or it is review

When an analysis is re-derived as a check, the person or process doing the
re-derivation is given the specification only: the regression equation, the
sample definition, the variable construction, the data. Not the results section,
not the tables, not the figures, not the target values.

An instruction to "report disagreements rather than tune toward the published
number" cannot be followed by anyone who already knows the published number. The
knowledge does the tuning whether or not the intent is there. Specification in,
number out, compare afterwards.

## 4. Disagreement rule, pre-committed

If a re-derivation disagrees with a published number, and the
published number originates from a working session rather than from committed
code, the re-derivation stands and the published number is retracted.

Not reconciled. Not averaged. Not investigated until the difference is explained
away. Retracted, with the re-derived value published in its place and the
disagreement stated.

The reasoning is that an unauditable number has no standing against an auditable
one, whatever their relative provenance feels like at the time. This rule is
written here before any such disagreement has arisen, because the temptation to
reconcile arrives together with the disagreement and not before it. The same
discipline applies as to pinning a hypothesis before seeing the data.

Where both numbers come from committed code, the disagreement is a defect in one
of them and is resolved on the merits.

## 5. Trials are reported

Every backtest is reported with the number of trials behind it, following
Lopez de Prado's third law of backtesting. The counts are in the
`kase-strategy-audit` writeup. A specification chosen after seeing results is
labelled as such at the point of use.

## 6. A recomputation is not evidence against committed code

An uncommitted script that disagrees with committed output is a hypothesis about
a bug. The first candidate for that bug is the uncommitted script.

Before a disagreement is treated as a defect in the committed code, the
challenging script must itself be committed and reviewed to the same standard. An
ad-hoc reconstruction written to check a number is not an independent
measurement: it was written by someone who knew the target, it has been run once,
and nobody has read it.

This is not a counsel of conservatism. It is what the record shows. Two
reconstructions written in a single evening to check committed numbers were both
wrong, and in both cases the committed number was right:

- One mixed raw-tenge prices from the bar store with USD aggregates from the
  session panel and produced a beta of -54.87. That one announced itself.
- One rebuilt the session set from the store rather than using the panel,
  reported a sample of 555 against the correct 591, and produced an opening-gap
  beta of 0.273 against the correct 0.2986. That one did not announce itself. It
  looked like a plausible small disagreement, and it was nearly used to retract a
  correct result.

The second case is the dangerous one, and it is the reason the rule in Section 4
turns on auditability rather than on which script ran most recently.

The procedure when a recomputation disagrees:

1. Run the committed script. Not a reconstruction of it, the script itself.
2. If the committed script reproduces the published number, the recomputation is
   the outlier and carries the burden of proof.
3. If it does not, the published number is stale and is updated to what the
   committed code produces.
4. Only where no committed code produces the number does Section 4 apply.

## 7. Stored constants are not results

A figure or table that plots values typed into the source is an assertion
wearing the costume of a computation, and it is worse than no figure, because it
cannot go stale visibly. It will agree with whatever it was copied from at the
moment of copying and will silently diverge from the data thereafter.

Where a figure disagrees with the analysis it illustrates, the disagreement is
the finding and the correct response is to publish both and explain them, never
to type the expected values into the plotting code.

The operational rule, which makes a stale figure impossible rather than merely
catchable:

> **No figure plots a literal. Every plotted series is read from a committed file
> under `data/derived/`, written by a committed analysis script.**

Plotting code draws; it does not measure. It holds no regression, no aggregation
over the bar store, and no typed values. Layout numbers are named constants at
the top of the file, so that any number appearing inside a plotting call is
either data or a name.

The rule is stated this way because the weaker version, "do not hardcode figure
values", was already the intent and was broken twice in this repository. The
overlap figure plotted three arrays of betas typed into `make_figures.py` and
went stale against the section it illustrated. The measurement-point curve was
computed inside `make_figures.py`, which meant the table in the writeup was
quoting the stdout of the plotting script, and the figure and the table were one
implementation, so neither checked the other. Both survived a clean-clone
gate, because that gate compares document numbers against script output and a
constant in plotting source is in neither set.

Enforcement is `analysis/check_figure_literals.py`, run as step 6 of Section 2.
It fails on a numeric literal outside a styling context, on an import or call
that performs analysis, and on a data read from outside `data/derived/`. It is
tested against both of the historical defects above. The check is implemented in
`kase-price-discovery`; it must be ported to any other repository in this project
before that repository is gated, and `kase-strategy-audit` has plotting code that
has not yet been checked.

## Status

`kase-price-discovery` has been through the Section 2 procedure three times.

At commit `a4b2d1e` (2026-08-27): cloned fresh into an empty directory, installed from
`requirements.txt` into a new virtual environment, the bar store attached as `data/README.md`
describes, all analysis scripts run in dependency order, the figures redrawn, step 6 clean, and
every decimal number in the two documents compared against the output; 444 numbers were checked.
An unpublished verification of 2026-10-12 then found what that gate cannot see: a convention
error (two full spreads read as half spreads), a misaligned regressor on some sessions, a
threshold reported from the wrong rule, and two committed year-end constructions that disagreed.
Each is described where it was corrected in `docs/price-discovery.md`.

At commit `05684ca` on the `final-writeup` branch (2026-10-28), after those corrections: cloned
fresh into an empty directory, a new virtual environment installed from `requirements.txt` only
(pandas 2.3.3, numpy 2.5.4, scipy 1.18.1, statsmodels 0.15.0, matplotlib 3.11.2, pyarrow 26.0.0,
each newer than the build that wrote the committed files), the two stores attached through
`KASE_STORE` and `KASE_DAILY` and nothing else, the thirteen scripts of the README run in its
order, then `git status data/derived` empty: all ten committed tables reproduced byte for byte,
including the two that depend on a Yahoo fetch at run time. The printed outputs differed from the
build environment only in deprecation warnings that pandas 2.3.3 emits on numpy 2.5.4 when a
`Timedelta` is built, and in a `ComplexWarning` from statsmodels' Johansen routine; no numeric line
differed. Step 6 passed. Step 7 found nothing, and a scan for any non-ASCII byte in the scripts and
documents found nothing. `foreign_legs.py`, which rebuilds the two foreign-leg tables from Yahoo
chart data this tree does not hold, stopped with its message as designed. Every number in
`README.md`, `docs/price-discovery.md`, `data/README.md` and `RELEASE.md` was then searched for in
the outputs and the committed tables at digit boundaries; nothing was unmatched apart from section
numbers, page numbers in references, the Python version and the row count of one table. Figure
PNGs are byte-identical within one matplotlib build and not across builds, and no claim is made
that they are. The same day, a re-derivation of every changed script from the raw
store matched every count and coefficient and found one further defect, since fixed and recorded
in Section 8.2 of the write-up.

At commit `a01045d` on `main` (2026-10-30), the fast-forward merge of `final-writeup`, which
after `05684ca` changed documents only, tree `250d2dc42fa0bd90748e6b39cf529c279afca4e0`: cloned
fresh into an empty directory, a new virtual environment installed from `requirements.txt` only
(the same package versions as above, under Python 3.13.5), the two stores attached through
`KASE_STORE` and `KASE_DAILY` and nothing else, the thirteen scripts of the README run in its
order, every one exiting 0, then `git status data/derived` empty: all ten committed tables
reproduced byte for byte, including the two that depend on a Yahoo fetch at run time.
`foreign_legs.py` stopped with its message as designed. Step 6 passed, step 7 found nothing, and a
scan for any non-ASCII byte in the scripts and documents found nothing. Every number in
`README.md`, `docs/price-discovery.md`, `data/README.md`, `RELEASE.md`, `CITATION.cff` and this
file was searched for in the outputs and the committed tables at digit boundaries. Unmatched: the
Python version and the package versions; the row counts of the two foreign-leg tables, which
only `foreign_legs.py` prints; the two figures of Section 6 that came from uncommitted
reconstructions; the count recorded for the run of 2026-08-27; and seven shares that Section 3
gives in percent and `panel_diagnostics.py` prints as fractions. Nothing else was unmatched.

`kase-market-data` and `kase-strategy-audit` each record their own gate in their copy of this
file.
