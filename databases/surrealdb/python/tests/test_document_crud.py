"""Tests for recipe_document_crud.py"""

from src.recipe_document_crud import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_produces_expected_output(capsys):
    """The recipe should output document CRUD operation results."""
    main()
    captured = capsys.readouterr()

    # Should contain CRUD operations in output
    assert "Created Alice:" in captured.out
    assert "Created Bob:" in captured.out
    assert "Created Charlie:" in captured.out
    assert "Found by ID" in captured.out
    assert "People over 20" in captured.out
    assert "Alice" in captured.out
    assert "Bob" in captured.out
    assert "Updated Charlie:" in captured.out
    assert "Created company:" in captured.out
    assert "Deleted Charlie:" in captured.out
    assert "After deletion, person:charlie" in captured.out

    # Should end with Done
    assert "Done." in captured.out
