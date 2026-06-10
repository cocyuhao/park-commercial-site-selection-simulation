import { startFlow } from "lighthouse";
import { launch } from "chrome-launcher";
import puppeteer from "puppeteer-core";
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import net from "node:net";
import path from "node:path";

const ROOT = path.resolve("../..");
const OUT_DIR = path.join(ROOT, "40_quality_evidence", "lighthouse_user_flow_20260605");
const OUT_JSON = path.join(ROOT, "40_quality_evidence", "lighthouse_user_flow_20260605.json");
const OUT_HTML = path.join(OUT_DIR, "p6_dashboard_user_flow.html");

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      const port = typeof address === "object" && address ? address.port : 0;
      server.close(() => resolve(port));
    });
    server.on("error", reject);
  });
}

async function waitForServer(baseUrl, serverProcess, timeoutMs = 22000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = "";
  while (Date.now() < deadline) {
    if (serverProcess.exitCode !== null) {
      throw new Error(`uvicorn exited early: ${serverProcess.exitCode}`);
    }
    try {
      const response = await fetch(`${baseUrl}/api/dashboard`);
      if (response.ok) return;
      lastError = `status=${response.status}`;
    } catch (error) {
      lastError = `${error.name}: ${error.message}`;
    }
    await new Promise((resolve) => setTimeout(resolve, 350));
  }
  throw new Error(`server not ready: ${lastError}`);
}

async function waitForText(page, text) {
  await page.waitForFunction(
    (expected) => document.body.innerText.includes(expected),
    { timeout: 8000 },
    text
  );
}

async function waitForActiveView(page, viewId) {
  await page.waitForSelector(`#${viewId}.view.active`, { timeout: 8000 });
}

function stepScores(flowResult) {
  return flowResult.steps.map((step) => {
    const categories = step.lhr.categories || {};
    return {
      name: step.name,
      gather_mode: step.lhr.gatherMode,
      final_url: step.lhr.finalDisplayedUrl,
      scores: Object.fromEntries(
        Object.entries(categories).map(([key, value]) => [key, value.score])
      ),
      warning_count: (step.lhr.runWarnings || []).length,
    };
  });
}

function check(name, passed, evidence) {
  return { name, passed: Boolean(passed), evidence };
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const appPort = await freePort();
  const baseUrl = `http://127.0.0.1:${appPort}`;
  const server = spawn(
    "py",
    ["-3.12", "-m", "uvicorn", "app:app", "--app-dir", "90_p6_expert_dashboard", "--host", "127.0.0.1", "--port", String(appPort), "--log-level", "warning"],
    { cwd: ROOT, stdio: ["ignore", "pipe", "pipe"] }
  );
  let stderr = "";
  server.stderr.on("data", (chunk) => { stderr += chunk.toString(); });

  let chrome;
  let browser;
  try {
    await waitForServer(baseUrl, server);
    chrome = await launch({
      chromeFlags: [
        "--headless=new",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--no-first-run",
      ],
      logLevel: "error",
    });
    browser = await puppeteer.connect({
      browserURL: `http://127.0.0.1:${chrome.port}`,
      defaultViewport: { width: 1440, height: 1000 },
    });
    const page = await browser.newPage();
    const flow = await startFlow(page, {
      name: "P6 全局仿真工作台主用户流",
      flags: {
        throttlingMethod: "provided",
      },
    });

    await flow.navigate(baseUrl, { name: "打开全局推进台" });
    await waitForText(page, "全局仿真链路台");

    await flow.startTimespan({ name: "切换 AI、资料池、节点与报告" });
    await page.click("#headerAiBtn");
    await waitForActiveView(page, "aiWorkspaceView");
    await waitForText(page, "专家 AI 工作台");
    await page.type("#chatInput", "请基于当前全局对象链，说明下一步应优先复核哪些变量。");
    await page.click("#assetDrawerBtn");
    await waitForText(page, "当前资料池");
    await page.click("#assetDrawerClose");
    await page.click("button.side-nav-item[data-view='nodes']");
    await waitForActiveView(page, "nodesView");
    await waitForText(page, "节点清单");
    await page.click("button.side-nav-item[data-view='report']");
    await waitForActiveView(page, "reportView");
    await flow.endTimespan();

    await flow.snapshot({ name: "报告页与资料池状态快照" });
    const flowResult = await flow.createFlowResult();
    const html = await flow.generateReport();
    await writeFile(OUT_HTML, html, "utf8");

    const scores = stepScores(flowResult);
    const accessibilityScores = scores
      .map((step) => step.scores.accessibility)
      .filter((score) => typeof score === "number");
    const bestPracticeScores = scores
      .map((step) => step.scores["best-practices"])
      .filter((score) => typeof score === "number");
    const performanceScores = scores
      .filter((step) => step.gather_mode !== "snapshot")
      .map((step) => step.scores.performance)
      .filter((score) => typeof score === "number");
    const snapshotPerformanceScores = scores
      .filter((step) => step.gather_mode === "snapshot")
      .map((step) => step.scores.performance)
      .filter((score) => typeof score === "number");
    const checks = [
      check("flow_has_three_steps", scores.length === 3, scores.map((step) => step.name)),
      check("accessibility_scores_present", accessibilityScores.length >= 2, accessibilityScores),
      check("accessibility_minimum_090", accessibilityScores.every((score) => score >= 0.9), accessibilityScores),
      check("best_practices_scores_present", bestPracticeScores.length >= 2, bestPracticeScores),
      check("performance_scores_recorded", performanceScores.length >= 1, performanceScores),
      check("navigation_timespan_performance_minimum_080", performanceScores.every((score) => score >= 0.8), performanceScores),
      check("flow_html_written", html.length > 100000, { path: path.relative(ROOT, OUT_HTML).replaceAll("\\", "/"), bytes: html.length }),
    ];
    const status = checks.every((item) => item.passed) ? "pass" : "fail";
    const report = {
      validator: "lighthouse_user_flow_probe.mjs",
      generated_at: new Date().toISOString(),
      status,
      check_count: checks.length,
      failure_count: checks.filter((item) => !item.passed).length,
      base_url: baseUrl,
      flow_report_html: path.relative(ROOT, OUT_HTML).replaceAll("\\", "/"),
      steps: scores,
      snapshot_performance_scores_recorded_not_gated: snapshotPerformanceScores,
      checks,
      server_stderr_tail: stderr.slice(-2000),
    };
    await writeFile(OUT_JSON, JSON.stringify(report, null, 2), "utf8");
    console.log(`status=${status}`);
    console.log(`wrote=${path.relative(ROOT, OUT_JSON)}`);
    console.log(`wrote=${path.relative(ROOT, OUT_HTML)}`);
    if (status !== "pass") process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    if (chrome) await chrome.kill();
    server.kill();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
