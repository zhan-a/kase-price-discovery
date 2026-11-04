"""
One place that decides where the bar store lives.

Every analysis script needs the same two directories, and before this module each
resolved them itself. That produced three different environment-variable names,
two scripts that honoured none, and a documented attach procedure that worked for
some scripts and not others. The failure was silent in the worst way: a script
that cannot find data raises somewhere deep in a concat rather than at the point
of the missing path.

Resolution order, for both the minute store and the daily companion:

1. the environment variable, KASE_STORE or KASE_DAILY
2. the directory inside this repository, if it has been populated or symlinked
3. the sibling checkout, for a working copy laid out beside the other repositories

Whatever is chosen, it is checked before it is returned, and a missing store
raises with the paths that were tried.
"""

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _pick(env_var, candidates, marker, what):
    override = os.environ.get(env_var)
    tried = []
    if override:
        p = Path(override)
        if (p / marker).exists():
            return p
        tried.append(f"{p} (from {env_var})")
    for p in candidates:
        if (p / marker).exists():
            return p
        tried.append(str(p))
    raise SystemExit(
        f"{what} was not found. Tried:\n  " + "\n  ".join(tried) +
        f"\nSet {env_var} to the directory containing {marker}, or attach the store as "
        "data/README.md describes."
    )


def store() -> Path:
    """Directory holding kase/intraday and nasdaq/intraday."""
    return _pick(
        "KASE_STORE",
        [REPO / "data", REPO.parent / "trading desk" / "data"],
        Path("kase") / "intraday",
        "The 1-minute bar store",
    )


def daily() -> Path:
    """Directory holding the daily companion parquets, one per ticker."""
    return _pick(
        "KASE_DAILY",
        [REPO / "data" / "kase" / "daily",
         REPO.parent / "kase-market-data" / "data" / "kase" / "daily"],
        Path("KSPI.KZ.parquet"),
        "The daily companion series",
    )
