This folder contains a few helper and troubleshooting scripts.

- `live_tail.py` - lightweight tail of `behavior_logs` (recommended, kept in repo).
- `print_db.py` - schema + newest-500 row dumper (recommended, kept in repo).
- `inspect_tables.py` - quick schema inspector (optional)

Archived tools (moved to `archive/`):
- `check_db.py` (JPype/jdbc)
- `check_mysql_users.py` (mysql client)
- `debug_db.py` (pyodbc/sqlserver tests)
- `ensure_database_mode.py` (mutates scripts; archived)

Security note:
- The project now loads DB credentials from environment variables. Copy `.env.template` to `.env` and fill in values if you want local convenience. Never commit `.env` to git.
