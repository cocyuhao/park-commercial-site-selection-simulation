"""
DeepSeek API 综合验证脚本 (Python 3.12)

验证方法:
  M1 - HTTP层连通性与延迟探测 (httpx, 5次采样, P50/P95统计)
  M2 - 模型列表端点验证 (GET /v1/models, 鉴权检查)
  M3 - JSON输出格式一致性测试 (3次重复请求, temperature=0)
  M4 - 历史分类样本重现性验证 (与 deepseek_table_classification_raw.jsonl 对比)

输出: 40_quality_evidence/verify_deepseek_api_report.json
      40_quality_evidence/postman_deepseek_collection.json
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "60_model" / "src"))

from llm_router import load_local_env  # noqa: E402

OUT_DIR = ROOT / "40_quality_evidence"
REPORT_FILE = OUT_DIR / "verify_deepseek_api_report.json"
POSTMAN_FILE = OUT_DIR / "postman_deepseek_collection.json"
RAW_JSONL = ROOT / "60_model" / "llm_runs" / "deepseek_table_classification_raw.jsonl"
CLASSIFICATION_CSV = ROOT / "30_extraction" / "tables" / "pdf_native_tables_summary.csv"

BASE_URL = "https://api.deepseek.com"
CHAT_URL = f"{BASE_URL}/v1/chat/completions"
MODELS_URL = f"{BASE_URL}/v1/models"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _get_api_key() -> str:
    load_local_env()
    key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY not set in .env")
    return key


def _masked(key: str) -> str:
    """Mask key for safe logging: sk-...last4."""
    if len(key) < 10:
        return "***"
    return f"{key[:5]}...{key[-4:]}"


def _extract_json_array(text: str) -> list[dict]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped, flags=re.IGNORECASE).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    start = stripped.find("[")
    end = stripped.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in response")
    return json.loads(stripped[start: end + 1])


# ---------------------------------------------------------------------------
# M1 - HTTP层连通性与延迟探测
# ---------------------------------------------------------------------------

def method1_http_latency(api_key: str) -> dict:
    """5次轻量级请求, 统计P50/P95延迟, 检查HTTP状态码和响应头."""
    print("\n[M1] HTTP层延迟探测 (5次采样)...")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
        "temperature": 0.0,
    }

    latencies_ms: list[float] = []
    status_codes: list[int] = []
    errors: list[str] = []

    for i in range(5):
        try:
            t0 = time.perf_counter()
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(CHAT_URL, headers=headers, json=payload)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            latencies_ms.append(elapsed_ms)
            status_codes.append(resp.status_code)
            print(f"  Probe {i+1}/5: HTTP {resp.status_code}, {elapsed_ms:.0f} ms")
        except Exception as exc:
            errors.append(str(exc))
            print(f"  Probe {i+1}/5: ERROR - {exc}")

    result = {
        "method": "M1_http_latency",
        "description": "HTTP层连通性与延迟探测",
        "probes": 5,
        "errors": errors,
        "status_codes": status_codes,
    }
    if latencies_ms:
        result["latency_ms"] = {
            "min": round(min(latencies_ms), 1),
            "max": round(max(latencies_ms), 1),
            "mean": round(statistics.mean(latencies_ms), 1),
            "p50": round(statistics.median(latencies_ms), 1),
            "p95": round(sorted(latencies_ms)[int(len(latencies_ms) * 0.95)], 1),
        }
        all_2xx = all(200 <= c < 300 for c in status_codes)
        result["verdict"] = "PASS" if all_2xx and not errors else "WARN"
        result["verdict_detail"] = (
            f"全部{len(status_codes)}次HTTP 2xx, 均值延迟{result['latency_ms']['mean']}ms"
            if all_2xx else f"存在非2xx状态码: {status_codes}"
        )
    else:
        result["verdict"] = "FAIL"
        result["verdict_detail"] = f"全部请求失败: {errors}"

    print(f"  => {result['verdict']}: {result.get('verdict_detail', '')}")
    return result


# ---------------------------------------------------------------------------
# M2 - 模型列表端点验证
# ---------------------------------------------------------------------------

def method2_models_endpoint(api_key: str) -> dict:
    """GET /v1/models, 验证鉴权、返回可用模型列表."""
    print("\n[M2] 模型列表端点验证 (GET /v1/models)...")
    headers = {"Authorization": f"Bearer {api_key}"}
    result = {
        "method": "M2_models_endpoint",
        "description": "GET /v1/models 鉴权与可用模型验证",
    }
    try:
        t0 = time.perf_counter()
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(MODELS_URL, headers=headers)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        result["http_status"] = resp.status_code
        result["latency_ms"] = round(elapsed_ms, 1)

        if resp.status_code == 200:
            data = resp.json()
            model_ids = [m.get("id", "") for m in data.get("data", [])]
            result["model_count"] = len(model_ids)
            result["model_ids"] = model_ids
            deepseek_models = [m for m in model_ids if "deepseek" in m.lower()]
            result["deepseek_models_found"] = deepseek_models
            result["verdict"] = "PASS"
            result["verdict_detail"] = f"发现{len(model_ids)}个模型, deepseek系列: {deepseek_models}"
            print(f"  HTTP {resp.status_code}: {len(model_ids)}个模型")
            for mid in model_ids:
                print(f"    - {mid}")
        elif resp.status_code == 401:
            result["verdict"] = "FAIL"
            result["verdict_detail"] = "鉴权失败(401), API Key无效"
            print(f"  HTTP 401: 鉴权失败")
        else:
            result["verdict"] = "WARN"
            result["verdict_detail"] = f"非预期状态码: {resp.status_code}"
            print(f"  HTTP {resp.status_code}: 非预期")
    except Exception as exc:
        result["verdict"] = "FAIL"
        result["verdict_detail"] = f"请求异常: {exc}"
        print(f"  ERROR: {exc}")

    print(f"  => {result['verdict']}: {result.get('verdict_detail', '')}")
    return result


# ---------------------------------------------------------------------------
# M3 - JSON输出格式一致性 (3次重复, temperature=0)
# ---------------------------------------------------------------------------

def method3_json_consistency(api_key: str) -> dict:
    """3次相同输入请求, temperature=0, 验证JSON格式、字段完整性、答案一致性."""
    print("\n[M3] JSON输出格式一致性测试 (3次重复, temperature=0)...")

    required_fields = {"table_id", "topic_draft", "topic_confidence", "reason_draft",
                       "evidence_keywords_draft", "output_status"}
    allowed_topics = {
        "visitor_flow", "time_peak", "demographic_profile", "origin_residence_work",
        "tgi_preference", "poi_hot_visit", "consumption_spending", "commercial_supply",
        "revenue_finance", "supply_gap", "empty_or_visual_noise", "other",
    }

    test_item = {
        "table_id": "TEST-001",
        "source_file": "test.pdf",
        "page": "7",
        "row_count": "11",
        "column_count": "6",
        "sample": (
            "排名 / 工作地名称 / 占比 / 排名 / 居住地名称 / 占比 | "
            "1 / 北京东光实业总公司 / 39.45% / 1 / 环湖小镇西区 / 4.379% | "
            "2 / 通州区出入境检验检疫局 / 14.679% / 2 / 北许场新村 / 4.096%"
        ),
    }

    allowed = ", ".join(sorted(allowed_topics))
    messages = [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的低成本批处理助手。"
                "只输出 JSON 数组，不要输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请对以下 PDF 原生表格摘要做主题分类草稿。\n"
                f"允许 topic 只能从这些值中选择：{allowed}。\n"
                "每个输入必须输出一条，字段为："
                "table_id, topic_draft, topic_confidence, reason_draft, evidence_keywords_draft, output_status。\n"
                "topic_confidence 只能是 low/medium/high；output_status 必须是 draft。\n"
                "输入 JSON：\n"
                + json.dumps([test_item], ensure_ascii=False)
            ),
        },
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    chat_payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.0,
    }

    runs: list[dict] = []
    topics_seen: list[str] = []

    for i in range(3):
        run: dict = {"run": i + 1}
        try:
            t0 = time.perf_counter()
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(CHAT_URL, headers=headers, json=chat_payload)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            run["latency_ms"] = round(elapsed_ms, 1)
            run["http_status"] = resp.status_code

            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"]
                items = _extract_json_array(content)
                if items:
                    item = items[0]
                    missing = required_fields - set(item.keys())
                    run["fields_ok"] = len(missing) == 0
                    run["missing_fields"] = list(missing)
                    topic = item.get("topic_draft", "")
                    run["topic_draft"] = topic
                    run["topic_valid"] = topic in allowed_topics
                    run["output_status"] = item.get("output_status", "")
                    run["output_status_ok"] = item.get("output_status") == "draft"
                    topics_seen.append(topic)
                    run["parse_ok"] = True
                    print(f"  Run {i+1}/3: topic={topic!r}, confidence={item.get('topic_confidence')}, {elapsed_ms:.0f}ms")
                else:
                    run["parse_ok"] = False
                    run["error"] = "empty JSON array"
                    print(f"  Run {i+1}/3: empty array, {elapsed_ms:.0f}ms")
            else:
                run["parse_ok"] = False
                run["error"] = f"HTTP {resp.status_code}"
                print(f"  Run {i+1}/3: HTTP {resp.status_code}")
        except Exception as exc:
            run["parse_ok"] = False
            run["error"] = str(exc)
            print(f"  Run {i+1}/3: ERROR - {exc}")
        runs.append(run)

    consistent = len(set(topics_seen)) == 1 if len(topics_seen) > 1 else (len(topics_seen) == 1)
    all_ok = all(r.get("parse_ok") and r.get("fields_ok") and r.get("output_status_ok") for r in runs)

    result = {
        "method": "M3_json_consistency",
        "description": "3次相同输入, temperature=0, JSON格式和答案一致性",
        "runs": runs,
        "topics_seen": topics_seen,
        "consistent_topic": consistent,
        "all_fields_ok": all_ok,
        "verdict": "PASS" if consistent and all_ok else ("WARN" if topics_seen else "FAIL"),
        "verdict_detail": (
            f"3次结果topic一致={consistent}, 字段完整={all_ok}, topics={topics_seen}"
        ),
    }
    print(f"  => {result['verdict']}: {result['verdict_detail']}")
    return result


# ---------------------------------------------------------------------------
# M4 - 历史分类样本重现性验证
# ---------------------------------------------------------------------------

def method4_historical_consistency(api_key: str) -> dict:
    """
    从历史 deepseek_table_classification_raw.jsonl 中取 5 个非噪声样本,
    重新分类, 计算与历史 topic_draft 的一致率.
    """
    print("\n[M4] 历史分类样本重现性验证 (抽样5条, 重新分类对比)...")

    result: dict = {
        "method": "M4_historical_consistency",
        "description": "从历史JSONL抽取样本, 重新分类, 与历史结果对比",
    }

    if not RAW_JSONL.exists():
        result["verdict"] = "SKIP"
        result["verdict_detail"] = f"历史JSONL不存在: {RAW_JSONL}"
        print(f"  SKIP: {result['verdict_detail']}")
        return result

    # 解析历史分类结果
    historical: dict[str, str] = {}
    lines = RAW_JSONL.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        obj = json.loads(line)
        excerpt = obj.get("response_excerpt", "")
        try:
            items = _extract_json_array(excerpt)
            for item in items:
                tid = item.get("table_id", "")
                topic = item.get("topic_draft", "")
                if tid and topic and topic != "empty_or_visual_noise":
                    historical[tid] = topic
        except Exception:
            pass

    print(f"  历史记录: {len(historical)} 条非噪声分类")

    if not historical:
        result["verdict"] = "SKIP"
        result["verdict_detail"] = "历史JSONL无可用非噪声样本"
        print(f"  SKIP: {result['verdict_detail']}")
        return result

    # 读取对应的摘要CSV
    import csv as csv_module
    if not CLASSIFICATION_CSV.exists():
        result["verdict"] = "SKIP"
        result["verdict_detail"] = f"摘要CSV不存在: {CLASSIFICATION_CSV}"
        return result

    with CLASSIFICATION_CSV.open(encoding="utf-8-sig", newline="") as f:
        all_rows = {r["table_id"]: r for r in csv_module.DictReader(f)}

    # 取前5个有历史记录的表
    sample_ids = [tid for tid in list(historical.keys())[:5] if tid in all_rows]
    if not sample_ids:
        result["verdict"] = "SKIP"
        result["verdict_detail"] = "无法在摘要CSV中找到历史样本"
        return result

    print(f"  抽样 {len(sample_ids)} 条: {sample_ids}")

    allowed_topics = {
        "visitor_flow", "time_peak", "demographic_profile", "origin_residence_work",
        "tgi_preference", "poi_hot_visit", "consumption_spending", "commercial_supply",
        "revenue_finance", "supply_gap", "empty_or_visual_noise", "other",
    }
    allowed = ", ".join(sorted(allowed_topics))

    def compact(row: dict) -> dict:
        sample = re.sub(r"\s+", " ", str(row.get("sample", "") or "")).strip()
        return {
            "table_id": row.get("table_id", ""),
            "source_file": Path(row.get("source_file", "")).name,
            "page": row.get("page", ""),
            "row_count": row.get("row_count", ""),
            "column_count": row.get("column_count", ""),
            "sample": sample[:360],
        }

    sample_items = [compact(all_rows[tid]) for tid in sample_ids]
    messages = [
        {
            "role": "system",
            "content": (
                "你是公园商业选址项目的低成本批处理助手。"
                "只输出 JSON 数组，不要输出 Markdown。"
            ),
        },
        {
            "role": "user",
            "content": (
                "请对以下 PDF 原生表格摘要做主题分类草稿。\n"
                f"允许 topic 只能从这些值中选择：{allowed}。\n"
                "每个输入必须输出一条，字段为："
                "table_id, topic_draft, topic_confidence, reason_draft, evidence_keywords_draft, output_status。\n"
                "topic_confidence 只能是 low/medium/high；output_status 必须是 draft。\n"
                "输入 JSON：\n"
                + json.dumps(sample_items, ensure_ascii=False)
            ),
        },
    ]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    chat_payload = {"model": "deepseek-chat", "messages": messages, "temperature": 0.0}

    comparisons: list[dict] = []
    try:
        t0 = time.perf_counter()
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(CHAT_URL, headers=headers, json=chat_payload)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        result["latency_ms"] = round(elapsed_ms, 1)
        result["http_status"] = resp.status_code

        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            new_items = _extract_json_array(content)
            new_by_id = {item["table_id"]: item.get("topic_draft", "") for item in new_items if "table_id" in item}

            for tid in sample_ids:
                old_topic = historical[tid]
                new_topic = new_by_id.get(tid, "NOT_RETURNED")
                match = old_topic == new_topic
                comparisons.append({
                    "table_id": tid,
                    "historical_topic": old_topic,
                    "new_topic": new_topic,
                    "match": match,
                })
                icon = "OK" if match else "DIFF"
                print(f"  {icon} {tid}: hist={old_topic!r}, new={new_topic!r}")

            match_count = sum(1 for c in comparisons if c["match"])
            agreement_rate = match_count / len(comparisons) if comparisons else 0.0
            result["comparisons"] = comparisons
            result["agreement_rate"] = round(agreement_rate, 3)
            result["match_count"] = match_count
            result["total"] = len(comparisons)
            result["verdict"] = "PASS" if agreement_rate >= 0.8 else ("WARN" if agreement_rate >= 0.6 else "FAIL")
            result["verdict_detail"] = (
                f"一致率 {match_count}/{len(comparisons)} = {agreement_rate:.1%}, "
                f"{elapsed_ms:.0f}ms"
            )
        else:
            result["verdict"] = "FAIL"
            result["verdict_detail"] = f"HTTP {resp.status_code}"
    except Exception as exc:
        result["verdict"] = "FAIL"
        result["verdict_detail"] = f"异常: {exc}"
        print(f"  ERROR: {exc}")

    print(f"  => {result['verdict']}: {result.get('verdict_detail', '')}")
    return result


# ---------------------------------------------------------------------------
# Postman Collection 生成
# ---------------------------------------------------------------------------

def generate_postman_collection(api_key: str) -> dict:
    """生成 Postman v2.1 collection JSON 供手动导入测试."""
    masked_key = _masked(api_key)
    collection = {
        "info": {
            "name": "DeepSeek API - 仿真设计项目验证",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {
                "key": "base_url",
                "value": "https://api.deepseek.com",
                "type": "string",
            },
            {
                "key": "api_key",
                "value": f"<填入真实Key, 当前masked={masked_key}>",
                "type": "string",
            },
        ],
        "item": [
            {
                "name": "1. 获取模型列表",
                "request": {
                    "method": "GET",
                    "url": "{{base_url}}/v1/models",
                    "header": [
                        {"key": "Authorization", "value": "Bearer {{api_key}}"},
                    ],
                },
            },
            {
                "name": "2. 连通性探测 (max_tokens=1)",
                "request": {
                    "method": "POST",
                    "url": "{{base_url}}/v1/chat/completions",
                    "header": [
                        {"key": "Authorization", "value": "Bearer {{api_key}}"},
                        {"key": "Content-Type", "value": "application/json"},
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "model": "deepseek-chat",
                            "messages": [{"role": "user", "content": "hi"}],
                            "max_tokens": 1,
                            "temperature": 0.0,
                        }, ensure_ascii=False, indent=2),
                        "options": {"raw": {"language": "json"}},
                    },
                },
            },
            {
                "name": "3. 表格分类 smoke test",
                "request": {
                    "method": "POST",
                    "url": "{{base_url}}/v1/chat/completions",
                    "header": [
                        {"key": "Authorization", "value": "Bearer {{api_key}}"},
                        {"key": "Content-Type", "value": "application/json"},
                    ],
                    "body": {
                        "mode": "raw",
                        "raw": json.dumps({
                            "model": "deepseek-chat",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": "只输出 JSON 数组，不要输出 Markdown。",
                                },
                                {
                                    "role": "user",
                                    "content": (
                                        "请对以下 PDF 原生表格摘要做主题分类草稿。\n"
                                        "输入 JSON：\n"
                                        + json.dumps([{
                                            "table_id": "TBL-00003",
                                            "source_file": "城市绿心.pdf",
                                            "page": "7",
                                            "row_count": "11",
                                            "column_count": "6",
                                            "sample": "排名 / 工作地名称 / 占比 | 1 / 北京东光实业 / 39.45%",
                                        }], ensure_ascii=False)
                                    ),
                                },
                            ],
                            "temperature": 0.0,
                        }, ensure_ascii=False, indent=2),
                        "options": {"raw": {"language": "json"}},
                    },
                },
            },
        ],
    }
    return collection


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("DeepSeek API 综合验证 (4种方法)")
    print("=" * 60)

    api_key = _get_api_key()
    print(f"API Key: {_masked(api_key)}")

    run_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    results: list[dict] = []

    results.append(method1_http_latency(api_key))
    results.append(method2_models_endpoint(api_key))
    results.append(method3_json_consistency(api_key))
    results.append(method4_historical_consistency(api_key))

    # 汇总
    verdicts = [r.get("verdict", "UNKNOWN") for r in results]
    pass_count = sum(1 for v in verdicts if v == "PASS")
    fail_count = sum(1 for v in verdicts if v == "FAIL")
    overall = "PASS" if fail_count == 0 else ("WARN" if pass_count > 0 else "FAIL")

    report = {
        "run_at": run_at,
        "api_key_masked": _masked(api_key),
        "overall_verdict": overall,
        "summary": {
            "PASS": pass_count,
            "WARN": sum(1 for v in verdicts if v == "WARN"),
            "FAIL": fail_count,
            "SKIP": sum(1 for v in verdicts if v == "SKIP"),
        },
        "methods": results,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n报告已写入: {REPORT_FILE}")

    # 生成 Postman collection
    postman = generate_postman_collection(api_key)
    POSTMAN_FILE.write_text(json.dumps(postman, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Postman集合已写入: {POSTMAN_FILE}")

    print(f"\n总体结果: {overall}  (PASS={pass_count}, FAIL={fail_count})")
    print("=" * 60)

    if fail_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
