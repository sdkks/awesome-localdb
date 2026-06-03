"""
Recipe: Datalog Queries (Relations, Joins, and Recursion)
Database: CozoDB
Description: Demonstrate CozoDB's Datalog query language by creating relations,
             inserting data, running joins across relations, and performing
             recursive ancestor queries.

Usage: python src/recipe_datalog_queries.py
"""

import shutil
import tempfile
from pathlib import Path

from pycozo.client import Client


def main() -> None:
    """Create relations, insert data, and run Datalog queries in CozoDB."""
    # 1. Setup — create an embedded SQLite-backed database
    db_path = Path(tempfile.mkdtemp(prefix="cozo_datalog_")) / "data.db"
    client = Client("sqlite", str(db_path), dataframe=False)

    # 2. Define relations (schema)
    # Person relation: name, age, city
    client.run(":create person {name: String, age: Int, city: String}")

    # Friend relation: person, friend
    client.run(":create friendship {person: String, friend: String}")

    # 3. Insert people
    client.run("""
        ?[name, age, city] <- [
            ['Alice', 30, 'NYC'],
            ['Bob', 25, 'SF'],
            ['Carol', 28, 'NYC'],
            ['Dan', 35, 'SF'],
            ['Eve', 22, 'Chicago'],
            ['Frank', 40, 'NYC'],
        ] :put person {name, age, city}
    """)

    # 4. Insert friendships
    client.run("""
        ?[person, friend] <- [
            ['Alice', 'Bob'],
            ['Alice', 'Carol'],
            ['Bob', 'Dan'],
            ['Carol', 'Dan'],
            ['Dan', 'Eve'],
            ['Eve', 'Frank'],
        ] :put friendship {person, friend}
    """)

    # 5. Basic query — all people in NYC
    print("=== People in NYC ===")
    res = client.run("?[name, age] := *person[name, age, 'NYC']")
    for row in res["rows"]:
        print(f"  {row[0]}, age {row[1]}")

    # 6. Join query — friends with age > 25
    print("\n=== Friends Where Both Over 25 ===")
    res = client.run("""
        ?[a, age_a, b, age_b] :=
            *friendship[a, b],
            *person[a, age_a, _],
            *person[b, age_b, _],
            age_a > 25,
            age_b > 25
    """)
    for row in res["rows"]:
        print(f"  {row[0]} (age {row[1]}) -> {row[2]} (age {row[3]})")

    # 7. Aggregation — count friends per person
    print("\n=== Friend Count ===")
    res = client.run("""
        count_friends[person, count(friend)] := *friendship[person, friend]
        ?[person, count] := count_friends[person, count]
    """)
    for row in res["rows"]:
        print(f"  {row[0]}: {row[1]} friend(s)")

    # 8. Recursive query — find all connections (transitive closure of friendship)
    print("\n=== All Reachable Connections ===")
    res = client.run("""
        connected[a, b] := *friendship[a, b]
        connected[a, c] := *friendship[a, b], connected[b, c]
        ?[a, b] := connected[a, b]
    """)
    for row in res["rows"]:
        print(f"  {row[0]} -> {row[1]}")

    # 9. Recursive with depth — find all reachable within 2 hops
    print("\n=== Connections Within 2 Hops ===")
    res = client.run("""
        hop[a, b, d] := *friendship[a, b], d = 1
        hop[a, c, d2] := *friendship[a, b], hop[b, c, d], d2 = d + 1, d < 2
        ?[a, c, d] := hop[a, c, d]
    """)
    for row in res["rows"]:
        print(f"  {row[0]} -> {row[1]} ({row[2]} hop(s))")

    # 10. Cleanup
    client.close()
    shutil.rmtree(db_path.parent, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
