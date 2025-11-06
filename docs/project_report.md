# PROJECT REPORT

**Project:** Behavior Logger — Real-time Telemetry and Anomaly Detection  
**Submitted by:** STUDENT NAME [REG NO]  
**Student 2:** STUDENT2 NAME [REG NO]  
**Guide:** GUIDE NAME (Designation, Department)  
Department of Computing Technologies  
College of Engineering and Technology  
SRM Institute of Science and Technology, Kattankulathur — 603203  
November 2025

---

## CERTIFICATE

This is to certify that the project titled “Behavior Logger — Real-time Telemetry and Anomaly Detection” carried out by STUDENT NAME [REG NO], STUDENT2 NAME [REG NO] is bonafide work carried out under my supervision.

Supervisor: _______________________  
Designation: ______________________  
Date: ____________________________

---

## ABSTRACT

Aim: Build a lightweight, reliable single-host pipeline for near-real-time workstation telemetry and anomaly detection.

Method: A Python collector captures keystrokes, mouse activity, active-application context, and system metrics, hashing payloads with a Rust hasher (with a Python SHA‑256 fallback) and persisting events to MySQL via JDBC (JPype/jaydebeapi) or mysql-connector-python as a fallback. A Java Swing UI (with JFreeChart) provides ~1 s live refresh, time-series charts, and a scheduled 5 s in-UI processor that classifies events, normalizes domain tables, and raises alerts. The project favors in-process JDBC for low-latency reads/writes and hybrid Rust/Python hashing for performance and portability.

Main result: The system achieves low-latency local ingestion, consistent domain-table population, and deterministic rule-based alerting. The UI provides live charts and a simple CSV exporter for downstream analysis.

Keywords: telemetry, keystroke, mouse, JDBC, MySQL, Rust, SHA-256, anomaly detection, Java Swing, real-time.

---

## TABLE OF CONTENTS

1. INTRODUCTION .............................................. 1  
1.1 General (Introduction to Project) ........................ 1  
1.2 Motivation .............................................. 2  
1.3 Objectives .............................................. 2  
1.4 Scope .................................................. 3  
1.5 Sustainable Development Goals .......................... 4

2. SYSTEM REQUIREMENTS ...................................... 5  
2.1 Hardware requirement .................................... 5  
2.2 Software requirement .................................... 6

3. SYSTEM DESIGN ............................................. 7  
3.1 System architecture diagram ............................. 7  
3.2 Use case diagram ....................................... 8  
3.3 Class diagram .......................................... 9

4. MODULE DESCRIPTION ...................................... 11  
4.1 Module 1 — Event Collector (Python) .................... 11  
4.2 Module 2 — Java UI & Processor ........................ 12  
4.3 Module 3 — Database Schema & Storage ................... 12  
4.4 Module 4 — Optional Processors & Utilities ............. 13

5. IMPLEMENTATION & TESTING ............................... 14

6. RESULTS & DISCUSSION ................................... 15

REFERENCES ................................................. 18

APPENDIX A — CODING ....................................... 19

---

# 1 INTRODUCTION

## 1.1 General (Introduction to Project)

Modern endpoint observability requires a system that can capture fine-grained user and system activity with low overhead and make useful signals available to analysts in near real time. This project delivers a single-host pipeline that records keystrokes, mouse activity, active window/application metadata, and lightweight system metrics (CPU, memory) into a structured MySQL schema for downstream analytics and alerting. The solution uses a small Python collector to gather events and a Java Swing UI to visualize and process these events; a Rust hasher provides performant payload hashing.

## 1.2 Motivation

- Provide near-real-time visibility into workstation behavior for rapid detection of anomalies and suspicious patterns.
- Enable a minimal-deployment, single-host agent useful for labs, small enterprises, or edge monitoring use cases.
- Combine high-performance hashing (Rust) with broad portability and library support in Python and Java.

## 1.3 Objectives

- Continuous capture of keystrokes, mouse events, application context, and system metrics while logging is enabled.
- Persist events to MySQL with a JDBC-first strategy and a pure-Python fallback connector.
- Provide a Java Swing UI with ~1 Hz refresh and time-series charting of event rates and resource usage.
- Process raw `behavior_logs` into domain tables every 5 s and raise rule-based alerts.
- Make code and configuration easy to read and deploy; include a formatted Appendix with code snippets and pointers to full source files.

## 1.4 Scope

- Single Windows host, local MySQL instance; not designed for multi-host ingestion.
- Heuristic rule-based detection (no large ML models bundled).
- Privacy-conscious: payloads are hashed before persistent storage by default.

## 1.5 Sustainable Development Goals mapping

- SDG 9 (Industry, Innovation and Infrastructure): improves monitoring infra for resilience.
- SDG 16 (Peace, Justice and Strong Institutions): supports accountable capturing and logging for investigations.

---

# 2 SYSTEM REQUIREMENTS

