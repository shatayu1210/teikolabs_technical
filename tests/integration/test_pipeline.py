"""
Integration test: runs the real pipeline, load_data through all three
analysis parts, against a small csv, and checks the output files land
where they're supposed to with sane content. This is the test that
actually proves the pieces work together, not just in isolation.
"""

import csv

import pytest

from load_data import load_csv
from src.frequencies import compute_frequencies
from src.stats_analysis import compare_responders_vs_non_responders
from src.subset_analysis import average_b_cells_melanoma_male_responders_at_baseline

CSV_HEADER = [
    "project", "subject", "condition", "age", "sex", "treatment", "response",
    "sample", "sample_type", "time_from_treatment_start",
    "b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte",
]


@pytest.fixture
def tiny_csv(tmp_path):
    csv_path = tmp_path / "cell-count.csv"
    rows = [
        ["prj1", "sbj000", "melanoma", "50", "M", "miraclib", "yes", "s000", "PBMC", "0", "100", "100", "100", "100", "100"],
        ["prj1", "sbj001", "melanoma", "55", "F", "miraclib", "no", "s001", "PBMC", "0", "200", "50", "50", "100", "100"],
        ["prj2", "sbj002", "carcinoma", "60", "M", "phauximab", "no", "s002", "WB", "0", "60", "60", "60", "60", "260"],
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_HEADER)
        writer.writerows(rows)
    return csv_path


def test_full_pipeline_runs_end_to_end(tmp_path, tiny_csv):
    db_path = tmp_path / "pipeline_test.db"

    load_csv(csv_path=tiny_csv, db_path=db_path)

    frequencies = compute_frequencies(db_path)
    assert len(frequencies) == 15  # 3 samples x 5 populations

    stats_results = compare_responders_vs_non_responders(db_path)
    assert set(stats_results["population"]) == {
        "b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte",
    }

    average = average_b_cells_melanoma_male_responders_at_baseline(db_path)
    assert average == 100.0  # only sbj000 qualifies, b_cell = 100
