"""
Part 2: Initial Analysis, Data Overview.

Answers Bob's question: what is the frequency of each cell type in each
sample. For every sample, we take the total cell count across all five
populations, then express each population as a percentage of that total.
"""

from pathlib import Path

import pandas as pd

from src.db import DEFAULT_DB_PATH, get_connection

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = ROOT_DIR / "output" / "frequencies.csv"


def compute_frequencies(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Return one row per sample per population, with columns:
    sample, total_count, population, count, percentage.
    """
    conn = get_connection(db_path)
    counts = pd.read_sql_query("SELECT sample_id, population, count FROM cell_counts", conn)
    conn.close()

    totals = counts.groupby("sample_id")["count"].sum().rename("total_count")
    counts = counts.join(totals, on="sample_id")
    counts["percentage"] = (counts["count"] / counts["total_count"] * 100).round(4)

    result = counts.rename(columns={"sample_id": "sample"})[
        ["sample", "total_count", "population", "count", "percentage"]
    ]
    return result.sort_values(["sample", "population"]).reset_index(drop=True)


def main() -> None:
    frequencies = compute_frequencies()
    DEFAULT_OUTPUT_PATH.parent.mkdir(exist_ok=True)
    frequencies.to_csv(DEFAULT_OUTPUT_PATH, index=False)
    print(f"Wrote {len(frequencies)} rows to {DEFAULT_OUTPUT_PATH}")
    print(frequencies.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
