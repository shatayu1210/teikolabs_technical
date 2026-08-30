"""
Shared test fixtures. Builds a tiny, hand-picked database where we know
the right answer ahead of time, so the tests are checking real behaviour
and not just "did it run without crashing".
"""

import sqlite3

import pytest

from src.db import init_schema

# sample_001 and sample_003 are melanoma, miraclib, PBMC, male responders at
# time 0 (b_cell 100 and 120, average should come out to 110.00).
# sample_002 is melanoma, miraclib, PBMC, female non-responder at time 0.
# sample_004 is carcinoma, phauximab, WB, and should be excluded from every
# melanoma/miraclib/PBMC filter.
FIXTURE_ROWS = [
    # subject_id, project, condition, age, sex, treatment, response
    ("subject_001", "prjA", "melanoma", 50, "M", "miraclib", "yes"),
    ("subject_002", "prjA", "melanoma", 55, "F", "miraclib", "no"),
    ("subject_003", "prjB", "melanoma", 60, "M", "miraclib", "yes"),
    ("subject_004", "prjA", "carcinoma", 45, "F", "phauximab", "no"),
]

FIXTURE_SAMPLES = [
    # sample_id, subject_id, sample_type, time_from_treatment_start
    ("sample_001", "subject_001", "PBMC", 0),
    ("sample_002", "subject_002", "PBMC", 0),
    ("sample_003", "subject_003", "PBMC", 0),
    ("sample_004", "subject_004", "WB", 0),
]

# Each sample totals 500 cells so percentages are easy to check by hand.
FIXTURE_COUNTS = {
    "sample_001": {"b_cell": 100, "cd8_t_cell": 100, "cd4_t_cell": 100, "nk_cell": 100, "monocyte": 100},
    "sample_002": {"b_cell": 200, "cd8_t_cell": 50, "cd4_t_cell": 50, "nk_cell": 100, "monocyte": 100},
    "sample_003": {"b_cell": 120, "cd8_t_cell": 80, "cd4_t_cell": 100, "nk_cell": 100, "monocyte": 100},
    "sample_004": {"b_cell": 60, "cd8_t_cell": 60, "cd4_t_cell": 60, "nk_cell": 60, "monocyte": 260},
}


@pytest.fixture
def small_db(tmp_path):
    db_path = tmp_path / "small.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)

    conn.executemany(
        "INSERT INTO subjects (subject_id, project, condition, age, sex, treatment, response) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        FIXTURE_ROWS,
    )
    conn.executemany(
        "INSERT INTO samples (sample_id, subject_id, sample_type, time_from_treatment_start) "
        "VALUES (?, ?, ?, ?)",
        FIXTURE_SAMPLES,
    )
    for sample_id, populations in FIXTURE_COUNTS.items():
        for population, count in populations.items():
            conn.execute(
                "INSERT INTO cell_counts (sample_id, population, count) VALUES (?, ?, ?)",
                (sample_id, population, count),
            )
    conn.commit()
    conn.close()
    return db_path
