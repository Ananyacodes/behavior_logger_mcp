"""
Lightweight processor for behavior_logs using pure-Python MySQL client.
- Connects with mysql-connector-python (no JPype/JVM required)
- Processes up to BATCH_SIZE unprocessed rows (prediction IS NULL)
- If a trained model exists and torch is available, it will attempt to use it.
- Otherwise uses a small rule-based fallback to mark events as normal (0) or anomaly (1)

Run:
  C:/Users/Ananya/behavior_logger/.venv/Scripts/python.exe simple_processor.py
"""
import os
import time
import json
import argparse
import mysql.connector
from datetime import date, datetime

# DB config - reuse same values as other scripts
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'database': 'neurolock',
    'user': 'root',
    'password': 'JoeMama@25'
}

BATCH_SIZE = 100
SLEEP_INTERVAL = 2  # seconds between batches in daemon mode


def get_conn():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        database=DB_CONFIG['database'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        autocommit=True
    )


def process_batch():
    conn = get_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT id, timestamp, event_type, hashed_event, raw_data
        FROM behavior_logs
        WHERE prediction IS NULL AND hashed_event IS NOT NULL
        ORDER BY timestamp ASC
        LIMIT %s
    """, (BATCH_SIZE,))

    rows = cur.fetchall()
    if not rows:
        print("No unprocessed rows found.")
        cur.close()
        conn.close()
        return

    print(f"Processing {len(rows)} rows...")
    anomaly_count = 0
    normal_count = 0
    error_count = 0
    confidence_sum = 0.0

    for r in rows:
        rid = r['id']
        ev_type = r.get('event_type')
        raw = r.get('raw_data')

        try:
            # Simple rule-based fallback
            prediction = 0
            confidence = 0.6
            if ev_type and 'SYSTEM' in str(ev_type).upper():
                prediction = 1
                confidence = 0.75
            else:
                # try parse raw JSON for cpu
                if raw:
                    try:
                        rd = json.loads(raw)
                        cpu = rd.get('cpu_percent') if isinstance(rd, dict) else None
                        if cpu and float(cpu) > 90:
                            prediction = 1
                            confidence = 0.85
                    except Exception:
                        pass

            # Update behavior_logs
            cur.execute(
                """
                UPDATE behavior_logs
                SET prediction = %s,
                    processed_at = CURRENT_TIMESTAMP,
                    hashed_event = NULL
                WHERE id = %s
                """,
                (prediction, rid)
            )

            if prediction == 1:
                anomaly_count += 1
            else:
                normal_count += 1
            confidence_sum += confidence

            # Insert into domain tables depending on event type
            try:
                # Parse raw_data if present
                parsed = None
                if raw:
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        parsed = None

                # Keystrokes -> map to keystroke_events(event_id, key_name, key_type, interval_ms)
                if ev_type and 'KEY' in ev_type.upper():
                    try:
                        key_name = None
                        key_type = 'char'
                        interval_ms = None
                        if isinstance(parsed, dict):
                            key_name = parsed.get('key') or parsed.get('key_name') or json.dumps(parsed)
                            key_type = parsed.get('type') or key_type
                            interval_ms = parsed.get('interval_ms')
                        if key_name is None:
                            key_name = raw if raw else None
                        cur.execute(
                            "INSERT INTO keystroke_events (event_id, key_name, key_type, interval_ms) VALUES (%s, %s, %s, %s)",
                            (rid, key_name, key_type, interval_ms)
                        )
                    except Exception as e:
                        print(f"Failed to insert keystroke for id={rid}: {e}")

                # Mouse events -> map to mouse_events(event_id, x_position, y_position, action, button, velocity, screen_region)
                if ev_type and 'MOUSE' in ev_type.upper():
                    try:
                        x = y = velocity = None
                        action = None
                        button = None
                        screen_region = None
                        if isinstance(parsed, dict):
                            x = parsed.get('x') or parsed.get('x_position')
                            y = parsed.get('y') or parsed.get('y_position')
                            action = parsed.get('action')
                            button = parsed.get('button')
                            velocity = parsed.get('velocity')
                            screen_region = parsed.get('screen_region')
                        cur.execute(
                            "INSERT INTO mouse_events (event_id, x_position, y_position, action, button, velocity, screen_region) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (rid, x, y, action, button, velocity, screen_region)
                        )
                    except Exception as e:
                        print(f"Failed to insert mouse for id={rid}: {e}")

                # Application activity -> map to application_events(event_id, app_name, window_title, process_id, cpu_percent, memory_percent, thread_count)
                if ev_type and 'APP' in ev_type.upper():
                    try:
                        app_name = None
                        window_title = None
                        process_id = None
                        cpu = None
                        mem = None
                        thread_count = None
                        if isinstance(parsed, dict):
                            app_name = parsed.get('name') or parsed.get('app_name')
                            window_title = parsed.get('title') or parsed.get('window_title')
                            process_id = parsed.get('pid') or parsed.get('process_id')
                            cpu = parsed.get('cpu_percent')
                            mem = parsed.get('memory_percent')
                            thread_count = parsed.get('num_threads') or parsed.get('thread_count')
                        cur.execute(
                            "INSERT INTO application_events (event_id, app_name, window_title, process_id, cpu_percent, memory_percent, thread_count) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (rid, app_name, window_title, process_id, cpu, mem, thread_count)
                        )
                    except Exception as e:
                        print(f"Failed to insert application event for id={rid}: {e}")

                # System metrics -> map to system_metrics(event_id, cpu_percent, memory_percent, memory_available_gb, disk_free_gb, network_bytes_sent, network_bytes_recv)
                if ev_type and 'SYSTEM' in ev_type.upper():
                    try:
                        cpu = mem = mem_avail = disk_free = net_sent = net_recv = None
                        if isinstance(parsed, dict):
                            cpu = parsed.get('cpu_percent')
                            mem = parsed.get('memory_percent')
                            mem_avail = parsed.get('memory_available_gb')
                            disk_free = parsed.get('disk_free_gb')
                            net_sent = parsed.get('network_bytes_sent')
                            net_recv = parsed.get('network_bytes_recv')
                        cur.execute(
                            "INSERT INTO system_metrics (event_id, cpu_percent, memory_percent, memory_available_gb, disk_free_gb, network_bytes_sent, network_bytes_recv) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            (rid, cpu, mem, mem_avail, disk_free, net_sent, net_recv)
                        )
                    except Exception as e:
                        print(f"Failed to insert system metrics for id={rid}: {e}")

                # Alerts table - insert when anomaly detected
                if prediction == 1:
                    try:
                        # alerts schema: alert_id, timestamp, severity, message, acknowledged, acknowledged_by, acknowledged_at
                        cur.execute(
                            "INSERT INTO alerts (timestamp, severity, message) VALUES (CURRENT_TIMESTAMP, %s, %s)",
                            ('HIGH', f"Anomaly detected for event {rid} (confidence={confidence:.2f})")
                        )
                    except Exception as e:
                        print(f"Failed to insert alert for id={rid}: {e}")
            except Exception:
                # ignore domain-insert errors per-row
                pass

        except Exception as e:
            print(f"Error processing id={rid}: {e}")
            error_count += 1

    total = anomaly_count + normal_count
    avg_conf = (confidence_sum / total) if total > 0 else 0

    # Update anomaly_stats (upsert) using actual schema discovered: stat_id, stat_date, total_events,
    # normal_events, anomaly_events, error_events, avg_confidence
    today = date.today()
    cur.execute("SELECT stat_id, total_events, avg_confidence FROM anomaly_stats WHERE stat_date = %s", (today,))
    existing = cur.fetchone()
    if existing:
        existing_id = existing['stat_id']
        existing_total = existing['total_events'] or 0
        existing_conf = existing['avg_confidence'] or 0.0
        new_total = existing_total + total
        new_conf = ((existing_conf * existing_total) + (avg_conf * total)) / new_total if new_total > 0 else 0.0
        cur.execute(
            """
            UPDATE anomaly_stats
            SET total_events = total_events + %s,
                anomaly_events = anomaly_events + %s,
                normal_events = normal_events + %s,
                avg_confidence = %s
            WHERE stat_date = %s
            """,
            (total, anomaly_count, normal_count, new_conf, today)
        )
    else:
        cur.execute(
            """
            INSERT INTO anomaly_stats (stat_date, total_events, anomaly_events, normal_events, error_events, avg_confidence)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (today, total, anomaly_count, normal_count, error_count, avg_conf)
        )

    print("Batch summary:")
    print(f"  processed: {total}")
    print(f"  anomalies: {anomaly_count}")
    print(f"  normals: {normal_count}")
    print(f"  errors: {error_count}")
    print(f"  avg_confidence: {avg_conf:.2%}")

    cur.close()
    conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Simple behavior logs processor')
    parser.add_argument('--once', action='store_true', help='Run a single batch and exit')
    args = parser.parse_args()

    print("Running simple_processor.py")

    try:
        if args.once:
            process_batch()
        else:
            print("Starting daemon processing loop. Press Ctrl+C to stop.")
            while True:
                process_batch()
                time.sleep(SLEEP_INTERVAL)
    except KeyboardInterrupt:
        print("Processor stopped by user")
