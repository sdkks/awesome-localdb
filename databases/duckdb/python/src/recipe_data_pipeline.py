"""
Recipe: Data Pipeline
Database: DuckDB
Description: Demonstrate DuckDB as an in-process data pipeline engine —
             read CSV, transform with SQL, write to Parquet.

Usage: python src/recipe_data_pipeline.py
"""

import os
import tempfile

import duckdb


def main() -> None:
    """Run an in-process data pipeline: CSV -> transform -> Parquet."""
    # 1. Setup — connect to in-memory database
    db = duckdb.connect(":memory:")

    # 2. Create a temporary CSV file as the input source
    csv_content = (
        "order_id,product,quantity,unit_price,customer_region,order_date\n"
        "1,Widget,5,10.00,North,2025-01-15\n"
        "2,Gadget,2,25.00,South,2025-01-20\n"
        "3,Widget,3,10.00,North,2025-02-10\n"
        "4,Sprocket,10,7.50,East,2025-02-05\n"
        "5,Gadget,4,25.00,South,2025-02-22\n"
        "6,Widget,8,10.00,East,2025-01-18\n"
        "7,Sprocket,6,7.50,North,2025-03-01\n"
        "8,Gadget,1,25.00,East,2025-03-05\n"
    )

    tmpdir = tempfile.mkdtemp()
    csv_path = os.path.join(tmpdir, "orders.csv")

    with open(csv_path, "w") as f:
        f.write(csv_content)

    # 3. Read CSV directly with DuckDB and inspect
    print("=== Raw CSV Data ===")
    raw = db.execute(f"SELECT * FROM '{csv_path}'").df()
    print(raw.to_string(index=False))

    # 4. Transform — compute revenue and aggregate by product and region
    print("\n=== Transformed: Revenue by Product and Region ===")
    transformed = db.execute(f"""
        SELECT
            product,
            customer_region AS region,
            COUNT(*) AS num_orders,
            SUM(quantity) AS total_quantity,
            ROUND(SUM(quantity * unit_price), 2) AS total_revenue,
            ROUND(AVG(quantity * unit_price), 2) AS avg_order_value
        FROM '{csv_path}'
        GROUP BY product, customer_region
        ORDER BY total_revenue DESC
    """).df()
    print(transformed.to_string(index=False))

    # 5. Write transformed result to Parquet (in-process, no external service)
    parquet_path = os.path.join(tmpdir, "revenue_by_product_region.parquet")
    db.execute(f"""
        COPY (
            SELECT
                product,
                customer_region AS region,
                COUNT(*) AS num_orders,
                SUM(quantity) AS total_quantity,
                ROUND(SUM(quantity * unit_price), 2) AS total_revenue,
                ROUND(AVG(quantity * unit_price), 2) AS avg_order_value
            FROM '{csv_path}'
            GROUP BY product, customer_region
            ORDER BY total_revenue DESC
        ) TO '{parquet_path}' (FORMAT PARQUET)
    """)

    # 6. Verify — read the Parquet file back and confirm data integrity
    print("\n=== Verify Parquet Output ===")
    verified = db.execute(f"SELECT * FROM '{parquet_path}'").df()
    print(verified.to_string(index=False))

    assert len(verified) == len(transformed), (
        f"Row count mismatch: {len(verified)} != {len(transformed)}"
    )
    print(f"\nPipeline verified: {len(verified)} rows written and read back successfully.")

    # 7. Cleanup
    db.close()
    for f in [csv_path, parquet_path]:
        if os.path.exists(f):
            os.remove(f)
    os.rmdir(tmpdir)
    print("Done.")


if __name__ == "__main__":
    main()
