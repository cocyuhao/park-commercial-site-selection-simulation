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
  group_context TEXT NOT NULL DEFAULT '',
  boundary_filter_status TEXT NOT NULL DEFAULT '',
  source_hint TEXT NOT NULL DEFAULT '',
  candidate_count INTEGER NOT NULL,
  inside_osm_polygon_count INTEGER NOT NULL,
  missing_business_field_count INTEGER NOT NULL,
  blocked_gate_count INTEGER NOT NULL,
  why_blocked_json TEXT NOT NULL DEFAULT '[]',
  missing_required_fields_json TEXT NOT NULL DEFAULT '[]',
  next_data_needed_json TEXT NOT NULL DEFAULT '[]',
  sampled_candidate_ids TEXT NOT NULL,
  output_status TEXT NOT NULL,
  not_final INTEGER NOT NULL,
  status_label TEXT NOT NULL DEFAULT '待复核 / 非最终',
  warnings_json TEXT NOT NULL,
  FOREIGN KEY(job_id) REFERENCES simulation_jobs(job_id)
);

CREATE INDEX IF NOT EXISTS idx_poi_candidates_park ON poi_candidates(park_id);
CREATE INDEX IF NOT EXISTS idx_simulation_results_job ON simulation_results(job_id);

CREATE TABLE IF NOT EXISTS runtime_uploads (
  upload_id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  source_type TEXT NOT NULL,
  category TEXT NOT NULL,
  size_bytes INTEGER NOT NULL DEFAULT 0,
  stored_path TEXT NOT NULL,
  review_status TEXT NOT NULL,
  target_gate TEXT NOT NULL DEFAULT '',
  note TEXT NOT NULL DEFAULT '',
  output_status TEXT NOT NULL DEFAULT 'needs_review',
  not_final INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS upload_candidates (
  candidate_id TEXT PRIMARY KEY,
  upload_id TEXT NOT NULL,
  filename TEXT NOT NULL,
  category TEXT NOT NULL,
  review_status TEXT NOT NULL,
  output_status TEXT NOT NULL DEFAULT 'needs_review',
  not_final INTEGER NOT NULL DEFAULT 1,
  generated_by TEXT NOT NULL DEFAULT '',
  related_gates_json TEXT NOT NULL DEFAULT '[]',
  related_nodes_json TEXT NOT NULL DEFAULT '[]',
  suggested_actions_json TEXT NOT NULL DEFAULT '[]',
  summary TEXT NOT NULL DEFAULT '',
  source_excerpt TEXT NOT NULL DEFAULT '',
  reviewer_note TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  confirmed_at TEXT NOT NULL DEFAULT '',
  raw_json TEXT NOT NULL,
  FOREIGN KEY(upload_id) REFERENCES runtime_uploads(upload_id)
);

CREATE TABLE IF NOT EXISTS gate_inputs (
  input_id TEXT PRIMARY KEY,
  calibration_domain TEXT NOT NULL,
  note TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL DEFAULT '',
  due_date TEXT NOT NULL DEFAULT '',
  source_hint TEXT NOT NULL DEFAULT '',
  output_status TEXT NOT NULL DEFAULT 'needs_review',
  not_final INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_runtime_uploads_gate ON runtime_uploads(target_gate);
CREATE INDEX IF NOT EXISTS idx_upload_candidates_upload ON upload_candidates(upload_id);
CREATE INDEX IF NOT EXISTS idx_gate_inputs_domain ON gate_inputs(calibration_domain);
