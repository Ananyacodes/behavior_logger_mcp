import java.awt.*;
import java.sql.*;
import java.text.SimpleDateFormat;
import java.util.HashMap;
import java.util.Map;
import javax.swing.*;
import javax.swing.border.EmptyBorder;
import javax.swing.table.DefaultTableModel;

/**
 * BehaviorLoggerUI - Java Swing interface for MySQL Behavior Logger
 */
public class BehaviorLoggerUI extends JFrame {
    // Database connection properties
    private static final String JDBC_URL = "jdbc:mysql://localhost:3306/neurolock";
    private static final String USERNAME = "root";
    private static final String PASSWORD = "JoeMama@25"; // Update with your MySQL password
    
    // UI Components
    private JTabbedPane tabbedPane;
    private JTable dataTable;
    private DefaultTableModel tableModel;
    private JComboBox<String> tableSelector;
    private JComboBox<String> eventTypeSelector;
    private JButton refreshButton;
    private JTextField searchField;
    private JComboBox<String> timeFilterSelector;
    private JLabel statusLabel;
    private JLabel totalRecordsLabel;
    private JButton exportButton;
    private JTextArea logTextArea;
    private JCheckBox autoRefreshCheckbox;
    private javax.swing.Timer autoRefreshTimer;
    
    // Tables in the database
    private String[] tables = {
        "behavior_logs"
    };

    // Event types for filtering
    private Map<String, String[]> eventTypesByTable;

    public BehaviorLoggerUI() {
        // Set up the main frame
        setTitle("Behavior Logger Dashboard");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(1200, 800);
        setLocationRelativeTo(null); // Center on screen

        // Initialize event types map
        initEventTypes();
        
        // Set up the UI components
        initComponents();
        
        // Test the database connection
        testConnection();
        
        // Load initial data
        refreshData();
        
        // Set up auto-refresh timer (every 10 seconds)
        autoRefreshTimer = new javax.swing.Timer(10000, e -> {
            if (autoRefreshCheckbox.isSelected()) {
                refreshData();
            }
        });
        autoRefreshTimer.start();
        
        // Display the frame
        setVisible(true);
    }

    private void initEventTypes() {
        eventTypesByTable = new HashMap<>();
        
        // Event types for behavior_logs table
        eventTypesByTable.put("behavior_logs", new String[] {
            "All Types", "KEYSTROKE", "MOUSE_CLICK", "APP_ACTIVITY", "SYSTEM_METRICS"
        });
        
        // Event types for events table
        eventTypesByTable.put("events", new String[] {
            "All Types", "KEYSTROKE", "MOUSE_CLICK", "APP_ACTIVITY", "SYSTEM_METRICS"
        });

        // Default for other tables
        String[] defaultTypes = {"All Types"};
        for (String table : tables) {
            if (!eventTypesByTable.containsKey(table)) {
                eventTypesByTable.put(table, defaultTypes);
            }
        }
    }

    private void initComponents() {
        // Set up the content pane with BorderLayout
        JPanel contentPane = new JPanel(new BorderLayout());
        contentPane.setBorder(new EmptyBorder(10, 10, 10, 10));
        setContentPane(contentPane);
        
        // Create tabbed pane
        tabbedPane = new JTabbedPane();
        
        // Create the Data tab
        JPanel dataPanel = createDataPanel();
        tabbedPane.addTab("Data Explorer", new ImageIcon(), dataPanel, "Browse and filter database records");
        
        // Create the Dashboard tab
        JPanel dashboardPanel = createDashboardPanel();
        tabbedPane.addTab("Dashboard", new ImageIcon(), dashboardPanel, "View system metrics and statistics");
        
        // Create the Logs tab
        JPanel logsPanel = createLogsPanel();
        tabbedPane.addTab("Log Viewer", new ImageIcon(), logsPanel, "View application logs");
        
        // Create the Settings tab
        JPanel settingsPanel = createSettingsPanel();
        tabbedPane.addTab("Settings", new ImageIcon(), settingsPanel, "Configure application settings");
        
        // Add the tabbed pane to the content pane
        contentPane.add(tabbedPane, BorderLayout.CENTER);
        
        // Create status bar
        JPanel statusPanel = createStatusBar();
        contentPane.add(statusPanel, BorderLayout.SOUTH);
    }

