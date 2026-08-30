"""
Part 4: Data Subset Analysis.

Two things Bob wants here:

1. Among melanoma, PBMC, miraclib, baseline (time_from_treatment_start = 0)
   samples, break the counts down by project, by responder/non-responder,
   and by sex.

2. Separately, across melanoma male subjects of any sample type and any
   treatment, the average B cell count for responders at time zero. This
   one is intentionally not restricted to PBMC or miraclib, it's a wider
   question about the whole cohort.
"""

from pathlib import Path

import pandas as pd

from src.db import DEFAULT_DB_PATH, get_connection

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SUMMARY_PATH = ROOT_DIR / "output" / "subset_summary.csv"
DEFAULT_ANSWER_PATH = ROOT_DIR / "output" / "part4_answer.txt"


def get_baseline_miraclib_melanoma_samples(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Melanoma, PBMC, miraclib, time_from_treatment_start = 0.
    One row per sample with the subject metadata attached.
    """
    conn = get_connection(db_path)
    query = """
        SELECT sm.sample_id, sub.subject_id, sub.project, sub.sex, sub.response
        FROM samples sm
        JOIN subjects sub ON sm.subject_id = sub.subject_id
        WHERE sub.condition = 'melanoma'
          AND sub.treatment = 'miraclib'
          AND sm.sample_type = 'PBMC'
          AND sm.time_from_treatment_start = 0
    """
    result = pd.read_sql_query(query, conn)
    conn.close()
    return result


def summarize_baseline_subset(db_path: Path = DEFAULT_DB_PATH) -> dict:
    """
    Returns three small breakdowns of the baseline subset: samples per
    project, subjects per response group, subjects per sex.
    """
    subset = get_baseline_miraclib_melanoma_samples(db_path)
    subjects = subset.drop_duplicates("subject_id")

    return {
        "samples_per_project": subset.groupby("project")["sample_id"].count().rename("sample_count"),
        "subjects_per_response": subjects.groupby("response")["subject_id"].count().rename("subject_count"),
        "subjects_per_sex": subjects.groupby("sex")["subject_id"].count().rename("subject_count"),
    }


def average_b_cells_melanoma_male_responders_at_baseline(db_path: Path = DEFAULT_DB_PATH) -> float:
    """
    Average B cell count for melanoma male responders at time = 0, across
    every sample type and every treatment. Not filtered to PBMC or
    miraclib on purpose, this is a broader cohort question than Part 3.
    """
    conn = get_connection(db_path)
    query = """
        SELECT cc.count
        FROM cell_counts cc
        JOIN samples sm ON cc.sample_id = sm.sample_id
        JOIN subjects sub ON sm.subject_id = sub.subject_id
        WHERE sub.condition = 'melanoma'
          AND sub.sex = 'M'
          AND sub.response = 'yes'
          AND sm.time_from_treatment_start = 0
          AND cc.population = 'b_cell'
    """
    counts = pd.read_sql_query(query, conn)["count"]
    conn.close()
    return round(counts.mean(), 2)


def main() -> None:
    DEFAULT_SUMMARY_PATH.parent.mkdir(exist_ok=True)

    summary = summarize_baseline_subset()
    with open(DEFAULT_SUMMARY_PATH, "w") as f:
        for name, table in summary.items():
            f.write(f"{name}\n")
            f.write(table.to_csv())
            f.write("\n")

    print("Baseline subset (melanoma, PBMC, miraclib, time=0):")
    for name, table in summary.items():
        print(f"\n{name}")
        print(table.to_string())

    answer = average_b_cells_melanoma_male_responders_at_baseline()
    with open(DEFAULT_ANSWER_PATH, "w") as f:
        f.write(
            "Average B cell count, melanoma males, responders, time_from_treatment_start = 0, "
            f"all sample and treatment types: {answer:.2f}\n"
        )
    print(f"\nAverage B cell count (melanoma males, responders, time=0, all types): {answer:.2f}")
    print(f"Summary written to {DEFAULT_SUMMARY_PATH}")
    print(f"Answer written to {DEFAULT_ANSWER_PATH}")


if __name__ == "__main__":
    main()
