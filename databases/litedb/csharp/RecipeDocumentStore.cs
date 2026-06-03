namespace AwesomeLocalDb.LiteDB;

using LiteDB;

/// <summary>
/// Recipe: Document Store CRUD
/// Database: LiteDB
/// Description: Demonstrates basic document operations — insert, query with expressions,
///              update, upsert, and delete — using LiteDB's typed collection API.
///
/// Usage: dotnet run
/// </summary>
public class RecipeDocumentStore
{
    public static void Main(string[] args)
    {
        Run();
    }

    public static void Run()
    {
        // Use a temporary file so we don't leave artifacts on disk
        var dbPath = Path.Combine(Path.GetTempPath(), $"litedb_recipe_{Guid.NewGuid():N}.db");

        try
        {
            using var db = new LiteDatabase(dbPath);

            // --- 1. Get typed collection ---
            var users = db.GetCollection<User>("users");

            // --- 2. Insert documents ---
            var alice = new User { Name = "Alice", Age = 30, City = "London" };
            var bob = new User { Name = "Bob", Age = 25, City = "Paris" };
            var charlie = new User { Name = "Charlie", Age = 35, City = "London" };

            users.Insert(alice);
            users.Insert(bob);
            users.Insert(charlie);
            users.InsertBulk(new[]
            {
                new User { Name = "Diana", Age = 28, City = "Berlin" },
                new User { Name = "Eve", Age = 22, City = "Paris" },
            });

            Console.WriteLine($"Inserted {users.Count()} documents.");

            // --- 3. Query with expression predicates ---

            // Exact match
            var aliceResult = users.FindOne(x => x.Name == "Alice");
            Console.WriteLine($"Found Alice: Id={aliceResult.Id}, Age={aliceResult.Age}, City={aliceResult.City}");

            // Comparison
            var young = users.Find(x => x.Age < 30);
            Console.WriteLine($"Users under 30: {string.Join(", ", young.Select(u => u.Name))}");

            // Combined query
            var londonAdults = users.Find(x => x.City == "London" && x.Age >= 30);
            Console.WriteLine($"London adults: {string.Join(", ", londonAdults.Select(u => u.Name))}");

            // Existence check
            var hasBob = users.Exists(x => x.Name == "Bob");
            var hasZelda = users.Exists(x => x.Name == "Zelda");
            Console.WriteLine($"Contains Bob: {hasBob}");
            Console.WriteLine($"Contains Zelda: {hasZelda}");

            // --- 4. Update documents ---
            aliceResult.Age = 31;
            users.Update(aliceResult);
            var updatedAlice = users.FindOne(x => x.Name == "Alice");
            Console.WriteLine($"Updated Alice: Age={updatedAlice.Age}");

            // --- 5. Upsert ---
            // Upsert a new document (no match => insert)
            users.Upsert(new User { Name = "Frank", Age = 40, City = "Tokyo" });
            // Upsert an existing document (match => update)
            users.Upsert(new User { Name = "Bob", Age = 26, City = "Paris" });

            Console.WriteLine($"After upserts, document count: {users.Count()}");
            var updatedBob = users.FindOne(x => x.Name == "Bob");
            Console.WriteLine($"Bob after upsert: Age={updatedBob.Age}");

            // --- 6. Count documents ---
            var parisCount = users.Count(x => x.City == "Paris");
            Console.WriteLine($"Users in Paris: {parisCount}");

            // --- 7. Delete documents ---
            var deletedCount = users.DeleteMany(x => x.Name == "Eve");
            Console.WriteLine($"Removed Eve, deleted count: {deletedCount}");
            Console.WriteLine($"Document count after delete: {users.Count()}");

            // --- 8. Retrieve all documents ---
            var allDocs = users.FindAll().ToList();
            Console.WriteLine($"All documents ({allDocs.Count}):");
            foreach (var doc in allDocs)
                Console.WriteLine($"  {doc}");

            db.Dispose();
        }
        finally
        {
            if (File.Exists(dbPath))
                File.Delete(dbPath);
        }
    }
}

/// <summary>
/// POCO class mapped to BSON documents by LiteDB.
/// The Id property is automatically mapped to the document's _id field.
/// </summary>
public class User
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public int Age { get; set; }
    public string City { get; set; } = string.Empty;

    public override string ToString() => $"User {{ Id={Id}, Name={Name}, Age={Age}, City={City} }}";
}
