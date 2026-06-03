"""
Recipe: Graph Triples
Database: CogDB
Description: Create a social graph using triples (subject-predicate-object),
             then run Torque traversal queries for pattern matching,
             filtering, and multi-hop path exploration.

Usage: python src/recipe_graph_triples.py
"""

import shutil
import tempfile
from pathlib import Path

from cog import config
from cog.torque import Graph


def main() -> None:
    """Create a social graph with triples and run Torque traversal queries."""
    # 1. Setup -- use a temporary directory for isolation
    tmpdir = Path(tempfile.mkdtemp(prefix="cogdb_triples_"))
    config.COG_PATH_PREFIX = str(tmpdir)
    config.COG_HOME = "recipe_graph"

    g = Graph("social")

    # 2. Insert triples -- people and their relationships
    g.put("alice", "follows", "bob")
    g.put("alice", "follows", "carol")
    g.put("alice", "status", "active")
    g.put("bob", "follows", "dan")
    g.put("bob", "status", "active")
    g.put("carol", "follows", "dan")
    g.put("carol", "follows", "eve")
    g.put("dan", "follows", "eve")
    g.put("dan", "status", "inactive")
    g.put("eve", "follows", "frank")
    g.put("frank", "status", "active")

    # People's cuisine preferences
    g.put("alice", "cooks", "italian")
    g.put("bob", "cooks", "indian")
    g.put("carol", "cooks", "italian")
    g.put("dan", "cooks", "mexican")
    g.put("eve", "cooks", "italian")
    g.put("frank", "cooks", "indian")

    # 3. Query -- who does alice follow?
    print("=== Who Alice Follows ===")
    result = g.v("alice").out("follows").all()
    for item in result["result"]:
        print(f"  alice follows {item['id']}")

    # 4. Query -- who follows dan? (incoming edges)
    print("\n=== Who Follows Dan ===")
    result = g.v("dan").inc("follows").all()
    for item in result["result"]:
        print(f"  {item['id']} follows dan")

    # 5. Query -- all active users
    print("\n=== Active Users ===")
    result = g.v().has("status", "active").all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 6. Query -- multi-hop: who does alice follow that also follows eve?
    print("\n=== People Alice Follows Who Also Follow Eve ===")
    result = g.v("alice").out("follows").out("follows").is_("eve").all()
    if result.get("result"):
        # alice -> X -> eve, so X is the intermediate
        for item in result["result"]:
            print(f"  {item['id']} is reachable from alice via follows chain")

    # 7. Query -- filter: people who cook italian
    print("\n=== People Who Cook Italian ===")
    result = g.v().has("cooks", "italian").all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 8. Query -- two hops from alice (friends of friends)
    print("\n=== Friends of Friends (from Alice) ===")
    result = g.v("alice").out("follows").out("follows").all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 9. Query -- count alice's outgoing follows
    print("\n=== Count of Alice's Follows ===")
    count = g.v("alice").out("follows").count()
    print(f"  {count}")

    # 10. Query -- bidirectional: who is connected to dan via follows?
    print("\n=== Bidirectional Connections to Dan ===")
    result = g.v("dan").both("follows").all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 11. Cleanup
    g.sync()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
