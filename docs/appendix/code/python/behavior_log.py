# Full copy of python/behavior_log.py from the project
# Placed here for appendix access. This file is a direct copy of the source.

import jaydebeapi
import jpype
import mysql.connector
import time
import subprocess
import psutil
from pynput import keyboard, mouse
from threading import Thread
import os
import json
import win32gui
import win32process

# Global variables
STOP_AFTER = 45  # Run for 45 seconds
start_time = time.time()
stop_flag = False

# Add the missing functions
def hash_with_rust(input_str):
    """Hash input string using Rust hasher"""
    try:
        result = subprocess.run(
            [r"C:\Users\Ananya\behavior_logger\rust_hasher\target\release\rust_hasher.exe", input_str],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip()
    except Exception as e:
        # If the Rust binary isn't available, fall back to a Python SHA-256 hash
        try:
            import hashlib
            h = hashlib.sha256()
            h.update(input_str.encode('utf-8'))
            digest = h.hexdigest()
            print(f"Rust hasher unavailable, using sha256 fallback: {digest[:16]}...")
            return digest
        except Exception:
            print(f"Rust hasher error and Python fallback failed: {e}")
            return None

# ... rest of file omitted in appendix copy for brevity; full file in project root
