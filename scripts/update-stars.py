#!/usr/bin/env python3
"""Update github_stars in metadata.json files with live counts from the GitHub API.

Reads repository_url from each databases/*/metadata.json, extracts the GitHub
owner/repo, fetches the current stargazers_count, and writes the value back.

Non-GitHub repository URLs are skipped with a warning.

Requires the GitHub CLI (gh) for authentication.  In CI, GITHUB_TOKEN is used
automatically; locally you must be logged in via ``gh auth login``.

Usage:
  python3 scripts/update-stars.py              # update all databases
  python3 scripts/update-stars.py --dry-run     # print what would change
  python3 scripts/update-stars.py <slug>        # update a single database
  python3 scripts/update-stars.py --help
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import NamedTuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DATABASES_DIR = REPO_ROOT / "databases"

# GitHub repository URLs have the form https://github.com/<owner>/<repo>
_GITHUB_REPO_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")

# Be polite to the API — small delay between requests (seconds)
_API_DELAY = 0.15


class RepoRef(NamedTuple):
    owner: str
    repo: str


def parse_github_repo(url: str) -> RepoRef | None:
    """Extract (owner, repo) from a GitHub URL, or None if it isn't one."""
    m = _GITHUB_REPO_RE.match(url.rstrip("/"))
    if not m:
        return None
    return RepoRef(m.group(1), m.group(2))


def fetch_stars(owner: str, repo: str) -> int:
    """Return the current stargazers_count for the given GitHub repo."""
    result = subprocess.run(
        [
            "gh", "api",
            f"repos/{owner}/{repo}",
            "--jq", ".stargazers_count",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise RuntimeError(
            f"gh api failed for {owner}/{repo}: {stderr or 'unknown error'}"
        )
    try:
        return int(result.stdout.strip())
    except ValueError:
        raise RuntimeError(
            f"unexpected output from gh api for {owner}/{repo}: {result.stdout!r}"
        )


def update_metadata(path: Path, new_stars: int, dry_run: bool) -> bool:
    """Update github_stars in a metadata.json file.  Returns True if changed."""
    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        print(f"  [ERROR] Could not read {path}: {e}", file=sys.stderr)
        return False

    old_stars = data.get("github_stars")
    if old_stars == new_stars:
        return False

    if dry_run:
        return True  # would change

    data["github_stars"] = new_stars
    with open(path, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Update github_stars from live GitHub API data.")
    parser.add_argument(
        "slug", nargs="?",
        help="Update a single database by slug (directory name).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without writing files.",
    )
    args = parser.parse_args()

    if not DATABASES_DIR.is_dir():
        print(f"No databases directory found at {DATABASES_DIR}", file=sys.stderr)
        return 1

    if args.slug:
        paths = [DATABASES_DIR / args.slug / "metadata.json"]
        if not paths[0].is_file():
            print(f"No metadata.json found for slug '{args.slug}'", file=sys.stderr)
            return 1
    else:
        paths = sorted(DATABASES_DIR.glob("*/metadata.json"))

    if not paths:
        print("No metadata.json files found.")
        return 0

    updated: list[tuple[str, int, int]] = []  # (slug, old, new)
    errors: list[str] = []
    skipped: list[str] = []

    for i, md_path in enumerate(paths):
        slug = md_path.parent.name

        try:
            with open(md_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"{slug}: could not read metadata — {e}")
            continue

        repo_url = data.get("repository_url", "")
        ref = parse_github_repo(repo_url)
        if ref is None:
            skipped.append(f"{slug}: not a GitHub repo ({repo_url})")
            continue

        try:
            stars = fetch_stars(ref.owner, ref.repo)
        except RuntimeError as e:
            errors.append(str(e))
            continue

        old = data.get("github_stars")
        if old == stars:
            print(f"  {slug}: unchanged ({stars} stars)")
        else:
            changed = update_metadata(md_path, stars, args.dry_run)
            if changed:
                tag = "DRY-RUN" if args.dry_run else "UPDATED"
                print(f"  [{tag}] {slug}: {old} -> {stars}")
                updated.append((slug, old or 0, stars))
            else:
                print(f"  {slug}: unchanged ({stars} stars)")

        if i < len(paths) - 1:
            time.sleep(_API_DELAY)

    # ── Summary ──────────────────────────────────────────────────────────
    print()
    total = len(paths)
    if errors:
        print(f"  Errors: {len(errors)}")
        for e in errors:
            print(f"    {e}")
    if skipped:
        print(f"  Skipped (non-GitHub): {len(skipped)}")
        for s in skipped:
            print(f"    {s}")

    if args.dry_run:
        print(f"  Would update {len(updated)} / {total} metadata files.")
    else:
        print(f"  Updated {len(updated)} / {total} metadata files.")
        if updated:
            print("\n  Rebuild the site index to reflect changes in the UI:")
            print("    bash scripts/build-index.sh")

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
