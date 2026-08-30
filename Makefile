.PHONY: setup pipeline dashboard test clean

# Installs into whichever python3 actually runs the pipeline below, using
# plain 'pip' can quietly point at a different python install on a Mac
# with more than one Python around, which is exactly what happened here.
setup:
	python3 -m pip install -r requirements.txt

# Runs the full pipeline start to finish: build the database, load the
# csv, then generate every output table and plot for parts 2 through 4.
pipeline:
	python3 load_data.py
	python3 -m src.frequencies
	python3 -m src.stats_analysis
	python3 -m src.subset_analysis

# Same reasoning as setup, going through python3 -m keeps this using the
# same install streamlit just got put into, instead of hoping the plain
# 'streamlit' command on PATH happens to match.
dashboard:
	python3 -m streamlit run dashboard/app.py

test:
	python3 -m pytest

clean:
	rm -f cell_counts.db
	rm -rf output/*.csv output/*.png output/*.txt
