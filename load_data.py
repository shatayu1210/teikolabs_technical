"""
Part 1: Data Management.

Builds the SQLite database from scratch and loads every row of
cell-count.csv into it. Run this with no arguments:

    python load_data.py

It will create cell_counts.db in the repository root. Safe to run more
than once, it clears out any existing rows first so you don't end up
with duplicates.
"""

import csv
from pathlib import Path

from src.db import DEFAULT_DB_PATH, get_connection, init_schema

ROOT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV_PATH = ROOT_DIR / "cell-count.csv"

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def load_csv(csv_path: Path = DEFAULT_CSV_PATH, db_path: Path = DEFAULT_DB_PATH) -> None:
    """Read cell-count.csv and populate the subjects, samples and cell_counts tables."""
    conn = get_connection(db_path)
    init_schema(conn)

    # Start clean each time this is run, so re-running the script never
    # doubles up the data.
    conn.execute("DELETE FROM cell_counts")
    conn.execute("DELETE FROM samples")
    conn.execute("DELETE FROM subjects")

    seen_subjects = set()

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subject_id = row["subject"]

            # A subject shows up on multiple rows (one per sample), so only
            # insert it the first time we see it.
            if subject_id not in seen_subjects:
                conn.execute(
                    """
                    INSERT INTO subjects (subject_id, project, condition, age, sex, treatment, response)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        subject_id,
                        row["project"],
                        row["condition"],
                        int(row["age"]) if row["age"] else None,
                        row["sex"],
                        row["treatment"],
                        row["response"] if row["response"] else None,
                    ),
                )
                seen_subjects.add(subject_id)

            conn.execute(
                """
                INSERT INTO samples (sample_id, subject_id, sample_type, time_from_treatment_start)
                VALUES (?, ?, ?, ?)
                """,
                (
                    row["sample"],
                    subject_id,
                    row["sample_type"],
                    int(row["time_from_treatment_start"]) if row["time_from_treatment_start"] else None,
                ),
            )

            for population in POPULATIONS:
                conn.execute(
                    """
                    INSERT INTO cell_counts (sample_id, population, count)
                    VALUES (?, ?, ?)
                    """,
                    (row["sample"], population, int(row[population])),
                )

    conn.commit()

    subject_count = conn.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
    sample_count = conn.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
    count_rows = conn.execute("SELECT COUNT(*) FROM cell_counts").fetchone()[0]
    conn.close()

    print(f"Loaded {subject_count} subjects, {sample_count} samples, {count_rows} cell count rows.")
    print(f"Database written to {db_path}")


if __name__ == "__main__":
    load_csv()
