"""
Recipe: Graph Analytics (PageRank)
Database: Kuzu
Description: Compute iterative PageRank on a graph stored in Kuzu.
             Demonstrates extracting the graph structure from Kuzu
             and running an analytical algorithm over it.

Usage: python src/recipe_graph_analytics.py
"""

import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

import kuzu


def compute_pagerank(edges: list[tuple[str, str]], damping: float = 0.85,
                     iterations: int = 20) -> dict[str, float]:
    """Compute PageRank from a list of (source, target) edges."""
    # Build adjacency
    outgoing: dict[str, list[str]] = defaultdict(list)
    incoming: dict[str, list[str]] = defaultdict(list)
    nodes: set[str] = set()

    for src, tgt in edges:
        outgoing[src].append(tgt)
        incoming[tgt].append(src)
        nodes.add(src)
        nodes.add(tgt)

    n = len(nodes)
    if n == 0:
        return {}

    # Initialize all ranks equally
    rank = {node: 1.0 / n for node in nodes}

    for _ in range(iterations):
        new_rank: dict[str, float] = {}
        for node in nodes:
            incoming_sum = 0.0
            for in_node in incoming[node]:
                out_degree = len(outgoing[in_node])
                if out_degree > 0:
                    incoming_sum += rank[in_node] / out_degree
            new_rank[node] = (1.0 - damping) / n + damping * incoming_sum
        rank = new_rank

    return rank


def main() -> None:
    """Build a citation graph in Kuzu and run PageRank on it."""
    # 1. Setup — create an embedded database
    db_path = Path(tempfile.mkdtemp(prefix="kuzu_pagerank_")) / "graph"
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)

    # 2. Define schema
    conn.execute(
        "CREATE NODE TABLE Paper("
        "  title STRING, year INT64, PRIMARY KEY (title)"
        ")"
    )
    conn.execute(
        "CREATE REL TABLE Cites("
        "  FROM Paper TO Paper"
        ")"
    )

    # 3. Create nodes — a small citation network
    papers = [
        ("Foundations of Graph Theory", 2000),
        ("Advances in PageRank", 2005),
        ("Scalable Graph Processing", 2010),
        ("Modern Database Systems", 2015),
        ("Graph Analytics in Practice", 2020),
        ("Vector Search and Graphs", 2023),
    ]
    for title, year in papers:
        conn.execute(
            f'CREATE (:Paper {{title: "{title}", year: {year}}})'
        )

    # 4. Create citation edges
    citations = [
        ("Advances in PageRank", "Foundations of Graph Theory"),
        ("Scalable Graph Processing", "Foundations of Graph Theory"),
        ("Scalable Graph Processing", "Advances in PageRank"),
        ("Modern Database Systems", "Scalable Graph Processing"),
        ("Graph Analytics in Practice", "Scalable Graph Processing"),
        ("Graph Analytics in Practice", "Advances in PageRank"),
        ("Graph Analytics in Practice", "Modern Database Systems"),
        ("Vector Search and Graphs", "Graph Analytics in Practice"),
        ("Vector Search and Graphs", "Scalable Graph Processing"),
    ]

    for citing, cited in citations:
        conn.execute(
            f'MATCH (a:Paper), (b:Paper) '
            f'WHERE a.title = "{citing}" AND b.title = "{cited}" '
            "CREATE (a)-[:Cites]->(b)"
        )

    # 5. Show the citation graph
    print("=== Citation Graph ===")
    results = conn.execute(
        "MATCH (a:Paper)-[:Cites]->(b:Paper) "
        "RETURN a.title, b.title "
        "ORDER BY a.title"
    )
    while results.has_next():
        row = results.get_next()
        print(f"  '{row[0]}' cites '{row[1]}'")

    # 6. Extract edges from Kuzu for PageRank computation
    results = conn.execute(
        "MATCH (a:Paper)-[:Cites]->(b:Paper) RETURN a.title, b.title"
    )
    edges: list[tuple[str, str]] = []
    while results.has_next():
        row = results.get_next()
        edges.append((row[0], row[1]))

    # 7. Compute PageRank
    ranks = compute_pagerank(edges, damping=0.85, iterations=30)

    # 8. Display results sorted by rank
    print("\n=== PageRank Scores ===")
    for paper, score in sorted(ranks.items(), key=lambda x: x[1], reverse=True):
        print(f"  {paper}: {score:.4f}")

    # 9. Verify PageRank properties — all scores should sum to ~1.0
    total = sum(ranks.values())
    print(f"\nSum of PageRank scores: {total:.4f}")

    # 10. Cleanup
    conn.close()
    db.close()
    shutil.rmtree(db_path.parent, ignore_errors=True)
    print("Done.")


if __name__ == "__main__":
    main()
