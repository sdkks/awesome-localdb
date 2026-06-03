"""
Recipe: Graph Traversal
Database: Kuzu
Description: Create nodes and edges in a property graph, then run
             Cypher MATCH queries for pattern matching and traversal.

Usage: python src/recipe_graph_traversal.py
"""

import shutil
import tempfile
from pathlib import Path

import kuzu


def main() -> None:
    """Create a recipe graph and run Cypher traversal queries."""
    # 1. Setup — create an embedded database in a temporary directory
    db_path = Path(tempfile.mkdtemp(prefix="kuzu_recipe_")) / "graph"
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)

    # 2. Define schema — node tables with primary keys and edge tables
    conn.execute(
        "CREATE NODE TABLE Person("
        "  name STRING, age INT64, PRIMARY KEY (name)"
        ")"
    )
    conn.execute(
        "CREATE NODE TABLE Recipe("
        "  title STRING, cuisine STRING, PRIMARY KEY (title)"
        ")"
    )
    conn.execute(
        "CREATE NODE TABLE Ingredient("
        "  name STRING, PRIMARY KEY (name)"
        ")"
    )
    conn.execute(
        "CREATE REL TABLE Follows("
        "  FROM Person TO Person, since INT64"
        ")"
    )
    conn.execute(
        "CREATE REL TABLE Cooked("
        "  FROM Person TO Recipe, rating INT64"
        ")"
    )
    conn.execute(
        "CREATE REL TABLE Uses("
        "  FROM Recipe TO Ingredient, amount STRING"
        ")"
    )

    # 3. Insert data — create nodes and relationships
    # People
    conn.execute('CREATE (:Person {name: "Alice", age: 30})')
    conn.execute('CREATE (:Person {name: "Bob", age: 25})')
    conn.execute('CREATE (:Person {name: "Carol", age: 28})')
    conn.execute('CREATE (:Person {name: "Dan", age: 35})')

    # Recipes
    conn.execute(
        'CREATE (:Recipe {title: "Spaghetti Bolognese", cuisine: "Italian"})'
    )
    conn.execute(
        'CREATE (:Recipe {title: "Chicken Curry", cuisine: "Indian"})'
    )
    conn.execute(
        'CREATE (:Recipe {title: "Avocado Toast", cuisine: "American"})'
    )

    # Ingredients
    conn.execute('CREATE (:Ingredient {name: "Pasta"})')
    conn.execute('CREATE (:Ingredient {name: "Tomato Sauce"})')
    conn.execute('CREATE (:Ingredient {name: "Chicken"})')
    conn.execute('CREATE (:Ingredient {name: "Curry Powder"})')
    conn.execute('CREATE (:Ingredient {name: "Avocado"})')
    conn.execute('CREATE (:Ingredient {name: "Bread"})')

    # Relationships: Follows
    conn.execute(
        'MATCH (a:Person), (b:Person) '
        'WHERE a.name = "Alice" AND b.name = "Bob" '
        "CREATE (a)-[:Follows {since: 2022}]->(b)"
    )
    conn.execute(
        'MATCH (a:Person), (b:Person) '
        'WHERE a.name = "Alice" AND b.name = "Carol" '
        "CREATE (a)-[:Follows {since: 2023}]->(b)"
    )
    conn.execute(
        'MATCH (a:Person), (b:Person) '
        'WHERE a.name = "Carol" AND b.name = "Dan" '
        "CREATE (a)-[:Follows {since: 2021}]->(b)"
    )
    conn.execute(
        'MATCH (a:Person), (b:Person) '
        'WHERE a.name = "Bob" AND b.name = "Dan" '
        "CREATE (a)-[:Follows {since: 2023}]->(b)"
    )

    # Relationships: Cooked
    conn.execute(
        'MATCH (p:Person), (r:Recipe) '
        'WHERE p.name = "Alice" AND r.title = "Spaghetti Bolognese" '
        "CREATE (p)-[:Cooked {rating: 5}]->(r)"
    )
    conn.execute(
        'MATCH (p:Person), (r:Recipe) '
        'WHERE p.name = "Bob" AND r.title = "Chicken Curry" '
        "CREATE (p)-[:Cooked {rating: 4}]->(r)"
    )
    conn.execute(
        'MATCH (p:Person), (r:Recipe) '
        'WHERE p.name = "Carol" AND r.title = "Avocado Toast" '
        "CREATE (p)-[:Cooked {rating: 3}]->(r)"
    )
    conn.execute(
        'MATCH (p:Person), (r:Recipe) '
        'WHERE p.name = "Alice" AND r.title = "Chicken Curry" '
        "CREATE (p)-[:Cooked {rating: 4}]->(r)"
    )
    conn.execute(
        'MATCH (p:Person), (r:Recipe) '
        'WHERE p.name = "Dan" AND r.title = "Spaghetti Bolognese" '
        "CREATE (p)-[:Cooked {rating: 5}]->(r)"
    )

    # Relationships: Uses
    conn.execute(
        'MATCH (r:Recipe), (i:Ingredient) '
        'WHERE r.title = "Spaghetti Bolognese" AND i.name = "Pasta" '
        'CREATE (r)-[:Uses {amount: "200g"}]->(i)'
    )
    conn.execute(
        'MATCH (r:Recipe), (i:Ingredient) '
        'WHERE r.title = "Spaghetti Bolognese" AND i.name = "Tomato Sauce" '
        'CREATE (r)-[:Uses {amount: "150ml"}]->(i)'
    )
    conn.execute(
        'MATCH (r:Recipe), (i:Ingredient) '
        'WHERE r.title = "Chicken Curry" AND i.name = "Chicken" '
        'CREATE (r)-[:Uses {amount: "300g"}]->(i)'
    )
    conn.execute(
        'MATCH (r:Recipe), (i:Ingredient) '
        'WHERE r.title = "Chicken Curry" AND i.name = "Curry Powder" '
        'CREATE (r)-[:Uses {amount: "2 tbsp"}]->(i)'
    )
    conn.execute(
        'MATCH (r:Recipe), (i:Ingredient) '
        'WHERE r.title = "Avocado Toast" AND i.name = "Avocado" '
        'CREATE (r)-[:Uses {amount: "1 whole"}]->(i)'
    )
    conn.execute(
        'MATCH (r:Recipe), (i:Ingredient) '
        'WHERE r.title = "Avocado Toast" AND i.name = "Bread" '
        'CREATE (r)-[:Uses {amount: "2 slices"}]->(i)'
    )

    # 4. Query — who follows whom?
    print("=== Who Follows Whom ===")
    results = conn.execute(
        "MATCH (a:Person)-[f:Follows]->(b:Person) "
        "RETURN a.name, b.name, f.since "
        "ORDER BY a.name"
    )
    while results.has_next():
        row = results.get_next()
        print(f"  {row[0]} follows {row[1]} (since {row[2]})")

    # 5. Query — recipes with their cooks and ratings
    print("\n=== Recipes and Their Cooks ===")
    results = conn.execute(
        "MATCH (p:Person)-[c:Cooked]->(r:Recipe) "
        "RETURN r.title, p.name, c.rating "
        "ORDER BY r.title, c.rating DESC"
    )
    while results.has_next():
        row = results.get_next()
        print(f"  {row[0]} — cooked by {row[1]} (rating: {row[2]})")

    # 6. Query — multi-hop traversal: who cooked the same recipe as Alice?
    print("\n=== People Who Cooked the Same Recipes as Alice ===")
    results = conn.execute(
        "MATCH (alice:Person)-[:Cooked]->(r:Recipe)<-[:Cooked]-(other:Person) "
        'WHERE alice.name = "Alice" AND other.name <> "Alice" '
        "RETURN DISTINCT other.name, r.title "
        "ORDER BY other.name"
    )
    while results.has_next():
        row = results.get_next()
        print(f"  {row[0]} also cooked {row[1]}")

    # 7. Query — ingredients for each recipe
    print("\n=== Ingredients by Recipe ===")
    results = conn.execute(
        "MATCH (r:Recipe)-[u:Uses]->(i:Ingredient) "
        "RETURN r.title, i.name, u.amount "
        "ORDER BY r.title"
    )
    while results.has_next():
        row = results.get_next()
        print(f"  {row[0]} uses {row[1]} ({row[2]})")

    # 8. Cleanup
    conn.close()
    db.close()
    shutil.rmtree(db_path.parent, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
