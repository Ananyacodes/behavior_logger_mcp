import java.awt.*;
import java.io.*;
import java.sql.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.Date;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;
import javax.swing.table.TableRowSorter;
// JFreeChart imports
import org.jfree.chart.ChartFactory;
import org.jfree.chart.ChartPanel;
import org.jfree.chart.JFreeChart;
import org.jfree.data.time.Second;
import org.jfree.data.time.TimeSeries;
import org.jfree.data.time.TimeSeriesCollection;
import java.time.LocalDate;
import java.sql.Types;

public class BehaviorLoggerUI extends JFrame {
    private JTabbedPane tabbedPane;
    private JTable dataTable;
    private DefaultTableModel tableModel;
    private JComboBox<String> tableSelector;
    private JButton refreshButton;
    private JButton filterButton;
    private JLabel statusLabel;
    private JButton startLoggingButton;
    private JButton stopLoggingButton;
    private JButton startProcessorButton;
    private JButton stopProcessorButton;
    private JButton startAnalysisButton;
    private JButton exportButton;
    private JTextArea logTextArea;
    private JPanel analyticsPanel;
    private JLabel mouseEventsCount;
    private JLabel keystrokeEventsCount;
    private JLabel applicationEventsCount;
    private JLabel totalEventsCount;
    private JProgressBar cpuUsageBar;
    private JProgressBar memoryUsageBar;
    // JFreeChart time series for events/sec
    private TimeSeries eventsPerSecSeries;
    private ChartPanel eventsChartPanel;
    // Internal processor scheduler
    private ScheduledExecutorService processorScheduler;
    private boolean processorRunning = false;
    // Analytics labels for anomalies
    private JLabel anomalyCountLabel;
    private JLabel avgConfidenceLabel;
    
    // Auto-refresh executor
    private ScheduledExecutorService scheduler;
    private boolean autoRefreshEnabled = false;
    private boolean realTimeMode = false;
    
    // Real-time monitoring
    private javax.swing.Timer realTimeTimer;
    private JLabel realTimeIndicator;
    private JProgressBar realTimeProgress;
    private long lastUpdateTime = 0;
    private int totalRowsLastCheck = 0;
    // Track last seen id per table for reliable real-time updates
    private Map<String, Long> lastSeenId = new HashMap<>();
    // Track last seen timestamp per table (when timestamp column exists)
    private Map<String, String> lastSeenTimestamp = new HashMap<>();
    // Track last known total row count for tables without id/timestamp
    private Map<String, Integer> lastRowCount = new HashMap<>();
    
    // Logger
    private PrintWriter logWriter;
    private SimpleDateFormat dateFormat = new SimpleDateFormat("yyyy-MM-dd HH:mm:ss");

    // Database connection info
    private String dbUrl = "jdbc:mysql://localhost:3306/neurolock";
    private String dbUser = "root";
    private String dbPassword = "JoeMama@25"; // Update with your actual password


    public BehaviorLoggerUI() {
        setTitle("Behavior Logger UI");
        setSize(1000, 600);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        // Initialize components
        initComponents();
        
        // Connect to database and load initial data
        loadTableNames();

        // Show the UI
        setVisible(true);
    }

    private void initComponents() {
        // Create main layout
        setLayout(new BorderLayout());
        
        // Setup logging
        try {
            File logDir = new File("logs");
            if (!logDir.exists()) {
                logDir.mkdir();
            }
            
            String logFileName = "logs/behavior_logger_ui_" + 
                new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date()) + ".log";
            logWriter = new PrintWriter(new FileWriter(logFileName));
            log("Application started");
        } catch (IOException e) {
            System.err.println("Failed to create log file: " + e.getMessage());
        }
        
        // Create toolbar panel
        JPanel toolbarPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        
        // Table selector
        JLabel tableLabel = new JLabel("Table:");
        tableSelector = new JComboBox<>();
        tableSelector.setPreferredSize(new Dimension(150, 25));
        tableSelector.addActionListener(e -> loadTableData((String)tableSelector.getSelectedItem()));
        
        // Refresh button
        refreshButton = new JButton("Refresh");
        refreshButton.addActionListener(e -> loadTableData((String)tableSelector.getSelectedItem()));
        
        // Filter button
        filterButton = new JButton("Filter");
        filterButton.addActionListener(e -> showFilterDialog());
        
    // Auto-refresh checkbox
    JCheckBox autoRefreshCheckbox = new JCheckBox("Real-time Streaming");
        
        // Export button
        exportButton = new JButton("Export");
        exportButton.addActionListener(e -> exportData());
        
        // Real-time indicator
        realTimeIndicator = new JLabel("o Offline");
        realTimeIndicator.setForeground(Color.RED);
        
        // Real-time progress bar
        realTimeProgress = new JProgressBar(0, 100);
        realTimeProgress.setStringPainted(true);
        realTimeProgress.setString("Ready");
        realTimeProgress.setPreferredSize(new Dimension(120, 20));
        
        // Live Log button
        JButton liveLogButton = new JButton("Live Log");
        liveLogButton.addActionListener(e -> showLiveLogWindow());
        
        // Store reference to update live indicator (this also toggles auto-refresh)
        // NOTE: avoid adding a second listener to prevent double-scheduling
        autoRefreshCheckbox.addActionListener(e -> {
            realTimeIndicator.setVisible(autoRefreshCheckbox.isSelected());
            if (autoRefreshCheckbox.isSelected()) {
                realTimeIndicator.setText("* LIVE");
                realTimeIndicator.setForeground(Color.GREEN);
            } else {
                realTimeIndicator.setText("o Offline");
                realTimeIndicator.setForeground(Color.RED);
            }
            toggleAutoRefresh(autoRefreshCheckbox.isSelected());
        });
        
        // Add components to toolbar
        toolbarPanel.add(tableLabel);
        toolbarPanel.add(tableSelector);
        toolbarPanel.add(refreshButton);
        toolbarPanel.add(filterButton);
        toolbarPanel.add(autoRefreshCheckbox);
        toolbarPanel.add(realTimeIndicator);
        toolbarPanel.add(realTimeProgress);
        toolbarPanel.add(exportButton);
    toolbarPanel.add(liveLogButton);
        
        // Create control panel
        JPanel controlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        startLoggingButton = new JButton("Start Logging");
        stopLoggingButton = new JButton("Stop Logging");
        stopLoggingButton.setEnabled(false);
    startProcessorButton = new JButton("Start Processor");
    stopProcessorButton = new JButton("Stop Processor");
    stopProcessorButton.setEnabled(false);
        
        startAnalysisButton = new JButton("Analyze Behavior");
        
        startLoggingButton.addActionListener(e -> startLogging());
        stopLoggingButton.addActionListener(e -> stopLogging());
        startAnalysisButton.addActionListener(e -> analyzeData());
    startProcessorButton.addActionListener(e -> startProcessor());
    stopProcessorButton.addActionListener(e -> stopProcessor());
        
        controlPanel.add(startLoggingButton);
        controlPanel.add(stopLoggingButton);
        controlPanel.add(startAnalysisButton);
    controlPanel.add(startProcessorButton);
    controlPanel.add(stopProcessorButton);
        
        JPanel topPanel = new JPanel(new BorderLayout());
        topPanel.add(toolbarPanel, BorderLayout.NORTH);
        topPanel.add(controlPanel, BorderLayout.SOUTH);
        
        // Create tabbed pane
        tabbedPane = new JTabbedPane();
        
        // Create data table tab
        tableModel = new DefaultTableModel();
        dataTable = new JTable(tableModel) {
            @Override
            public boolean isCellEditable(int row, int column) {
                return false; // Make table non-editable
            }
        };
        
        dataTable.setAutoResizeMode(JTable.AUTO_RESIZE_OFF);
        dataTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        
        // Enable sorting
        TableRowSorter<DefaultTableModel> sorter = new TableRowSorter<>(tableModel);
        dataTable.setRowSorter(sorter);
        
