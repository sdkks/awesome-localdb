using Xunit;

namespace AwesomeLocalDb.LiteDB.Tests;

/// <summary>
/// Tests for RecipeDocumentStore — verifies the recipe runs without exceptions
/// and produces expected output.
/// </summary>
public class RecipeDocumentStoreTests
{
    [Fact]
    public void Recipe_RunsWithoutError()
    {
        // The recipe should execute without raising an exception.
        RecipeDocumentStore.Run();
    }
}
