#!/usr/bin/env python3
"""Validate all metadata.json files against the JSON Schema.

Usage:
  python3 scripts/validate-metadata.py           # validates all databases
  python3 scripts/validate-metadata.py <path>    # validates a single file
"""

import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("Error: jsonschema library is required. Install with: pip install jsonschema")
    sys.exit(1)


def load_json(path: Path) -> dict:
    """Load and parse a JSON file, returning the parsed data."""
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)


def validate_metadata(metadata_path: Path, schema: dict) -> list[str]:
    """Validate a single metadata.json against the schema. Returns list of error messages."""
    errors = []
    data = load_json(metadata_path)

    try:
        jsonschema.validate(data, schema)
    except jsonschema.ValidationError as e:
        errors.append(f"{metadata_path}: {e.message}")

    # Additional validations beyond JSON Schema
    slug_expected = metadata_path.parent.name
    if data.get("slug") != slug_expected:
        errors.append(
            f"{metadata_path}: slug '{data.get('slug')}' does not match directory name '{slug_expected}'"
        )

    if "category" in data and "categories" in data:
        if data["category"] not in data["categories"]:
            errors.append(
                f"{metadata_path}: primary category '{data['category']}' must be in categories array"
            )

    if "languages" in data:
        seen = set()
        for i, lang in enumerate(data["languages"]):
            key = (lang.get("name"), lang.get("ecosystem"))
            if key in seen:
                errors.append(
                    f"{metadata_path}: duplicate language entry for {key[0]}/{key[1]}"
                )
            seen.add(key)

    return errors


def main():
    repo_root = Path(__file__).resolve().parent.parent
    schema_path = repo_root / "schemas" / "metadata.schema.json"
    databases_dir = repo_root / "databases"

    schema = load_json(schema_path)

    if len(sys.argv) > 1:
        paths = [Path(sys.argv[1])]
    else:
        paths = sorted(databases_dir.glob("*/metadata.json"))

    if not paths:
        print("No metadata.json files found.")
        sys.exit(0)

    all_errors = []
    slugs_seen = {}

    for md_path in paths:
        errors = validate_metadata(md_path, schema)
        all_errors.extend(errors)

        # Check duplicate slugs
        data = load_json(md_path)
        slug = data.get("slug", "")
        if slug and slug not in slugs_seen:
            slugs_seen[slug] = md_path
        elif slug:
            all_errors.append(
                f"{md_path}: duplicate slug '{slug}' (also at {slugs_seen[slug]})"
            )

    if all_errors:
        print(f"\n{len(all_errors)} validation error(s):\n", file=sys.stderr)
        for err in all_errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print(f"OK: {len(paths)} metadata file(s) validated successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
