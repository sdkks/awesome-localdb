# Contributing to Awesome Local DB

Thanks for helping build the most useful catalog of embedded databases.

## Before You Start

- **Find or create an issue** for your change. This lets maintainers and the community discuss scope before you write code.
- **Check existing PRs** to avoid duplicating work.
- **Read the [AI Contribution Policy](AI_CONTRIBUTING.md)** if you plan to use AI tools.

## Scope

A database qualifies for inclusion if it **can run embedded** — imported as a library or linked into a binary, without requiring a separate server or daemon process. The database must be actively maintained (`active` or `slow` maintenance status) or a significant new project (`beta`). Archived or abandoned projects are not accepted.

## Local Development

### Prerequisites

- Python 3.9+
- `pip install jsonschema pre-commit`
- `jq` (for build-index.sh)

### Setup

```bash
# Clone and enter the repo
git clone https://github.com/sdkks/awesome-localdb.git
cd awesome-localdb

# Install pre-commit hooks
pre-commit install

# Validate everything is set up
python3 scripts/validate-metadata.py
bash scripts/build-index.sh

# Serve the SPA locally
python3 -m http.server -d site 8080
```

### Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to catch issues before they reach CI. After running `pre-commit install`, the following checks run on every commit:

| Hook | What it checks |
|------|---------------|
| `trailing-whitespace` | Removes trailing whitespace |
| `end-of-file-fixer` | Ensures files end with a newline |
| `check-yaml` / `check-json` | Validates YAML and JSON syntax |
| `validate-metadata` | Validates `metadata.json` against the JSON Schema |
| `build-index` | Rebuilds `site/index.json` |

You can run all hooks manually at any time:

```bash
pre-commit run --all-files
```

## Adding a New Database

1. **Pick a slug** — lowercased, hyphenated identifier matching the directory name (e.g., `sqlite`, `libsql`, `duckdb`).
2. **Create the directory** at `databases/<slug>/`.
3. **Write `metadata.json`** following the schema at `schemas/metadata.schema.json`. All required fields must be populated.
4. **Write `README.md`** using the [database README template](templates/DATABASE_README.md). Include inline code snippets for at least one language.
5. **Add at least one language example** as a self-contained project in `databases/<slug>/<lang>/` with:
   - A package manager config file (`pyproject.toml`, `Cargo.toml`, `go.mod`, `package.json`, etc.)
   - At least one recipe file in `src/`
   - At least one test file in `tests/`
   - Tests must pass with a single standard command
6. **Run `bash scripts/build-index.sh`** to regenerate `site/index.json` and verify your metadata passes validation.
7. **Open a pull request** using the PR template.

## Adding Examples for an Existing Database

1. Create a new language subdirectory at `databases/<slug>/<lang>/`.
2. Follow the recipe template for your language (see `templates/`).
3. Update the database's `README.md` to include an inline snippet for the new language.
4. If the database's `metadata.json` doesn't list this language, add it to the `languages` array.
5. Run tests and `build-index.sh` before opening a PR.

## Testing Your Changes

```bash
# Python recipes
cd databases/<slug>/python
pip install -e ".[dev]"
python -m pytest -v

# Rust recipes
cd databases/<slug>/rust
cargo test
cargo fmt --check

# Validate metadata and rebuild index
cd /path/to/repo-root
python3 scripts/validate-metadata.py
bash scripts/build-index.sh
```

## Code Style

- **Python:** Format with [Black](https://github.com/psf/black) (`black .`). Follow PEP 8.
- **Rust:** Format with `cargo fmt`. Follow standard Rust conventions.
- **JavaScript:** No build step. Use consistent indentation (2 spaces). Keep it readable.
- **Go:** Format with `gofmt`. Follow effective Go conventions.

## Metadata Schema

The `metadata.json` schema is defined in `schemas/metadata.schema.json`. Key rules:

- `category` must be one of 10 predefined values (the primary category)
- `categories` must include the primary category plus any additional applicable categories
- `languages` must use canonical names from the schema's enum
- `tags` must use values from the closed-set enum (42 predefined tags)
- `custom_tags` allows up to 5 freeform tags for niche descriptors — use sparingly and expect reviewer scrutiny

### Custom Tags

`custom_tags` is for descriptors that do not fit into the standard tag set. When you use a custom tag:

- Document why the standard tags are insufficient in your PR description.
- Prefer a single custom tag over multiple — the field is for truly niche descriptors.
- If a custom tag feels broadly useful, open an issue to propose promoting it to the main `tags` enum.

Common custom tags that have been promoted to the main set include `vector-search` and `p2p`. Before adding a new custom tag, check whether a standard tag already covers the concept.

### Updating an Existing Database

To update a database that is already in the catalog:

1. Edit its `databases/<slug>/metadata.json` with the new or corrected information.
2. If changing tags or categories, verify they pass schema validation.
3. If updating `github_stars`, round to the nearest 100.
4. Run `python3 scripts/validate-metadata.py` and `bash scripts/build-index.sh`.
5. Open a PR explaining what changed and why.

The monthly [staleness check](.github/workflows/staleness-check.yml) workflow prints warnings when `github_stars` may be stale, but it does not block builds. Maintainers may prompt you to refresh star counts during review.

## Site & Decision Tree

The SPA at `site/` is a client-side filtering application powered by `site/index.json` (generated by `build-index.sh`) and `site/decision-tree.json` (the interactive wizard). When modifying schemas, tagsets, or category values:

- `site/decision-tree.json` — the interactive "Find Your Database" wizard. Each step narrows results by category, tags, and language. New languages, categories, or commonly used tags should have corresponding choices here.
- `site/index.json` and `site/filter-options.json` — regenerated by `build-index.sh`. Never edit these manually.
- `site/js/app.js` — the client-side search and filter engine. Modify only when changing filter behavior or tree logic.

Before committing changes that touch the tag enum or categories, run `bash scripts/build-index.sh` and confirm the generated files are up to date.

## Troubleshooting

### `validate-metadata.py` fails with a validation error

- Check that all `tags` values are in the closed-set enum in `schemas/metadata.schema.json`.
- Verify `categories` includes the primary `category`.
- Ensure `custom_tags` values match the pattern `^[a-z][a-z0-9-]*$`.
- The total number of `tags` must not exceed 14.

### `build-index.sh` fails

- Ensure `jq` and `python3` are installed (`python3` must have `jsonschema`).
- Check that all `metadata.json` files are valid JSON and pass `validate-metadata.py`.
- If you added a new database directory, make sure it contains a valid `metadata.json`.

### Stale github_stars warning

- A monthly CI job prints warnings when a `metadata.json` hasn't been updated in 6+ months.
- To fix: check the current star count on GitHub, update `github_stars` (rounded to nearest 100), and push the change.

## Review Process

Maintainers will check that:
- All CI checks pass (schema validation, index regeneration, recipe tests)
- The database qualifies as embedded (no mandatory daemon)
- Metadata is accurate and complete
- Example code is idiomatic, tested, and follows the template structure
- Pre-commit hooks were installed and ran (verified by CI)

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/). Be respectful, constructive, and welcoming.

## License

By contributing, you agree that your contributions will be licensed under the MIT License. See [LICENSE](LICENSE).
