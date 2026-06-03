import java.sql.*;

/**
 * H2 Embedded CRUD Recipe — persistent, file-backed database.
 *
 * Connects to an embedded H2 database stored in a file on disk.
 * Demonstrates the full CRUD cycle:
 *   CREATE table, INSERT rows, SELECT (read), UPDATE, DELETE.
 *
 * The database file is created at the given path (e.g. "./employees" creates
 * "employees.mv.db" in the working directory).
 *
 * Run: mvn compile exec:java -Dexec.mainClass="recipe_embedded_crud"
 *       (add exec-maven-plugin to pom.xml, or compile and run with java)
 *
 * H2 version: 2.4.240
 */
public class recipe_embedded_crud {

    // jdbc:h2:<path> opens (or creates) a persistent file-backed database
    private static final String JDBC_URL = "jdbc:h2:./employees";

    public static void main(String[] args) throws Exception {
        // Load the H2 JDBC driver (optional for modern JDBC 4+, but safe)
        Class.forName("org.h2.Driver");

        // ── Connect & create schema ──────────────────────────────────────
        try (Connection conn = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            try (Statement stmt = conn.createStatement()) {
                stmt.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id          INT AUTO_INCREMENT PRIMARY KEY,
                        name        VARCHAR(100) NOT NULL,
                        department  VARCHAR(50)  NOT NULL,
                        salary      DECIMAL(10, 2)
                    )
                    """);
            }
            System.out.println("Table 'employees' ready.\n");

            // ── CREATE: insert rows ──────────────────────────────────────
            String insertSQL = "INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)";
            try (PreparedStatement pstmt = conn.prepareStatement(insertSQL)) {
                pstmt.setString(1, "Alice Johnson");
                pstmt.setString(2, "Engineering");
                pstmt.setBigDecimal(3, new java.math.BigDecimal("95000.00"));
                pstmt.executeUpdate();

                pstmt.setString(1, "Bob Smith");
                pstmt.setString(2, "Marketing");
                pstmt.setBigDecimal(3, new java.math.BigDecimal("72000.00"));
                pstmt.executeUpdate();

                pstmt.setString(1, "Carol Chen");
                pstmt.setString(2, "Engineering");
                pstmt.setBigDecimal(3, new java.math.BigDecimal("108000.00"));
                pstmt.executeUpdate();
            }
            System.out.println("Inserted 3 employees.\n");

            // ── READ: SELECT ────────────────────────────────────────────
            System.out.println("--- All Employees ---");
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(
                     "SELECT id, name, department, salary FROM employees ORDER BY id")) {
                while (rs.next()) {
                    System.out.printf("  [%d] %-20s | %-15s | $%,10.2f%n",
                        rs.getInt("id"),
                        rs.getString("name"),
                        rs.getString("department"),
                        rs.getDouble("salary"));
                }
            }

            // ── UPDATE: give Engineering a 5% raise ──────────────────────
            String updateSQL = "UPDATE employees SET salary = salary * 1.05 WHERE department = ?";
            try (PreparedStatement pstmt = conn.prepareStatement(updateSQL)) {
                pstmt.setString(1, "Engineering");
                int updated = pstmt.executeUpdate();
                System.out.printf("%nUpdated %d Engineering employee(s) with a 5%% raise.%n%n", updated);
            }

            // ── READ after update ────────────────────────────────────────
            System.out.println("--- After Raise ---");
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(
                     "SELECT id, name, department, salary FROM employees ORDER BY id")) {
                while (rs.next()) {
                    System.out.printf("  [%d] %-20s | %-15s | $%,10.2f%n",
                        rs.getInt("id"),
                        rs.getString("name"),
                        rs.getString("department"),
                        rs.getDouble("salary"));
                }
            }

            // ── DELETE: remove Marketing ─────────────────────────────────
            String deleteSQL = "DELETE FROM employees WHERE department = ?";
            try (PreparedStatement pstmt = conn.prepareStatement(deleteSQL)) {
                pstmt.setString(1, "Marketing");
                int deleted = pstmt.executeUpdate();
                System.out.printf("%nDeleted %d employee(s) from Marketing.%n%n", deleted);
            }

            // ── Aggregation query ────────────────────────────────────────
            System.out.println("--- Department Summary ---");
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(
                     "SELECT department, COUNT(*) AS count, AVG(salary) AS avg_salary " +
                     "FROM employees GROUP BY department ORDER BY department")) {
                while (rs.next()) {
                    System.out.printf("  %-15s | %d employee(s) | Avg salary: $%,10.2f%n",
                        rs.getString("department"),
                        rs.getInt("count"),
                        rs.getDouble("avg_salary"));
                }
            }
        }

        System.out.println("\nDatabase persisted to: ./employees.mv.db");
    }
}