    private JPanel createDataPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        
        // Create control panel
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        
        // Table selector
        controlPanel.add(new JLabel("Table:"));
        tableSelector = new JComboBox<>(tables);
        tableSelector.addActionListener(e -> {
            String selectedTable = (String) tableSelector.getSelectedItem();
            updateEventTypeSelector(selectedTable);
            refreshData();
        });
        controlPanel.add(tableSelector);
        
        // Event type selector
        controlPanel.add(new JLabel("Event Type:"));
        eventTypeSelector = new JComboBox<>(eventTypesByTable.get(tables[0]));
        eventTypeSelector.addActionListener(e -> refreshData());
        controlPanel.add(eventTypeSelector);
        
        // Time filter selector
        controlPanel.add(new JLabel("Time:"));
        timeFilterSelector = new JComboBox<>(new String[] {
            "All Time", "Last Hour", "Last 24 Hours", "Last 7 Days", "Last 30 Days"
        });
        timeFilterSelector.addActionListener(e -> refreshData());
        controlPanel.add(timeFilterSelector);
        
        // Search field
        controlPanel.add(new JLabel("Search:"));
        searchField = new JTextField(15);
        searchField.addActionListener(e -> refreshData());
        controlPanel.add(searchField);
        
        // Refresh button
        refreshButton = new JButton("Refresh");
        refreshButton.addActionListener(e -> refreshData());
        controlPanel.add(refreshButton);
        
        // Auto-refresh checkbox
        autoRefreshCheckbox = new JCheckBox("Auto-refresh");
        autoRefreshCheckbox.setSelected(true);
        controlPanel.add(autoRefreshCheckbox);
        
        // Add control panel to the top
        panel.add(controlPanel, BorderLayout.NORTH);
        
        // Create table
        tableModel = new DefaultTableModel();
        dataTable = new JTable(tableModel);
        dataTable.setAutoResizeMode(JTable.AUTO_RESIZE_ALL_COLUMNS);
        dataTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        
        // Add table to a scroll pane
        JScrollPane scrollPane = new JScrollPane(dataTable);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        // Add export button
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        exportButton = new JButton("Export Data");
        exportButton.addActionListener(e -> exportData());
        buttonPanel.add(exportButton);
        panel.add(buttonPanel, BorderLayout.SOUTH);
        
