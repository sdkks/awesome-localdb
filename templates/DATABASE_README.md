# {Database Name}

> **Category:** {Primary Category} | **License:** {License} | **Stars:** ~{Stars}

## Overview

{2-3 sentence description of what the database is and why you'd use it.}

## Quick Start

### Python

```python
# Install: pip install {package}
import {package}

# Connect / open
db = {package}.connect("mydb.{ext}")

# Write
db.execute("INSERT INTO ...")

# Read
results = db.query("SELECT ...")
```

### Rust

```rust
// Cargo.toml: {package} = "..."
use {package};

fn main() {
    let db = {package}::open("mydb.{ext}")?;
    // ...
}
```

<!-- Add more language sections as needed -->

## On-Disk Format

{format_on_disk}

## Core Strengths

- {strength 1}
- {strength 2}
- {strength 3}

## Best Use Cases

1. **{Use Case 1}** — {brief description}
2. **{Use Case 2}** — {brief description}
3. **{Use Case 3}** — {brief description}

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_name.py`](python/src/recipe_name.py) | {what it demonstrates} |
| Rust | [`recipe_name.rs`](rust/src/recipe_name.rs) | {what it demonstrates} |

<!-- Link to each recipe in the language subdirectories -->

## Limitations & Caveats

- {limitation 1}
- {limitation 2}

## Further Reading

- [Official Documentation]({homepage_url})
- [Source Repository]({repository_url})
{comparison_links}
