from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import route_for, run_deepseek_task  # noqa: E402


OUT_DIR = ROOT / "60_model" / "llm_runs"
OUT_FILE = OUT_DIR / "deepseek_smoke_test_latest.json"


def main() -> None:
    task_id = "LLM-001"
    route = route_for(task_id)
    messages = [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的低成本批处理助手。"
                "只输出 JSON，不做最终结论。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请把这段页面文本分类到一个主题："
                "页面内容：游客到访峰值、咖啡 TGI、热门到访 POI、人均消费。"
                "可选主题：客流、画像、TGI、POI、消费、收益、缺口。"
                "输出字段：topic, reason, output_status。"
            ),
        },
    ]
    payload = {
        "run_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "task_id": task_id,
        "task_name": route.task_name,
        "executor": route.default_executor,
        "model": route.model,
        "expected_output_status": route.output_status,
        "status": "started",
    }
    try:
        content = run_deepseek_task(task_id, messages, temperature=0.0)
        payload.update(
            {
                "status": "ok",
                "response_excerpt": content[:1000],
                "notes": "Real DeepSeek API call succeeded. Output remains draft and is not evidence.",
            }
        )
    except Exception as exc:
        payload.update(
            {
                "status": "error",
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "notes": "No secret value is stored in this report.",
            }
        )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"status={payload['status']}")
    print(f"wrote={OUT_FILE}")
    if payload["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
