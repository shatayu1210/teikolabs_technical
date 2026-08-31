"""
Interactive dashboard for Bob. Three tabs, one per analysis part:
the frequency table, the responder vs non-responder comparison, and the
baseline subset breakdown. Reads straight from cell_counts.db, so run
load_data.py first (or just use make pipeline, which does it for you).
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.db import DEFAULT_DB_PATH
from src.frequencies import compute_frequencies
from src.stats_analysis import compare_responders_vs_non_responders, get_responder_comparison_data
from src.subset_analysis import (
    average_b_cells_melanoma_male_responders_at_baseline,
    summarize_baseline_subset,
)

st.set_page_config(page_title="Teiko Cell Count Dashboard", layout="wide")
st.title("Immune Cell Population Dashboard")
st.caption("Loblaw Bio, miraclib trial")

if not DEFAULT_DB_PATH.exists():
    st.error(
        "No database found yet. Run `python load_data.py` (or `make pipeline`) first, "
        "then reload this page."
    )
    st.stop()

tab_overview, tab_stats, tab_subset = st.tabs(
    ["Cell frequencies", "Responders vs non-responders", "Baseline subset"]
)

with tab_overview:
    st.subheader("Relative frequency of each cell population, per sample")
    st.write(
        "For every sample, each population's share of that sample's total cell count."
    )
    frequencies = compute_frequencies()

    samples = sorted(frequencies["sample"].unique())
    selected_samples = st.multiselect("Filter by sample", samples, default=samples[:10])
    filtered = frequencies[frequencies["sample"].isin(selected_samples)] if selected_samples else frequencies
    st.dataframe(filtered, width="stretch", hide_index=True)

with tab_stats:
    st.subheader("Melanoma, miraclib, PBMC: responders vs non-responders")
    st.write(
        "Mann-Whitney U test per population, with a Benjamini-Hochberg correction "
        "across the five populations since five tests are being run at once. "
        "See the README for the full reasoning behind both choices."
    )

    results = compare_responders_vs_non_responders()
    st.dataframe(results, width="stretch", hide_index=True)

    significant = results[results["significant"]]["population"].tolist()
    if significant:
        st.success(f"Significant after correction (p < 0.05): {', '.join(significant)}")
    else:
        st.info("No population was significant after correction in this dataset.")

    st.subheader("Boxplots by population")
    comparison_data = get_responder_comparison_data()
    populations = sorted(comparison_data["population"].unique())
    cols = st.columns(len(populations))
    for col, population in zip(cols, populations):
        with col:
            pop_data = comparison_data[comparison_data["population"] == population]
            responders = pop_data[pop_data["response"] == "yes"]["percentage"]
            non_responders = pop_data[pop_data["response"] == "no"]["percentage"]

            fig, ax = plt.subplots(figsize=(3, 3.5))
            ax.boxplot([non_responders, responders], tick_labels=["non-resp", "resp"])
            ax.set_title(population, fontsize=10)
            ax.set_ylabel("% of sample")
            st.pyplot(fig)
            plt.close(fig)

with tab_subset:
    st.subheader("Baseline subset: melanoma, PBMC, miraclib, time = 0")
    summary = summarize_baseline_subset()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.write("Samples per project")
        st.dataframe(summary["samples_per_project"])
    with col2:
        st.write("Subjects per response")
        st.dataframe(summary["subjects_per_response"])
    with col3:
        st.write("Subjects per sex")
        st.dataframe(summary["subjects_per_sex"])

    st.divider()
    st.subheader("Melanoma males, responders, time = 0, all sample and treatment types")
    average = average_b_cells_melanoma_male_responders_at_baseline()
    st.metric("Average B cell count", f"{average:.2f}")
