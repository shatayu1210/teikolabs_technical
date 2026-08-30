"""Checks that the schema actually creates the tables we expect."""

from src.db import get_connection, init_schema


def test_init_schema_creates_all_tables(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    init_schema(conn)

    tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    conn.close()

    assert {"subjects", "samples", "cell_counts"}.issubset(tables)


def test_init_schema_is_safe_to_run_twice(tmp_path):
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    init_schema(conn)
    init_schema(conn)  # should not raise
    conn.close()
