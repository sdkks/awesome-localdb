"""
Recipe: Graph Cypher
Database: FalkorDBLite
Description: Create a social graph with nodes and relationships using
             Cypher queries, then traverse and query the graph.

Usage: python src/recipe_graph_cypher.py
"""

import shutil
import tempfile
from pathlib import Path

try:
    from redislite.falkordb_client import FalkorDB
except ImportError:
    print("Error: falkordblite is not installed. Run: pip install falkordblite")
    raise


def main() -> None:
    """Create a social graph and run Cypher traversal queries."""
    # 1. Setup — create an embedded database in a temporary directory
    db_path = Path(tempfile.mkdtemp(prefix="falkordblite_recipe_")) / "social.db"
    db = FalkorDB(str(db_path))

    # 2. Select a graph
    g = db.select_graph("social")

    # 3. Create nodes
    g.query("CREATE (:Person {name: 'Alice', age: 30})")
    g.query("CREATE (:Person {name: 'Bob', age: 25})")
    g.query("CREATE (:Person {name: 'Carol', age: 28})")
    g.query("CREATE (:Person {name: 'Dan', age: 35})")

    # 4. Create relationships between people
    g.query("""
        MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
        CREATE (a)-[:KNOWS {since: 2022}]->(b)
    """)
    g.query("""
        MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Carol'})
        CREATE (a)-[:KNOWS {since: 2023}]->(b)
    """)
    g.query("""
        MATCH (a:Person {name: 'Carol'}), (b:Person {name: 'Dan'})
        CREATE (a)-[:KNOWS {since: 2021}]->(b)
    """)
    g.query("""
        MATCH (a:Person {name: 'Bob'}), (b:Person {name: 'Dan'})
        CREATE (a)-[:KNOWS {since: 2023}]->(b)
    """)

    # 5. Query — list all people
    print("=== All People ===")
    result = g.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.name")
    for row in result.result_set:
        print(f"  {row[0]}, age {row[1]}")

    # 6. Query — who knows whom?
    print("\n=== Who Knows Whom ===")
    result = g.query("""
        MATCH (a:Person)-[k:KNOWS]->(b:Person)
        RETURN a.name, b.name, k.since
        ORDER BY a.name
    """)
    for row in result.result_set:
        print(f"  {row[0]} knows {row[1]} (since {row[2]})")

    # 7. Query — friends of Alice
    print("\n=== Friends of Alice ===")
    result = g.query("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(friend:Person)
        RETURN friend.name, friend.age
        ORDER BY friend.name
    """)
    for row in result.result_set:
        print(f"  {row[0]}, age {row[1]}")

    # 8. Query — multi-hop: who knows someone Alice knows?
    print("\n=== People Who Know Someone Alice Knows ===")
    result = g.query("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(:Person)-[:KNOWS]->(fof:Person)
        WHERE fof.name <> 'Alice'
        RETURN DISTINCT fof.name
        ORDER BY fof.name
    """)
    for row in result.result_set:
        print(f"  {row[0]}")

    # 9. Cleanup
    g.delete()
    shutil.rmtree(db_path.parent, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
