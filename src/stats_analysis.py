"""
Part 3: Statistical Analysis.

Compares relative cell population frequencies between responders and
non-responders, for melanoma patients on miraclib, PBMC samples only.

Why the Mann-Whitney U test: relative frequencies from a small clinical
cohort are not guaranteed to be normally distributed, and a couple of
outlier patients can easily skew a mean. Mann-Whitney compares the ranks
of the two groups instead of their raw means, so it does not assume a
normal distribution and is far less sensitive to outliers. That makes it
the safer default here rather than a t-test.

Why the Benjamini-Hochberg correction: we are running one test per cell
population, five tests in total, against the same two groups. Testing
five hypotheses at once raises the odds of a false positive by chance
alone. Benjamini-Hochberg adjusts the p-values to control that, so a
population is only called significant if the evidence holds up after
accounting for the multiple comparisons, not just on a single lucky
p-value.
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats

from src.db import DEFAULT_DB_PATH, get_connection
from src.frequencies import compute_frequencies

ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_PATH = ROOT_DIR / "output" / "stats_results.csv"
DEFAULT_BOXPLOT_PATH = ROOT_DIR / "output" / "boxplots.png"

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]


def get_responder_comparison_data(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Return relative frequency rows for melanoma, miraclib, PBMC samples only,
    tagged with the subject's response.
    """
    conn = get_connection(db_path)
    subjects = pd.read_sql_query(
        """
        SELECT s.subject_id, s.response
        FROM subjects s
        WHERE s.condition = 'melanoma' AND s.treatment = 'miraclib'
        """,
        conn,
    )
    samples = pd.read_sql_query(
        "SELECT sample_id, subject_id FROM samples WHERE sample_type = 'PBMC'",
        conn,
    )
    conn.close()

    freq = compute_frequencies(db_path)
    freq = freq.merge(samples, left_on="sample", right_on="sample_id")
    freq = freq.merge(subjects, on="subject_id")
    return freq[["sample", "population", "percentage", "response"]]


def compare_responders_vs_non_responders(db_path: Path = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Run a Mann-Whitney U test per population, responders vs non-responders,
    then apply a Benjamini-Hochberg correction across the five results.
    Returns one row per population with the test statistic, raw p-value,
    adjusted p-value and whether it's significant at 0.05.
    """
    data = get_responder_comparison_data(db_path)

    raw_results = []
    for population in POPULATIONS:
        pop_data = data[data["population"] == population]
        responders = pop_data[pop_data["response"] == "yes"]["percentage"]
        non_responders = pop_data[pop_data["response"] == "no"]["percentage"]

        statistic, p_value = stats.mannwhitneyu(responders, non_responders, alternative="two-sided")
        raw_results.append(
            {
                "population": population,
                "n_responders": len(responders),
                "n_non_responders": len(non_responders),
                "median_responders": round(responders.median(), 4),
                "median_non_responders": round(non_responders.median(), 4),
                "u_statistic": statistic,
                "p_value": p_value,
            }
        )

    results = pd.DataFrame(raw_results)
    results["p_value_adjusted"] = benjamini_hochberg(results["p_value"].values)
    results["significant"] = results["p_value_adjusted"] < 0.05
    return results.sort_values("p_value_adjusted").reset_index(drop=True)


def benjamini_hochberg(p_values):
    """
    Standard Benjamini-Hochberg step-up procedure. Sort the p-values
    smallest to largest, scale each one by n / rank, then walk back from
    the largest so the adjusted values never decrease as the raw p-value
    gets smaller (that's what keeps the correction valid).
    """
    import numpy as np

    p_values = np.asarray(p_values, dtype=float)
    n = len(p_values)

    sort_order = np.argsort(p_values)
    sorted_p = p_values[sort_order]
    ranks = np.arange(1, n + 1)

    adjusted_sorted = np.minimum(sorted_p * n / ranks, 1.0)
    for i in range(n - 2, -1, -1):
        adjusted_sorted[i] = min(adjusted_sorted[i], adjusted_sorted[i + 1])

    adjusted = np.empty(n)
    adjusted[sort_order] = adjusted_sorted
    return adjusted.tolist()


def make_boxplots(db_path: Path = DEFAULT_DB_PATH, output_path: Path = DEFAULT_BOXPLOT_PATH) -> None:
    """One boxplot per population, responders vs non-responders, in a single figure."""
    data = get_responder_comparison_data(db_path)

    fig, axes = plt.subplots(1, len(POPULATIONS), figsize=(20, 4.5))
    for ax, population in zip(axes, POPULATIONS):
        pop_data = data[data["population"] == population]
        responders = pop_data[pop_data["response"] == "yes"]["percentage"]
        non_responders = pop_data[pop_data["response"] == "no"]["percentage"]

        ax.boxplot([non_responders, responders], tick_labels=["non-responder", "responder"])
        ax.set_title(population)
        ax.set_ylabel("relative frequency (%)")

    fig.suptitle("Cell population frequency, responders vs non-responders (melanoma, miraclib, PBMC)")
    fig.tight_layout()
    output_path.parent.mkdir(exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    results = compare_responders_vs_non_responders()
    DEFAULT_RESULTS_PATH.parent.mkdir(exist_ok=True)
    results.to_csv(DEFAULT_RESULTS_PATH, index=False)
    make_boxplots()

    print(results.to_string(index=False))
    significant = results[results["significant"]]["population"].tolist()
    if significant:
        print(f"\nSignificant after correction (p < 0.05): {', '.join(significant)}")
    else:
        print("\nNo population was significant after correction.")
    print(f"Boxplots saved to {DEFAULT_BOXPLOT_PATH}")


if __name__ == "__main__":
    main()
