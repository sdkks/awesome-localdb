"""
Recipe: Multi-Model Operations
Database: ArcadeDB
Description: Demonstrate ArcadeDB Embedded in Python with graph vertices and edges,
             document CRUD, vector index creation, and time-series ingestion.

Usage: python src/recipe_multi_model.py
"""

import os
import tempfile
import arcadedb_embedded as arcadedb


def main() -> None:
    """Run multi-model operations on an embedded ArcadeDB instance."""
    # 1. Setup -- create a temporary database directory
    db_path = os.path.join(tempfile.mkdtemp(), "arcadedb-recipe")
    os.makedirs(db_path, exist_ok=True)

    with arcadedb.create_database(db_path) as db:

        # ── 2. Graph: vertices, edges, and traversal ──────────────────────
        with db.transaction():
            db.command("sql", "CREATE VERTEX TYPE Person")
            db.command("sql", "CREATE VERTEX TYPE Company")
            db.command("sql", "CREATE EDGE TYPE WorksAt")
            db.command("sql", "CREATE EDGE TYPE Knows")

            db.command("sql",
                "INSERT INTO Person SET name = 'Alice', age = 32, city = 'London'")
            db.command("sql",
                "INSERT INTO Person SET name = 'Bob', age = 28, city = 'New York'")
            db.command("sql",
                "INSERT INTO Person SET name = 'Charlie', age = 35, city = 'Paris'")
            db.command("sql",
                "INSERT INTO Company SET name = 'TechCorp', industry = 'Software'")

            db.command("sql",
                "CREATE EDGE WorksAt FROM "
                "(SELECT FROM Person WHERE name='Alice') TO "
                "(SELECT FROM Company WHERE name='TechCorp') "
                "SET role = 'Engineer'")
            db.command("sql",
                "CREATE EDGE Knows FROM "
                "(SELECT FROM Person WHERE name='Alice') TO "
                "(SELECT FROM Person WHERE name='Bob') "
                "SET since = 2020")
            db.command("sql",
                "CREATE EDGE Knows FROM "
                "(SELECT FROM Person WHERE name='Bob') TO "
                "(SELECT FROM Person WHERE name='Charlie') "
                "SET since = 2021")

        # Graph traversal: find people Alice knows
        print("=== Graph: People Alice knows ===")
        result = db.query("cypher",
            "MATCH (p:Person {name: 'Alice'})-[:Knows]->(f:Person) "
            "RETURN f.name, f.age")
        for row in result:
            print(f"  Alice knows {row.get('name')} (age {row.get('age')})")

        # Two-hop traversal: who does Alice know, and who do they know?
        print("\n=== Graph: Two-hop from Alice ===")
        result = db.query("cypher",
            "MATCH (a:Person {name: 'Alice'})"
            "-[:Knows]->(f:Person)-[:Knows]->(fof:Person) "
            "RETURN fof.name AS friend_of_friend")
        for row in result:
            print(f"  Alice -> friend -> {row.get('friend_of_friend')}")

        # ── 3. Documents: CRUD operations ─────────────────────────────────
        with db.transaction():
            db.command("sql", "CREATE DOCUMENT TYPE Article")

            db.command("sql",
                "INSERT INTO Article SET "
                "title = 'Graph Databases 101', "
                "author = 'Alice', "
                "tags = ['graph', 'database', 'tutorial'], "
                "views = 1500")

            db.command("sql",
                "INSERT INTO Article SET "
                "title = 'Vector Search Explained', "
                "author = 'Bob', "
                "tags = ['vector', 'ai', 'search'], "
                "views = 2300")

        print("\n=== Documents: All articles ===")
        result = db.query("sql", "SELECT title, author, views FROM Article ORDER BY views DESC")
        for row in result:
            print(f"  \"{row.get('title')}\" by {row.get('author')} ({row.get('views')} views)")

        # ── 4. Vector: index creation and similarity ──────────────────────
        with db.transaction():
            db.command("sql", "CREATE DOCUMENT TYPE Embedding")
            db.command("sql",
                "CREATE VECTOR INDEX ON Embedding(embedding) LSM TYPE COSINE")

            # Insert documents with 4-dimensional embeddings
            db.command("sql",
                "INSERT INTO Embedding SET "
                "content = 'graph database tutorial', "
                "embedding = [0.1, 0.2, 0.3, 0.9]")
            db.command("sql",
                "INSERT INTO Embedding SET "
                "content = 'vector search guide', "
                "embedding = [0.2, 0.1, 0.8, 0.3]")
            db.command("sql",
                "INSERT INTO Embedding SET "
                "content = 'completely unrelated topic', "
                "embedding = [0.9, 0.8, 0.1, 0.1]")

        # Vector similarity search
        query_vector = [0.15, 0.18, 0.35, 0.85]
        print("\n=== Vector: Similarity search ===")
        result = db.query("sql",
            "SELECT content, embedding.cosineDistance(?) AS score "
            "FROM Embedding "
            "ORDER BY score LIMIT 3",
            query_vector)
        for row in result:
            print(f"  \"{row.get('content')}\" (score: {row.get('score'):.3f})")

        # ── 5. Time-series: ingestion with time bucket ────────────────────
        with db.transaction():
            db.command("sql",
                "CREATE DOCUMENT TYPE SensorReading "
                "BUCKET timestamp EVERY 1 HOUR")

            db.command("sql",
                "INSERT INTO SensorReading SET "
                "timestamp = '2025-01-15T10:00:00Z', "
                "device = 'sensor-1', "
                "temperature = 22.5, "
                "humidity = 65.0")
            db.command("sql",
                "INSERT INTO SensorReading SET "
                "timestamp = '2025-01-15T10:15:00Z', "
                "device = 'sensor-1', "
                "temperature = 22.7, "
                "humidity = 64.8")
            db.command("sql",
                "INSERT INTO SensorReading SET "
                "timestamp = '2025-01-15T10:30:00Z', "
                "device = 'sensor-1', "
                "temperature = 23.1, "
                "humidity = 64.5")

        print("\n=== Time-series: Sensor readings ===")
        result = db.query("sql",
            "SELECT timestamp, device, temperature, humidity "
            "FROM SensorReading ORDER BY timestamp")
        for row in result:
            print(f"  [{row.get('timestamp')}] {row.get('device')}: "
                  f"{row.get('temperature')}C, {row.get('humidity')}%")

        # Time-series aggregation
        result = db.query("sql",
            "SELECT device, "
            "avg(temperature) AS avg_temp, "
            "min(humidity) AS min_humidity "
            "FROM SensorReading GROUP BY device")
        for row in result:
            print(f"  Aggregate for {row.get('device')}: "
                  f"avg_temp={row.get('avg_temp')}C, "
                  f"min_humidity={row.get('min_humidity')}%")

    print("\nDone.")


if __name__ == "__main__":
    main()