        JScrollPane tableScrollPane = new JScrollPane(dataTable);
        tableScrollPane.setHorizontalScrollBarPolicy(JScrollPane.HORIZONTAL_SCROLLBAR_AS_NEEDED);
        tableScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_AS_NEEDED);
        
        tabbedPane.addTab("Data View", tableScrollPane);
        
        // Create analytics tab
        analyticsPanel = new JPanel();
        analyticsPanel.setLayout(new BorderLayout());
        
        JPanel statsPanel = new JPanel(new GridLayout(0, 2, 10, 5));
        statsPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));
        
        // Summary statistics
        totalEventsCount = createStatsLabel(statsPanel, "Total Events:");
        mouseEventsCount = createStatsLabel(statsPanel, "Mouse Events:");
        keystrokeEventsCount = createStatsLabel(statsPanel, "Keystroke Events:");
        applicationEventsCount = createStatsLabel(statsPanel, "Application Events:");
    anomalyCountLabel = createStatsLabel(statsPanel, "Anomalies:");
    avgConfidenceLabel = createStatsLabel(statsPanel, "Avg Confidence:");
        
        JPanel resourcePanel = new JPanel(new GridLayout(0, 1, 10, 5));
        resourcePanel.setBorder(BorderFactory.createTitledBorder("System Resources"));
        
        JPanel cpuPanel = new JPanel(new BorderLayout(5, 0));
        cpuPanel.add(new JLabel("CPU:"), BorderLayout.WEST);
        cpuUsageBar = new JProgressBar(0, 100);
        cpuUsageBar.setStringPainted(true);
        cpuPanel.add(cpuUsageBar, BorderLayout.CENTER);
        
        JPanel memoryPanel = new JPanel(new BorderLayout(5, 0));
        memoryPanel.add(new JLabel("Memory:"), BorderLayout.WEST);
        memoryUsageBar = new JProgressBar(0, 100);
        memoryUsageBar.setStringPainted(true);
        memoryPanel.add(memoryUsageBar, BorderLayout.CENTER);
        
        resourcePanel.add(cpuPanel);
        resourcePanel.add(memoryPanel);
        
        JPanel northStatsPanel = new JPanel(new BorderLayout());
        northStatsPanel.add(statsPanel, BorderLayout.CENTER);
        northStatsPanel.add(resourcePanel, BorderLayout.SOUTH);
        
        analyticsPanel.add(northStatsPanel, BorderLayout.NORTH);
        
        // Add placeholder for chart
        JPanel chartPanel = new JPanel();
        chartPanel.setLayout(new BorderLayout());
        chartPanel.add(new JLabel("Event Activity over Time", JLabel.CENTER), BorderLayout.NORTH);
        chartPanel.add(new JLabel("(Chart will be generated when data is analyzed)", JLabel.CENTER), BorderLayout.CENTER);
        
        analyticsPanel.add(chartPanel, BorderLayout.CENTER);
        // Create real-time events/sec chart (JFreeChart)
        eventsPerSecSeries = new TimeSeries("Events/sec");
        TimeSeriesCollection dataset = new TimeSeriesCollection(eventsPerSecSeries);
        JFreeChart chart = ChartFactory.createTimeSeriesChart(
            "Events per Second",
            "Time",
            "Events/sec",
            dataset,
            false,
            true,
            false
        );

        eventsChartPanel = new ChartPanel(chart);
        eventsChartPanel.setPreferredSize(new Dimension(800, 200));
        analyticsPanel.add(eventsChartPanel, BorderLayout.SOUTH);
        
        tabbedPane.addTab("Analytics", analyticsPanel);
        
        // Create log tab with enhanced real-time view
        JPanel logPanel = new JPanel(new BorderLayout());
        
        // Log controls
        JPanel logControlPanel = new JPanel(new FlowLayout(FlowLayout.LEFT));
        JButton clearLogButton = new JButton("Clear Log");
        JCheckBox autoScrollCheckbox = new JCheckBox("Auto-scroll", true);
        JButton saveLogButton = new JButton("Save Log");
        
        clearLogButton.addActionListener(e -> {
            logTextArea.setText("");
            log("Log cleared by user");
        });
        
        saveLogButton.addActionListener(e -> exportLogToFile());
        
        logControlPanel.add(clearLogButton);
        logControlPanel.add(autoScrollCheckbox);
        logControlPanel.add(saveLogButton);
        
        logPanel.add(logControlPanel, BorderLayout.NORTH);
        
        logTextArea = new JTextArea();
        logTextArea.setEditable(false);
        logTextArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 11));
        logTextArea.setBackground(Color.BLACK);
        logTextArea.setForeground(Color.GREEN);
        
        JScrollPane logScrollPane = new JScrollPane(logTextArea);
        logScrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
        logPanel.add(logScrollPane, BorderLayout.CENTER);
        
        tabbedPane.addTab("Live Log", logPanel);
        
        // Create status bar
        statusLabel = new JLabel("Ready");
        
        // Add components to frame
        add(topPanel, BorderLayout.NORTH);
        add(tabbedPane, BorderLayout.CENTER);
        add(statusLabel, BorderLayout.SOUTH);
        
        // Initialize scheduler for auto-refresh
        scheduler = Executors.newScheduledThreadPool(1);
        // liveAll scheduler removed
    }
    
    private JLabel createStatsLabel(JPanel panel, String labelText) {
        JLabel dataLabel = new JLabel("0");
        dataLabel.setFont(new Font(dataLabel.getFont().getName(), Font.BOLD, 14));
        
        panel.add(new JLabel(labelText));
        panel.add(dataLabel);
        
        return dataLabel;
    }
    
    private void toggleAutoRefresh(boolean enabled) {
        autoRefreshEnabled = enabled;
        
        if (enabled) {
            // Schedule real-time refresh every 1 second for live data streaming
            scheduler.scheduleAtFixedRate(() -> {
                if (autoRefreshEnabled) {
                    SwingUtilities.invokeLater(() -> {
                        try {
                            // Get currently selected table
                            String selectedTable = (String)tableSelector.getSelectedItem();
                            if (selectedTable != null && !selectedTable.isEmpty()) {
                                loadTableDataRealTime(selectedTable);
                                updateAnalytics();
                                    updateChartSeries();
                                updateRealTimeStats();
                            }
                        } catch (Exception e) {
                            log("Error during real-time refresh: " + e.getMessage());
                        }
                    });
                }
            }, 0, 1, TimeUnit.SECONDS);
            
            log("Real-time streaming enabled - refreshing every second");
        } else {
            // Clear any scheduled tasks
            if (scheduler != null && !scheduler.isShutdown()) {
                scheduler.shutdownNow();
                scheduler = Executors.newScheduledThreadPool(1);
            }
            log("Real-time streaming disabled");
        }
    }

    // Update the events/sec time series (called on each refresh tick)
    private void updateChartSeries() {
        // Query recent events count efficiently
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            boolean hasTimestamp = hasColumn("behavior_logs", "timestamp");
            double eventsPerSec = 0.0;

            if (hasTimestamp) {
                try (PreparedStatement ps = conn.prepareStatement(
                        "SELECT COUNT(*) FROM behavior_logs WHERE timestamp >= (UNIX_TIMESTAMP(NOW(3)) - 1)")) {
                    ResultSet rs = ps.executeQuery();
                    if (rs.next()) {
                        eventsPerSec = rs.getInt(1);
                    }
                } catch (SQLException e) {
                    // fallback to id-delta
                    hasTimestamp = false;
                }
            }

            if (!hasTimestamp) {
                // use lastSeenId delta across all tables as approximation
                try (Statement stmt = conn.createStatement()) {
                    ResultSet rs = stmt.executeQuery("SELECT MAX(id) FROM behavior_logs");
                    long maxId = 0;
                    if (rs.next()) maxId = rs.getLong(1);
                    long prev = lastSeenId.getOrDefault("behavior_logs", 0L);
                    eventsPerSec = Math.max(0, maxId - prev);
                    lastSeenId.put("behavior_logs", maxId);
                }
            }

            final double eps = eventsPerSec;
            SwingUtilities.invokeLater(() -> {
                try {
                    eventsPerSecSeries.addOrUpdate(new Second(new Date()), eps);
                    // trim series to last 10 minutes (~600 points at 1s)
                    if (eventsPerSecSeries.getItemCount() > 600) {
                        eventsPerSecSeries.delete(0, eventsPerSecSeries.getItemCount() - 600 - 1);
                    }
                } catch (Exception ex) {
                    // ignore duplicate time item issues
                }
            });
        } catch (SQLException e) {
            log("Chart update failed: " + e.getMessage());
        }
    }
    
    private void log(String message) {
        String timestamp = dateFormat.format(new Date());
        String logMessage = "[" + timestamp + "] " + message;
        
        // Add to log text area (with error handling)
        try {
            if (logTextArea != null) {
                // Use invokeLater to ensure thread safety
                SwingUtilities.invokeLater(() -> {
                    try {
                        logTextArea.append(logMessage + "\n");
                        // Scroll to bottom
                        logTextArea.setCaretPosition(logTextArea.getDocument().getLength());
                    } catch (Exception e) {
                        System.err.println("Error updating log text area: " + e.getMessage());
                    }
                });
            }
        } catch (Exception e) {
            System.err.println("Error in log text area update: " + e.getMessage());
        }
        
        // Write to log file (with error handling)
        try {
            if (logWriter != null) {
                logWriter.println(logMessage);
                logWriter.flush();
            }
        } catch (Exception e) {
            System.err.println("Error writing to log file: " + e.getMessage());
        }
        
        // Also print to console for debugging
        System.out.println(logMessage);
    }
    
    private void loadTableNames() {
        try {
            tableSelector.removeAllItems();

            try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
                DatabaseMetaData metaData = conn.getMetaData();
                ResultSet tables = metaData.getTables(null, null, "%", new String[] {"TABLE"});
                
                // Only include relevant tables by skipping common unrelated tables
                // Add 'city' and 'behavior_events' to the blacklist to avoid showing or querying them in the UI
                Set<String> blacklist = new HashSet<>(Arrays.asList("actor", "address", "category", "city", "behavior_events"));
                while (tables.next()) {
                    String tableName = tables.getString("TABLE_NAME");
                    if (tableName == null) continue;
                    if (blacklist.contains(tableName.toLowerCase())) continue;

                    // Only include tables that can be live-updated: have rows now OR have an id/timestamp column
                    boolean hasId = false;
                    boolean hasTs = false;
                    try (ResultSet cols = metaData.getColumns(null, null, tableName, "%")) {
                        while (cols.next()) {
                            String col = cols.getString("COLUMN_NAME");
                            if (col == null) continue;
                            String lc = col.toLowerCase();
                            if (lc.equals("id")) hasId = true;
                            if (lc.equals("timestamp")) hasTs = true;
                        }
                    }

                    boolean hasRows = false;
                    try (Statement s = conn.createStatement()) {
                        try (ResultSet rs = s.executeQuery("SELECT COUNT(*) FROM " + tableName)) {
                            if (rs.next()) {
                                hasRows = rs.getInt(1) > 0;
                            }
                        }
                    } catch (SQLException e) {
                        // ignore tables we can't count
                    }

                    if (hasRows || hasId || hasTs) {
                        tableSelector.addItem(tableName);
                    } else {
                        // skip tables that have no rows and no id/timestamp - cannot stream live
                        log("Skipping non-live table: " + tableName);
                    }
                }

                // Do NOT inject virtual tables; only show actual DB tables
                
                statusLabel.setText("Connected to database successfully");
                
                // Select behavior_logs by default if it exists
                boolean behaviorLogsFound = false;
                for (int i = 0; i < tableSelector.getItemCount(); i++) {
                    if (tableSelector.getItemAt(i).equals("behavior_logs")) {
                        tableSelector.setSelectedIndex(i);
                        behaviorLogsFound = true;
                        break;
                    }
                }
                
                // If behavior_logs not found, select the first available table
                if (!behaviorLogsFound && tableSelector.getItemCount() > 0) {
                    tableSelector.setSelectedIndex(0);
                }
                
                // Load data for the selected table
                String selectedTable = (String)tableSelector.getSelectedItem();
                if (selectedTable != null) {
                    loadTableData(selectedTable);
                    updateAnalytics();
                }
            }
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, 
                "Error connecting to database: " + e.getMessage(), 
                "Database Error", 
                JOptionPane.ERROR_MESSAGE);
            statusLabel.setText("Error: " + e.getMessage());
        }
    }

    // startLiveAll/stopLiveAll removed — UI returns to simple behavior
    
    private void loadTableData(String tableName) {
        if (tableName == null || tableName.isEmpty()) {
            return;
        }

        // Defensive: explicitly skip blacklisted tables like 'city' or 'behavior_events' in case they appear
        if (tableName.equalsIgnoreCase("city") || tableName.equalsIgnoreCase("behavior_events")) {
            log("Skipping blacklisted table (load): " + tableName);
            statusLabel.setText("Skipping blacklisted table: " + tableName);
            return;
        }
        
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            // Clear existing data
            tableModel.setRowCount(0);
            tableModel.setColumnCount(0);
            
            // Get column names (use underlying table if virtual)
            boolean hasId = false;
            boolean hasTimestamp = false;
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery("SELECT * FROM " + getUnderlyingTable(tableName) + " LIMIT 0");
                ResultSetMetaData metaData = rs.getMetaData();

                int columnCount = metaData.getColumnCount();
                for (int i = 1; i <= columnCount; i++) {
                    String colName = metaData.getColumnName(i);
                    tableModel.addColumn(colName);
                    if (colName != null) {
                        String lc = colName.toLowerCase();
                        if (lc.equals("id")) hasId = true;
                        if (lc.equals("timestamp")) hasTimestamp = true;
                    }
                }
            }

            // Get data with appropriate ordering for each table
            String baseTable = getUnderlyingTable(tableName);
            String virtualWhere = getVirtualWhereClause(tableName);

            String orderClause = "";
            if (hasId) {
                orderClause = " ORDER BY id DESC";
            } else if (hasTimestamp) {
                orderClause = " ORDER BY timestamp DESC";
            }

            String query = "SELECT * FROM " + baseTable;
            if (virtualWhere != null && !virtualWhere.isEmpty()) query += " WHERE " + virtualWhere;
            if (!orderClause.isEmpty()) query += orderClause;
            query += " LIMIT 1000";
            
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery(query);
                ResultSetMetaData metaData = rs.getMetaData();
                int columnCount = metaData.getColumnCount();
                
                int rowCount = 0;
                while (rs.next()) {
                    Object[] row = new Object[columnCount];
                    for (int i = 1; i <= columnCount; i++) {
                        row[i-1] = rs.getObject(i);
                    }
                    tableModel.addRow(row);
                    rowCount++;
                }
                
                    // Count total rows (respect virtual where clause)
                    try (Statement countStmt = conn.createStatement()) {
                        String countQuery = "SELECT COUNT(*) FROM " + baseTable;
                        if (virtualWhere != null && !virtualWhere.isEmpty()) countQuery += " WHERE " + virtualWhere;
                        ResultSet countRs = countStmt.executeQuery(countQuery);
                        if (countRs.next()) {
                            int totalRows = countRs.getInt(1);
                            statusLabel.setText("Showing " + Math.min(totalRows, 1000) + 
                                " of " + totalRows + " records from " + tableName + " (last updated: " + 
                                new SimpleDateFormat("HH:mm:ss").format(new Date()) + ")");
                        }
                    }
                
                log("Loaded " + rowCount + " rows from " + tableName);

                // Update lastSeenId or lastSeenTimestamp for this table
                try {
                    if (hasId) {
                        try (Statement idStmt = conn.createStatement()) {
                            String maxIdQuery = "SELECT MAX(id) FROM " + baseTable;
                            if (virtualWhere != null && !virtualWhere.isEmpty()) maxIdQuery += " WHERE " + virtualWhere;
                            ResultSet idRs = idStmt.executeQuery(maxIdQuery);
                            if (idRs.next()) {
                                long maxId = idRs.getLong(1);
                                lastSeenId.put(tableName, maxId);
                            }
                        }
                    } else if (hasTimestamp) {
                        try (Statement tsStmt = conn.createStatement()) {
                            String maxTsQuery = "SELECT MAX(timestamp) FROM " + baseTable;
                            if (virtualWhere != null && !virtualWhere.isEmpty()) maxTsQuery += " WHERE " + virtualWhere;
                            ResultSet tsRs = tsStmt.executeQuery(maxTsQuery);
                            if (tsRs.next()) {
                                String maxTs = tsRs.getString(1);
                                lastSeenTimestamp.put(tableName, maxTs);
                            }
                        }
                    } else {
                        // Fallback: record total count
                        try (Statement countStmt = conn.createStatement()) {
                            ResultSet countRs = countStmt.executeQuery("SELECT COUNT(*) FROM " + baseTable);
                            if (countRs.next()) lastRowCount.put(tableName, countRs.getInt(1));
                        }
                    }
                } catch (SQLException ex) {
                    // ignore metadata update errors
                }
            }
            
            // Auto-resize columns
            for (int i = 0; i < dataTable.getColumnCount(); i++) {
                int width = 100; // Default width
                dataTable.getColumnModel().getColumn(i).setPreferredWidth(width);
            }
            
        } catch (SQLException e) {
            String errorMsg = "Error loading table data from " + tableName + ": " + e.getMessage();
            log(errorMsg);
            statusLabel.setText("Error: " + e.getMessage());
            
            // Show error in a non-blocking way
            SwingUtilities.invokeLater(() -> {
                JOptionPane.showMessageDialog(this, 
                    errorMsg, 
                    "Database Error", 
                    JOptionPane.ERROR_MESSAGE);
            });
        }
    }
    
    private void loadTableDataRealTime(String tableName) {
        if (tableName == null || tableName.isEmpty()) return;

        // Defensive: explicitly skip blacklisted tables like 'city' or 'behavior_events' during real-time polling
        if (tableName.equalsIgnoreCase("city") || tableName.equalsIgnoreCase("behavior_events")) {
            log("Skipping blacklisted table (real-time): " + tableName);
            return;
        }

        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            String baseTable = getUnderlyingTable(tableName);
            String virtualWhere = getVirtualWhereClause(tableName);

            boolean hasId = hasColumn(baseTable, "id");
            boolean hasTimestamp = hasColumn(baseTable, "timestamp");
            int currentRowCount = tableModel.getRowCount();

            // If table hasn't been initialized yet, populate columns and load initial data
            if (currentRowCount == 0) {
                tableModel.setRowCount(0);
                tableModel.setColumnCount(0);

                try (Statement stmt = conn.createStatement();
                     ResultSet rs = stmt.executeQuery("SELECT * FROM " + baseTable + " LIMIT 0")) {
                    ResultSetMetaData md = rs.getMetaData();
                    for (int i = 1; i <= md.getColumnCount(); i++) {
                        tableModel.addColumn(md.getColumnName(i));
                    }
                }

                loadTableData(tableName);
                return;
            }

            boolean useCountFallback = !hasId && !hasTimestamp;

            // Build incremental condition using lastSeenId or lastSeenTimestamp
            String incrementalWhere = "";
            if (hasId) {
                long lastId = lastSeenId.getOrDefault(tableName, 0L);
                if (lastId > 0) incrementalWhere = "id > " + lastId;
            } else if (hasTimestamp) {
                String lastTs = lastSeenTimestamp.get(tableName);
                if (lastTs != null && !lastTs.isEmpty()) incrementalWhere = "timestamp > '" + lastTs + "'";
            }

            String whereClause = "";
            if (virtualWhere != null && !virtualWhere.isEmpty()) {
                whereClause = virtualWhere;
                if (!incrementalWhere.isEmpty()) whereClause = "(" + virtualWhere + ") AND (" + incrementalWhere + ")";
            } else if (!incrementalWhere.isEmpty()) {
                whereClause = incrementalWhere;
            }

            String orderClause = hasId ? " ORDER BY id DESC" : (hasTimestamp ? " ORDER BY timestamp DESC" : "");
            String query = "SELECT * FROM " + baseTable + (whereClause.isEmpty() ? "" : " WHERE " + whereClause) + orderClause + " LIMIT 50";

            if (useCountFallback) {
                // Use count-based polling
                String countQuery = "SELECT COUNT(*) FROM " + baseTable + (virtualWhere != null && !virtualWhere.isEmpty() ? " WHERE " + virtualWhere : "");
                try (Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(countQuery)) {
                    int currentCount = 0;
                    if (rs.next()) currentCount = rs.getInt(1);
                    int prev = lastRowCount.getOrDefault(tableName, 0);
                    if (currentCount > prev) {
                        lastRowCount.put(tableName, currentCount);
                        loadTableData(tableName);
                    }
                }
            } else {
                try (Statement stmt = conn.createStatement(); ResultSet rs = stmt.executeQuery(query)) {
                    ResultSetMetaData md = rs.getMetaData();
                    int columnCount = md.getColumnCount();

                    java.util.List<Object[]> newRows = new java.util.ArrayList<>();
                    while (rs.next()) {
                        Object[] row = new Object[columnCount];
                        for (int i = 1; i <= columnCount; i++) row[i-1] = rs.getObject(i);
                        newRows.add(row);
                    }

                    // Insert new rows at the top (newest first)
                    for (int i = newRows.size() - 1; i >= 0; i--) tableModel.insertRow(0, newRows.get(i));

                    // Trim to keep reasonable history
                    while (tableModel.getRowCount() > 2000) tableModel.removeRow(tableModel.getRowCount() - 1);

                    if (!newRows.isEmpty()) {
                        // Update counts and status
                        String countQuery = "SELECT COUNT(*) FROM " + baseTable + (virtualWhere != null && !virtualWhere.isEmpty() ? " WHERE " + virtualWhere : "");
                        try (Statement countStmt = conn.createStatement(); ResultSet crs = countStmt.executeQuery(countQuery)) {
                            if (crs.next()) {
                                int totalRows = crs.getInt(1);
                                statusLabel.setText("LIVE: " + newRows.size() + " new rows | Showing " + Math.min(tableModel.getRowCount(), 2000) + " of " + totalRows + " records from " + tableName + " (updated: " + new SimpleDateFormat("HH:mm:ss").format(new Date()) + ")");
                            }
                        }

                        log("LIVE UPDATE: " + newRows.size() + " new rows from " + tableName);

                        // Update lastSeen values
                        try {
                            if (hasId) {
                                Object topRowIdObj = tableModel.getValueAt(0, getColumnIndexByName(baseTable, "id"));
                                if (topRowIdObj instanceof Number) lastSeenId.put(tableName, ((Number)topRowIdObj).longValue());
                            } else if (hasTimestamp) {
                                Object topTsObj = tableModel.getValueAt(0, getColumnIndexByName(baseTable, "timestamp"));
                                if (topTsObj != null) lastSeenTimestamp.put(tableName, topTsObj.toString());
                            }
                        } catch (Exception ex) {
                            // ignore
                        }

                        // Scroll to top
                        if (dataTable.getRowCount() > 0) dataTable.scrollRectToVisible(dataTable.getCellRect(0, 0, true));
                    }
                }
            }
        } catch (SQLException e) {
            String errorMsg = "Error loading real-time data from " + tableName + ": " + e.getMessage();
            log(errorMsg);
            loadTableData(tableName);
        }
    }
    
    private void updateRealTimeStats() {
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            // Get events in last 60 seconds for real-time rate
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery(
                    "SELECT COUNT(*) FROM behavior_logs WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 60 SECOND)");
                if (rs.next()) {
                    int recentEvents = rs.getInt(1);
                    double eventsPerSecond = recentEvents / 60.0;
                    
                    // Update title with live rate
                    String title = "Behavior Logger UI - LIVE (" + String.format("%.1f", eventsPerSecond) + " events/sec)";
                    this.setTitle(title);
                }
            }
            
            // Flash analytics numbers when they change
            updateAnalytics();
            
        } catch (SQLException e) {
            // Silently handle errors in real-time stats
        }
    }
    
    private void exportLogToFile() {
        try {
            JFileChooser fileChooser = new JFileChooser();
            fileChooser.setDialogTitle("Save Log File");
            fileChooser.setSelectedFile(new File("behavior_logger_" + 
                new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date()) + ".log"));
            
            if (fileChooser.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) {
                File file = fileChooser.getSelectedFile();
                
                try (PrintWriter writer = new PrintWriter(file)) {
                    writer.print(logTextArea.getText());
                    
                    JOptionPane.showMessageDialog(this,
                        "Log saved to: " + file.getAbsolutePath(),
                        "Log Exported",
                        JOptionPane.INFORMATION_MESSAGE);
                    
                    log("Log exported to: " + file.getAbsolutePath());
                }
            }
        } catch (Exception e) {
            JOptionPane.showMessageDialog(this,
                "Error saving log: " + e.getMessage(),
                "Export Error",
                JOptionPane.ERROR_MESSAGE);
        }
    }
    
    private void showFilterDialog() {
        String tableName = (String)tableSelector.getSelectedItem();
        if (tableName == null || tableName.isEmpty()) {
            JOptionPane.showMessageDialog(this, 
                "Please select a table first", 
                "Filter", 
                JOptionPane.WARNING_MESSAGE);
            return;
        }
        
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            // Get column names for the selected table
            ArrayList<String> columns = new ArrayList<>();
            
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery("SELECT * FROM " + tableName + " LIMIT 0");
                ResultSetMetaData metaData = rs.getMetaData();
                
                int columnCount = metaData.getColumnCount();
                for (int i = 1; i <= columnCount; i++) {
                    columns.add(metaData.getColumnName(i));
                }
            }
            
            // Create filter dialog
            JPanel filterPanel = new JPanel(new BorderLayout());
            
            JPanel fieldPanel = new JPanel(new GridLayout(0, 2, 5, 5));
            JComboBox<String> columnSelector = new JComboBox<>(columns.toArray(new String[0]));
            JTextField valueField = new JTextField(20);
            
            fieldPanel.add(new JLabel("Column:"));
            fieldPanel.add(columnSelector);
            fieldPanel.add(new JLabel("Value:"));
            fieldPanel.add(valueField);
            
            filterPanel.add(fieldPanel, BorderLayout.CENTER);
            
            int result = JOptionPane.showConfirmDialog(this, filterPanel, 
                "Filter Data", JOptionPane.OK_CANCEL_OPTION);
            
            if (result == JOptionPane.OK_OPTION) {
                String column = (String)columnSelector.getSelectedItem();
                String value = valueField.getText();
                
                if (column != null && !value.isEmpty()) {
                    applyFilter(tableName, column, value);
                }
            }
            
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, 
                "Error setting up filter: " + e.getMessage(), 
                "Database Error", 
                JOptionPane.ERROR_MESSAGE);
        }
    }
    
    private void applyFilter(String tableName, String column, String value) {
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            // Clear existing data
            tableModel.setRowCount(0);
            
            // Apply filter
            String query = "SELECT * FROM " + tableName + " WHERE " + column + " LIKE ? LIMIT 1000";
            
            try (PreparedStatement pstmt = conn.prepareStatement(query)) {
                pstmt.setString(1, "%" + value + "%");
                ResultSet rs = pstmt.executeQuery();
                
                ResultSetMetaData metaData = rs.getMetaData();
                int columnCount = metaData.getColumnCount();
                
                while (rs.next()) {
                    Object[] row = new Object[columnCount];
                    for (int i = 1; i <= columnCount; i++) {
                        row[i-1] = rs.getObject(i);
                    }
                    tableModel.addRow(row);
                }
                
                statusLabel.setText("Applied filter: " + column + " LIKE '%" + value + "%'");
            }
            
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, 
                "Error applying filter: " + e.getMessage(), 
                "Database Error", 
                JOptionPane.ERROR_MESSAGE);
            statusLabel.setText("Error: " + e.getMessage());
        }
    }
    
    private Process loggingProcess = null;
    private Process processorProcess = null;
    private Thread processorOutputReader = null;
    
    private void startLogging() {
        try {
            // Prefer venv python if available so the child process uses the project's virtualenv
            String venvPython = "C:\\Users\\Ananya\\behavior_logger\\.venv\\Scripts\\python.exe";
            java.io.File venvFile = new java.io.File(venvPython);
            java.util.List<String> cmd = new java.util.ArrayList<>();
            if (venvFile.exists() && venvFile.isFile()) {
                cmd.add(venvPython);
            } else {
                // fallback to system python
                cmd.add("python");
            }
            cmd.add("C:\\Users\\Ananya\\behavior_logger\\python\\behavior_log.py");
            ProcessBuilder pb = new ProcessBuilder(cmd);
            // Set working directory to project root so relative paths resolve correctly
            pb.directory(new java.io.File("C:\\Users\\Ananya\\behavior_logger"));
            pb.redirectErrorStream(true);
            
            loggingProcess = pb.start();
            
            // Read process output and append to UI log in background
            new Thread(() -> {
                try (BufferedReader reader = new BufferedReader(new InputStreamReader(loggingProcess.getInputStream()))) {
                    String line;
                    while ((line = reader.readLine()) != null) {
                        final String l = line;
                        SwingUtilities.invokeLater(() -> log("Logger: " + l));
                    }
                } catch (IOException e) {
                    SwingUtilities.invokeLater(() -> log("Error reading logger output: " + e.getMessage()));
                }
            }).start();
            
            startLoggingButton.setEnabled(false);
            stopLoggingButton.setEnabled(true);
            statusLabel.setText("Logging started. Data is being collected...");
            
            // Start a thread to wait for the process to exit
            new Thread(() -> {
                try {
                    loggingProcess.waitFor();
                    SwingUtilities.invokeLater(() -> {
                        startLoggingButton.setEnabled(true);
                        stopLoggingButton.setEnabled(false);
                        statusLabel.setText("Logging stopped.");
                        
                        // Refresh the data
                        loadTableData((String)tableSelector.getSelectedItem());
                    });
                } catch (InterruptedException e) {
                    log("Logger wait interrupted: " + e.getMessage());
                }
            }).start();
            
        } catch (Exception e) {
            JOptionPane.showMessageDialog(this, 
                "Error starting logging: " + e.getMessage(), 
                "Process Error", 
                JOptionPane.ERROR_MESSAGE);
            statusLabel.setText("Error: " + e.getMessage());
        }
    }
    
    private void stopLogging() {
        if (loggingProcess != null) {
            try {
                if (loggingProcess.isAlive()) loggingProcess.destroyForcibly();
            } catch (Exception ex) {
                try { loggingProcess.destroy(); } catch (Exception ex2) {}
            }
            loggingProcess = null;
            startLoggingButton.setEnabled(true);
            stopLoggingButton.setEnabled(false);
            statusLabel.setText("Logging stopped manually.");
            log("Behavior logging stopped manually");

            // After logging stops, process unprocessed logs in the UI so domain tables update
            new Thread(() -> {
                try {
                    log("Processing captured logs into domain tables...");
                    processLogsInUI();
                    log("Processing complete. Refreshing view...");
                    SwingUtilities.invokeLater(() -> loadTableData((String)tableSelector.getSelectedItem()));
                } catch (Exception ex) {
                    log("Error during in-UI processing: " + ex.getMessage());
                }
            }).start();
        }
    }

    /**
     * Process unprocessed rows from behavior_logs inside the UI process.
     * This is a best-effort processor: applies simple rules and inserts into domain tables.
     */
    private void processLogsInUI() {
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            conn.setAutoCommit(true);

            // Select any behavior_logs that haven't been processed yet. Using processed_at IS NULL
            // matches the Python realtime processor's logic and ensures rows are not skipped
            String selectSql = "SELECT id, timestamp, event_type, hashed_event, raw_data FROM behavior_logs WHERE processed_at IS NULL ORDER BY timestamp ASC LIMIT 1000";
            try (PreparedStatement sel = conn.prepareStatement(selectSql);
                 ResultSet rs = sel.executeQuery()) {

                int processed = 0;
                int anomalies = 0;
                double confidenceSum = 0.0;

                // Prepare common statements
                PreparedStatement updLog = conn.prepareStatement("UPDATE behavior_logs SET prediction = ?, processed_at = CURRENT_TIMESTAMP, hashed_event = NULL WHERE id = ?");
                PreparedStatement insKeystroke = null;
                PreparedStatement insMouse = null;
                PreparedStatement insApp = null;
                PreparedStatement insSystem = null;
                PreparedStatement insBehavior = null;
                PreparedStatement insAlert = null;

                // Prepare optional inserts matching actual schemas
                try { insKeystroke = conn.prepareStatement("INSERT INTO keystroke_events (event_id, key_name, key_type, interval_ms) VALUES (?, ?, ?, ?)"); } catch (SQLException e) { log("keystroke preparedstmt missing: " + e.getMessage()); }
                try { insMouse = conn.prepareStatement("INSERT INTO mouse_events (event_id, x_position, y_position, action, button, velocity, screen_region) VALUES (?, ?, ?, ?, ?, ?, ?)"); } catch (SQLException e) { log("mouse preparedstmt missing: " + e.getMessage()); }
                try { insApp = conn.prepareStatement("INSERT INTO application_events (event_id, app_name, window_title, process_id, cpu_percent, memory_percent, thread_count) VALUES (?, ?, ?, ?, ?, ?, ?)"); } catch (SQLException e) { log("app preparedstmt missing: " + e.getMessage()); }
                try { insSystem = conn.prepareStatement("INSERT INTO system_metrics (event_id, cpu_percent, memory_percent, memory_available_gb, disk_free_gb, network_bytes_sent, network_bytes_recv) VALUES (?, ?, ?, ?, ?, ?, ?)"); } catch (SQLException e) { log("system preparedstmt missing: " + e.getMessage()); }
                try { insBehavior = conn.prepareStatement("INSERT INTO behavior_events (timestamp, event_type, hashed_value, prediction, confidence) VALUES (?, ?, ?, ?, ?)"); } catch (SQLException e) { log("behavior_events preparedstmt missing: " + e.getMessage()); }
                try { insAlert = conn.prepareStatement("INSERT INTO alerts (timestamp, severity, message) VALUES (CURRENT_TIMESTAMP, ?, ?)"); } catch (SQLException e) { log("alerts preparedstmt missing: " + e.getMessage()); }

                while (rs.next()) {
                    long id = rs.getLong("id");
                    Timestamp tsObj = null;
                    try { tsObj = rs.getTimestamp("timestamp"); } catch (SQLException ex) { tsObj = null; }
                    String eventType = rs.getString("event_type");
                    String raw = rs.getString("raw_data");

                    int prediction = 0;
                    double confidence = 0.6;

                    try {
                        if (eventType != null && eventType.toUpperCase().contains("SYSTEM")) {
                            prediction = 1; confidence = 0.75;
                        } else if (raw != null && raw.toUpperCase().contains("CPU")) {
                            prediction = 1; confidence = 0.8;
                        }

                        // Update behavior_logs
                        try {
                            updLog.setInt(1, prediction);
                            updLog.setLong(2, id);
                            updLog.executeUpdate();
                        } catch (SQLException e) {
                            // log and continue
                            log("Failed to update behavior_logs id=" + id + ": " + e.getMessage());
                        }

                        // Domain inserts - map fields to actual schema columns
                        try {
                            if (eventType != null && eventType.toUpperCase().contains("KEY") && insKeystroke != null) {
                                // parsed JSON may contain key_name, type, interval_ms
                                String key_name = null;
                                String key_type = null;
                                Integer interval_ms = null;
                                try {
                                    if (raw != null) {
                                        // try simple parse for JSON-like strings
                                        if (raw.trim().startsWith("{")) {
                                            // attempt naive parse
                                            // leave robust parsing to Python processor; best-effort here
                                            int k = raw.indexOf("\"key\"");
                                            if (k >= 0) key_name = raw.substring(k, Math.min(raw.length(), k+50));
                                        } else {
                                            key_name = raw;
                                        }
                                    }
                                } catch (Exception ex) {}
                                insKeystroke.setLong(1, id);
                                // default key_name and key_type to safe values to satisfy NOT NULL constraints
                                String safeKeyName = key_name != null ? key_name : (raw != null ? raw : "UNKNOWN_KEY");
                                String safeKeyType = key_type != null ? key_type : "char";
                                insKeystroke.setString(2, safeKeyName);
                                insKeystroke.setString(3, safeKeyType);
                                if (interval_ms != null) insKeystroke.setInt(4, interval_ms); else insKeystroke.setNull(4, Types.INTEGER);
                                insKeystroke.executeUpdate();
                            }
                        } catch (SQLException e) { log("keystroke insert failed id=" + id + ": " + e.getMessage()); }

                        try {
                            if (eventType != null && eventType.toUpperCase().contains("MOUSE") && insMouse != null) {
                                Integer x = null; Integer y = null; Float velocity = null; String action = null; String button = null; String screen_region = null;
                                try {
                                    // best-effort extraction
                                    if (raw != null && raw.contains("x")) {
                                        x = null; // leave null unless parsed
                                    }
                                } catch (Exception ex) {}
                                insMouse.setLong(1, id);
                                // supply safe defaults for coordinates and other fields
                                if (x != null) insMouse.setInt(2, x); else insMouse.setInt(2, 0);
                                if (y != null) insMouse.setInt(3, y); else insMouse.setInt(3, 0);
                                insMouse.setString(4, action != null ? action : "click");
                                insMouse.setString(5, button != null ? button : "unknown");
                                if (velocity != null) insMouse.setFloat(6, velocity); else insMouse.setNull(6, Types.FLOAT);
                                insMouse.setString(7, screen_region);
                                insMouse.executeUpdate();
                            }
                        } catch (SQLException e) { log("mouse insert failed id=" + id + ": " + e.getMessage()); }

                        try {
                            if (eventType != null && eventType.toUpperCase().contains("APP") && insApp != null) {
                                String app_name = null; String window_title = null; Integer process_id = null; Double cpu = null; Double mem = null; Integer thread_count = null;
                                try {
                                    // best-effort extraction from raw
                                } catch (Exception ex) {}
                                insApp.setLong(1, id);
                                // provide defaults for app fields to avoid NOT NULL violations
                                insApp.setString(2, app_name != null ? app_name : "UnknownApp");
                                insApp.setString(3, window_title != null ? window_title : "");
                                if (process_id != null) insApp.setInt(4, process_id); else insApp.setNull(4, Types.INTEGER);
                                if (cpu != null) insApp.setDouble(5, cpu); else insApp.setDouble(5, 0.0);
                                if (mem != null) insApp.setDouble(6, mem); else insApp.setDouble(6, 0.0);
                                if (thread_count != null) insApp.setInt(7, thread_count); else insApp.setNull(7, Types.INTEGER);
                                insApp.executeUpdate();
                            }
                        } catch (SQLException e) { log("app insert failed id=" + id + ": " + e.getMessage()); }

                        try {
                            if (eventType != null && eventType.toUpperCase().contains("SYSTEM") && insSystem != null) {
                                Double cpu = null; Double mem = null; Double mem_avail = null; Double disk_free = null; Long net_sent = null; Long net_recv = null;
                                try {
                                    // attempt to parse raw JSON for metrics
                                    if (raw != null && raw.trim().startsWith("{")) {
                                        // leave parsing to Python processor; best-effort here
                                    }
                                } catch (Exception ex) {}
                                insSystem.setLong(1, id);
                                // default numeric metrics to zero to satisfy NOT NULL constraints
                                if (cpu != null) insSystem.setDouble(2, cpu); else insSystem.setDouble(2, 0.0);
                                if (mem != null) insSystem.setDouble(3, mem); else insSystem.setDouble(3, 0.0);
                                if (mem_avail != null) insSystem.setDouble(4, mem_avail); else insSystem.setNull(4, Types.DOUBLE);
                                if (disk_free != null) insSystem.setDouble(5, disk_free); else insSystem.setNull(5, Types.DOUBLE);
                                if (net_sent != null) insSystem.setLong(6, net_sent); else insSystem.setNull(6, Types.BIGINT);
                                if (net_recv != null) insSystem.setLong(7, net_recv); else insSystem.setNull(7, Types.BIGINT);
                                insSystem.executeUpdate();
                            }
                        } catch (SQLException e) { log("system insert failed id=" + id + ": " + e.getMessage()); }

                        // Alerts when anomaly
                        // Note: prepared statement is "INSERT INTO alerts (timestamp, severity, message) VALUES (CURRENT_TIMESTAMP, ?, ?)"
                        // so parameter 1 => severity, parameter 2 => message. Do not send the behavior_logs id as a param here.
                        if (prediction == 1 && insAlert != null) {
                            try {
                                String severity = "HIGH";
                                String message = "Anomaly detected (confidence=" + String.format("%.2f", confidence) + ")";
                                // Truncate message to avoid column size issues (defensive)
                                if (message.length() > 1024) message = message.substring(0, 1024);
                                insAlert.setString(1, severity);
                                insAlert.setString(2, message);
                                insAlert.executeUpdate();
                            } catch (SQLException e) { log("alert insert failed id=" + id + ": " + e.getMessage()); }
                        }

                            // Also insert a summary record into behavior_events so the UI can show general events
                            try {
                                if (insBehavior != null) {
                                    if (tsObj != null) insBehavior.setTimestamp(1, tsObj); else insBehavior.setTimestamp(1, new Timestamp(System.currentTimeMillis()));
                                    // Defensive: truncate event_type to 50 chars to match common schema limits
                                    String safeEventType = eventType == null ? null : (eventType.length() > 50 ? eventType.substring(0, 50) : eventType);
                                    insBehavior.setString(2, safeEventType);
                                    // Use the hashed value from the behavior_logs row if present
                                    try { insBehavior.setString(3, rs.getString("hashed_event")); } catch (Exception ex) { insBehavior.setNull(3, Types.VARCHAR); }
                                    insBehavior.setInt(4, prediction);
                                    insBehavior.setDouble(5, confidence);
                                    insBehavior.executeUpdate();
                                }
                            } catch (SQLException e) { log("behavior_events insert failed id=" + id + ": " + e.getMessage()); }

                        if (prediction == 1) anomalies++; else { }
                        confidenceSum += confidence;
                        processed++;

                    } catch (Exception e) {
                        log("Error processing id=" + id + ": " + e.getMessage());
                    }
                }

                // Update anomaly_stats (upsert)
                try {
                    LocalDate today = LocalDate.now();
                    PreparedStatement selStat = conn.prepareStatement("SELECT stat_id, total_events, avg_confidence FROM anomaly_stats WHERE stat_date = ?");
                    selStat.setDate(1, java.sql.Date.valueOf(today));
                    ResultSet srs = selStat.executeQuery();
                    int total = processed;
                    double avgConf = total > 0 ? confidenceSum / total : 0.0;
                    if (srs.next()) {
                        int statId = srs.getInt("stat_id");
                        int existingTotal = srs.getInt("total_events");
                        double existingConf = srs.getDouble("avg_confidence");
                        int newTotal = existingTotal + total;
                        double newAvg = (existingConf * existingTotal + avgConf * total) / (newTotal > 0 ? newTotal : 1);
                        PreparedStatement upd = conn.prepareStatement("UPDATE anomaly_stats SET total_events = total_events + ?, anomaly_events = anomaly_events + ?, normal_events = normal_events + ?, avg_confidence = ? WHERE stat_date = ?");
                        upd.setInt(1, total);
                        upd.setInt(2, anomalies);
                        upd.setInt(3, total - anomalies);
                        upd.setDouble(4, newAvg);
                        upd.setDate(5, java.sql.Date.valueOf(today));
                        upd.executeUpdate();
                    } else {
                        PreparedStatement ins = conn.prepareStatement("INSERT INTO anomaly_stats (stat_date, total_events, anomaly_events, normal_events, error_events, avg_confidence) VALUES (?, ?, ?, ?, ?, ?)");
                        ins.setDate(1, java.sql.Date.valueOf(today));
                        ins.setInt(2, total);
                        ins.setInt(3, anomalies);
                        ins.setInt(4, total - anomalies);
                        ins.setInt(5, 0);
                        ins.setDouble(6, avgConf);
                        ins.executeUpdate();
                    }
                } catch (SQLException e) {
                    log("Failed to update anomaly_stats: " + e.getMessage());
                }

                log("Processed " + processed + " rows (" + anomalies + " anomalies)");

                // close optional statements
                try { if (insKeystroke != null) insKeystroke.close(); } catch (Exception ex) {}
                try { if (insMouse != null) insMouse.close(); } catch (Exception ex) {}
                try { if (insApp != null) insApp.close(); } catch (Exception ex) {}
                try { if (insSystem != null) insSystem.close(); } catch (Exception ex) {}
                try { if (insAlert != null) insAlert.close(); } catch (Exception ex) {}
                try { if (updLog != null) updLog.close(); } catch (Exception ex) {}
            }
        } catch (SQLException e) {
            log("Processing DB error: " + e.getMessage());
        }
    }
    
    private void exportData() {
        String tableName = (String)tableSelector.getSelectedItem();
        if (tableName == null || tableName.isEmpty()) {
            JOptionPane.showMessageDialog(this, 
                "Please select a table first", 
                "Export", 
                JOptionPane.WARNING_MESSAGE);
            return;
        }
        
        // Choose file location
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setDialogTitle("Save CSV File");
        fileChooser.setSelectedFile(new File(tableName + "_export.csv"));
        
        if (fileChooser.showSaveDialog(this) != JFileChooser.APPROVE_OPTION) {
            return;
        }
        
        File file = fileChooser.getSelectedFile();
        
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword);
             PrintWriter writer = new PrintWriter(file)) {
            
            log("Exporting data from " + tableName + " to " + file.getAbsolutePath());
            
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery("SELECT * FROM " + tableName);
                ResultSetMetaData metaData = rs.getMetaData();
                int columnCount = metaData.getColumnCount();
                
                // Write header
                for (int i = 1; i <= columnCount; i++) {
                    if (i > 1) writer.print(",");
                    writer.print(escapeCSV(metaData.getColumnName(i)));
                }
                writer.println();
                
                // Write data
                int rowCount = 0;
                while (rs.next()) {
                    rowCount++;
                    for (int i = 1; i <= columnCount; i++) {
                        if (i > 1) writer.print(",");
                        String value = rs.getString(i);
                        writer.print(escapeCSV(value == null ? "" : value));
                    }
                    writer.println();
                }
                
                log("Exported " + rowCount + " rows to CSV file");
                JOptionPane.showMessageDialog(this, 
                    "Successfully exported " + rowCount + " rows to:\n" + file.getAbsolutePath(), 
                    "Export Complete", 
                    JOptionPane.INFORMATION_MESSAGE);
            }
            
        } catch (SQLException | IOException e) {
            log("Export failed: " + e.getMessage());
            JOptionPane.showMessageDialog(this, 
                "Error exporting data: " + e.getMessage(), 
                "Export Error", 
                JOptionPane.ERROR_MESSAGE);
        }
    }
    
    private String escapeCSV(String value) {
        if (value == null) return "";
        
        boolean needsQuotes = value.contains(",") || value.contains("\"") || value.contains("\n");
        if (!needsQuotes) return value;
        
        // Escape quotes by doubling them and wrap in quotes
        return "\"" + value.replace("\"", "\"\"") + "\"";
    }
    
    private void analyzeData() {
        log("Starting behavior analysis");
        statusLabel.setText("Analyzing behavior data...");
        
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            // Update analytics tab
            updateAnalytics();
            
            // Run real-time inference if available
            try {
                ProcessBuilder pb = new ProcessBuilder("python", 
                    "C:\\Users\\Ananya\\behavior_logger\\python\\realtime_infer.py");
                pb.redirectErrorStream(true);
                
                Process process = pb.start();
                
                // Read output in a separate thread
                new Thread(() -> {
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(process.getInputStream()))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            final String logLine = line;
                            SwingUtilities.invokeLater(() -> log("Analyzer: " + logLine));
                        }
                    } catch (IOException e) {
                        SwingUtilities.invokeLater(() -> log("Error reading analyzer output: " + e.getMessage()));
                    }
                }).start();
                
                // Wait for a bit to allow process to start
                Thread.sleep(2000);
                
                JOptionPane.showMessageDialog(this,
                    "Behavior analysis started in background.\n" +
                    "Check the Log tab for results.",
                    "Analysis Started",
                    JOptionPane.INFORMATION_MESSAGE);
                
            } catch (IOException | InterruptedException e) {
                log("Failed to start analyzer: " + e.getMessage());
                JOptionPane.showMessageDialog(this,
                    "Failed to start analyzer: " + e.getMessage(),
                    "Analysis Error",
                    JOptionPane.ERROR_MESSAGE);
            }
            
        } catch (SQLException e) {
            log("Database error during analysis: " + e.getMessage());
            JOptionPane.showMessageDialog(this,
                "Database error during analysis: " + e.getMessage(),
                "Analysis Error",
                JOptionPane.ERROR_MESSAGE);
        }
        
        statusLabel.setText("Analysis complete. Check the Log tab for results.");
    }

    private void startProcessor() {
        // Start internal scheduled processor to run processLogsInUI every 5 seconds
        if (processorRunning) return;
        processorScheduler = Executors.newSingleThreadScheduledExecutor();
        processorScheduler.scheduleAtFixedRate(() -> {
            try {
                processLogsInUI();
            } catch (Exception e) {
                log("Processor error: " + e.getMessage());
            }
        }, 0, 5, TimeUnit.SECONDS);
        processorRunning = true;
        startProcessorButton.setEnabled(false);
        stopProcessorButton.setEnabled(true);
        statusLabel.setText("Internal processor started (every 5s)");
    }

    private void stopProcessor() {
        if (!processorRunning) return;
        try {
            if (processorScheduler != null && !processorScheduler.isShutdown()) {
                processorScheduler.shutdownNow();
            }
        } catch (Exception e) {
            log("Error stopping processor: " + e.getMessage());
        }
        processorRunning = false;
        startProcessorButton.setEnabled(true);
        stopProcessorButton.setEnabled(false);
        statusLabel.setText("Internal processor stopped");
        log("Internal processor stopped");
        // Refresh view
        SwingUtilities.invokeLater(() -> loadTableData((String)tableSelector.getSelectedItem()));
    }
    
    private void updateAnalytics() {
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            // Get total events count
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery(
                    "SELECT COUNT(*) FROM behavior_logs");
                if (rs.next()) {
                    int count = rs.getInt(1);
                    totalEventsCount.setText(String.valueOf(count));
                }
            }
            
            // Get count by event type
            try (Statement stmt = conn.createStatement()) {
                ResultSet rs = stmt.executeQuery(
                    "SELECT event_type, COUNT(*) FROM behavior_logs GROUP BY event_type");

                
                
                // Reset counts
                mouseEventsCount.setText("0");
                keystrokeEventsCount.setText("0");
                applicationEventsCount.setText("0");
                
                while (rs.next()) {
                    String eventType = rs.getString(1);
                    int count = rs.getInt(2);
                    
                    if (eventType.contains("MOUSE")) {
                        mouseEventsCount.setText(String.valueOf(count));
                    } else if (eventType.contains("KEY") || eventType.contains("KEYSTROKE")) {
                        keystrokeEventsCount.setText(String.valueOf(count));
                    } else if (eventType.contains("APP")) {
                        applicationEventsCount.setText(String.valueOf(count));
                    }
                }
            }
            
            // Simulate system metrics (in a real app, you'd get these from the OS)
            Random rand = new Random();
            cpuUsageBar.setValue(30 + rand.nextInt(40)); // 30-70%
            memoryUsageBar.setValue(40 + rand.nextInt(30)); // 40-70%
            
            log("Analytics updated");
            
        } catch (SQLException e) {
            log("Error updating analytics: " + e.getMessage());
        }
    }
    
    // Map logical/virtual tables to the underlying physical table
    private String getUnderlyingTable(String tableName) {
        // No virtual-table mapping any more. Return the table name as-is.
        return tableName == null ? "" : tableName;
    }

    // Provide WHERE clauses for virtual table filters over behavior_logs
    private String getVirtualWhereClause(String tableName) {
        // No virtual filters when using real DB tables
        return "";
    }

    // Return the index of a column in the current table model by column name
    private int getColumnIndexByName(String tableName, String columnName) {
        if (columnName == null) return -1;
        // Prefer to check the current tableModel first
        for (int i = 0; i < tableModel.getColumnCount(); i++) {
            String col = tableModel.getColumnName(i);
            if (col != null && col.equalsIgnoreCase(columnName)) return i;
        }

        // If tableModel isn't populated yet, query DB metadata
        if (tableName != null && !tableName.isEmpty()) {
            try (Connection c = DriverManager.getConnection(dbUrl, dbUser, dbPassword);
                 Statement s = c.createStatement();
                 ResultSet rs = s.executeQuery("SELECT * FROM " + tableName + " LIMIT 0")) {
                ResultSetMetaData md = rs.getMetaData();
                for (int i = 1; i <= md.getColumnCount(); i++) {
                    if (md.getColumnName(i).equalsIgnoreCase(columnName)) return i - 1; // convert to 0-based
                }
            } catch (SQLException e) {
                // ignore
            }
        }
        return -1;
    }

    // Check whether given table has a specific column using database metadata
    private boolean hasColumn(String tableName, String columnName) {
        if (tableName == null || columnName == null) return false;
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            ResultSet rs = conn.getMetaData().getColumns(null, null, tableName, columnName);
            return rs.next();
        } catch (SQLException e) {
            return false;
        }
    }

    private void showLiveLogWindow() {
        JFrame logWindow = new JFrame("Live Log Viewer");
        logWindow.setSize(800, 600);
        logWindow.setLocationRelativeTo(this);
        
        JTextArea liveLogArea = new JTextArea();
        liveLogArea.setEditable(false);
        liveLogArea.setFont(new Font(Font.MONOSPACED, Font.PLAIN, 12));
        liveLogArea.setBackground(Color.BLACK);
        liveLogArea.setForeground(Color.GREEN);
        
        JScrollPane scrollPane = new JScrollPane(liveLogArea);
        scrollPane.setVerticalScrollBarPolicy(JScrollPane.VERTICAL_SCROLLBAR_ALWAYS);
        
        // Control panel for the live log
        JPanel controlPanel = new JPanel(new FlowLayout());
        JButton clearLogButton = new JButton("Clear");
        JButton exportLogButton = new JButton("Export Log");
        JCheckBox autoScrollBox = new JCheckBox("Auto-scroll", true);
        
        clearLogButton.addActionListener(e -> liveLogArea.setText(""));
        exportLogButton.addActionListener(e -> exportLogToFile(liveLogArea.getText()));
        
        controlPanel.add(clearLogButton);
        controlPanel.add(exportLogButton);
        controlPanel.add(autoScrollBox);
        
        logWindow.add(scrollPane, BorderLayout.CENTER);
        logWindow.add(controlPanel, BorderLayout.SOUTH);
        
        // Start real-time log monitoring
        javax.swing.Timer logTimer = new javax.swing.Timer(1000, e -> {
            try {
                // Monitor database activity
                updateLiveLog(liveLogArea, autoScrollBox.isSelected());
            } catch (Exception ex) {
                liveLogArea.append("[ERROR] " + ex.getMessage() + "\n");
            }
        });
        
        logWindow.addWindowListener(new java.awt.event.WindowAdapter() {
            @Override
            public void windowClosing(java.awt.event.WindowEvent windowEvent) {
                logTimer.stop();
            }
        });
        
        logTimer.start();
        logWindow.setVisible(true);
    }
    
    private void updateLiveLog(JTextArea logArea, boolean autoScroll) {
        try (Connection conn = DriverManager.getConnection(dbUrl, dbUser, dbPassword)) {
            // Get recent activity from behavior_logs
            // The behavior_logs table stores event payload in raw_data (JSON). Use event_type and timestamp.
            String query = "SELECT timestamp, event_type, raw_data FROM behavior_logs " +
                          "WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 10 SECOND) " +
                          "ORDER BY timestamp DESC LIMIT 20";
            
            try (Statement stmt = conn.createStatement();
                 ResultSet rs = stmt.executeQuery(query)) {
                
                StringBuilder newEntries = new StringBuilder();
                int entryCount = 0;
                
                while (rs.next()) {
                    Timestamp timestamp = rs.getTimestamp("timestamp");
                    String eventType = rs.getString("event_type");
                    String rawData = rs.getString("raw_data");

                    String timeStr = new SimpleDateFormat("HH:mm:ss.SSS").format(timestamp);
                    String preview = rawData != null ? rawData.substring(0, Math.min(120, rawData.length())) : "";
                    newEntries.append(String.format("[%s] %s | %s\n", timeStr, eventType, preview));
                    entryCount++;
                }
                
                if (entryCount > 0) {
                    String currentText = logArea.getText();
                    // Keep only last 500 lines to prevent memory issues
                    String[] lines = currentText.split("\n");
                    if (lines.length > 500) {
                        StringBuilder trimmed = new StringBuilder();
                        for (int i = lines.length - 400; i < lines.length; i++) {
                            trimmed.append(lines[i]).append("\n");
                        }
                        currentText = trimmed.toString();
                    }
                    
                    logArea.setText(newEntries.toString() + currentText);
                    
                    if (autoScroll) {
                        logArea.setCaretPosition(0);
                    }
                }
            }
        } catch (SQLException e) {
            logArea.append("[SQL ERROR] " + e.getMessage() + "\n");
        }
    }
    
    private void exportLogToFile(String logContent) {
        JFileChooser fileChooser = new JFileChooser();
        fileChooser.setSelectedFile(new File("live_log_" + 
            new SimpleDateFormat("yyyyMMdd_HHmmss").format(new Date()) + ".txt"));
        
        if (fileChooser.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) {
            try (FileWriter writer = new FileWriter(fileChooser.getSelectedFile())) {
                writer.write(logContent);
                JOptionPane.showMessageDialog(this, "Log exported successfully!");
            } catch (IOException e) {
                JOptionPane.showMessageDialog(this, "Error exporting log: " + e.getMessage());
            }
        }
    }
    
    @Override
    public void dispose() {
        // Clean up resources
        if (scheduler != null && !scheduler.isShutdown()) {
            scheduler.shutdownNow();
        }
        
        // Stop any running process
        if (loggingProcess != null && loggingProcess.isAlive()) {
            loggingProcess.destroy();
        }
        
        if (logWriter != null) {
            log("Application shutting down");
            logWriter.close();
        }
        
        super.dispose();
    }

    public static void main(String[] args) {
        // Set look and feel
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception e) {
            e.printStackTrace();
        }
        
        // Start the UI
        SwingUtilities.invokeLater(() -> new BehaviorLoggerUI());
    }
}