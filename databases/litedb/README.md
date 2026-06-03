# LiteDB

> **Category:** Document | **License:** MIT | **Stars:** ~9,000

## Overview

LiteDB is a lightweight, embedded NoSQL document database for .NET, inspired by MongoDB. It stores data as BSON documents in a single data file with no server required. LiteDB provides a fluent API with POCO mapping, LINQ queries, ACID transactions, and cross-collection document references. It is ideal for desktop, mobile (Xamarin/MAUI), and small web applications that need a zero-configuration embedded database.

## Quick Start

### C#

```csharp
// Install: dotnet add package LiteDB
using LiteDB;

// Connect / open (creates if not exists)
using var db = new LiteDatabase("mydata.db");

// Get a collection (auto-creates)
var customers = db.GetCollection<Customer>("customers");

// Insert documents
customers.Insert(new Customer { Name = "Alice", Age = 30 });
customers.Insert(new Customer { Name = "Bob", Age = 25 });

// Query with LINQ
var results = customers.Find(x => x.Age > 20);
foreach (var c in results)
    Console.WriteLine($"{c.Name} ({c.Age})");

// Update documents
var alice = customers.FindOne(x => x.Name == "Alice");
alice.Age = 31;
customers.Update(alice);

// Delete documents
customers.DeleteMany(x => x.Age < 21);

// POCO class
public class Customer
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int Age { get; set; }
}
```

## On-Disk Format

Binary JSON (BSON) Single File

## Core Strengths

- Zero-configuration embedded database -- single DLL under 450 KB
- MongoDB-like document API with BSON storage and POCO mapping
- LINQ query support with expression-based filtering and indexing
- ACID transactions with thread-safe operations
- Cross-collection document references (DbRef) for relational patterns
- Built-in FileStorage for storing files and streams (like GridFS)
- Cross-platform: .NET Framework, .NET Core, Xamarin, Unity, UWP

## Best Use Cases

1. **Desktop App Storage** -- Local persistence for WPF, WinForms, and Avalonia desktop applications with zero setup.
2. **Mobile Local Data** -- Xamarin and .NET MAUI mobile apps needing embedded document storage without SQLite's relational overhead.
3. **Application File Format** -- Single-file data format for .NET applications, similar to how SQLite is used as an application file format.
4. **Per-User Data Stores** -- One database per user or account in web applications where document-model data fits better than relational tables.
5. **Prototyping** -- Rapid prototyping of .NET applications where a document model is more natural than relational schemas.

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| C# | [`RecipeDocumentStore.cs`](csharp/RecipeDocumentStore.cs) | Basic document CRUD with BsonMapper and typed collections |
| C# | [`RecipeLinqQueries.cs`](csharp/RecipeLinqQueries.cs) | LINQ queries with filtering, projection, ordering, and indexing |

## Limitations & Caveats

- Documents are limited to 1 MB each (use FileStorage for larger payloads)
- Not designed for concurrent access from multiple processes
- Writes are serialized per collection (reader-writer lock model)
- No built-in replication or sync -- purely embedded, single-node storage
- Query performance depends on proper indexing; full collection scans on unindexed fields

## Further Reading

- [Official Documentation](https://www.litedb.org/docs/)
- [Source Repository](https://github.com/mbdavid/LiteDB)
- [NuGet Package](https://www.nuget.org/packages/LiteDB)
