# H2

> **Category:** relational | **License:** MPL-2.0 / EPL-1.0 | **Stars:** ~4,600

## Overview

H2 is an embeddable Java SQL database engine. It runs in-process as a library with zero external dependencies, supports both disk-based and in-memory databases, and provides a JDBC API. Its tiny footprint (around 2.5 MB) makes it the go-to embedded relational database for Java applications, used extensively in Spring Boot dev mode, integration testing, and desktop apps.

## Quick Start

### Java

```java
// Maven: com.h2database:h2:2.4.240

import java.sql.*;

public class QuickStart {
    public static void main(String[] args) throws Exception {
        // Embedded persistent database — a file named "mydb.mv.db" is created
        try (Connection conn = DriverManager.getConnection("jdbc:h2:./mydb")) {
            try (Statement stmt = conn.createStatement()) {
                stmt.execute("CREATE TABLE IF NOT EXISTS users (" +
                             "id INT AUTO_INCREMENT PRIMARY KEY, " +
                             "name VARCHAR(100) NOT NULL)");
                stmt.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob')");
            }
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT * FROM users")) {
                while (rs.next()) {
                    System.out.printf("id=%d, name=%s%n",
                                      rs.getInt("id"), rs.getString("name"));
                }
            }
        }
    }
}
```

## On-Disk Format

MVStore (single `.mv.db` file per database)

## Core Strengths

- Embedded in-process operation with zero external dependencies
- Ultra-fast in-memory mode for testing and transient workloads
- Small footprint: around 2.5 MB jar file size
- Full JDBC API with broad SQL standard support
- Browser-based Console application for administration
- Multi-version concurrency control and transaction support

## Best Use Cases

1. **Embedded database inside Java desktop applications** — Ship an SQL database inside a Swing/JavaFX app with no separate install
2. **In-memory database for fast integration testing in CI/CD pipelines** — Replace heavy external RDBMS with an in-memory H2 that resets between test runs
3. **Development-time stand-in for heavier RDBMS like PostgreSQL or MySQL** — Use H2 with PostgreSQL compatibility mode during local development, switch to the real thing in production
4. **Local storage for Spring Boot microservices running in dev mode** — Spring Boot auto-configures H2 when it's on the classpath and no other datasource is configured
5. **Lightweight SQL engine for Java-based IoT and edge deployments** — Full SQL on resource-constrained devices with a JVM

## Recipes

| Language | Recipe | Description |
|----------|--------|-------------|
| Java | [`recipe_embedded_crud.java`](java/src/main/java/recipe_embedded_crud.java) | Persistent embedded database with full CRUD operations |
| Java | [`recipe_in_memory.java`](java/src/main/java/recipe_in_memory.java) | Named in-memory database shared across connections |

## Limitations & Caveats

- H2's primary strength is embedded use; server mode exists but is less battle-tested than dedicated server databases
- The dual MPL 2.0 / EPL 1.0 license requires modified H2 source code to be published
- PostgreSQL compatibility mode does not support all PostgreSQL features; verify before relying on it as a drop-in replacement
- In-memory databases are lost when the JVM exits unless you explicitly export or use `DB_CLOSE_DELAY=-1`

## Further Reading

- [Official Documentation](https://www.h2database.com/html/main.html)
- [Source Repository](https://github.com/h2database/h2database)
- [Quickstart Guide](https://www.h2database.com/html/quickstart.html)
- [Features Overview](https://www.h2database.com/html/features.html)
