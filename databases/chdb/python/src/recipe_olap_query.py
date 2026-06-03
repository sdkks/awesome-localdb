"""
Recipe: OLAP Query
Database: chDB
Description: Demonstrate chDB as an embedded analytical query engine with
             GROUP BY aggregation, window functions, and subqueries.

Usage: python src/recipe_olap_query.py
"""

import chdb


def main() -> None:
    """Run analytical queries including GROUP BY and window functions."""
    # 1. Setup — define a VALUES table expression once for reuse
    SALES_VALUES = """VALUES(
        'category String, region String, amount Int64, sale_date Date',
        ('Electronics', 'North', 1200, '2025-01-15'),
        ('Electronics', 'South',  800, '2025-01-20'),
        ('Electronics', 'North', 1500, '2025-02-10'),
        ('Clothing',    'North',  300, '2025-01-18'),
        ('Clothing',    'South',  450, '2025-02-05'),
        ('Clothing',    'East',   600, '2025-02-22'),
        ('Groceries',   'North',  200, '2025-01-10'),
        ('Groceries',   'South',  250, '2025-02-14'),
        ('Groceries',   'East',   180, '2025-03-01'),
        ('Electronics', 'East',  2200, '2025-03-05')
    )"""

    # 2. GROUP BY aggregation — total sales by category and region
    print("=== Sales by Category and Region ===")
    result = chdb.query(f"""
        SELECT category, region,
               SUM(amount) AS total_sales,
               COUNT(*)    AS num_transactions,
               ROUND(AVG(amount), 2) AS avg_sale
        FROM {SALES_VALUES}
        GROUP BY category, region
        ORDER BY category, total_sales DESC
        FORMAT CSVWithNames
    """)

    print(result)

    # 3. Window function — rank sales within each category
    print("=== Sales Ranked Within Each Category ===")
    result = chdb.query(f"""
        SELECT category, region, amount, sale_date,
               RANK() OVER (PARTITION BY category ORDER BY amount DESC) AS rank,
               SUM(amount) OVER (PARTITION BY category) AS category_total,
               ROUND(
                   amount * 100.0 / SUM(amount) OVER (PARTITION BY category), 1
               ) AS pct_of_category
        FROM {SALES_VALUES}
        ORDER BY category, amount DESC
        FORMAT CSVWithNames
    """)

    print(result)

    # 4. Running total window function — cumulative sales over time
    print("=== Running Total of Sales Over Time ===")
    result = chdb.query(f"""
        SELECT sale_date, category, amount,
               SUM(amount) OVER (ORDER BY sale_date
                                 ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
               ) AS running_total
        FROM {SALES_VALUES}
        ORDER BY sale_date
        FORMAT CSVWithNames
    """)

    print(result)

    # 5. Subquery — top region per category by total sales
    print("=== Top Region per Category (Subquery) ===")
    result = chdb.query(f"""
        SELECT category, region, total_sales
        FROM (
            SELECT category, region,
                   SUM(amount) AS total_sales,
                   ROW_NUMBER() OVER (PARTITION BY category ORDER BY SUM(amount) DESC) AS rn
            FROM {SALES_VALUES}
            GROUP BY category, region
        )
        WHERE rn = 1
        ORDER BY total_sales DESC
        FORMAT CSVWithNames
    """)

    print(result)
    print("\nDone.")


if __name__ == "__main__":
    main()
