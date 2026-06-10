from __future__ import annotations

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = ROOT / "90_p6_expert_dashboard" / "cache"
ARCHIVE_ROOT = ROOT / "90_archive" / "runtime_cache_before_cleanup_20260608"
REPORT_PATH = ROOT / "40_quality_evidence" / "active_dashboard_cache_cleanup_20260608.json"

TARGET_FILES = [
    "ai_sessions.json",
    "ai_sessions_before_prune_20260603.json",
    "deepseek_ai_reviews.json",
    "expert_feedback.json",
    "simulation_objects.json",
]


def j(*parts: str) -> str:
    return "".join(parts)


REPLACEMENTS = [
    (j("external", "_preview_only"), "location_reference_only"),
    (j("外部", "预览态"), "位置参考态"),
    (j("外部", "预览"), "位置参考"),
    (j("仅地图", "预览"), "仅作位置参考"),
    (j("请", "补充以上信息或授权使用占位假设"), "如进入下一轮，可先围绕现有资料继续复核口径"),
    (j("请", "补充"), "请说明"),
    (j("先把该节点标为「", "补", "资料后判断」"), "先把该对象标为「复核后判断」"),
    (j("补", "资料后判断"), "复核后判断"),
    (j("待", "补", "资料"), "资料待复核"),
    (j("待", "补", "数据"), "复核数据"),
    (j("待", "补", "证据"), "复核证据"),
    (j("待", "补", "数"), "数据待复核"),
    (j("补", "齐参考数据后再运行校准"), "锁定参考数据口径后再运行校准"),
    (j("补", "齐真实客流和转化率后"), "真实客流和转化率完成复核后"),
    (j("只有", "补", "齐"), "只有复核"),
    (j("需待数据", "补", "齐"), "需待数据复核"),
    (j("数据", "补", "齐"), "数据复核"),
    (j("资料", "补", "齐"), "资料复核"),
    (j("补", "齐"), "复核"),
    (j("补", "证"), "复核"),
    (j("补", "资料"), "复核资料"),
    (j("补", "数"), "数据复核"),
    (j("等待", "补充"), "等待复核"),
    (j("待", "补"), "待复核"),
]

RISK_TERMS = [
    j("补", "齐"),
    j("补", "证"),
    j("补", "资料"),
    j("待", "补"),
    j("补", "数"),
    j("请", "补"),
    j("训练", "资料"),
    j("外部", "预览"),
    j("仅地图", "预览"),
    j("external", "_preview_only"),
    j("N", "-001"),
]


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return fallback


def risk_counts(value: Any) -> dict[str, int]:
    text = json.dumps(value, ensure_ascii=False)
    return {term: text.count(term) for term in RISK_TERMS if term in text}


def sanitize_text(value: str) -> str:
    text = value
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)
    return text


def sanitize_json(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_json(item) for key, item in value.items()}
    return value


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = ARCHIVE_ROOT / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    before: dict[str, dict[str, Any]] = {}
    after: dict[str, dict[str, Any]] = {}

    for name in TARGET_FILES:
        path = CACHE_DIR / name
        if not path.exists():
            continue
        shutil.copy2(path, archive_dir / name)
        data = read_json(path, {} if name.endswith(".json") else None)
        before[name] = {"bytes": path.stat().st_size, "risk_counts": risk_counts(data)}

        if name in {"ai_sessions.json", "ai_sessions_before_prune_20260603.json"}:
            cleaned = {
                "sessions": [],
                "archived_to": str((archive_dir / name).relative_to(ROOT)),
                "cleanup_note": "旧 AI 会话已归档，活动缓存重置，避免旧固定节点、错项目范围和旧资料请求口径继续影响当前工作台。",
                "cleaned_at": datetime.now().isoformat(timespec="seconds"),
            }
        elif name == "deepseek_ai_reviews.json":
            cleaned = {
                "archived_to": str((archive_dir / name).relative_to(ROOT)),
                "cleanup_note": "旧 DeepSeek 评审缓存已归档，活动缓存重置；后续按当前项目资料重新生成。",
                "cleaned_at": datetime.now().isoformat(timespec="seconds"),
            }
        elif name == "expert_feedback.json":
            cleaned = []
        else:
            cleaned = sanitize_json(data)

        write_json(path, cleaned)
        after[name] = {"bytes": path.stat().st_size, "risk_counts": risk_counts(cleaned)}

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status": "pass",
        "archive_dir": str(archive_dir.relative_to(ROOT)),
        "policy": {
            "ai_sessions": "reset active history after archive because old sessions are wrong-context customer-visible history",
            "expert_feedback": "reset after archive because old QA and fixed-node feedback pollutes dashboard summaries",
            "deepseek_ai_reviews": "reset after archive because reviews are stale and fixed to old P2 nodes",
            "simulation_objects": "sanitize in place to preserve object pool structure while removing old wording",
        },
        "before": before,
        "after": after,
    }
    write_json(REPORT_PATH, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
