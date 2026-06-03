"""
Recipe: Data Pipeline
Database: chDB
Description: Demonstrate chDB as an in-process data pipeline engine —
             read CSV, transform with SQL, write to Parquet.

Usage: python src/recipe_data_pipeline.py
"""

import os
import tempfile

import chdb


def main() -> None:
    """Run an in-process data pipeline: CSV -> transform -> Parquet."""
    # 1. Create a temporary CSV file as the input source
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

    # 2. Read CSV directly with chDB and inspect
    print("=== Raw CSV Data ===")
    raw = chdb.query(f"SELECT * FROM file('{csv_path}', 'CSV') FORMAT CSVWithNames")
    print(raw)

    # 3. Transform — compute revenue and aggregate by product and region
    print("=== Transformed: Revenue by Product and Region ===")
    transformed = chdb.query(f"""
        SELECT
            product,
            customer_region AS region,
            COUNT(*) AS num_orders,
            SUM(quantity) AS total_quantity,
            ROUND(SUM(quantity * unit_price), 2) AS total_revenue,
            ROUND(AVG(quantity * unit_price), 2) AS avg_order_value
        FROM file('{csv_path}', 'CSV')
        GROUP BY product, customer_region
        ORDER BY total_revenue DESC
        FORMAT CSVWithNames
    """)
    print(transformed)

    # 4. Write transformed result to Parquet (in-process, no external service)
    parquet_path = os.path.join(tmpdir, "revenue_by_product_region.parquet")
    chdb.query(f"""
        INSERT INTO FUNCTION file('{parquet_path}', 'Parquet')
        SELECT
            product,
            customer_region AS region,
            COUNT(*) AS num_orders,
            SUM(quantity) AS total_quantity,
            ROUND(SUM(quantity * unit_price), 2) AS total_revenue,
            ROUND(AVG(quantity * unit_price), 2) AS avg_order_value
        FROM file('{csv_path}', 'CSV')
        GROUP BY product, customer_region
        ORDER BY total_revenue DESC
    """)

    # 5. Verify — read the Parquet file back and confirm data integrity
    print("=== Verify Parquet Output ===")
    verified = chdb.query(f"SELECT * FROM file('{parquet_path}', 'Parquet') FORMAT CSVWithNames")
    verified_str = str(verified)
    print(verified_str)

    # Count lines to verify output (minus header)
    output_lines = verified_str.strip().split("\n")
    # Input has 6 unique (product, region) combinations
    expected_rows = 6
    assert len(output_lines) == expected_rows + 1, (
        f"Row count mismatch: got {len(output_lines) - 1}, expected {expected_rows}"
    )
    print(f"\nPipeline verified: {expected_rows} rows written and read back successfully.")

    # 6. Cleanup
    for f in [csv_path, parquet_path]:
        if os.path.exists(f):
            os.remove(f)
    os.rmdir(tmpdir)
    print("Done.")


if __name__ == "__main__":
    main()
