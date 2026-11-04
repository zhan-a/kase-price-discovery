# Release plan: a fresh-history public copy

This repository has been private while its text was being finalised. It cannot be made public by
flipping its visibility, because two things that must not be published sit in its history:

- five raw Yahoo chart-JSON files under `data/cache/yahoo/`, tracked from commit 4d15202
  (2026-08-26) until commit 381173c on this branch;
- a tracked symlink `data/kase/daily` whose target was an absolute path on the build machine,
  tracked from commit e5f446b until the same commit.

Removing them in a new commit, which this branch does, leaves both in every earlier commit. The
history also holds deleted work that has no successor here (archival figures, an earlier
`analysis/staged/` tree); it is kept in the archived `kase-cross-listing` repository and need not
travel. The repository's own rule is never to rewrite history, so the route is a copy with a new
history: one initial commit holding the finished tree, pushed by the owner to a new public
repository, with this private repository kept as the record. Nothing below has been run; this is
the plan.

## 1. Before the copy

Decisions taken on 2026-10-28:

- The public repository keeps the name `kase-price-discovery`, which `CITATION.cff` and the README
  citation already carry. The private repository is renamed first (for example to
  `kase-price-discovery-private`), then the public one is created under the original name.
- The Yahoo-derived tables stay: `foreign_daily.csv`, `foreign_split.csv`, and the KSPI closes
  inside `transmission_daily.csv` and `regressor_alignment.csv`. The rule, for all three KASE
  repositories: raw vendor feeds (the broker's minute bars, Yahoo chart JSON, AIX data) are never
  published; small derived tables that the published results depend on may be committed, with the
  source named, as `data/README.md` does. Dropping them would make Section 8 of the write-up
  irreproducible for everyone, because Yahoo no longer serves the hourly bars behind
  `foreign_split.csv`.

Steps:

- [ ] Merge `final-writeup` into `main` with a merge commit, or fast-forward; do not squash.
- [ ] Run the clean-clone gate of `docs/reproducibility.md` section 2 on the merged `main` and
      confirm its Status paragraph names the merged commit. The gate's last run is recorded there.
- [ ] Push `main` to the private remote.
- [ ] Add `date-released` to `CITATION.cff` with the day of the public push.

## 2. Make the copy

From a clean checkout of the merged `main`, with no untracked files:

```sh
git -C /path/to/kase-price-discovery status --porcelain      # must print nothing
mkdir /path/to/kase-price-discovery-public
git -C /path/to/kase-price-discovery archive --format=tar HEAD | tar -x -C /path/to/kase-price-discovery-public
cd /path/to/kase-price-discovery-public
git init -b main
git add -A
git commit -m "Price discovery between KASE and its foreign co-listing venues"
```

`git archive` copies only tracked files at `HEAD`, so the exclusions below are applied by
construction; the checklist in section 4 confirms it.

## 3. What the copy excludes

Every path that exists on the build machine or in this repository's history and is not in the
public tree:

| path | why it is excluded |
|---|---|
| `data/cache/yahoo/AIRA_IL_eventsdiv_interval1d_period11600000000_period22000000000.json` | raw Yahoo chart JSON; untracked since 381173c, in history from 4d15202 |
| `data/cache/yahoo/AIRA_IL_interval60m_range2y.json` | same |
| `data/cache/yahoo/KAP_IL_eventsdiv_interval1d_period11600000000_period22000000000.json` | same |
| `data/cache/yahoo/KAP_IL_interval60m_range2y.json` | same |
| `data/cache/yahoo/KSPI_eventsdiv_interval1d_period11600000000_period22000000000.json` | same |
| `data/kase/daily` (symlink) | absolute local path; untracked since 381173c, in history from e5f446b |
| `data/kase/intraday` (symlink) | local attachment of the bar store; never tracked |
| `data/nasdaq/intraday` (symlink) | same |
| `data/kase/intraday/**`, `data/nasdaq/intraday/**`, `data/kase/daily/**` | the bar stores, if ever placed inside the tree; never tracked |
| `analysis/__pycache__/`, `analysis/*/__pycache__/` | bytecode; never tracked |
| `analysis/calendar/yearend_rally_recheck.py` | removed on this branch; its construction is now the floor rule inside `yearend_constructions.py` |
| `figures/microstructure/**`, `figures/overview/**`, `figures/archive/**`, `figures/paper/overlap-regimes.png`, `analysis/staged/**` | deleted earlier in this history; preserved in the archived `kase-cross-listing` repository |
| `.git/` | the private history itself |

The git history also carries the earlier versions of `README.md`, `docs/price-discovery.md` and
the scripts, including the doubled spread convention and the two year-end constructions. The
write-up describes those corrections; the private repository is where their history can be read.

## 4. After the copy, before the push

- [ ] `git -C /path/to/kase-price-discovery-public ls-files` lists exactly the files in section 5.
- [ ] `grep -rn "/Users/" .` in the copy prints nothing.
- [ ] `grep -rnP '[^\x00-\x7F]' --include='*.md' --include='*.cff' --include='*.py' .` prints
      nothing (ASCII only).
- [ ] `grep -rnP '[\x{200b}-\x{200d}\x{2060}\x{feff}\x{00a0}\x{00ad}]' --include='*.py' --include='*.md' --include='*.cff' .`
      prints nothing (no invisible characters).
- [ ] Run the clean-clone gate on the copy with `KASE_STORE` and `KASE_DAILY` exported:
      the thirteen scripts in the README's order, then `git status data/derived` prints nothing
      apart from the three tables that carry a Yahoo series fetched at run time
      (`transmission_daily.csv`, `regressor_alignment.csv`, `yearend_windows.csv`) if Yahoo has
      revised a close, and `analysis/check_figure_literals.py` exits 0. `foreign_legs.py` is
      expected to stop with its cache-absent message.
- [ ] Create the public repository empty, with no README, licence or gitignore of its own, add it
      as `origin` and push `main`.

## 5. The public tree

```
.gitignore
CITATION.cff
LICENSE
README.md
RELEASE.md
requirements.txt
analysis/_store.py
analysis/check_figure_literals.py
analysis/make_figures.py
analysis/panel_diagnostics.py
analysis/calendar/yearend_constructions.py
analysis/calendar/yearend_global_decomposition.py
analysis/transmission/entry_timing.py
analysis/transmission/foreign_legs.py
analysis/transmission/foreign_session_conditioning.py
analysis/transmission/hac_inference.py
analysis/transmission/intraday_transmission.py
analysis/transmission/overlap_comparison.py
analysis/transmission/transmission_robustness.py
analysis/transmission/transmission_tradeable.py
analysis/transmission/venue_liquidity.py
data/README.md
data/derived/entry_delay.csv
data/derived/foreign_daily.csv
data/derived/foreign_split.csv
data/derived/measurement_point_curve.csv
data/derived/overlap_contrasts.csv
data/derived/regressor_alignment.csv
data/derived/spread_estimates.csv
data/derived/transmission_daily.csv
data/derived/venue_liquidity.csv
data/derived/yearend_windows.csv
docs/price-discovery.md
docs/reproducibility.md
figures/paper/entry-delay.png
figures/paper/measurement-point-curve.png
figures/paper/overlap-contrasts.png
figures/paper/venue-liquidity.png
```

## 6. After the push

- [ ] Keep this repository private and unchanged as the record; add a line to its README pointing
      at the public copy, or leave it as it is.
- [ ] The companion repositories `kase-strategy-audit` and `kase-market-data` quote this
      repository's spread convention, year-end figures and `transmission_daily.csv`; their own
      finalisation sessions restate them from this version. `kase-cross-listing` must never acquire
      a remote.
