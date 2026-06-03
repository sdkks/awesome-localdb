import org.junit.jupiter.api.*;

import java.sql.*;
import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the H2 in-memory database patterns demonstrated in
 * recipe_in_memory.java.
 *
 * Verifies that named in-memory databases survive connection closes when
 * DB_CLOSE_DELAY=-1 is set, and that transactions work correctly.
 */
class RecipeInMemoryTest {

    private static final String JDBC_URL = "jdbc:h2:mem:test_orders;DB_CLOSE_DELAY=-1";

    @BeforeEach
    void setUp() throws Exception {
        try (Connection conn = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            try (Statement stmt = conn.createStatement()) {
                stmt.execute("""
                    CREATE TABLE IF NOT EXISTS orders (
                        id          INT AUTO_INCREMENT PRIMARY KEY,
                        product     VARCHAR(100) NOT NULL,
                        quantity    INT          NOT NULL,
                        price_each  DECIMAL(8, 2) NOT NULL
                    )
                    """);
            }
        }
    }

    @AfterEach
    void tearDown() throws Exception {
        // Clean up for next test
        try (Connection conn = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            try (Statement stmt = conn.createStatement()) {
                stmt.execute("DROP TABLE IF EXISTS orders");
            }
        }
    }

    @Test
    void shouldPersistDataAcrossConnections() throws Exception {
        // Connection 1 — insert
        try (Connection conn1 = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            try (PreparedStatement pstmt = conn1.prepareStatement(
                    "INSERT INTO orders (product, quantity, price_each) VALUES (?, ?, ?)")) {
                pstmt.setString(1, "Widget");
                pstmt.setInt(2, 10);
                pstmt.setBigDecimal(3, new BigDecimal("12.50"));
                pstmt.executeUpdate();
            }
        }

        // Connection 2 — data should still be there
        try (Connection conn2 = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            try (Statement stmt = conn2.createStatement();
                 ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM orders")) {
                assertTrue(rs.next());
                assertEquals(1, rs.getInt(1),
                        "Data should survive connection close with DB_CLOSE_DELAY=-1");
            }
        }
    }

    @Test
    void shouldAggregateByProduct() throws Exception {
        try (Connection conn = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            // Insert data
            try (PreparedStatement pstmt = conn.prepareStatement(
                    "INSERT INTO orders (product, quantity, price_each) VALUES (?, ?, ?)")) {
                pstmt.setString(1, "Widget");
                pstmt.setInt(2, 10);
                pstmt.setBigDecimal(3, new BigDecimal("12.50"));
                pstmt.executeUpdate();

                pstmt.setString(1, "Gadget");
                pstmt.setInt(2, 5);
                pstmt.setBigDecimal(3, new BigDecimal("29.99"));
                pstmt.executeUpdate();

                pstmt.setString(1, "Widget");
                pstmt.setInt(2, 7);
                pstmt.setBigDecimal(3, new BigDecimal("12.50"));
                pstmt.executeUpdate();
            }

            // Aggregate
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(
                         "SELECT product, SUM(quantity) AS total_qty, " +
                         "SUM(quantity * price_each) AS total_value " +
                         "FROM orders GROUP BY product ORDER BY total_value DESC")) {

                // Widget should come first (higher total value)
                assertTrue(rs.next());
                assertEquals("Widget", rs.getString("product"));
                assertEquals(17, rs.getInt("total_qty"));
                assertEquals(212.50, rs.getDouble("total_value"), 0.01);

                // Gadget
                assertTrue(rs.next());
                assertEquals("Gadget", rs.getString("product"));
                assertEquals(5, rs.getInt("total_qty"));
                assertEquals(149.95, rs.getDouble("total_value"), 0.01);
            }
        }
    }

    @Test
    void shouldCommitTransaction() throws Exception {
        try (Connection conn = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            // Insert initial data with auto-commit
            try (PreparedStatement pstmt = conn.prepareStatement(
                    "INSERT INTO orders (product, quantity, price_each) VALUES (?, ?, ?)")) {
                pstmt.setString(1, "Gadget");
                pstmt.setInt(2, 3);
                pstmt.setBigDecimal(3, new BigDecimal("29.99"));
                pstmt.executeUpdate();
            }

            // Transaction: update quantity
            conn.setAutoCommit(false);
            try (PreparedStatement pstmt = conn.prepareStatement(
                    "UPDATE orders SET quantity = quantity + 2 WHERE product = ?")) {
                pstmt.setString(1, "Gadget");
                int updated = pstmt.executeUpdate();
                assertEquals(1, updated);
            }
            conn.commit();
            conn.setAutoCommit(true);

            // Verify
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(
                         "SELECT quantity FROM orders WHERE product = 'Gadget'")) {
                assertTrue(rs.next());
                assertEquals(5, rs.getInt("quantity"));
            }
        }
    }

    @Test
    void shouldRollbackTransactionOnError() throws Exception {
        try (Connection conn = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            // Insert initial data
            try (PreparedStatement pstmt = conn.prepareStatement(
                    "INSERT INTO orders (product, quantity, price_each) VALUES (?, ?, ?)")) {
                pstmt.setString(1, "Widget");
                pstmt.setInt(2, 10);
                pstmt.setBigDecimal(3, new BigDecimal("12.50"));
                pstmt.executeUpdate();
            }

            // Start transaction, update, then force rollback
            conn.setAutoCommit(false);
            try (PreparedStatement pstmt = conn.prepareStatement(
                    "UPDATE orders SET quantity = 999 WHERE product = ?")) {
                pstmt.setString(1, "Widget");
                pstmt.executeUpdate();
            }
            conn.rollback();
            conn.setAutoCommit(true);

            // Verify rollback — quantity should be unchanged
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(
                         "SELECT quantity FROM orders WHERE product = 'Widget'")) {
                assertTrue(rs.next());
                assertEquals(10, rs.getInt("quantity"),
                        "Quantity should be unchanged after rollback");
            }
        }
    }

    @Test
    void shouldSupportAutoIncrementPrimaryKey() throws Exception {
        try (Connection conn = DriverManager.getConnection(JDBC_URL, "sa", "")) {
            try (PreparedStatement pstmt = conn.prepareStatement(
                    "INSERT INTO orders (product, quantity, price_each) VALUES (?, ?, ?)",
                    Statement.RETURN_GENERATED_KEYS)) {
                pstmt.setString(1, "Widget");
                pstmt.setInt(2, 1);
                pstmt.setBigDecimal(3, BigDecimal.ONE);
                pstmt.executeUpdate();

                try (ResultSet keys = pstmt.getGeneratedKeys()) {
                    assertTrue(keys.next());
                    assertTrue(keys.getInt(1) > 0, "Should get a positive generated id");
                }
            }
        }
    }
}
