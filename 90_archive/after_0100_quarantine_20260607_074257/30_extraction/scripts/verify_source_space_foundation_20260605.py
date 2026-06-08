from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "40_quality_evidence" / "source_space_foundation_validation_20260605.json"
OUT_MD = ROOT / "40_quality_evidence" / "source_space_foundation_validation_20260605.md"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def contains_all(text: str, terms: list[str]) -> dict[str, object]:
    missing = [term for term in terms if term not in text]
    return {"passed": not missing, "missing": missing, "terms": terms}


def load_dashboard_payload() -> dict[str, object]:
    sys.path.insert(0, str(ROOT / "90_p6_expert_dashboard"))
    import app  # type: ignore

    return app.load_dashboard()


def main() -> None:
    index_html = read("90_p6_expert_dashboard/static/index.html")
    app_js = read("90_p6_expert_dashboard/static/app.js")
    styles_css = read("90_p6_expert_dashboard/static/styles.css")
    dashboard = load_dashboard_payload()
    preflight = dashboard.get("simulation_task_preflight") or {}
    amap = dashboard.get("amap") or {}
    uploads = dashboard.get("uploads") or []
    assets = preflight.get("local_data_assets") or []
    asset_labels = {asset.get("label") for asset in assets if isinstance(asset, dict)}
    required_asset_labels = {
        "证据台账",
        "PDF 原生表格",
        "高德 POI 候选",
        "CAD / 图纸资料",
        "老板方法资料",
        "人物仿真覆盖池",
    }
    banned_visible_tokens = [
        "raw json",
        "payload",
        "debug",
        "traceback",
        "ConnectError",
        "smoke test",
        "API contract",
        "external_preview_only",
        "needs_review",
        "not_final",
        "validation_status",
    ]
    foundation_js_start = app_js.find("function renderSourceFoundation")
    foundation_js_end = app_js.find("function renderCandidateList")
    foundation_js = app_js[foundation_js_start:foundation_js_end]
    visible_surface = "\n".join([index_html, foundation_js, styles_css])

    checks: list[dict[str, object]] = [
        {
            "id": "SOURCE_FOUNDATION_UI_EXISTS",
            **contains_all(
                index_html,
                [
                    "sourceFoundationSummary",
                    "localDataAssets",
                    "资料与空间底座",
                    "先把真实资料放到同一张工作台",
                    "查看预检",
                ],
            ),
        },
        {
            "id": "SOURCE_FOUNDATION_RENDERER_EXISTS",
            **contains_all(
                app_js,
                [
                    "function renderSourceFoundation",
                    "local_data_assets",
                    "map_context",
                    "进入对象",
                    "使用边界",
                    "DeepSeek 只能生成候选",
                ],
            ),
        },
        {
            "id": "MAP_ENGINE_LAZY_ON_NON_MAP_VIEWS",
            "passed": 'if (state.currentView === "map") {' in app_js
            and 'if (view === "map" && state.data)' in app_js
            and 'renderSourceFoundation();' in app_js,
            "evidence": {
                "render_all_map_guard_count": app_js.count('if (state.currentView === "map") {'),
                "set_view_map_guard_count": app_js.count('if (view === "map" && state.data)'),
            },
        },
        {
            "id": "SOURCE_FOUNDATION_VISUAL_SYSTEM_EXISTS",
            **contains_all(
                styles_css,
                [
                    ".source-foundation-panel",
                    ".source-foundation-summary",
                    ".local-data-assets-head",
                    ".local-data-asset-grid",
                    ".local-data-asset-card",
                    ".foundation-next-steps",
                ],
            ),
        },
        {
            "id": "LOCAL_ASSETS_BACKEND_PRESENT",
            "passed": len(assets) >= 8 and required_asset_labels.issubset(asset_labels),
            "evidence": {
                "asset_count": len(assets),
                "required": sorted(required_asset_labels),
                "found": sorted(str(label) for label in asset_labels),
            },
        },
        {
            "id": "SPACE_CONTEXT_PRESENT_BUT_REVIEW_BOUNDARY_VISIBLE",
            "passed": bool(amap.get("map_context")) and bool(amap.get("supply_points")) and "不替代授权" in app_js,
            "evidence": {
                "has_map_context": bool(amap.get("map_context")),
                "poi_count": len(amap.get("supply_points") or []),
                "boundary_phrase_in_renderer": "不替代授权" in app_js,
            },
        },
        {
            "id": "UPLOAD_POOL_STILL_AVAILABLE",
            "passed": isinstance(uploads, list) and "uploadList" in index_html and "renderUploadList" in app_js,
            "evidence": {"upload_count": len(uploads)},
        },
        {
            "id": "NO_INTERNAL_TOKENS_IN_VISIBLE_FOUNDATION_SURFACE",
            "passed": not [token for token in banned_visible_tokens if token in visible_surface],
            "evidence": {
                "banned_tokens_found": [token for token in banned_visible_tokens if token in visible_surface],
            },
        },
        {
            "id": "CACHE_BUSTER_UPDATED_FOR_FOUNDATION_SLICE",
            "passed": "20260605-foundation" in index_html and "20260605-workflow" not in index_html,
            "evidence": {
                "foundation_version_count": index_html.count("20260605-foundation"),
                "old_workflow_version_count": index_html.count("20260605-workflow"),
            },
        },
    ]

    failure_count = sum(1 for check in checks if not check["passed"])
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if failure_count == 0 else "fail",
        "scope": "验证资料与空间底座切片已从旧资料导入页升级为仿真输入工作区；不证明完整仿真已经完成。",
        "checks": checks,
        "failure_count": failure_count,
        "backend_asset_count": len(assets),
        "backend_upload_count": len(uploads),
        "backend_poi_count": len(amap.get("supply_points") or []),
        "source_files": [
            "90_p6_expert_dashboard/static/index.html",
            "90_p6_expert_dashboard/static/app.js",
            "90_p6_expert_dashboard/static/styles.css",
            "90_p6_expert_dashboard/app.py",
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 资料与空间底座验证 2026-06-05",
        "",
        f"- 状态：{payload['status']}",
        f"- 失败数：{failure_count}",
        f"- 后端底座资产：{len(assets)} 类",
        f"- 后端上传资料：{len(uploads)} 份",
        f"- 后端 POI 线索：{len(amap.get('supply_points') or [])} 条",
        f"- 范围：{payload['scope']}",
        "",
        "## 检查项",
    ]
    for check in checks:
        mark = "PASS" if check["passed"] else "FAIL"
        lines.append(f"- {mark} `{check['id']}`")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": payload["status"], "failure_count": failure_count}, ensure_ascii=False))


if __name__ == "__main__":
    main()
