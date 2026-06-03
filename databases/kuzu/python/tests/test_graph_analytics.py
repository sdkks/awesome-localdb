"""Tests for recipe_graph_analytics.py"""

from src.recipe_graph_analytics import main, compute_pagerank


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output citation graph and PageRank results."""
    main()
    captured = capsys.readouterr()

    # Should contain section headers
    assert "Citation Graph" in captured.out
    assert "PageRank Scores" in captured.out

    # Should contain paper titles
    assert "Foundations of Graph Theory" in captured.out
    assert "Advances in PageRank" in captured.out
    assert "Scalable Graph Processing" in captured.out
    assert "Modern Database Systems" in captured.out
    assert "Graph Analytics in Practice" in captured.out
    assert "Vector Search and Graphs" in captured.out

    # Should have computed PageRank sum
    assert "Sum of PageRank scores:" in captured.out

    # Should end with Done
    assert "Done." in captured.out


def test_pagerank_sums_to_one():
    """PageRank scores should sum to approximately 1.0."""
    edges = [
        ("A", "B"),
        ("B", "C"),
        ("A", "C"),
        ("C", "A"),
        ("B", "A"),
    ]
    ranks = compute_pagerank(edges, damping=0.85, iterations=40)
    total = sum(ranks.values())
    assert 0.99 < total < 1.01, f"PageRank sum {total} not close to 1.0"


def test_pagerank_empty_graph():
    """Empty graph should return empty dict."""
    ranks = compute_pagerank([], damping=0.85, iterations=20)
    assert ranks == {}


def test_pagerank_single_node():
    """Single node with self-loop should have rank ~1.0."""
    edges = [("X", "X")]
    ranks = compute_pagerank(edges, damping=0.85, iterations=30)
    assert len(ranks) == 1
    assert 0.99 < ranks["X"] < 1.01


def test_pagerank_dangling_node():
    """Dangling node (no outgoing) should still get non-zero rank."""
    edges = [("A", "B")]
    ranks = compute_pagerank(edges, damping=0.85, iterations=30)
    # Both A and B should have non-zero scores
    assert ranks["A"] > 0
    assert ranks["B"] > 0
    # B receives links, so should have higher rank
    assert ranks["B"] > ranks["A"]


def test_pagerank_equal_graph():
    """Fully connected equal graph should have equal ranks."""
    edges = [
        ("A", "B"), ("B", "A"),
        ("A", "C"), ("C", "A"),
        ("B", "C"), ("C", "B"),
    ]
    ranks = compute_pagerank(edges, damping=0.85, iterations=30)
    assert len(ranks) == 3
    # All should be approximately equal
    values = list(ranks.values())
    assert max(values) - min(values) < 0.01
