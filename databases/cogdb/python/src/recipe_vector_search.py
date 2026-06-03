"""
Recipe: Vector Search
Database: CogDB
Description: Store embeddings on graph vertices and run SIMD-accelerated
             vector similarity search. Demonstrates put_embedding,
             k_nearest neighbors, cosine similarity filtering, and
             combining graph traversal with vector search.

Usage: python src/recipe_vector_search.py
"""

import shutil
import tempfile
from pathlib import Path

from cog import config
from cog.torque import Graph


def main() -> None:
    """Store embeddings and run vector similarity search on a graph."""
    # 1. Setup -- use a temporary directory for isolation
    tmpdir = Path(tempfile.mkdtemp(prefix="cogdb_vector_"))
    config.COG_PATH_PREFIX = str(tmpdir)
    config.COG_HOME = "recipe_vector"

    g = Graph("fruits")

    # 2. Insert graph data -- fruit categories and properties
    g.put("orange", "type", "citrus")
    g.put("tangerine", "type", "citrus")
    g.put("lemon", "type", "citrus")
    g.put("apple", "type", "pome")
    g.put("pear", "type", "pome")
    g.put("banana", "type", "tropical")
    g.put("mango", "type", "tropical")
    g.put("grape", "type", "berry")
    g.put("blueberry", "type", "berry")

    # Embeddings: [sweetness, size, tartness, color_warmth]
    # Citrus fruits cluster together in the embedding space
    g.put_embedding("orange", [0.8, 0.7, 0.4, 0.9])
    g.put_embedding("tangerine", [0.85, 0.6, 0.35, 0.85])
    g.put_embedding("lemon", [0.2, 0.5, 0.95, 0.7])
    # Pome fruits
    g.put_embedding("apple", [0.6, 0.6, 0.3, 0.4])
    g.put_embedding("pear", [0.65, 0.55, 0.25, 0.35])
    # Tropical fruits
    g.put_embedding("banana", [0.9, 0.8, 0.1, 0.6])
    g.put_embedding("mango", [0.95, 0.75, 0.15, 0.7])
    # Berries
    g.put_embedding("grape", [0.85, 0.1, 0.2, 0.3])
    g.put_embedding("blueberry", [0.75, 0.05, 0.4, 0.2])

    # 3. Find k-nearest neighbors of orange
    print("=== Top 3 Nearest Neighbors of Orange ===")
    result = g.k_nearest("orange", k=3).all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 4. Filter by similarity threshold -- fruits similar to orange (> 0.8)
    print("\n=== Fruits Similar to Orange (cosine > 0.8) ===")
    result = g.sim("orange", ">", 0.8).all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 5. Filter by similarity range -- fruits moderately similar to apple
    print("\n=== Fruits Moderately Similar to Apple (0.5 to 0.9) ===")
    result = g.sim("apple", "in", [0.5, 0.9]).all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 6. Combine graph traversal with vector search --
    #    among citrus fruits, find those similar to orange
    print("\n=== Citrus Fruits Similar to Orange (> 0.7) ===")
    result = g.v().has("type", "citrus").sim("orange", ">", 0.7).all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 7. Filter by similarity below threshold -- fruits dissimilar to banana
    print("\n=== Fruits Dissimilar to Banana (cosine < 0.7) ===")
    result = g.sim("banana", "<", 0.7).all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 8. k-NN among tropical fruits only
    print("\n=== Tropical Fruits Nearest to Mango ===")
    result = g.v().has("type", "tropical").k_nearest("mango", k=2).all()
    for item in result["result"]:
        print(f"  {item['id']}")

    # 9. Embedding stats
    print("\n=== Embedding Stats ===")
    stats = g.embedding_stats()
    print(f"  Count: {stats['count']}, Dimensions: {stats['dimensions']}")

    # 10. Cleanup
    g.sync()
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("\nDone.")


if __name__ == "__main__":
    main()
