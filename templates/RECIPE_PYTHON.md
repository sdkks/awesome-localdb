# Python Recipe Template

Each recipe is a single-file example in `src/` demonstrating one best use case of the database.

## Directory Structure

```
databases/<db-slug>/python/
├── pyproject.toml
├── src/
│   ├── recipe_use_case_1.py
│   └── recipe_use_case_2.py
└── tests/
    ├── test_use_case_1.py
    └── test_use_case_2.py
```

## pyproject.toml Template

```toml
[project]
name = "awesome-localdb-{db-slug}-python"
version = "0.1.0"
description = "Recipe examples for {Database Name}"
requires-python = ">=3.9"
dependencies = [
    "{package-name}",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Recipe File Template

```python
"""
Recipe: {Use Case Name}
Database: {Database Name}
Description: {What this recipe demonstrates}

Usage: python src/recipe_{slug}.py
"""

def main():
    # 1. Setup — import and open the database
    pass

    # 2. Write — insert or update data
    pass

    # 3. Read — query or retrieve data
    pass

    # 4. Cleanup — close or clean up
    pass


if __name__ == "__main__":
    main()
```

## Test File Template

```python
"""Tests for recipe_{slug}.py"""

from src.recipe_{slug} import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()  # If no exception, test passes


def test_recipe_expected_output():
    """The recipe should produce the expected output."""
    # Add assertions about the recipe's behavior
    pass
```

## Rules

- Recipes must run with `python src/recipe_name.py` from the `python/` directory
- Tests must pass with `pytest` from the `python/` directory
- Use the database's recommended client library — not ORMs or wrappers unless canonical
- Format with `black` (default settings)
- No external services, network calls, or user input required
