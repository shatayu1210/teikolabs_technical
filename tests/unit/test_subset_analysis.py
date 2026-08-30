from src.subset_analysis import (
    average_b_cells_melanoma_male_responders_at_baseline,
    get_baseline_miraclib_melanoma_samples,
    summarize_baseline_subset,
)


def test_baseline_subset_excludes_non_matching_samples(small_db):
    # sample_004 is carcinoma/phauximab/WB, should never show up here.
    subset = get_baseline_miraclib_melanoma_samples(small_db)
    assert set(subset["sample_id"]) == {"sample_001", "sample_002", "sample_003"}


def test_samples_per_project_breakdown(small_db):
    summary = summarize_baseline_subset(small_db)
    per_project = summary["samples_per_project"]
    assert per_project["prjA"] == 2  # sample_001, sample_002
    assert per_project["prjB"] == 1  # sample_003


def test_subjects_per_response_breakdown(small_db):
    summary = summarize_baseline_subset(small_db)
    per_response = summary["subjects_per_response"]
    assert per_response["yes"] == 2  # subject_001, subject_003
    assert per_response["no"] == 1  # subject_002


def test_subjects_per_sex_breakdown(small_db):
    summary = summarize_baseline_subset(small_db)
    per_sex = summary["subjects_per_sex"]
    assert per_sex["M"] == 2
    assert per_sex["F"] == 1


def test_average_b_cells_for_melanoma_male_responders(small_db):
    # subject_001 has b_cell 100, subject_003 has b_cell 120.
    # Average should be exactly 110.00, and this isn't limited to PBMC or
    # miraclib on purpose, matching how the question is worded.
    average = average_b_cells_melanoma_male_responders_at_baseline(small_db)
    assert average == 110.0
