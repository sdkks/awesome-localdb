# DuckDB

> **Category:** olap | **License:** MIT | **Stars:** ~38,600

## Overview

DuckDB is an in-process SQL OLAP database management system designed for analytical workloads. Often called "the SQLite for analytics," it runs embedded within the host process with zero external dependencies, supports a rich SQL dialect, and can query Parquet, CSV, and JSON files directly without import. It excels at fast aggregation and joins on single-machine datasets.

## Quick Start

### Python

```python
# Install: pip install duckdb
import duckdb

# Connect — in-memory or persistent file
db = duckdb.connect("analytics.duckdb")

# Query a Parquet file directly, aggregate, and get a DataFrame
results = db.execute("""
    SELECT category, COUNT(*) AS cnt, AVG(price) AS avg_price
    FROM 'products.parquet'
    GROUP BY category
    ORDER BY cnt DESC
""").df()

print(results)
```

### Rust

```rust
// Cargo.toml: duckdb = "1.2"
use duckdb::{Connection, Result};

fn main() -> Result<()> {
    let db = Connection::open_in_memory()?;

    db.execute_batch(
        "CREATE TABLE sales (product TEXT, amount INTEGER);
         INSERT INTO sales VALUES ('Widget', 100), ('Gadget', 200);
         INSERT INTO sales VALUES ('Widget', 150);"
    )?;

    let mut stmt = db.prepare(
        "SELECT product, SUM(amount) AS total FROM sales GROUP BY product"
    )?;
    let rows = stmt.query_map([], |row| {
        Ok((row.get::<_, String>(0)?, row.get::<_, i64>(1)?))
    })?;

    for row in rows {
        let (product, total) = row?;
        println!("{}: {}", product, total);
    }
    Ok(())
}
```

## On-Disk Format

Vectorized Columnar Storage (single `.duckdb` file)

## Core Strengths

- Vectorized columnar execution engine for fast OLAP queries
- Zero-configuration in-process operation with no external daemon
- Direct querying of Parquet, CSV, and JSON files without import
- Full SQL support including window functions, CTEs, and correlated subqueries
- Transactional (ACID) with multi-version concurrency control
- Automatic out-of-core execution for datasets larger than memory

## Best Use Cases

1. **Local analytical queries on Parquet/CSV data lakes** — Query S3 downloads or local files with SQL instead of loading everything into memory
2. **Embedded analytics inside data processing scripts and notebooks** — Replace pandas/Polars in scripts that need SQL power without a server
3. **Interactive data exploration on single-machine datasets** — Fire up the CLI or connect from Python for ad-hoc analysis
4. **In-process transformation pipelines (ELT without a server)** — Read from one format, transform with SQL, write to another format, all in-process
5. **SQL-powered DataFrame operations** — Use DuckDB's SQL engine as a faster alternative to pandas for grouped aggregations and joins

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_analytical_query.py`](python/src/recipe_analytical_query.py) | Connect, create table, run GROUP BY and window function queries |
| Python | [`recipe_data_pipeline.py`](python/src/recipe_data_pipeline.py) | Read CSV, transform with SQL, write to Parquet, all in-process |

## Limitations & Caveats

- Optimized for single-machine analytical (OLAP) workloads, not OLTP with high concurrent writes
- Memory usage can be high for very large datasets without proper memory limits configured
- The Rust crate bundles and compiles C++ from source, making first builds slow

## Further Reading

- [Official Documentation](https://duckdb.org/docs/)
- [Source Repository](https://github.com/duckdb/duckdb)
- [DuckDB Benchmarks](https://duckdblabs.com/benchmarks/)
- [Why DuckDB](https://duckdb.org/why_duckdb)
