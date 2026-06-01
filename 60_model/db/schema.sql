CREATE TABLE IF NOT EXISTS data_sources (
  source_id TEXT PRIMARY KEY,
  source_path TEXT NOT NULL,
  source_type TEXT NOT NULL,
  loaded_at TEXT NOT NULL,
  row_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS poi_candidates (
  candidate_id TEXT PRIMARY KEY,
  park_id TEXT NOT NULL,
  park_name TEXT NOT NULL,
  poi_name TEXT NOT NULL,
  standard_categories TEXT NOT NULL,
  longitude REAL,
  latitude REAL,
  rating REAL,
  cost_yuan REAL,
  opentime_today TEXT NOT NULL DEFAULT '',
  tel TEXT NOT NULL DEFAULT '',
  boundary_filter_status TEXT NOT NULL,
  supply_use_status TEXT NOT NULL,
  source_path TEXT NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS calibration_gates (
  gate_id TEXT PRIMARY KEY,
  calibration_domain TEXT NOT NULL,
  required_before_p4_conclusion TEXT NOT NULL,
  current_gate_status TEXT NOT NULL,
  blocking_reason TEXT NOT NULL,
  source_table TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simulation_jobs (
  job_id TEXT PRIMARY KEY,
  scenario_name TEXT NOT NULL,
  seed INTEGER NOT NULL,
  iterations INTEGER NOT NULL,
  status TEXT NOT NULL,
  output_status TEXT NOT NULL,
  not_final INTEGER NOT NULL,
  created_at TEXT NOT NULL,
  completed_at TEXT,
  request_json TEXT NOT NULL,
  error_message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS simulation_results (
  result_id TEXT PRIMARY KEY,
  job_id TEXT NOT NULL,
  park_id TEXT NOT NULL,
  category TEXT NOT NULL,
  candidate_count INTEGER NOT NULL,
  inside_osm_polygon_count INTEGER NOT NULL,
  missing_business_field_count INTEGER NOT NULL,
  blocked_gate_count INTEGER NOT NULL,
  sampled_candidate_ids TEXT NOT NULL,
  output_status TEXT NOT NULL,
  not_final INTEGER NOT NULL,
  warnings_json TEXT NOT NULL,
  FOREIGN KEY(job_id) REFERENCES simulation_jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_poi_candidates_park ON poi_candidates(park_id);
CREATE INDEX IF NOT EXISTS idx_simulation_results_job ON simulation_results(job_id);
