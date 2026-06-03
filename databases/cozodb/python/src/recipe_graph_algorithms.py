"""
Recipe: Graph Algorithms (Shortest Path and Centrality)
Database: CozoDB
Description: Build a social graph with edge weights (interaction scores),
             compute shortest paths using recursive Datalog rules, and
             calculate degree centrality via aggregation.

Usage: python src/recipe_graph_algorithms.py
"""

import shutil
import tempfile
from pathlib import Path

from pycozo.client import Client


def main() -> None:
    """Build a weighted social graph and run graph algorithms with Datalog."""
    # 1. Setup — create an embedded SQLite-backed database
    db_path = Path(tempfile.mkdtemp(prefix="cozo_graph_")) / "data.db"
    client = Client("sqlite", str(db_path), dataframe=False)

    # 2. Define relations
    client.run(":create person {name: String, dept: String}")
    client.run(":create interacts {a: String, b: String, score: Int}")

    # 3. Insert people
    client.run("""
        ?[name, dept] <- [
            ['Alice', 'Engineering'],
            ['Bob', 'Engineering'],
            ['Carol', 'Design'],
            ['Dan', 'Design'],
            ['Eve', 'Marketing'],
            ['Frank', 'Marketing'],
            ['Grace', 'Engineering'],
            ['Hank', 'Design'],
        ] :put person {name, dept}
    """)

    # 4. Insert interaction edges with scores (higher = stronger connection)
    client.run("""
        ?[a, b, score] <- [
            ['Alice', 'Bob', 10],
            ['Alice', 'Carol', 5],
            ['Bob', 'Grace', 8],
            ['Carol', 'Dan', 12],
            ['Carol', 'Hank', 4],
            ['Dan', 'Eve', 3],
            ['Eve', 'Frank', 15],
            ['Frank', 'Grace', 2],
            ['Grace', 'Hank', 6],
            ['Hank', 'Alice', 1],
            ['Bob', 'Dan', 3],
            ['Eve', 'Carol', 2],
        ] :put interacts {a, b, score}
    """)

    # 5. Show the interaction graph
    print("=== Social Graph (Interaction Scores) ===")
    res = client.run("?[a, b, score] := *interacts[a, b, score]")
    for row in res["rows"]:
        print(f"  {row[0]} -> {row[1]} (score: {row[2]})")

    # 6. Shortest path (unweighted) — find paths from Alice to everyone
    # Using recursive Datalog: breadth-first path search
    print("\n=== Shortest Paths from Alice ===")
    res = client.run("""
        path[a, b, d] := *interacts[a, b, _], d = 1
        path[a, b, d] := *interacts[b, a, _], d = 1
        path[a, c, d2] := path[a, b, d], *interacts[b, c, _], d2 = d + 1, d < 6
        path[a, c, d2] := path[a, b, d], *interacts[c, b, _], d2 = d + 1, d < 6
        shortest[a, c, min(d)] := path[a, c, d]
        ?[target, distance] := shortest['Alice', target, distance]
    """)
    for row in res["rows"]:
        print(f"  Alice -> {row[0]}: {row[1]} hop(s)")

    # 7. Degree centrality — count connections per person
    print("\n=== Degree Centrality (Connection Count) ===")
    res = client.run("""
        out_deg[person, count(b)] := *interacts[person, b, _]
        in_deg[person, count(a)] := *interacts[a, person, _]
        all_conn[person, other] := *interacts[person, other, _]
        all_conn[person, other] := *interacts[other, person, _]
        centrality[person, count(other)] := all_conn[person, other]
        ?[person, degree] := centrality[person, degree]
    """)
    for row in res["rows"]:
        print(f"  {row[0]}: degree {row[1]}")

    # 8. Cross-department interactions
    print("\n=== Cross-Department Interactions ===")
    res = client.run("""
        ?[dept1, dept2, count(a)] :=
            *interacts[a, b, _],
            *person[a, dept1],
            *person[b, dept2],
            dept1 != dept2
    """)
    for row in res["rows"]:
        print(f"  {row[0]} <-> {row[1]}: {row[2]} interactions")

    # 9. Most influential people (by weighted score)
    print("\n=== Most Influential (Weighted Outgoing Score) ===")
    res = client.run("""
        influence[person, sum(score)] := *interacts[person, _, score]
        ?[person, total_score] := influence[person, total_score]
    """)
    for row in res["rows"]:
        print(f"  {row[0]}: total outgoing score {row[1]}")

    # 10. Cleanup
    client.close()
    shutil.rmtree(db_path.parent, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
