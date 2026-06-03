import java.sql.*;

/**
 * H2 In-Memory Recipe — named in-memory database shared across connections.
 *
 * jdbc:h2:mem:<name> creates a named in-memory database. Multiple connections
 * to the same name share the same database for the lifetime of the JVM.
 *
 * Use DB_CLOSE_DELAY=-1 to keep the database alive even when the last
 * connection closes (useful for application-scoped in-memory databases).
 *
 * Run: mvn compile exec:java -Dexec.mainClass="recipe_in_memory"
 *
 * H2 version: 2.4.240
 */
public class recipe_in_memory {

    private static final String DB_NAME = "orders_db";
    // DB_CLOSE_DELAY=-1 keeps the in-memory database alive after last connection closes
    private static final String JDBC_URL =
        "jdbc:h2:mem:" + DB_NAME + ";DB_CLOSE_DELAY=-1";

    public static void main(String[] args) throws Exception {
        Class.forName("org.h2.Driver");

        // ── Connection 1: create schema and insert data ──────────────────
        try (Connection conn1 = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            try (Statement stmt = conn1.createStatement()) {
                stmt.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id          INT AUTO_INCREMENT PRIMARY KEY,
                        product     VARCHAR(100) NOT NULL,
                        quantity    INT          NOT NULL,
                        price_each  DECIMAL(8, 2) NOT NULL
                    )
                    """);
            }

            String insertSQL = "INSERT INTO orders (product, quantity, price_each) VALUES (?, ?, ?)";
            try (PreparedStatement pstmt = conn1.prepareStatement(insertSQL)) {
                pstmt.setString(1, "Widget");
                pstmt.setInt(2, 10);
                pstmt.setBigDecimal(3, new java.math.BigDecimal("12.50"));
                pstmt.executeUpdate();

                pstmt.setString(1, "Gadget");
                pstmt.setInt(2, 5);
                pstmt.setBigDecimal(3, new java.math.BigDecimal("29.99"));
                pstmt.executeUpdate();

                pstmt.setString(1, "Widget");
                pstmt.setInt(2, 7);
                pstmt.setBigDecimal(3, new java.math.BigDecimal("12.50"));
                pstmt.executeUpdate();
            }
            System.out.println("Connection 1: created table and inserted 3 orders.\n");
        }
        // conn1 is closed, but DB_CLOSE_DELAY=-1 keeps the database alive

        // ── Connection 2: the data is still there ────────────────────────
        try (Connection conn2 = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            System.out.println("Connection 2: data is still available!\n");

            // Aggregate query — total by product
            System.out.println("--- Order Summary ---");
            String summarySQL = """
                SELECT product,
                       SUM(quantity) AS total_qty,
                       SUM(quantity * price_each) AS total_value
                FROM orders
                GROUP BY product
                ORDER BY total_value DESC
                """;

            try (Statement stmt = conn2.createStatement();
                 ResultSet rs = stmt.executeQuery(summarySQL)) {
                while (rs.next()) {
                    System.out.printf("  %-15s | Qty: %3d | Total: $%,10.2f%n",
                        rs.getString("product"),
                        rs.getInt("total_qty"),
                        rs.getDouble("total_value"));
                }
            }

            // Demonstrate explicit transaction
            System.out.println("\n--- Transaction Demo ---");
            conn2.setAutoCommit(false);
            try {
                try (PreparedStatement pstmt = conn2.prepareStatement(
                        "UPDATE orders SET quantity = quantity + 2 WHERE product = ?")) {
                    pstmt.setString(1, "Gadget");
                    pstmt.executeUpdate();
                }
                conn2.commit();
                System.out.println("Committed: added 2 more Gadgets.\n");
            } catch (SQLException e) {
                conn2.rollback();
                System.out.println("Rolled back on error: " + e.getMessage());
            }

            // Re-read after transaction
            System.out.println("--- Final State ---");
            try (Statement stmt = conn2.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT * FROM orders ORDER BY id")) {
                while (rs.next()) {
                    System.out.printf("  [%d] %-15s | Qty: %3d | @ $%6.2f | Line: $%,8.2f%n",
                        rs.getInt("id"),
                        rs.getString("product"),
                        rs.getInt("quantity"),
                        rs.getDouble("price_each"),
                        rs.getInt("quantity") * rs.getDouble("price_each"));
                }
            }

            conn2.setAutoCommit(true);
        }

        System.out.println("\nIn-memory database discarded on JVM exit (no file on disk).");
    }
}
