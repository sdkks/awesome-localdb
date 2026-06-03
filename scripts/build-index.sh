#!/usr/bin/env bash
# build-index.sh — Aggregate databases/*/metadata.json into site/index.json
#
# Usage: bash scripts/build-index.sh
#
# Walks databases/, validates each metadata.json against the schema,
# aggregates entries, enriches with search tokens and computed fields,
# and writes site/index.json and site/filter-options.json.
# Exits non-zero on validation failure.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DATABASES_DIR="$REPO_ROOT/databases"
SITE_DIR="$REPO_ROOT/site"
SCHEMAS_DIR="$REPO_ROOT/schemas"
INDEX_FILE="$SITE_DIR/index.json"
FILTER_FILE="$SITE_DIR/filter-options.json"
METADATA_SCHEMA="$SCHEMAS_DIR/metadata.schema.json"
INDEX_SCHEMA="$SCHEMAS_DIR/index.schema.json"

# ─── Prerequisite checks ──────────────────────────────────────────────

command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required."; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Error: jq is required."; exit 1; }

# ─── Validate all metadata files ──────────────────────────────────────

echo "Validating metadata files..."
python3 "$SCRIPT_DIR/validate-metadata.py" || exit 1

# ─── Compute search tokens ────────────────────────────────────────────

compute_tokens() {
  # Read JSON from stdin, output JSON array of lowercased unique search tokens.
  jq -c '
    [
      .name,
      .slug,
      .category,
      .categories[]?,
      .description,
      .license,
      .languages[]?.name,
      .languages[]?.ecosystem,
      .tags[]?,
      .custom_tags[]?,
      .format_on_disk,
      .core_strengths[]?,
      .best_use_cases[]?
    ]
    | join(" ")
    | ascii_downcase
    | gsub("[^a-z0-9 ]"; " ")
    | split(" ")
    | map(select(length > 0))
    | unique
  ' 2>/dev/null || echo "[]"
}

# ─── Build the index ──────────────────────────────────────────────────

echo "Building index..."

GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Check if databases directory has any subdirectories
DB_COUNT=0
if [ -d "$DATABASES_DIR" ]; then
  DB_COUNT=$(find "$DATABASES_DIR" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
fi

if [ "$DB_COUNT" -eq 0 ]; then
  # Empty index
  jq -n \
    --arg generated_at "$GENERATED_AT" \
    '{
      generated_at: $generated_at,
      schema_version: 1,
      count: 0,
      databases: []
    }' > "$INDEX_FILE"
else
  # Build databases array
  DB_ARRAY="["

  FIRST=true
  for db_dir in "$DATABASES_DIR"/*/; do
    [ -d "$db_dir" ] || continue
    MD_FILE="${db_dir}metadata.json"
    [ -f "$MD_FILE" ] || continue

    SLUG="$(basename "$db_dir")"

    # Check for example directories
    HAS_EXAMPLES="false"
    if find "$db_dir" -mindepth 2 -maxdepth 2 -type f -name "*.py" -o -name "*.rs" -o -name "*.go" -o -name "*.js" 2>/dev/null | grep -q .; then
      HAS_EXAMPLES="true"
    fi

    # Compute search tokens for this database
    TOKENS=$(compute_tokens < "$MD_FILE")

    # Build the enriched JSON entry
    ENTRY=$(jq -c \
      --arg repo_path "databases/$SLUG" \
      --argjson has_examples "$HAS_EXAMPLES" \
      --argjson search_tokens "$TOKENS" \
      '. + {
        _repo_path: $repo_path,
        _has_examples: $has_examples,
        _search_tokens: $search_tokens
      }' "$MD_FILE")

    if [ "$FIRST" = true ]; then
      FIRST=false
    else
      DB_ARRAY+=","
    fi
    DB_ARRAY+="$ENTRY"
  done

  DB_ARRAY+="]"

  echo "$DB_ARRAY" | jq -s \
    --arg generated_at "$GENERATED_AT" \
    '{
      generated_at: $generated_at,
      schema_version: 1,
      count: .[0] | length,
      databases: .[0]
    }' > "$INDEX_FILE"
fi

# ─── Build filter options ─────────────────────────────────────────────

echo "Building filter options..."

jq -n \
  --argjson categories "$(jq '[.databases[]?.category] | unique | sort' "$INDEX_FILE")" \
  --argjson all_categories "$(jq '[.databases[]?.categories[]?] | unique | sort' "$INDEX_FILE")" \
  --argjson languages "$(jq '[.databases[]?.languages[]?.name] | unique | sort' "$INDEX_FILE")" \
  --argjson ecosystems "$(jq '[.databases[]?.languages[]?.ecosystem] | unique | sort' "$INDEX_FILE")" \
  --argjson licenses "$(jq '[.databases[]?.license] | unique | sort' "$INDEX_FILE")" \
  --argjson statuses "$(jq '[.databases[]?.maintenance_status] | unique | sort' "$INDEX_FILE")" \
  --argjson tags "$(jq '[.databases[]?.tags[]?] | unique | sort' "$INDEX_FILE")" \
  '{
    categories: $categories,
    all_categories: $all_categories,
    languages: $languages,
    ecosystems: $ecosystems,
    licenses: $licenses,
    statuses: $statuses,
    tags: $tags
  }' > "$FILTER_FILE"

# ─── Validate generated index ─────────────────────────────────────────

echo "Validating generated index..."

python3 -c "
import json, sys
from pathlib import Path
sys.path.insert(0, '$(dirname "$SCRIPT_DIR")')

# Basic structural validation of the generated index
with open('$INDEX_FILE') as f:
    data = json.load(f)

errors = []

if not isinstance(data.get('generated_at'), str):
    errors.append('generated_at must be a string')
if data.get('schema_version') != 1:
    errors.append('schema_version must be 1')
if not isinstance(data.get('count'), int):
    errors.append('count must be an integer')
if not isinstance(data.get('databases'), list):
    errors.append('databases must be an array')

if data.get('count') != len(data.get('databases', [])):
    errors.append(f'count ({data[\"count\"]}) != databases.length ({len(data.get(\"databases\", []))})')

for i, db in enumerate(data.get('databases', [])):
    for field in ['name', 'slug', 'category', 'description', '_repo_path']:
        if field not in db:
            errors.append(f'databases[{i}]: missing required field \"{field}\"')

if errors:
    for e in errors:
        print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
"

# ─── Summary ──────────────────────────────────────────────────────────

INDEX_SIZE=$(wc -c < "$INDEX_FILE" | tr -d ' ')
echo ""
echo "  Databases: $DB_COUNT"
echo "  Index size: ${INDEX_SIZE} bytes"
echo "  Output: $INDEX_FILE"
echo "  Filters: $FILTER_FILE"
echo ""
echo "Done."
