import org.junit.jupiter.api.*;

import java.io.File;
import java.sql.*;
import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Tests for the H2 embedded persistent CRUD pattern demonstrated in
 * recipe_embedded_crud.java.
 *
 * Each test method uses a fresh H2 in-memory database so tests are isolated,
 * but the pattern tested is identical to the file-backed embedded usage.
 */
class RecipeEmbeddedCrudTest {

    private Connection conn;

    @BeforeEach
    void setUp() throws Exception {
        // Use in-memory for test isolation; the SQL patterns are the same
        conn = DriverManager.getConnection("jdbc:h2:mem:test_embedded;DB_CLOSE_DELAY=-1", "sa", "");
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
    }

    @AfterEach
    void tearDown() throws Exception {
        if (conn != null && !conn.isClosed()) {
            try (Statement stmt = conn.createStatement()) {
                stmt.execute("DROP TABLE IF EXISTS employees");
            }
            conn.close();
        }
    }

    @Test
    void shouldInsertAndReadEmployees() throws Exception {
        String insertSQL = "INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)";
        try (PreparedStatement pstmt = conn.prepareStatement(insertSQL)) {
            pstmt.setString(1, "Alice Johnson");
            pstmt.setString(2, "Engineering");
            pstmt.setBigDecimal(3, new BigDecimal("95000.00"));
            pstmt.executeUpdate();

            pstmt.setString(1, "Bob Smith");
            pstmt.setString(2, "Marketing");
            pstmt.setBigDecimal(3, new BigDecimal("72000.00"));
            pstmt.executeUpdate();
        }

        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM employees")) {
            assertTrue(rs.next());
            assertEquals(2, rs.getInt(1));
        }
    }

    @Test
    void shouldUpdateEmployeeSalary() throws Exception {
        // Insert
        try (PreparedStatement pstmt = conn.prepareStatement(
                "INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)")) {
            pstmt.setString(1, "Carol Chen");
            pstmt.setString(2, "Engineering");
            pstmt.setBigDecimal(3, new BigDecimal("108000.00"));
            pstmt.executeUpdate();
        }

        // Update — give a 5% raise
        try (PreparedStatement pstmt = conn.prepareStatement(
                "UPDATE employees SET salary = salary * 1.05 WHERE department = ?")) {
            pstmt.setString(1, "Engineering");
            int updated = pstmt.executeUpdate();
            assertEquals(1, updated);
        }

        // Verify
        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(
                     "SELECT salary FROM employees WHERE name = 'Carol Chen'")) {
            assertTrue(rs.next());
            assertEquals(113400.00, rs.getDouble("salary"), 0.01);
        }
    }

    @Test
    void shouldDeleteByDepartment() throws Exception {
        // Insert
        try (PreparedStatement pstmt = conn.prepareStatement(
                "INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)")) {
            pstmt.setString(1, "Alice");
            pstmt.setString(2, "Engineering");
            pstmt.setBigDecimal(3, BigDecimal.ZERO);
            pstmt.executeUpdate();

            pstmt.setString(1, "Bob");
            pstmt.setString(2, "Marketing");
            pstmt.setBigDecimal(3, BigDecimal.ZERO);
            pstmt.executeUpdate();
        }

        // Delete Marketing
        try (PreparedStatement pstmt = conn.prepareStatement(
                "DELETE FROM employees WHERE department = ?")) {
            pstmt.setString(1, "Marketing");
            int deleted = pstmt.executeUpdate();
            assertEquals(1, deleted);
        }

        // Verify
        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery("SELECT department FROM employees")) {
            assertTrue(rs.next());
            assertEquals("Engineering", rs.getString("department"));
            assertFalse(rs.next(), "Only Engineering should remain");
        }
    }

    @Test
    void shouldAggregateByDepartment() throws Exception {
        // Insert
        try (PreparedStatement pstmt = conn.prepareStatement(
                "INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)")) {
            pstmt.setString(1, "Alice");
            pstmt.setString(2, "Engineering");
            pstmt.setBigDecimal(3, new BigDecimal("90000.00"));
            pstmt.executeUpdate();

            pstmt.setString(1, "Bob");
            pstmt.setString(2, "Engineering");
            pstmt.setBigDecimal(3, new BigDecimal("110000.00"));
            pstmt.executeUpdate();

            pstmt.setString(1, "Carol");
            pstmt.setString(2, "Marketing");
            pstmt.setBigDecimal(3, new BigDecimal("70000.00"));
            pstmt.executeUpdate();
        }

        try (Statement stmt = conn.createStatement();
             ResultSet rs = stmt.executeQuery(
                     "SELECT department, COUNT(*) AS cnt, AVG(salary) AS avg_sal " +
                     "FROM employees GROUP BY department ORDER BY department")) {

            // Engineering
            assertTrue(rs.next());
            assertEquals("Engineering", rs.getString("department"));
            assertEquals(2, rs.getInt("cnt"));
            assertEquals(100000.00, rs.getDouble("avg_sal"), 0.01);

            // Marketing
            assertTrue(rs.next());
            assertEquals("Marketing", rs.getString("department"));
            assertEquals(1, rs.getInt("cnt"));
            assertEquals(70000.00, rs.getDouble("avg_sal"), 0.01);
        }
    }

    @Test
    void shouldSupportAutoIncrementPrimaryKey() throws Exception {
        try (PreparedStatement pstmt = conn.prepareStatement(
                "INSERT INTO employees (name, department, salary) VALUES (?, ?, ?)",
                Statement.RETURN_GENERATED_KEYS)) {
            pstmt.setString(1, "Test User");
            pstmt.setString(2, "QA");
            pstmt.setBigDecimal(3, new BigDecimal("50000.00"));
            pstmt.executeUpdate();

            try (ResultSet keys = pstmt.getGeneratedKeys()) {
                assertTrue(keys.next());
                assertEquals(1, keys.getInt(1), "First row should have id = 1");
            }
        }
    }
}
