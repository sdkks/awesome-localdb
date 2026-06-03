"""
Recipe: Analytical Query
Database: DuckDB
Description: Demonstrate DuckDB as an analytical query engine with
             GROUP BY aggregation and window functions on local data.

Usage: python src/recipe_analytical_query.py
"""

import duckdb


def main() -> None:
    """Run analytical queries including GROUP BY and window functions."""
    # 1. Setup — connect to an in-memory database
    db = duckdb.connect(":memory:")

    # 2. Create sample data inline (simulating a sales dataset)
    db.execute("""
        CREATE TABLE sales AS
        SELECT * FROM (VALUES
            ('Electronics', 'North', 1200, DATE '2025-01-15'),
            ('Electronics', 'South',  800, DATE '2025-01-20'),
            ('Electronics', 'North', 1500, DATE '2025-02-10'),
            ('Clothing',    'North',  300, DATE '2025-01-18'),
            ('Clothing',    'South',  450, DATE '2025-02-05'),
            ('Clothing',    'East',   600, DATE '2025-02-22'),
            ('Groceries',   'North',  200, DATE '2025-01-10'),
            ('Groceries',   'South',  250, DATE '2025-02-14'),
            ('Groceries',   'East',   180, DATE '2025-03-01'),
            ('Electronics', 'East',  2200, DATE '2025-03-05'),
        ) AS t(category, region, amount, sale_date)
    """)

    # 3. GROUP BY aggregation — total sales by category and region
    print("=== Sales by Category and Region ===")
    result = db.execute("""
        SELECT category, region,
               SUM(amount) AS total_sales,
               COUNT(*)    AS num_transactions,
               ROUND(AVG(amount), 2) AS avg_sale
        FROM sales
        GROUP BY category, region
        ORDER BY category, total_sales DESC
    """).df()
    print(result.to_string(index=False))

    # 4. Window function — rank sales within each category
    print("\n=== Sales Ranked Within Each Category ===")
    result = db.execute("""
        SELECT category, region, amount, sale_date,
               RANK() OVER (PARTITION BY category ORDER BY amount DESC) AS rank,
               SUM(amount) OVER (PARTITION BY category) AS category_total,
               ROUND(
                   amount * 100.0 / SUM(amount) OVER (PARTITION BY category), 1
               ) AS pct_of_category
        FROM sales
        ORDER BY category, amount DESC
    """).df()
    print(result.to_string(index=False))

    # 5. Running total window function — cumulative sales over time
    print("\n=== Running Total of Sales Over Time ===")
    result = db.execute("""
        SELECT sale_date, category, amount,
               SUM(amount) OVER (ORDER BY sale_date
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ) AS running_total
        FROM sales
        ORDER BY sale_date
    """).df()
    print(result.to_string(index=False))

    # 6. Cleanup
    db.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
