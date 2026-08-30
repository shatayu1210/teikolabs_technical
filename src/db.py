"""
Small helper module for opening a connection to the cell count database
and making sure the schema is in place. Kept separate from load_data.py
so the analysis scripts can reuse the same connection logic without
re-reading the schema file every time.
"""

import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT_DIR / "cell_counts.db"
SCHEMA_PATH = ROOT_DIR / "db" / "schema.sql"


def get_connection(db_path: Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Open a connection to the SQLite database at db_path."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection, schema_path: Path = SCHEMA_PATH) -> None:
    """Create the subjects, samples and cell_counts tables if they don't exist yet."""
    schema_sql = schema_path.read_text()
    conn.executescript(schema_sql)
    conn.commit()
