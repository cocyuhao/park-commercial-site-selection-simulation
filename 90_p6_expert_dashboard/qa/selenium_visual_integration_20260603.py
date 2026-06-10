from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "40_quality_evidence" / "selenium_visual_integration_20260603"
BASE_URL = "http://127.0.0.1:8000"
FORBIDDEN_VISIBLE = [
    "外部" + "预览",
    "仅地图" + "预览",
    "后端草案分",
    "debug",
    "raw",
    "payload",
    "smoke test",
    "API contract",
    "ConnectError",
    "traceback",
    "needs_review",
    "not_final",
    "external" + "_preview_only",
]


def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--lang=zh-CN")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=options)


def click(wait: WebDriverWait, selector: str) -> None:
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector))).click()


def text_of(driver: webdriver.Chrome, selector: str) -> str:
    els = driver.find_elements(By.CSS_SELECTOR, selector)
    return els[0].text.strip() if els else ""


def set_value(driver: webdriver.Chrome, selector: str, value: str) -> None:
    el = driver.find_element(By.CSS_SELECTOR, selector)
    el.clear()
    el.send_keys(value)


def visible_text_issues(driver: webdriver.Chrome) -> list[str]:
    text = driver.find_element(By.TAG_NAME, "body").text
    return [word for word in FORBIDDEN_VISIBLE if word in text]


def console_errors(driver: webdriver.Chrome) -> list[str]:
    errors: list[str] = []
    try:
        for item in driver.get_log("browser"):
            if item.get("level") in {"SEVERE", "ERROR"}:
                errors.append(item.get("message", ""))
    except Exception as exc:  # pragma: no cover - browser capability dependent
        errors.append(f"log_unavailable: {exc}")
    return errors


def run_round(driver: webdriver.Chrome, round_index: int) -> dict[str, object]:
    wait = WebDriverWait(driver, 15)
    actions: list[str] = []
    failures: list[str] = []
    notes: list[str] = []

    driver.get(BASE_URL)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#overviewStatusCards, #overviewNodeList")))
    actions.append("open_overview")

    click(wait, "[data-view='ai']")
    actions.append("open_ai_workspace")
    badge = text_of(driver, "#aiModeBadge")
    if badge != "项目综合":
        failures.append(f"AI 工作台默认模式异常：{badge}")
    if "桃花源白房子" in driver.find_element(By.TAG_NAME, "body").text:
        failures.append("页面仍出现桃花源白房子")
    click(wait, "#aiRailToggle")
    actions.append("collapse_ai_rail")
    click(wait, "#aiRailToggle")
    actions.append("expand_ai_rail")
    click(wait, "#newAiSessionBtn")
    actions.append("new_ai_session")
    set_value(driver, "#chatInput", "请综合项目资料、地图 POI 和节点缺口，说明目前最需要补什么。 " * 8)
    actions.append("long_text_input")
    composer_height = driver.execute_script("return document.querySelector('#chatInput').getBoundingClientRect().height")
    if not 30 <= float(composer_height) <= 180:
        failures.append(f"输入框高度异常：{composer_height}")
    if not driver.find_elements(By.CSS_SELECTOR, "#generateChatReportBtn") or not driver.find_elements(By.CSS_SELECTOR, "#composerReportBtn"):
        failures.append("生成报告按钮缺失")

    click(wait, "[data-view='nodes']")
    actions.append("open_nodes")
    click(wait, "#quickNewNodeBtn")
    actions.append("new_node_form")
    node_name = f"Codex验证节点R{round_index}"
    set_value(driver, "#nodeNameInput", node_name)
    set_value(driver, "#nodeLocationInput", "Selenium 模拟用户新增的待复核位置")
    set_value(driver, "#nodeBusinessInput", "咖啡、轻餐、便利零售")
    set_value(driver, "#nodeAreaInput", "待测")
    set_value(driver, "#nodeNoteInput", "用于验证节点新增、地图联动和删除。")
    click(wait, "[data-node-save='true']")
    actions.append("save_node")
    wait.until(lambda d: node_name in text_of(d, "#detailTitle") or node_name in d.find_element(By.TAG_NAME, "body").text)
    created_node_id = driver.find_element(By.CSS_SELECTOR, "#nodeEditForm").get_attribute("data-node-id")

    click(wait, "[data-view='map']")
    actions.append("open_map")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#mapResultList")))
    click(wait, "[data-map-mode='poi']")
    actions.append("switch_poi_layer")
    time.sleep(0.25)
    poi_items = driver.find_elements(By.CSS_SELECTOR, "[data-poi-id]")
    if poi_items:
        poi_items[0].click()
        actions.append("select_poi")
    else:
        notes.append("本轮没有可点击 POI，保留为空结果状态。")
    click(wait, "[data-map-mode='nodes']")
    actions.append("switch_node_layer")
    click(wait, "[data-map-mode='all']")
    actions.append("switch_all_layer")

    click(wait, "#assetDrawerBtn")
    actions.append("open_asset_drawer")
    time.sleep(0.1)
    click(wait, "#assetDrawerClose")
    actions.append("close_asset_drawer")

    click(wait, "[data-view='overview']")
    actions.append("back_overview")
    overview_nodes = driver.find_elements(By.CSS_SELECTOR, "#overviewNodeList [data-node-id]")
    if len(overview_nodes) >= 2:
        target = overview_nodes[1].get_attribute("data-node-id")
        overview_nodes[1].click()
        actions.append("overview_node_jump")
        if target not in driver.page_source:
            failures.append("项目总览节点跳转没有保留目标节点 ID")
    else:
        notes.append("概览节点不足两个，跳过第二节点跳转验证。")

    if created_node_id:
        deleted = driver.execute_async_script(
            """
            const done = arguments[arguments.length - 1];
            fetch(`/api/nodes/${encodeURIComponent(arguments[0])}`, { method: "DELETE" })
              .then((response) => done(response.ok))
              .catch(() => done(false));
            """,
            created_node_id,
        )
        actions.append("delete_created_node")
        if not deleted:
            failures.append(f"自动测试节点清理失败：{created_node_id}")

    screenshot = OUT_DIR / f"round_{round_index:02d}.png"
    driver.save_screenshot(str(screenshot))
    issues = visible_text_issues(driver)
    errors = console_errors(driver)
    if issues:
        failures.append(f"可见技术文案未清理：{issues}")
    if errors:
        notes.append(f"console_errors={len(errors)}")

    return {
        "round": round_index,
        "action_count": len(actions),
        "actions": actions,
        "failures": failures,
        "screenshot": str(screenshot),
        "visible_text_issues": issues,
        "console_errors": errors,
        "human_visual_notes": notes,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    driver = make_driver()
    try:
      for index in range(1, 11):
          results.append(run_round(driver, index))
    finally:
      driver.quit()

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "base_url": BASE_URL,
        "round_count": len(results),
        "failure_count": sum(len(item["failures"]) for item in results),
        "results": results,
    }
    out = OUT_DIR / "selenium_visual_integration_20260603.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    print(json.dumps({"round_count": payload["round_count"], "failure_count": payload["failure_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
