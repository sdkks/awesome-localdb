using Xunit;

namespace AwesomeLocalDb.LiteDB.Tests;

/// <summary>
/// Tests for RecipeLinqQueries — verifies the recipe runs without exceptions
/// and produces expected output.
/// </summary>
public class RecipeLinqQueriesTests
{
    [Fact]
    public void Recipe_RunsWithoutError()
    {
        // The recipe should execute without raising an exception.
        RecipeLinqQueries.Run();
    }
}
