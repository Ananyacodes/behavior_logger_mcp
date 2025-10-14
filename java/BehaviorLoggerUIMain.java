import javax.swing.*;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Main entry point for the Behavior Logger UI
 * This class will try to run the enhanced UI with JFreeChart visualizations,
 * but will fall back to the basic UI if JFreeChart is not available.
 */
public class BehaviorLoggerUIMain {
    public static void main(String[] args) {
        // Set look and feel
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (UnsupportedLookAndFeelException | ClassNotFoundException |
                 InstantiationException | IllegalAccessException e) {
            System.err.println("Warning: could not set look and feel: " + e.getMessage());
        }
        
        // Try to load the JFreeChart class to check if it's available
        boolean hasJFreeChart = false;
        try {
            Class.forName("org.jfree.chart.JFreeChart");
            hasJFreeChart = true;
            System.out.println("JFreeChart is available. Starting enhanced UI...");
        } catch (ClassNotFoundException e) {
            System.out.println("JFreeChart not found. Starting basic UI...");
            System.out.println("To enable enhanced visualizations, download JFreeChart from:");
            System.out.println("https://repo1.maven.org/maven2/org/jfree/jfreechart/1.5.3/jfreechart-1.5.3.jar");
        }
        
        // Create a final flag for the lambda
        final boolean jfreeChartAvailable = hasJFreeChart;

        // Try to launch a terminal that runs the live-tail script so the user
        // sees the same streaming logs in a terminal window while the UI runs.
        // This is best-effort; failures are logged to stderr but do not stop the UI.
        try {
            startTerminalLiveTail();
        } catch (Exception e) {
            System.err.println("Could not start terminal live-tail: " + e.getMessage());
        }
        
        // Start the appropriate UI version
        SwingUtilities.invokeLater(() -> {
            if (jfreeChartAvailable) {
                // Try to run the enhanced UI; constructor will show the window
                try {
                    BehaviorLoggerUIEnhanced enhanced = (BehaviorLoggerUIEnhanced)
                        Class.forName("BehaviorLoggerUIEnhanced").getDeclaredConstructor().newInstance();
                    enhanced.setVisible(true);
                    System.out.println("Enhanced UI started successfully!");
                } catch (ReflectiveOperationException e) {
                    System.err.println("Error starting enhanced UI: " + e.getMessage());
                    System.out.println("Falling back to basic UI...");
                    BehaviorLoggerUI fallback = new BehaviorLoggerUI(); // shown by constructor
                    fallback.setVisible(true);
                }
            } else {
                // Run the basic UI; shown by constructor
                BehaviorLoggerUI ui = new BehaviorLoggerUI();
                ui.setVisible(true);
            }
        });
    }

    /**
     * Best-effort: launches a PowerShell window that runs the workspace venv python
     * with the `python\live_tail.py` script and redirects its output to files in
     * the `logs` directory. If PowerShell is unavailable or the process fails,
     * an IOException is thrown.
     */
    private static void startTerminalLiveTail() throws IOException {
        // Build absolute paths based on current working directory
        Path cwd = Paths.get(System.getProperty("user.dir"));
        Path venvPython = cwd.resolve(".venv\\Scripts\\python.exe");
        Path script = cwd.resolve("python\\live_tail.py");
        Path logsDir = cwd.resolve("logs");

        // Ensure logs directory exists (PowerShell will create it too, but this is defensive)
        java.io.File logs = logsDir.toFile();
        if (!logs.exists()) {
            logs.mkdirs();
        }

        // Prefer the project's venv python, but fall back to the system python if not present
        String pythonExe = venvPython.toString();
        if (!venvPython.toFile().exists()) {
            pythonExe = "python"; // rely on PATH
        }

        // PowerShell command to open a visible window and run the live_tail script
        // We avoid redirecting to files so the window shows live output and isn't locked by background processes.
        String psCommandVisible = String.format("Start-Process -FilePath 'powershell.exe' -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"%s %s\"' -WorkingDirectory '%s'", pythonExe.replace("'","''"), script.toString().replace("'","''"), cwd.toString().replace("'","''"));

        // Launch PowerShell to execute the command which itself starts a new visible window
        new ProcessBuilder("powershell.exe", "-NoProfile", "-Command", psCommandVisible)
            .directory(cwd.toFile())
            .start();
    }
}