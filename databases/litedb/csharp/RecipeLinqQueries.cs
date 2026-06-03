namespace AwesomeLocalDb.LiteDB;

using LiteDB;

/// <summary>
/// Recipe: LINQ Queries and Indexing
/// Database: LiteDB
/// Description: Demonstrates LINQ-style queries with filtering, projection, ordering,
///              and indexing — using LiteDB's expression-based query engine.
///
/// Usage: dotnet run --project . --StartupObject AwesomeLocalDb.LiteDB.RecipeLinqQueries
/// </summary>
public class RecipeLinqQueries
{
    public static void Main(string[] args)
    {
        Run();
    }

    public static void Run()
    {
        var dbPath = Path.Combine(Path.GetTempPath(), $"litedb_recipe_{Guid.NewGuid():N}.db");

        try
        {
            using var db = new LiteDatabase(dbPath);

            var products = db.GetCollection<Product>("products");
            var orders = db.GetCollection<Order>("orders");

            // --- 1. Seed data ---
            products.InsertBulk(new[]
            {
                new Product { Name = "Laptop", Price = 1200m, Category = "Electronics", InStock = true },
                new Product { Name = "Mouse", Price = 25m, Category = "Electronics", InStock = true },
                new Product { Name = "Desk Chair", Price = 350m, Category = "Furniture", InStock = true },
                new Product { Name = "Notebook", Price = 5m, Category = "Stationery", InStock = true },
                new Product { Name = "Monitor", Price = 400m, Category = "Electronics", InStock = false },
                new Product { Name = "Water Bottle", Price = 15m, Category = "Accessories", InStock = true },
                new Product { Name = "Headphones", Price = 80m, Category = "Electronics", InStock = true },
            });

            orders.InsertBulk(new[]
            {
                new Order { ProductName = "Laptop", Quantity = 1, Total = 1200m, OrderDate = DateTime.UtcNow.AddDays(-30) },
                new Order { ProductName = "Mouse", Quantity = 2, Total = 50m, OrderDate = DateTime.UtcNow.AddDays(-7) },
                new Order { ProductName = "Desk Chair", Quantity = 1, Total = 350m, OrderDate = DateTime.UtcNow.AddDays(-14) },
                new Order { ProductName = "Notebook", Quantity = 10, Total = 50m, OrderDate = DateTime.UtcNow.AddDays(-1) },
                new Order { ProductName = "Monitor", Quantity = 1, Total = 400m, OrderDate = DateTime.UtcNow.AddDays(-90) },
                new Order { ProductName = "Headphones", Quantity = 1, Total = 80m, OrderDate = DateTime.UtcNow.AddDays(-3) },
            });

            Console.WriteLine($"Seeded {products.Count()} products and {orders.Count()} orders.");

            // --- 2. LINQ-style filtering ---
            var electronics = products.Find(x => x.Category == "Electronics");
            Console.WriteLine($"\nElectronics ({electronics.Count()}):");
            foreach (var p in electronics)
                Console.WriteLine($"  {p.Name} - ${p.Price}");

            // --- 3. Combined conditions ---
            var cheapAvailable = products.Find(x => x.Price < 100m && x.InStock);
            Console.WriteLine($"\nCheap & in stock ({cheapAvailable.Count()}):");
            foreach (var p in cheapAvailable)
                Console.WriteLine($"  {p.Name} - ${p.Price}");

            // --- 4. Query with ordering ---
            var topExpensive = products.Query()
                .Where(x => x.InStock)
                .OrderByDescending(x => x.Price)
                .Limit(3)
                .ToList();
            Console.WriteLine($"\nTop 3 most expensive in stock:");
            foreach (var p in topExpensive)
                Console.WriteLine($"  {p.Name} - ${p.Price}");

            // --- 5. Projection (returning subsets) ---
            var productNames = products.Query()
                .Where(x => x.Category == "Electronics")
                .Select(x => new { x.Name, x.Price })
                .ToList();
            Console.WriteLine($"\nElectronics names & prices:");
            foreach (var p in productNames)
                Console.WriteLine($"  {p.Name}: ${p.Price}");

            // --- 6. Indexing for faster queries ---
            // Create an index on Category for faster lookups
            products.EnsureIndex(x => x.Category);
            Console.WriteLine($"\nCreated index on Category.");

            // Create a compound-like index on Price for range queries
            products.EnsureIndex(x => x.Price);
            Console.WriteLine("Created index on Price.");

            // --- 7. Aggregation-style query ---
            var totalByCategory = products.FindAll()
                .GroupBy(p => p.Category)
                .Select(g => new
                {
                    Category = g.Key,
                    Count = g.Count(),
                    AvgPrice = g.Average(p => p.Price)
                });
            Console.WriteLine($"\nProducts by category (in-memory aggregation):");
            foreach (var g in totalByCategory)
                Console.WriteLine($"  {g.Category}: {g.Count} items, avg ${g.AvgPrice:F2}");

            // --- 8. Date-range query on orders ---
            var recentOrders = orders.Find(x => x.OrderDate >= DateTime.UtcNow.AddDays(-7));
            Console.WriteLine($"\nRecent orders (last 7 days): {recentOrders.Count()}");
            foreach (var o in recentOrders)
                Console.WriteLine($"  {o.ProductName} x{o.Quantity} = ${o.Total} on {o.OrderDate:yyyy-MM-dd}");

            // --- 9. Exists and Count ---
            var hasExpensive = products.Exists(x => x.Price > 1000m);
            Console.WriteLine($"\nHas items over $1000: {hasExpensive}");
            var totalInventory = products.Count(x => x.InStock);
            Console.WriteLine($"Items in stock: {totalInventory} of {products.Count()}");

            db.Dispose();
        }
        finally
        {
            if (File.Exists(dbPath))
                File.Delete(dbPath);
        }
    }
}

public class Product
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public decimal Price { get; set; }
    public string Category { get; set; } = string.Empty;
    public bool InStock { get; set; }
}

public class Order
{
    public int Id { get; set; }
    public string ProductName { get; set; } = string.Empty;
    public int Quantity { get; set; }
    public decimal Total { get; set; }
    public DateTime OrderDate { get; set; }
}
