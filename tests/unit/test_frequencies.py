from src.frequencies import compute_frequencies


def test_percentages_sum_to_100_per_sample(small_db):
    result = compute_frequencies(small_db)
    totals = result.groupby("sample")["percentage"].sum()
    for total in totals:
        assert abs(total - 100) < 0.01


def test_known_sample_has_even_20_percent_split(small_db):
    # sample_001 has 100 cells in each of the 5 populations, out of 500 total.
    result = compute_frequencies(small_db)
    sample_001 = result[result["sample"] == "sample_001"]

    assert sample_001["total_count"].unique().tolist() == [500]
    assert set(sample_001["percentage"].round(1)) == {20.0}


def test_known_sample_with_uneven_split(small_db):
    # sample_002: b_cell 200 of 500 total, should be 40 percent.
    result = compute_frequencies(small_db)
    row = result[(result["sample"] == "sample_002") & (result["population"] == "b_cell")].iloc[0]

    assert row["count"] == 200
    assert row["percentage"] == 40.0


def test_row_count_matches_samples_times_populations(small_db):
    result = compute_frequencies(small_db)
    # 4 fixture samples, 5 populations each
    assert len(result) == 20
