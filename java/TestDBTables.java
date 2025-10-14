import java.sql.Connection;
import java.sql.DatabaseMetaData;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;

public class TestDBTables {
    public static void main(String[] args) {
        String url = "jdbc:mysql://localhost:3306/neurolock";
        String user = "root";
        String pass = "JoeMama@25";

        System.out.println("Testing DatabaseMetaData.getTables on: " + url);
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            System.out.println("Driver class not found: " + e.getMessage());
        }

        try (Connection conn = DriverManager.getConnection(url, user, pass)) {
            DatabaseMetaData md = conn.getMetaData();
            try (ResultSet rs = md.getTables(null, null, "%", new String[]{"TABLE"})) {
                int count = 0;
                while (rs.next()) {
                    String name = rs.getString("TABLE_NAME");
                    System.out.println("Table: " + name);
                    count++;
                }
                System.out.println("Total tables: " + count);
            }
        } catch (SQLException e) {
            System.out.println("SQLException: " + e.getMessage());
            e.printStackTrace(System.out);
        } catch (Throwable t) {
            System.out.println("Other error: " + t.getMessage());
            t.printStackTrace(System.out);
        }
    }
}
