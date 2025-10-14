import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class TestDBConnection {
    public static void main(String[] args) {
        String url = "jdbc:mysql://localhost:3306/neurolock";
        String user = "root";
        String pass = "JoeMama@25";

        System.out.println("Testing DB connection to: " + url);
        System.out.println("java.class.path=" + System.getProperty("java.class.path"));
        try {
            // Explicitly load the MySQL JDBC driver
            Class.forName("com.mysql.cj.jdbc.Driver");
            System.out.println("Driver class loaded");
        } catch (ClassNotFoundException cnfe) {
            System.out.println("Driver class not found: " + cnfe.getMessage());
        }
        try {
            Connection c = DriverManager.getConnection(url, user, pass);
            System.out.println("Connection successful: " + (c != null));
            if (c != null) c.close();
        } catch (SQLException e) {
            System.out.println("SQLException: " + e.getMessage());
            e.printStackTrace(System.out);
        } catch (Throwable t) {
            System.out.println("Other error: " + t.getMessage());
            t.printStackTrace(System.out);
        }
    }
}
