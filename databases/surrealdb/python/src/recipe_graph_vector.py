"""
Recipe: Graph and Vector Search
Database: SurrealDB
Description: Demonstrate graph traversals using record links, graph operators
             (->, <-), and multi-hop path queries in SurrealQL.

Usage: python src/recipe_graph_vector.py
"""

from surrealdb import Surreal


def main() -> None:
    """Run graph traversal operations on an embedded SurrealDB instance."""
    # 1. Setup — open embedded database (in-memory)
    with Surreal("memory://") as db:
        db.use("test", "test")

        # 2. Create nodes (people and cities)
        db.create("person:alice", {"name": "Alice"})
        db.create("person:bob", {"name": "Bob"})
        db.create("person:carol", {"name": "Carol"})
        db.create("city:london", {"name": "London", "country": "UK"})
        db.create("city:nyc", {"name": "New York", "country": "USA"})
        db.create("city:paris", {"name": "Paris", "country": "France"})

        print("Created 3 people and 3 cities")

        # 3. Create edges (graph relationships)
        db.query("RELATE person:alice->lives_in->city:london")
        db.query("RELATE person:bob->lives_in->city:nyc")
        db.query("RELATE person:carol->lives_in->city:paris")
        db.query("RELATE person:alice->knows->person:bob")
        db.query("RELATE person:bob->knows->person:carol")

        print("Created 5 graph edges")

        # 4. Forward graph traversal — who does Alice know?
        print("\n=== Who does Alice know? ===")
        result = db.query(
            "SELECT ->knows->person.name AS knows FROM person:alice"
        )
        for row in result:
            print(f"  {row}")

        # 5. Chained traversal — where do Alice's friends live?
        print("\n=== Where do Alice's friends live? ===")
        result = db.query(
            "SELECT ->knows->person->lives_in->city.name AS city FROM person:alice"
        )
        for row in result:
            print(f"  {row}")

        # 6. Reverse traversal — who lives in London?
        print("\n=== Who lives in London? ===")
        result = db.query(
            "SELECT <-lives_in<-person.name AS resident FROM city:london"
        )
        for row in result:
            print(f"  {row}")

        # 7. Multi-hop traversal — friend-of-friend
        print("\n=== Who can Alice reach through friends? ===")
        print("Direct friends:")
        result = db.query(
            "SELECT ->knows->person.name AS name FROM person:alice"
        )
        for row in result:
            print(f"  {row}")

        print("Friends of friends:")
        result = db.query(
            "SELECT ->knows->person->knows->person.name AS name FROM person:alice"
        )
        for row in result:
            print(f"  {row}")

        # 8. Create items with vector embeddings for similarity search
        db.create("item:1", {
            "name": "Rust Programming Book",
            "description": "Learn Rust systems programming language",
            "embedding": [1.0, 0.8, 0.1]
        })
        db.create("item:2", {
            "name": "Python Machine Learning",
            "description": "ML with Python and scikit-learn",
            "embedding": [0.1, 0.2, 1.0]
        })
        db.create("item:3", {
            "name": "Advanced Rust Patterns",
            "description": "Design patterns in Rust",
            "embedding": [0.9, 1.0, 0.15]
        })

        print("\n=== Approximate vector similarity search ===")
        # Search for items similar to [0.95, 0.85, 0.1] (closest to Rust books)
        result = db.query("""
            SELECT name, description,
                   vector::similarity::cosine(embedding, [0.95, 0.85, 0.1]) AS similarity
            FROM item
            ORDER BY similarity DESC
            LIMIT 3
        """)
        for row in result:
            print(f"  {row}")

    print("\nDone.")


if __name__ == "__main__":
    main()
