-- Schema for the Teiko cell count database.
--
-- Three tables, split by what actually changes together:
--
-- subjects: one row per patient. Condition, age, sex, treatment and response
--   never change across a subject's samples in this dataset, so they belong
--   here and not repeated on every sample.
--
-- samples: one row per biological sample. Each sample belongs to one
--   subject and carries the things that do vary sample to sample, like
--   sample type and time from treatment start.
--
-- cell_counts: one row per population per sample (long format), instead of
--   one column per population. This means Part 2's summary table is just a
--   join and a group by, no reshaping needed. It also means adding a new
--   immune population later is a new set of rows, not a new column and a
--   migration.

CREATE TABLE IF NOT EXISTS subjects (
    subject_id TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    condition TEXT NOT NULL,
    age INTEGER,
    sex TEXT,
    treatment TEXT,
    response TEXT
);

CREATE TABLE IF NOT EXISTS samples (
    sample_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    sample_type TEXT NOT NULL,
    time_from_treatment_start INTEGER,
    FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
);

CREATE TABLE IF NOT EXISTS cell_counts (
    sample_id TEXT NOT NULL,
    population TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (sample_id, population),
    FOREIGN KEY (sample_id) REFERENCES samples (sample_id)
);

-- Indexes for the joins and filters Parts 2 to 4 actually run.
CREATE INDEX IF NOT EXISTS idx_samples_subject_id ON samples (subject_id);
CREATE INDEX IF NOT EXISTS idx_cell_counts_sample_id ON cell_counts (sample_id);
CREATE INDEX IF NOT EXISTS idx_subjects_condition_treatment ON subjects (condition, treatment);
