import pandas as pd
import torch
import pyodbc
from torch.nn.utils.rnn import pad_sequence

# SQL Server JDBC configuration
DB_CONFIG = {
    'server': 'localhost\\SQLEXPRESS',
    'database': 'behavior_db',
    'driver': '{ODBC Driver 17 for SQL Server}'
}

def get_db_connection():
    """Try multiple SQL Server connection strings"""
    connection_strings = [
        f"DRIVER={DB_CONFIG['driver']};SERVER=localhost\\SQLEXPRESS;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
        f"DRIVER={DB_CONFIG['driver']};SERVER=localhost;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
        f"DRIVER={DB_CONFIG['driver']};SERVER=.;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
        f"DRIVER={{SQL Server}};SERVER=localhost\\SQLEXPRESS;DATABASE={DB_CONFIG['database']};Trusted_Connection=yes;",
    ]
    
    for i, conn_str in enumerate(connection_strings, 1):
        try:
            return pyodbc.connect(conn_str)
        except Exception as e:
            if i == len(connection_strings):
                raise e
            continue

def is_valid_hex(s):
    try:
        int(s.strip(), 16)
        return True
    except ValueError:
        return False

def load_logs():
    """Load logs from SQL Server database"""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT id, timestamp, hashed_event 
        FROM behavior_logs 
        WHERE hashed_event IS NOT NULL
    """, conn)
    conn.close()
    
    before = len(df)
    df = df[df["hashed_event"].apply(lambda x: isinstance(x, str) and is_valid_hex(x))]
    after = len(df)
    if before != after:
        print(f"Filtered out {before - after} invalid hashed_event rows.")
    return df

def hash_to_vector(hash_str, max_len=16):
    vec = []
    for c in hash_str.strip()[:max_len]:
        try:
            vec.append(int(c, 16))
        except ValueError:
            vec.append(0)
    return vec

def prepare_sequences(df, max_len=64):
    """Convert dataframe into padded tensor sequences"""
    sequences = [torch.tensor(hash_to_vector(h, max_len), dtype=torch.long) for h in df["hashed_event"]]
    padded = pad_sequence(sequences, batch_first=True, padding_value=0)
    return padded