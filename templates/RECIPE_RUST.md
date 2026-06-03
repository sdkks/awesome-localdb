# Rust Recipe Template

Each recipe is a single-file example in `src/bin/` demonstrating one best use case of the database.

## Directory Structure

```
databases/<db-slug>/rust/
├── Cargo.toml
├── src/
│   └── bin/
│       ├── recipe_use_case_1.rs
│       └── recipe_use_case_2.rs
└── tests/
    └── integration_test.rs
```

## Cargo.toml Template

```toml
[package]
name = "awesome-localdb-{db-slug}-rust"
version = "0.1.0"
edition = "2021"
description = "Recipe examples for {Database Name}"

[dependencies]
{crate-name} = "{version}"

[dev-dependencies]
```

## Recipe File Template

```rust
//! Recipe: {Use Case Name}
//! Database: {Database Name}
//! Description: {What this recipe demonstrates}
//!
//! Usage: cargo run --bin recipe_{slug}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // 1. Setup — open the database
    let db = {CrateName}::open("mydb")?;

    // 2. Write — insert or update data

    // 3. Read — query or retrieve data

    // 4. Cleanup

    Ok(())
}
```

## Test File Template

```rust
#[test]
fn test_recipe_runs_without_error() {
    // Run the recipe logic and assert expected behavior
}
```

## Rules

- Recipes must run with `cargo run --bin recipe_name` from the `rust/` directory
- Tests must pass with `cargo test` from the `rust/` directory
- Use the database's canonical Rust crate — not wrappers unless they are the standard way
- Format with `cargo fmt`
- No external services, network calls, or user input required
