# chDB

> **Category:** olap | **License:** Apache-2.0 | **Stars:** ~22,000

## Overview

chDB is an in-process SQL OLAP engine powered by ClickHouse. It embeds the full ClickHouse query engine directly into Python, enabling fast analytical queries on Parquet, CSV, JSON, Arrow, and 70+ other formats. With zero external dependencies and a pandas-compatible DataStore API, it delivers up to 20x speedup over pandas for grouped aggregations and complex pipelines.

## Quick Start

### Python

```python
# Install: pip install chdb
import chdb

# Run a SQL query against a CSV file — returns results as text
result = chdb.query("""
    SELECT category, COUNT(*) AS cnt, AVG(price) AS avg_price
    FROM 'file://products.csv'
    GROUP BY category
    ORDER BY cnt DESC
""", "CSV")

print(result)

# Or get a pandas DataFrame directly
df = chdb.query("SELECT * FROM 'file://sales.parquet' LIMIT 10", "DataFrame")
print(df)
```

## On-Disk Format

ClickHouse MergeTree columnar format (persistent or in-memory)

## Core Strengths

- Full ClickHouse SQL engine embedded in-process with zero external dependencies
- Direct querying of Parquet, CSV, JSON, Arrow, ORC and 70+ formats
- pandas-compatible DataStore API with 630+ methods and SQL optimization
- Minimized data copies from C++ to Python via memoryview
- Columnar vectorized execution for fast OLAP aggregations and joins
- Up to 20x faster than pandas on common grouped aggregation operations

## Best Use Cases

1. **Accelerating pandas workflows** — Replace pandas with chDB's DataStore API for up to 20x speedup on groupbys and transformations
2. **In-process analytical queries** — Query local Parquet, CSV, and Arrow files with full ClickHouse SQL, no server needed
3. **Embedded OLAP in data science** — Run complex analytical queries inside Jupyter notebooks and Python scripts
4. **Data pipeline transformations** — Read, transform with SQL, and write across 70+ formats, all in-process
5. **Ad-hoc analysis on large datasets** — Handle datasets too large for pandas without setting up a database server

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Python | [`recipe_olap_query.py`](python/src/recipe_olap_query.py) | Create table, run GROUP BY, window functions, and subqueries |
| Python | [`recipe_data_pipeline.py`](python/src/recipe_data_pipeline.py) | Read CSV, transform with SQL, write to Parquet, all in-process |

## Limitations & Caveats

- Python-only for the bundled bindings; Go, Rust, Node.js, Bun, and C/C++ bindings are available separately
- The DataStore API covers 630+ methods but not every pandas edge case — check the compatibility guide
- Optimized for analytical (OLAP) workloads, not transactional (OLTP) with high concurrent writes
- The chDB package bundles the ClickHouse engine binary, which adds approximately 100 MB to the install size

## Further Reading

- [Official Documentation](https://clickhouse.com/docs/chdb)
- [Source Repository](https://github.com/chdb-io/chdb)
- [ClickBench: Embedded Engine Benchmarks](https://benchmark.clickhouse.com/)
- [chDB Blog: Birth of the Project](https://clickhouse.com/blog/chdb-embedded-clickhouse-rocket-engine-on-a-bicycle)