## Summary

Minimum: Windows 10/11 (64-bit), Python 3.10+, JDK 11+, MySQL 8.x, 4 GB RAM, 10 GB free disk. Recommended: 8 GB RAM, SSD, JDK 17, Python 3.11, 1+ GB DB free space.

## 2.1 Hardware requirement

Minimum:
- CPU: Dual-core 2 GHz
- RAM: 4 GB
- Disk: 10 GB free
Recommended:
- CPU: Quad-core 2.5 GHz
- RAM: 8+ GB
- Disk: SSD 20+ GB free

## 2.2 Software requirement

- OS: Windows 10/11 (64-bit)
- Java: JDK 11 or newer (JDK 17 recommended)
- MySQL Server 8.x (local)
- Python 3.10+ in virtualenv; packages:
  - psutil, pynput, mysql-connector-python, jpype1, jaydebeapi, pywin32
- MySQL Connector/J jar(s) placed in `java/lib`
- JFreeChart jar in `java/lib`
- Rust toolchain (optional) to build `rust_hasher` binary

---

# 3 SYSTEM DESIGN

## 3.1 System architecture diagram

Single-host, three-layer design: Data Collector (Python) → Storage (MySQL) ←→ Presentation/Processor (Java UI). Collector hashes payloads via Rust hasher and writes to MySQL via JDBC (or python connector fallback). UI reads via JDBC and processes logs every 5 s to normalize domain tables and create alerts.

ASCII diagram:

```
+----------------+         JDBC         +--------------------+
| Java Swing UI  | <------------------> |    MySQL Server    |
|  - Charts      |                      |  Tables:           |
|  - Processor   |                      |  behavior_logs,    |
|  - Export CSV  |                      |  behavior_events,  |
+-------^--------+                      |  keystroke_events, |
        |                               |  mouse_events, ... |
        | spawn                          +--------------------+
        |
+-------+--------+
| Python Logger  |
| - keystrokes   |
| - mouse events |
| - app context  |
| - system mets  |
+-------+--------+
        |
        v
[Rust Hasher -> fallback SHA256]
        |
      MySQL (via JDBC or mysql-connector)
```

## 3.2 Use case diagram (text)

- Actor: User — start/stop logging, view live data, export CSV, review alerts.
- Actor: Python Logger — capture and persist events.
- Actor: UI Processor — normalize logs into domain tables and raise alerts.

## 3.3 Class diagram (textual)

Key classes / modules:
- Java
  - `BehaviorLoggerUI` — main window, spawn logger, live updates, `processLogsInUI()`.
  - `BehaviorLoggerUIMain` — launcher and environment checks.
  - `DBUtils` — helper JDBC functions (recommended).
- Python
  - `behavior_log.py` — capture and insert events, hashing.
  - `realtime_processor.py` — optional external normalization.
- Rust
  - `rust_hasher` — binary to compute SHA-256 or optimized hash.

---

# 4 MODULE DESCRIPTION

## 4.1 Module 1 — Event Collector (Python)

Purpose: Capture keyboard, mouse, application, and system metrics; hash payloads; insert into `behavior_logs`.

Key functions:
- `log_event(event_type, data)` — hash payload; insert via JDBC or mysql-connector.
- `setup_database()` — create `behavior_logs` if missing.

Inputs: keyboard/mouse hooks, active window/process info, psutil metrics.  
Dependencies: Rust hasher binary (optional), JPype/jaydebeapi (optional), mysql-connector-python fallback.

Design notes:
- Keep payloads small; use JSON for `raw_data` column if DB supports it.
- Hash before storing to reduce privacy risk; configure raw storage via a boolean flag.

## 4.2 Module 2 — Java UI & Processor

Purpose: Display live data, spawn Python logger, run in-UI processor to create domain tables and alerts.

Key functions:
- `startLogging()` — launch the Python logger from the project venv and set working dir.
- `processLogsInUI()` — read unprocessed rows, populate `behavior_events` and child tables (`keystroke_events`, `mouse_events`, `application_events`, `system_metrics`), insert alerts, and mark rows processed.
- `updateAnalytics()` — update charts and counters (executed at ~1 Hz).

Implementation notes:
- Use prepared statements to avoid SQL injection and improve performance.
- When inserting parent/child rows obey FK: insert `behavior_events` first and obtain generated `event_id` to use in child inserts.

## 4.3 Module 3 — Database Schema & Storage (MySQL)

Core tables:
- `behavior_logs` — raw events with `id`, `timestamp`, `event_type`, `hashed_event`, `raw_data`, `prediction`, `processed_at`, `created_at`.
- `behavior_events` — normalized event summaries (parent table).
- Domain detail tables: `keystroke_events`, `mouse_events`, `application_events`, `system_metrics`.
- `alerts` — store heuristic or analytic alerts (severity, message, event_id).

Indexing:
- Index `id`, `timestamp`, and `processed_at` for fast selection of unprocessed rows.

