import java.sql.*;

public class QueryEventTypes {
    public static void main(String[] args) {
        String dbUrl = "jdbc:mysql://localhost:3306/neurolock";
        String dbUser = "root";
        String dbPassword = "JoeMama@25";
        String jarPath = "..\\java_ui\\lib\\mysql-connector-j-9.4.0.jar";

        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            System.out.println("Connected to DB");
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery("SELECT event_type, COUNT(*) FROM behavior_logs GROUP BY event_type ORDER BY COUNT(*) DESC");
                System.out.println("Distinct event_type counts:");
                while (rs.next()) {
                    String et = rs.getString(1);
                    int c = rs.getInt(2);
                    System.out.println("  '" + et + "' : " + c);
                }
            }
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs2 = stmt.executeQuery("DESCRIBE behavior_logs");
                System.out.println("\nbehavior_logs structure:");
                while (rs2.next()) {
                    System.out.println("  " + rs2.getString(1) + " - " + rs2.getString(2));
                }
            }
        } catch (SQLException e) {
            e.printStackTrace();
        }
    }
}
