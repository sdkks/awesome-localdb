"""Tests for recipe_data_pipeline.py"""

from src.recipe_data_pipeline import main


def test_recipe_runs_without_error():
    """The recipe should execute without raising an exception."""
    main()


def test_recipe_pipeline_output(capsys):
    """The pipeline should read CSV, transform, write Parquet, and verify."""
    main()
    captured = capsys.readouterr()

    # Should show raw data inspection
    assert "Raw CSV Data" in captured.out
    assert "Widget" in captured.out
    assert "Gadget" in captured.out

    # Should show transformation results
    assert "Transformed: Revenue by Product and Region" in captured.out
    assert "total_revenue" in captured.out

    # Should verify Parquet output
    assert "Verify Parquet Output" in captured.out
    assert "Pipeline verified" in captured.out

    # Should end cleanly
    assert "Done." in captured.out
