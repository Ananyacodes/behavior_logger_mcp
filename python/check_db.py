#!/usr/bin/env python3
import jaydebeapi
import jpype

try:
    jpype.shutdownJVM()
except:
    pass

jpype.startJVM("C:/Program Files/Java/jdk-16.0.2/bin/server/jvm.dll", 
               '-Djava.class.path=C:/Users/Ananya/behavior_logger/python/mysql-connector-j-8.4.0.jar')

conn = jaydebeapi.connect('com.mysql.cj.jdbc.Driver', 
                         'jdbc:mysql://localhost:3306/behavioral_analysis', 
                         ['root', 'password'])
cursor = conn.cursor()

print("=== TABLES IN DATABASE ===")
cursor.execute('SHOW TABLES')
tables = cursor.fetchall()
for table in tables:
    print(f"  - {table[0]}")

print("\n=== BEHAVIOR_LOGS STRUCTURE ===")
cursor.execute('DESCRIBE behavior_logs')
columns = cursor.fetchall()
for col in columns:
    print(f"  {col[0]} - {col[1]}")

print("\n=== EVENT TYPE COUNTS ===")
cursor.execute('SELECT event_type, COUNT(*) FROM behavior_logs GROUP BY event_type')
counts = cursor.fetchall()
for row in counts:
    print(f"  {row[0]}: {row[1]} events")

print("\n=== RECENT EVENTS ===")
cursor.execute('SELECT timestamp, event_type, details FROM behavior_logs ORDER BY timestamp DESC LIMIT 5')
recent = cursor.fetchall()
for event in recent:
    print(f"  {event[0]} | {event[1]} | {event[2][:50]}...")

cursor.close()
conn.close()
jpype.shutdownJVM()