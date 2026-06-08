from __future__ import annotations

import csv
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "60_model" / "db" / "simulation.sqlite3"
SCHEMA_PATH = ROOT / "60_model" / "db" / "schema.sql"
PROCESSED = ROOT / "70_outputs" / "processed_tables"


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    with connect(db_path) as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        migrate_db(conn)


def migrate_db(conn: sqlite3.Connection) -> None:
    table_columns = {
        "simulation_results": {
            "group_context": "TEXT NOT NULL DEFAULT ''",
            "boundary_filter_status": "TEXT NOT NULL DEFAULT ''",
            "source_hint": "TEXT NOT NULL DEFAULT ''",
            "why_blocked_json": "TEXT NOT NULL DEFAULT '[]'",
            "missing_required_fields_json": "TEXT NOT NULL DEFAULT '[]'",
            "next_data_needed_json": "TEXT NOT NULL DEFAULT '[]'",
            "feature_scene_context_json": "TEXT NOT NULL DEFAULT '[]'",
            "scenario_pressure_json": "TEXT NOT NULL DEFAULT '{}'",
            "accuracy_context_json": "TEXT NOT NULL DEFAULT '{}'",
            "calibration_constraints_json": "TEXT NOT NULL DEFAULT '[]'",
            "feature_scene_count": "INTEGER NOT NULL DEFAULT 0",
            "matched_feature_scene_count": "INTEGER NOT NULL DEFAULT 0",
            "status_label": "TEXT NOT NULL DEFAULT '待复核 / 非最终'",
        }
    }
    for table, columns in table_columns.items():
        existing = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
        }
        for name, definition in columns.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} {definition}")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def to_float(value: str | None) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def import_existing_outputs(db_path: Path = DB_PATH) -> dict[str, int]:
    init_db(db_path)
    poi_path = PROCESSED / "poi_supply_candidates_amap_boundary_filter.csv"
    gate_path = PROCESSED / "p3_calibration_gate_status.csv"
    poi_rows = read_csv_rows(poi_path)
    gate_rows = read_csv_rows(gate_path)
    loaded_at = utc_now()
    with connect(db_path) as conn:
        for row in poi_rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO poi_candidates (
                  candidate_id, park_id, park_name, poi_name, standard_categories,
                  longitude, latitude, rating, cost_yuan, opentime_today, tel,
                  boundary_filter_status, supply_use_status, source_path, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("candidate_id", ""),
                    row.get("park_id", ""),
                    row.get("park_name", ""),
                    row.get("poi_name", ""),
                    row.get("standard_categories", ""),
                    to_float(row.get("longitude")),
                    to_float(row.get("latitude")),
                    to_float(row.get("rating")),
                    to_float(row.get("cost_yuan")),
                    row.get("opentime_today", "") or "",
                    row.get("tel", "") or "",
                    row.get("boundary_filter_status", ""),
                    row.get("supply_use_status", ""),
                    str(poi_path.relative_to(ROOT)),
                    json.dumps(row, ensure_ascii=False),
                ),
            )
        for row in gate_rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO calibration_gates (
                  gate_id, calibration_domain, required_before_p4_conclusion,
                  current_gate_status, blocking_reason, source_table
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row.get("gate_id", ""),
                    row.get("calibration_domain", ""),
                    row.get("required_before_p4_conclusion", ""),
                    row.get("current_gate_status", ""),
                    row.get("blocking_reason", ""),
                    row.get("source_table", ""),
                ),
            )
        conn.execute(
            "INSERT OR REPLACE INTO data_sources VALUES (?, ?, ?, ?, ?)",
            ("poi_candidates", str(poi_path.relative_to(ROOT)), "csv", loaded_at, len(poi_rows)),
        )
        conn.execute(
            "INSERT OR REPLACE INTO data_sources VALUES (?, ?, ?, ?, ?)",
            ("calibration_gates", str(gate_path.relative_to(ROOT)), "csv", loaded_at, len(gate_rows)),
        )
    return {"poi_candidates": len(poi_rows), "calibration_gates": len(gate_rows)}


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def list_poi_candidates(db_path: Path = DB_PATH, limit: int = 200) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM poi_candidates ORDER BY park_id, candidate_id LIMIT ?",
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def list_calibration_gates(db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM calibration_gates ORDER BY gate_id").fetchall()
    return rows_to_dicts(rows)


def create_job(
    job_id: str,
    scenario_name: str,
    seed: int,
    iterations: int,
    request: dict[str, Any],
    db_path: Path = DB_PATH,
) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO simulation_jobs (
              job_id, scenario_name, seed, iterations, status, output_status,
              not_final, created_at, request_json
            ) VALUES (?, ?, ?, ?, 'running', 'needs_review', 1, ?, ?)
            """,
            (job_id, scenario_name, seed, iterations, utc_now(), json.dumps(request, ensure_ascii=False)),
        )


def complete_job(
    job_id: str,
    results: list[dict[str, Any]],
    status: str = "completed",
    error_message: str = "",
    db_path: Path = DB_PATH,
) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            "DELETE FROM simulation_results WHERE job_id = ?",
            (job_id,),
        )
        for index, row in enumerate(results, start=1):
            conn.execute(
                """
                INSERT INTO simulation_results (
                  result_id, job_id, park_id, category, group_context,
                  boundary_filter_status, source_hint, candidate_count,
                  inside_osm_polygon_count, missing_business_field_count,
                  blocked_gate_count, why_blocked_json, missing_required_fields_json,
                  next_data_needed_json, feature_scene_context_json,
                  scenario_pressure_json, accuracy_context_json,
                  calibration_constraints_json, feature_scene_count,
                  matched_feature_scene_count, sampled_candidate_ids, output_status,
                  not_final, status_label, warnings_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'needs_review', 1, '待复核 / 非最终', ?)
                """,
                (
                    f"{job_id}-R{index:03d}",
                    job_id,
                    row["park_id"],
                    row["category"],
                    row.get("group_context", ""),
                    row.get("boundary_filter_status", ""),
                    row.get("source_hint", ""),
                    row["candidate_count"],
                    row["inside_osm_polygon_count"],
                    row["missing_business_field_count"],
                    row["blocked_gate_count"],
                    json.dumps(row.get("why_blocked", []), ensure_ascii=False),
                    json.dumps(row.get("missing_required_fields", []), ensure_ascii=False),
                    json.dumps(row.get("next_data_needed", []), ensure_ascii=False),
                    json.dumps(row.get("feature_scene_context", []), ensure_ascii=False),
                    json.dumps(row.get("scenario_pressure", {}), ensure_ascii=False),
                    json.dumps(row.get("accuracy_context", {}), ensure_ascii=False),
                    json.dumps(row.get("calibration_constraints", []), ensure_ascii=False),
                    int(row.get("feature_scene_count") or 0),
                    int(row.get("matched_feature_scene_count") or 0),
                    json.dumps(row["sampled_candidate_ids"], ensure_ascii=False),
                    json.dumps(row["warnings"], ensure_ascii=False),
                ),
            )
        conn.execute(
            """
            UPDATE simulation_jobs
            SET status = ?, completed_at = ?, error_message = ?
            WHERE job_id = ?
            """,
            (status, utc_now(), error_message, job_id),
        )


def get_job(job_id: str, db_path: Path = DB_PATH) -> dict[str, Any] | None:
    init_db(db_path)
    with connect(db_path) as conn:
        row = conn.execute("SELECT * FROM simulation_jobs WHERE job_id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def list_jobs(db_path: Path = DB_PATH, limit: int = 50) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM simulation_jobs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def get_results(job_id: str, db_path: Path = DB_PATH) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM simulation_results WHERE job_id = ? ORDER BY result_id",
            (job_id,),
        ).fetchall()
    results = rows_to_dicts(rows)
    for row in results:
        row["sampled_candidate_ids"] = json.loads(row["sampled_candidate_ids"])
        row["warnings"] = json.loads(row.pop("warnings_json"))
        row["why_blocked"] = json.loads(row.pop("why_blocked_json", "[]") or "[]")
        row["missing_required_fields"] = json.loads(row.pop("missing_required_fields_json", "[]") or "[]")
        row["next_data_needed"] = json.loads(row.pop("next_data_needed_json", "[]") or "[]")
        row["feature_scene_context"] = json.loads(row.pop("feature_scene_context_json", "[]") or "[]")
        row["scenario_pressure"] = json.loads(row.pop("scenario_pressure_json", "{}") or "{}")
        row["accuracy_context"] = json.loads(row.pop("accuracy_context_json", "{}") or "{}")
        row["calibration_constraints"] = json.loads(row.pop("calibration_constraints_json", "[]") or "[]")
        row["not_final"] = bool(row["not_final"])
    return results


def upsert_runtime_upload(row: dict[str, Any], db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO runtime_uploads (
              upload_id, filename, source_type, category, size_bytes, stored_path,
              review_status, target_gate, note, output_status, not_final,
              created_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("upload_id", ""),
                row.get("filename", ""),
                row.get("source_type", ""),
                row.get("category", ""),
                int(row.get("size_bytes") or 0),
                row.get("stored_path", ""),
                row.get("review_status", ""),
                row.get("target_gate", ""),
                row.get("note", ""),
                row.get("output_status", "needs_review"),
                1 if row.get("not_final", True) else 0,
                row.get("created_at", utc_now()),
                json.dumps(row, ensure_ascii=False),
            ),
        )


def upsert_upload_candidate(row: dict[str, Any], db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO upload_candidates (
              candidate_id, upload_id, filename, category, review_status,
              output_status, not_final, generated_by, related_gates_json,
              related_nodes_json, suggested_actions_json, summary, source_excerpt,
              reviewer_note, created_at, confirmed_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("candidate_id", ""),
                row.get("upload_id", ""),
                row.get("filename", ""),
                row.get("category", ""),
                row.get("review_status", ""),
                row.get("output_status", "needs_review"),
                1 if row.get("not_final", True) else 0,
                row.get("generated_by", ""),
                json.dumps(row.get("related_gates", []), ensure_ascii=False),
                json.dumps(row.get("related_nodes", []), ensure_ascii=False),
                json.dumps(row.get("suggested_actions", []), ensure_ascii=False),
                row.get("summary", ""),
                row.get("source_excerpt", ""),
                row.get("reviewer_note", ""),
                row.get("created_at", utc_now()),
                row.get("confirmed_at", ""),
                json.dumps(row, ensure_ascii=False),
            ),
        )


def upsert_gate_input(row: dict[str, Any], db_path: Path = DB_PATH) -> None:
    init_db(db_path)
    with connect(db_path) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO gate_inputs (
              input_id, calibration_domain, note, owner, due_date, source_hint,
              output_status, not_final, created_at, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row.get("input_id", ""),
                row.get("calibration_domain", ""),
                row.get("note", ""),
                row.get("owner", ""),
                row.get("due_date", ""),
                row.get("source_hint", ""),
                row.get("output_status", "needs_review"),
                1 if row.get("not_final", True) else 0,
                row.get("created_at", utc_now()),
                json.dumps(row, ensure_ascii=False),
            ),
        )


def list_runtime_uploads(db_path: Path = DB_PATH, limit: int = 200) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM runtime_uploads ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def list_upload_candidates(db_path: Path = DB_PATH, limit: int = 200) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM upload_candidates ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)


def list_gate_inputs(db_path: Path = DB_PATH, limit: int = 200) -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM gate_inputs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return rows_to_dicts(rows)
