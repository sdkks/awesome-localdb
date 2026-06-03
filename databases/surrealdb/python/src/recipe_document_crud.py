"""
Recipe: Document CRUD Operations
Database: SurrealDB
Description: Demonstrate SurrealDB embedded with document creation, reading,
             updating, deletion, SurrealQL queries, and record linking.

Usage: python src/recipe_document_crud.py
"""

from surrealdb import Surreal


def main() -> None:
    """Run document CRUD operations on an embedded SurrealDB instance."""
    # 1. Setup — open embedded database (in-memory)
    with Surreal("memory://") as db:
        db.use("test", "test")

        # 2. Create — insert documents
        alice = db.create("person", {
            "name": "Alice",
            "age": 30,
            "city": "London"
        })
        print("Created Alice:", alice)

        bob = db.create("person", {
            "name": "Bob",
            "age": 25,
            "city": "New York"
        })
        print("Created Bob:", bob)

        # 3. Create with specific ID
        charlie = db.create("person:charlie", {
            "name": "Charlie",
            "age": 35,
            "city": "Paris"
        })
        print("Created Charlie:", charlie)

        # 4. Read — select by specific ID
        found = db.select("person:charlie")
        print("\nFound by ID 'person:charlie':", found)

        # 5. Query — use SurrealQL to filter
        result = db.query("SELECT * FROM person WHERE age > 20 ORDER BY age DESC")
        print("\nPeople over 20 (SurrealQL):")
        for row in result:
            print(f"  {row}")

        # 6. Query with aggregation
        stats = db.query(
            "SELECT count() AS total, math::mean(age) AS avg_age FROM person GROUP ALL"
        )
        print("\nStats:", stats)

        # 7. Update — modify a document
        updated = db.merge("person:charlie", {"age": 36, "city": "Berlin"})
        print("\nUpdated Charlie:", updated)

        # 8. Create a company and relate a person to it
        company = db.create("company:techcorp", {
            "name": "TechCorp",
            "industry": "Software"
        })
        print("\nCreated company:", company)

        db.query(
            "RELATE person:charlie->works_at->company:techcorp"
        )
        print("Related Charlie to TechCorp")

        # 9. Delete — remove a record
        deleted = db.delete("person:charlie")
        print("\nDeleted Charlie:", deleted)

        # 10. Verify deletion
        not_found = db.select("person:charlie")
        print("After deletion, person:charlie =", not_found)

    print("\nDone.")


if __name__ == "__main__":
    main()