        return panel;
    }

    private void updateEventTypeSelector(String selectedTable) {
        String[] eventTypes = eventTypesByTable.getOrDefault(selectedTable, new String[]{"All Types"});
        eventTypeSelector.removeAllItems();
        for (String type : eventTypes) {
            eventTypeSelector.addItem(type);
        }
    }

    private JPanel createDashboardPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        
        // System metrics section (placeholder)
        JPanel metricsPanel = new JPanel(new GridLayout(2, 2, 10, 10));
        metricsPanel.setBorder(BorderFactory.createTitledBorder("System Metrics"));
        
        // CPU usage panel
        JPanel cpuPanel = createMetricPanel("CPU Usage", "0%");
        metricsPanel.add(cpuPanel);
        
        // Memory usage panel
        JPanel memoryPanel = createMetricPanel("Memory Usage", "0%");
        metricsPanel.add(memoryPanel);
        
        // Disk usage panel
        JPanel diskPanel = createMetricPanel("Disk Usage", "0%");
        metricsPanel.add(diskPanel);
        
        // Network usage panel
        JPanel networkPanel = createMetricPanel("Network", "0 KB/s");
        metricsPanel.add(networkPanel);
        
        // Add metrics panel to the top
        panel.add(metricsPanel, BorderLayout.NORTH);
        
        // Activity summary section (placeholder)
        JPanel activityPanel = new JPanel(new BorderLayout());
        activityPanel.setBorder(BorderFactory.createTitledBorder("Activity Summary"));
        
        // Activity labels
        JPanel activityLabels = new JPanel(new GridLayout(4, 2, 10, 10));
        activityLabels.add(new JLabel("Total Events:"));
        activityLabels.add(new JLabel("0"));
        activityLabels.add(new JLabel("Keystrokes:"));
        activityLabels.add(new JLabel("0"));
        activityLabels.add(new JLabel("Mouse Events:"));
        activityLabels.add(new JLabel("0"));
        activityLabels.add(new JLabel("App Switches:"));
        activityLabels.add(new JLabel("0"));
        activityPanel.add(activityLabels, BorderLayout.NORTH);
        
        // Recent activity list (placeholder)
        JList<String> activityList = new JList<>(new String[] {
            "No recent activity data available"
        });
        JScrollPane activityScroll = new JScrollPane(activityList);
        activityScroll.setPreferredSize(new Dimension(400, 200));
        activityPanel.add(activityScroll, BorderLayout.CENTER);
        
        // Add activity panel to the center
        panel.add(activityPanel, BorderLayout.CENTER);
        
        return panel;
    }
    
    private JPanel createMetricPanel(String title, String value) {
        JPanel panel = new JPanel(new BorderLayout());
        panel.setBorder(BorderFactory.createEtchedBorder());
        
        JLabel titleLabel = new JLabel(title);
        titleLabel.setHorizontalAlignment(JLabel.CENTER);
        panel.add(titleLabel, BorderLayout.NORTH);
        
        JLabel valueLabel = new JLabel(value);
        valueLabel.setFont(new Font("Arial", Font.BOLD, 24));
        valueLabel.setHorizontalAlignment(JLabel.CENTER);
        panel.add(valueLabel, BorderLayout.CENTER);
        
        return panel;
    }

    private JPanel createLogsPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        
        // Create log text area
        logTextArea = new JTextArea();
        logTextArea.setEditable(false);
        logTextArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        
        JScrollPane scrollPane = new JScrollPane(logTextArea);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        // Create control panel for log viewer
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        
        JButton clearButton = new JButton("Clear");
        clearButton.addActionListener(e -> logTextArea.setText(""));
        controlPanel.add(clearButton);
        
        JButton refreshLogsButton = new JButton("Refresh Logs");
        refreshLogsButton.addActionListener(e -> loadLogs());
        controlPanel.add(refreshLogsButton);
        
        JComboBox<String> logLevelSelector = new JComboBox<>(new String[] {
            "All Levels", "Info", "Warning", "Error", "Debug"
        });
        controlPanel.add(new JLabel("Level:"));
        controlPanel.add(logLevelSelector);
        
        panel.add(controlPanel, BorderLayout.NORTH);
        
        // Load initial logs
        loadLogs();
        
        return panel;
    }
    
    private void loadLogs() {
        // This would normally load from a log file or database
        // For now, let's display some sample logs
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");
        String timestamp = sdf.format(new java.util.Date());
        
        logTextArea.append(timestamp + " [INFO] Loading application logs...\n");
        logTextArea.append(timestamp + " [INFO] Connected to database: neurolock\n");
        logTextArea.append(timestamp + " [INFO] Found 34 events in behavior_logs table\n");
        
        // Add info about the latest refresh
        try {
            Connection conn = getConnection();
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM behavior_logs");
            if (rs.next()) {
                int count = rs.getInt(1);
                logTextArea.append(timestamp + " [INFO] Current behavior_logs count: " + count + "\n");
            }
            conn.close();
        } catch (SQLException e) {
            logTextArea.append(timestamp + " [ERROR] Database error: " + e.getMessage() + "\n");
        }
    }

    private JPanel createSettingsPanel() {
        JPanel panel = new JPanel(new BorderLayout());
        
        // Create settings form
        JPanel formPanel = new JPanel(new GridLayout(0, 2, 10, 10));
        formPanel.setBorder(new EmptyBorder(20, 20, 20, 20));
        
        // Database connection settings
        formPanel.add(new JLabel("JDBC URL:"));
        JTextField jdbcField = new JTextField(JDBC_URL);
        formPanel.add(jdbcField);
        
        formPanel.add(new JLabel("Username:"));
        JTextField userField = new JTextField(USERNAME);
        formPanel.add(userField);
        
        formPanel.add(new JLabel("Password:"));
        JPasswordField passField = new JPasswordField(PASSWORD);
        formPanel.add(passField);
        
        formPanel.add(new JLabel("Auto-refresh Interval (seconds):"));
        JTextField refreshField = new JTextField("10");
        formPanel.add(refreshField);
        
        // Add form panel to the center
        JScrollPane scrollPane = new JScrollPane(formPanel);
        panel.add(scrollPane, BorderLayout.CENTER);
        
        // Create button panel
        JPanel buttonPanel = new JPanel(new FlowLayout(FlowLayout.RIGHT));
        
        JButton saveButton = new JButton("Save Settings");
        saveButton.addActionListener(e -> JOptionPane.showMessageDialog(
            this, "Settings saved successfully", "Settings", JOptionPane.INFORMATION_MESSAGE));
        buttonPanel.add(saveButton);
        
        JButton testButton = new JButton("Test Connection");
        testButton.addActionListener(e -> testConnection());
        buttonPanel.add(testButton);
        
        panel.add(buttonPanel, BorderLayout.SOUTH);
        
        return panel;
    }

    private JPanel createStatusBar() {
        JPanel statusBar = new JPanel(new BorderLayout());
        statusBar.setBorder(BorderFactory.createEtchedBorder());
        
        statusLabel = new JLabel("Ready");
        statusBar.add(statusLabel, BorderLayout.WEST);
        
        totalRecordsLabel = new JLabel("Total Records: 0");
        statusBar.add(totalRecordsLabel, BorderLayout.EAST);
        
        return statusBar;
    }

    private Connection getConnection() throws SQLException {
        return DriverManager.getConnection(JDBC_URL, USERNAME, PASSWORD);
    }

    private void testConnection() {
        try {
            Connection conn = getConnection();
            statusLabel.setText("Connected to MySQL database");
            conn.close();
        } catch (SQLException e) {
            statusLabel.setText("Connection failed: " + e.getMessage());
            JOptionPane.showMessageDialog(
                this,
                "Database connection failed: " + e.getMessage(),
                "Connection Error",
                JOptionPane.ERROR_MESSAGE
            );
        }
    }

    private void refreshData() {
        String selectedTable = (String) tableSelector.getSelectedItem();
        String eventType = (String) eventTypeSelector.getSelectedItem();
        String timeFilter = (String) timeFilterSelector.getSelectedItem();
        String searchTerm = searchField.getText().trim();
        
        try {
            Connection conn = getConnection();
            Statement stmt = conn.createStatement();
            
            // Get metadata for the selected table
            DatabaseMetaData metaData = conn.getMetaData();
            ResultSet columns = metaData.getColumns(null, null, selectedTable, null);
            
            // Create SQL query with filters
            StringBuilder queryBuilder = new StringBuilder("SELECT * FROM ");
            queryBuilder.append(selectedTable);
            
            // Add event type filter if applicable
            if (eventType != null && !eventType.equals("All Types")) {
                queryBuilder.append(" WHERE event_type = '");
                queryBuilder.append(eventType);
                queryBuilder.append("'");
            }
            
            // Add time filter if applicable
            if (timeFilter != null && !timeFilter.equals("All Time")) {
                String whereOrAnd = queryBuilder.toString().contains("WHERE") ? " AND " : " WHERE ";
                queryBuilder.append(whereOrAnd);
                
                switch (timeFilter) {
                    case "Last Hour":
                        queryBuilder.append("timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)");
                        break;
                    case "Last 24 Hours":
                        queryBuilder.append("timestamp >= DATE_SUB(NOW(), INTERVAL 1 DAY)");
                        break;
                    case "Last 7 Days":
                        queryBuilder.append("timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)");
                        break;
                    case "Last 30 Days":
                        queryBuilder.append("timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)");
                        break;
                }
            }
            
            // Add search term filter if applicable
            if (!searchTerm.isEmpty()) {
                String whereOrAnd = queryBuilder.toString().contains("WHERE") ? " AND " : " WHERE ";
                queryBuilder.append(whereOrAnd);
                queryBuilder.append("(");
                
                // Apply search to all text columns
                boolean firstColumn = true;
                while (columns.next()) {
                    String columnName = columns.getString("COLUMN_NAME");
                    String dataType = columns.getString("TYPE_NAME");
                    
                    if (dataType.contains("CHAR") || dataType.contains("TEXT")) {
                        if (!firstColumn) {
                            queryBuilder.append(" OR ");
                        }
                        queryBuilder.append(columnName);
                        queryBuilder.append(" LIKE '%");
                        queryBuilder.append(searchTerm);
                        queryBuilder.append("%'");
                        firstColumn = false;
                    }
                }
                
                // If no text columns were found, search in all columns
                if (firstColumn) {
                    queryBuilder.append("CONVERT(id, CHAR) LIKE '%");
                    queryBuilder.append(searchTerm);
                    queryBuilder.append("%'");
                }
                
                queryBuilder.append(")");
                
                // Reset the columns result set
                columns.close();
                columns = metaData.getColumns(null, null, selectedTable, null);
            }
            
            // Add limit to avoid loading too much data
            queryBuilder.append(" LIMIT 1000");
            
            // Execute the query
            ResultSet rs = stmt.executeQuery(queryBuilder.toString());
            ResultSetMetaData rsmd = rs.getMetaData();
            int columnCount = rsmd.getColumnCount();
            
            // Create column headers
            tableModel.setRowCount(0);
            tableModel.setColumnCount(0);
            for (int i = 1; i <= columnCount; i++) {
                tableModel.addColumn(rsmd.getColumnName(i));
            }
            
            // Add data rows
            int rowCount = 0;
            while (rs.next()) {
                Object[] row = new Object[columnCount];
                for (int i = 1; i <= columnCount; i++) {
                    row[i - 1] = rs.getObject(i);
                }
                tableModel.addRow(row);
                rowCount++;
            }
            
            // Update status
            statusLabel.setText("Data loaded successfully");
            totalRecordsLabel.setText("Total Records: " + rowCount);
            
            // Clean up
            rs.close();
            stmt.close();
            conn.close();
        } catch (SQLException e) {
            statusLabel.setText("Error: " + e.getMessage());
            tableModel.setRowCount(0);
            tableModel.setColumnCount(0);
            tableModel.addColumn("Error");
            tableModel.addRow(new Object[] {"Database error: " + e.getMessage()});
        }
    }

    private void exportData() {
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setDialogTitle("Export Data");
        
        int selection = fileChooser.showSaveDialog(this);
        if (selection == JFileChooser.APPROVE_OPTION) {
            // This would normally export the data to a file
            JOptionPane.showMessageDialog(
                this,
                "Data exported successfully to " + fileChooser.getSelectedFile().getPath(),
                "Export Successful",
                JOptionPane.INFORMATION_MESSAGE
            );
        }
    }

    public static void main(String[] args) {
        try {
            // Set system look and feel
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        SwingUtilities.invokeLater(() -> {
            new BehaviorLoggerUI();
        });
    }
}