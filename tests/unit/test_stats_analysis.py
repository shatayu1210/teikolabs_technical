import sqlite3

import pytest

from src.db import init_schema
from src.stats_analysis import benjamini_hochberg, compare_responders_vs_non_responders


def test_benjamini_hochberg_known_values():
    # Hand-computed: p * n / rank for the sorted p-values, then made
    # monotonic. For [0.01, 0.02, 0.03, 0.5, 0.9] that works out to
    # [0.05, 0.05, 0.05, 0.625, 0.9].
    p_values = [0.01, 0.02, 0.03, 0.5, 0.9]
    adjusted = benjamini_hochberg(p_values)

    assert adjusted == pytest.approx([0.05, 0.05, 0.05, 0.625, 0.9])


def test_benjamini_hochberg_never_decreases_significance_order():
    # A smaller raw p-value should never end up with a larger adjusted
    # p-value than one that started bigger, once both are sorted.
    p_values = [0.2, 0.001, 0.04, 0.03, 0.9]
    adjusted = benjamini_hochberg(p_values)

    order_by_raw = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted_in_raw_order = [adjusted[i] for i in order_by_raw]
    assert adjusted_in_raw_order == sorted(adjusted_in_raw_order)


@pytest.fixture
def stats_db(tmp_path):
    """
    30 melanoma/miraclib/PBMC responders and 30 non-responders. b_cell and
    cd8_t_cell trade mass between groups so every sample still totals 600
    cells. That matters: relative frequency is a percentage of the total,
    so if b_cell moved but the total didn't stay fixed, cd4_t_cell,
    nk_cell and monocyte would look different too even with an unchanged
    raw count. Keeping the total identical is what makes this a clean
    "no real difference" case for those three.
    """
    db_path = tmp_path / "stats.db"
    conn = sqlite3.connect(db_path)
    init_schema(conn)

    for i in range(30):
        responder_subject = f"resp_{i}"
        non_responder_subject = f"nonresp_{i}"
        conn.execute(
            "INSERT INTO subjects VALUES (?, 'prjA', 'melanoma', 50, 'M', 'miraclib', 'yes')",
            (responder_subject,),
        )
        conn.execute(
            "INSERT INTO subjects VALUES (?, 'prjA', 'melanoma', 50, 'M', 'miraclib', 'no')",
            (non_responder_subject,),
        )

        responder_sample = f"resp_sample_{i}"
        non_responder_sample = f"nonresp_sample_{i}"
        conn.execute(
            "INSERT INTO samples VALUES (?, ?, 'PBMC', 0)", (responder_sample, responder_subject)
        )
        conn.execute(
            "INSERT INTO samples VALUES (?, ?, 'PBMC', 0)", (non_responder_sample, non_responder_subject)
        )

        jitter = (i % 5) * 5
        responder_counts = {
            "b_cell": 250 + jitter,
            "cd8_t_cell": 50 - jitter,
            "cd4_t_cell": 100,
            "nk_cell": 100,
            "monocyte": 100,
        }
        non_responder_counts = {
            "b_cell": 100 - jitter,
            "cd8_t_cell": 200 + jitter,
            "cd4_t_cell": 100,
            "nk_cell": 100,
            "monocyte": 100,
        }
        for population, count in responder_counts.items():
            conn.execute(
                "INSERT INTO cell_counts VALUES (?, ?, ?)", (responder_sample, population, count)
            )
        for population, count in non_responder_counts.items():
            conn.execute(
                "INSERT INTO cell_counts VALUES (?, ?, ?)", (non_responder_sample, population, count)
            )

    conn.commit()
    conn.close()
    return db_path


def test_obvious_difference_is_flagged_significant(stats_db):
    results = compare_responders_vs_non_responders(stats_db)
    b_cell_row = results[results["population"] == "b_cell"].iloc[0]

    assert b_cell_row["significant"]
    assert b_cell_row["median_responders"] > b_cell_row["median_non_responders"]


def test_identical_distributions_are_not_flagged_significant(stats_db):
    results = compare_responders_vs_non_responders(stats_db)
    monocyte_row = results[results["population"] == "monocyte"].iloc[0]

    assert not monocyte_row["significant"]
