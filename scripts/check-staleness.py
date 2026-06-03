#!/usr/bin/env python3
"""Check for potentially stale github_stars values in metadata.json files.

Compares the last-modified time of each metadata.json against the current date.
Prints a warning if a file hasn't been updated in more than 6 months and still
carries a github_stars value (which may have drifted).

This script never fails the build — it only prints warnings.  The goal is to
prompt manual review, not to block PRs or deploys.

Usage:
  python3 scripts/check-staleness.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────

STALE_THRESHOLD_DAYS = 180  # 6 months — warn if no metadata update in this window
REPO_ROOT = Path(__file__).resolve().parent.parent
DATABASES_DIR = REPO_ROOT / "databases"


# ─── Helpers ─────────────────────────────────────────────────────────────

def last_modified_utc(path: Path) -> datetime:
    """Return the file's last-modified time as a UTC-aware datetime."""
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime, tz=timezone.utc)


def check_file(metadata_path: Path) -> list[str]:
    """Return a list of warning strings for the given metadata.json, if any."""
    warnings: list[str] = []

    try:
        with open(metadata_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        warnings.append(f"{metadata_path}: could not read file — {e}")
        return warnings

    # Does the file carry a github_stars value?
    stars = data.get("github_stars")
    if stars is None:
        # No stars field — nothing to check
        return warnings

    modified = last_modified_utc(metadata_path)
    now = datetime.now(tz=timezone.utc)
    age_days = (now - modified).days

    if age_days > STALE_THRESHOLD_DAYS:
        slug = data.get("slug", metadata_path.parent.name)
        days_str = f"{age_days} days"
        warnings.append(
            f"STALE: {slug} — github_stars={stars}, last metadata update {modified.strftime('%Y-%m-%d')} "
            f"({days_str} ago, exceeds {STALE_THRESHOLD_DAYS}-day threshold). "
            f"Consider re-checking the star count and updating the metadata."
        )

    return warnings


# ─── Main ────────────────────────────────────────────────────────────────

def main() -> int:
    if not DATABASES_DIR.is_dir():
        print(f"No databases directory found at {DATABASES_DIR}")
        return 0

    metadata_files = sorted(DATABASES_DIR.glob("*/metadata.json"))
    if not metadata_files:
        print("No metadata.json files found.")
        return 0

    all_warnings: list[str] = []
    for md_path in metadata_files:
        all_warnings.extend(check_file(md_path))

    total = len(metadata_files)

    if all_warnings:
        print(f"\n  {len(all_warnings)} / {total} metadata files may have stale github_stars:\n")
        for w in all_warnings:
            print(f"  [WARNING] {w}")
        print(f"\n  Staleness check complete — {len(all_warnings)} warning(s) (build NOT failed).")
    else:
        print(f"  All {total} metadata files are within the {STALE_THRESHOLD_DAYS}-day freshness window.")
        print("  Staleness check complete — 0 warnings.")

    # Never fail the build — this is purely advisory
    return 0


if __name__ == "__main__":
    sys.exit(main())
