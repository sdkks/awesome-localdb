"""
Recipe: Document Store CRUD
Database: TinyDB
Description: Demonstrates basic document operations — insert, search with Query() builder,
             update, upsert, and delete — using TinyDB's in-memory storage.

Usage: python src/recipe_document_store.py
"""

import os
import tempfile

from tinydb import Query, TinyDB


def main() -> None:
    # Use a temporary file so we don't leave artifacts on disk
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.close()
    db_path = tmp.name

    try:
        db = TinyDB(db_path)
        User = Query()

        # --- 1. Insert documents ---
        db.insert({"name": "Alice", "age": 30, "city": "London"})
        db.insert({"name": "Bob", "age": 25, "city": "Paris"})
        db.insert({"name": "Charlie", "age": 35, "city": "London"})
        db.insert_multiple(
            [
                {"name": "Diana", "age": 28, "city": "Berlin"},
                {"name": "Eve", "age": 22, "city": "Paris"},
            ]
        )

        print(f"Inserted {len(db)} documents.")

        # --- 2. Search with Query() builder ---
        # Exact match
        alice = db.search(User.name == "Alice")
        print(f"Found Alice: {alice}")

        # Comparison
        young = db.search(User.age < 30)
        print(f"Users under 30: {[u['name'] for u in young]}")

        # Combined query
        london_adults = db.search((User.city == "London") & (User.age >= 30))
        print(f"London adults: {[u['name'] for u in london_adults]}")

        # Existence check
        has_bob = db.contains(User.name == "Bob")
        print(f"Contains Bob: {has_bob}")
        has_zelda = db.contains(User.name == "Zelda")
        print(f"Contains Zelda: {has_zelda}")

        # --- 3. Update documents ---
        db.update({"age": 31}, User.name == "Alice")
        updated_alice = db.get(User.name == "Alice")
        print(f"Updated Alice: {updated_alice}")

        # --- 4. Upsert ---
        # Upsert a new document (no match → insert)
        db.upsert(
            {"name": "Frank", "age": 40, "city": "Tokyo"},
            User.name == "Frank",
        )
        # Upsert an existing document (match → update)
        db.upsert(
            {"name": "Bob", "age": 26, "city": "Paris"},
            User.name == "Bob",
        )
        print(f"After upserts, document count: {len(db)}")
        bob = db.get(User.name == "Bob")
        print(f"Bob after upsert: {bob}")

        # --- 5. Count documents ---
        count = db.count(User.city == "Paris")
        print(f"Users in Paris: {count}")

        # --- 6. Delete documents ---
        removed_ids = db.remove(User.name == "Eve")
        print(f"Removed Eve, affected IDs: {removed_ids}")
        print(f"Document count after remove: {len(db)}")

        # --- 7. Retrieve all documents ---
        all_docs = db.all()
        print(f"All documents ({len(all_docs)}):")
        for doc in all_docs:
            print(f"  {doc}")

        db.close()

    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    main()