## 4.4 Module 4 — Optional Processors & Utilities

- `realtime_processor.py` — external normalization service (optional) if you want processing outside the UI.
- Utility scripts: `inspect_tables.py`, `show_counts.py` for quick DB diagnostics.

---

# 5 IMPLEMENTATION & TESTING

## Implementation notes

- Python collector: run inside `.venv/` to ensure pinned dependencies. The UI spawns `.venv\Scripts\python.exe`.
- JDBC vs connector: prefer JDBC via JPype/jaydebeapi for reliability; fall back to `mysql.connector`.
- Hashing: prefer `rust_hasher` binary; fall back to Python builtin `hashlib.sha256`.

## Testing approach

- Unit tests: small Python tests for `hash_with_rust()` fallback and DB insert functions.
- Integration tests: run the UI locally with MySQL, start logging, verify `behavior_logs` rows appear and `processLogsInUI()` normalizes them into domain tables.
- Edge cases: long `event_type` strings (truncate to 50 chars), NULL handling for optional fields, missing rust binary, missing JDBC.

---

# 6 RESULTS & DISCUSSION

- Live refresh: UI updates analytics every ~1 s; bulk-loads show newest-1000 rows by default.
- Processing: 5 s scheduled processor normalizes rows; ensure parent `behavior_events` insertion before child tables — otherwise FK errors occur.
- Observed issues & mitigations:
  - Module import errors for the logger when UI spawned system Python — fix: spawn project venv python.
  - Data truncation — fix: defensive truncation or adjust column sizes.
  - FK violations — fix: insert parent summary first and use returned generated keys for children.

---

# 7 SECURITY, PRIVACY & ETHICS

- Store hashed payloads by default; only retain raw text when explicitly enabled and documented.
- Protect DB access with least-privilege users; do not run connector as root in production.
- Provide documentation for opt-out and secure storage procedures.

---

# 8 LIMITATIONS & FUTURE WORK

- Not a distributed ingestion architecture — add a central collector or message queue for scale.
- Add configurable ML model integration for anomaly scoring rather than heuristics.
- Improve schema to handle larger `event_type` or optional JSON payload fields.

---

# REFERENCES

1. MySQL Documentation — https://dev.mysql.com/doc/  
2. JPype & JayDeBeApi docs.  
3. psutil and pynput documentation.  
4. MySQL Connector/J documentation.

---

# APPENDIX A — CODING (excerpts + placement guidance)

Where to put code in your repo (recommended)
- Full source files (complete, unmodified) should be added under:
  - `docs/appendix/code/python/behavior_log.py`
  - `docs/appendix/code/java/BehaviorLoggerUI.java`
  - `docs/appendix/code/rust/hasher.rs`
- Short readable excerpts will be included in the document. Include the full files in `docs/appendix/code/` so readers can open them separately.

How to present code in the Word document
- Use monospaced font (Consolas 10 or Courier New 10), single-spaced.
- Apply a border or gray shading to each code block and a caption like “Listing A.1 — behavior_log.py: log_event”.
- If a code listing is longer than a page, break at logical function boundaries; reference the full file path.

### Python — hashing + DB insert (excerpt)

```python
# docs/appendix/code/python/behavior_log.py (excerpt)
import hashlib
import subprocess
import json

def hash_with_rust(payload: str) -> str:
    try:
        proc = subprocess.run(['rust_hasher', payload], capture_output=True, text=True, check=True)
        return proc.stdout.strip()
    except Exception:
        # Fallback to Python SHA-256
        return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def insert_behavior_log(conn, event_type, raw_data):
    hashed = hash_with_rust(json.dumps(raw_data))
    sql = "INSERT INTO behavior_logs (timestamp, event_type, hashed_event, raw_data) VALUES (%s, %s, %s, %s)"
    cursor = conn.cursor()
    cursor.execute(sql, (time.time(), event_type[:50], hashed, json.dumps(raw_data)))
    conn.commit()
```

### Java — parent-first insertion (excerpt)

```java
// docs/appendix/code/java/BehaviorLoggerUI.java (excerpt)
PreparedStatement insertEvent = conn.prepareStatement(
  "INSERT INTO behavior_events (timestamp, event_type, summary) VALUES (?, ?, ?)",
  Statement.RETURN_GENERATED_KEYS
);

insertEvent.setDouble(1, timestamp);
insertEvent.setString(2, eventType);
insertEvent.setString(3, summary);
insertEvent.executeUpdate();

ResultSet rs = insertEvent.getGeneratedKeys();
long eventId = -1;
if (rs.next()) {
  eventId = rs.getLong(1);
}
// Now insert child rows referencing eventId
```

Full code
- I will place full source files in `docs/appendix/code/` on request. This keeps the PDF/Word report readable and allows code browsing separately.

---

Footer note: Generated by project assistant — end of report markdown.
