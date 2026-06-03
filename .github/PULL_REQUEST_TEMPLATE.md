---
name: New Database or Examples
about: Add a new embedded database or new language examples
title: 'Add: '
labels: ''
assignees: ''
---

## What

<!-- Database name and what this PR adds (new database, new language examples, metadata update, etc.). -->

## Database Qualification

<!-- For new databases: explain why this database qualifies as embedded (no mandatory daemon/server). Include a link to the project's official repository. -->

## Language Examples Included

<!-- List which language subdirectories and recipes are included. -->

## AI Disclosure

<!-- This project welcomes AI-assisted contributions. See AI_CONTRIBUTING.md for the full policy. -->

- [ ] This PR contains AI-assisted code

If yes, briefly describe tooling used:

## Breaking Changes

<!-- Does this PR change the metadata schema, SPA API, or build script output? If yes, describe the impact. -->

## Screenshots

<!-- For SPA changes, include before/after screenshots. -->

## Pre-submission Checklist

- [ ] I installed pre-commit hooks (`pre-commit install`) before committing
- [ ] I tested all changes locally (`pytest`, `cargo test`, etc.)
- [ ] I ran `bash scripts/build-index.sh` and committed the updated `site/index.json` if changed
- [ ] `metadata.json` passes JSON Schema validation (`python3 scripts/validate-metadata.py`)
- [ ] All recipe tests pass with the language's standard test command
- [ ] README.md includes inline snippets for all supported languages
- [ ] I have read and agree to the [Contributing Guide](CONTRIBUTING.md)
- [ ] I have read the [AI Contribution Policy](AI_CONTRIBUTING.md)
