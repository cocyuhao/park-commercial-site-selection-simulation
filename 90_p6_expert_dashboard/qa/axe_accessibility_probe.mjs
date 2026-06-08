import { AxeBuilder } from "@axe-core/playwright";
import { chromium } from "@playwright/test";
import { spawn } from "node:child_process";
import { mkdir, writeFile } from "node:fs/promises";
import net from "node:net";
import path from "node:path";

const ROOT = path.resolve("../..");
const OUT_DIR = path.join(ROOT, "40_quality_evidence", "axe_accessibility_probe_20260605");
const OUT_JSON = path.join(ROOT, "40_quality_evidence", "axe_accessibility_probe_20260605.json");

const VIEWS = [
  { name: "overview", click: null, requiredText: "全局仿真链路台" },
  { name: "ai", click: "button.side-nav-item[data-view='ai']", requiredText: "专家 AI 工作台" },
  { name: "data", click: "button.side-nav-item[data-view='data']", requiredText: "人物仿真对象池" }
];

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

async function waitForServer(baseUrl, process, timeoutMs = 22000) {
  const deadline = Date.now() + timeoutMs;
  let lastError = "";
  while (Date.now() < deadline) {
    if (process.exitCode !== null) throw new Error(`uvicorn exited early: ${process.exitCode}`);
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

function summarizeViolations(results) {
  return results.violations.map((item) => ({
    id: item.id,
    impact: item.impact,
    description: item.description,
    node_count: item.nodes.length,
    targets: item.nodes.slice(0, 5).map((node) => node.target.join(" "))
  }));
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });
  const port = await freePort();
  const baseUrl = `http://127.0.0.1:${port}`;
  const server = spawn(
    "py",
    ["-3.12", "-m", "uvicorn", "app:app", "--app-dir", "90_p6_expert_dashboard", "--host", "127.0.0.1", "--port", String(port), "--log-level", "warning"],
    { cwd: ROOT, stdio: ["ignore", "pipe", "pipe"] }
  );
  let stderr = "";
  server.stderr.on("data", (chunk) => { stderr += chunk.toString(); });

  const checks = [];
  const viewReports = [];
  let browser;
  try {
    await waitForServer(baseUrl, server);
    browser = await chromium.launch({ channel: "chrome", headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page = await context.newPage();
    await page.goto(baseUrl, { waitUntil: "domcontentloaded" });
    for (const view of VIEWS) {
      if (view.click) await page.locator(view.click).click();
      await page.getByText(view.requiredText).first().waitFor({ timeout: 8000 });
      const screenshot = path.join(OUT_DIR, `${view.name}.png`);
      await page.screenshot({ path: screenshot, fullPage: true });
      const results = await new AxeBuilder({ page }).analyze();
      const violations = summarizeViolations(results);
      viewReports.push({
        view: view.name,
        required_text: view.requiredText,
        violation_count: violations.length,
        violations,
        screenshot: path.relative(ROOT, screenshot).replaceAll("\\", "/")
      });
      checks.push({
        name: `axe_${view.name}_no_serious_or_critical`,
        passed: !violations.some((item) => ["serious", "critical"].includes(item.impact)),
        evidence: violations.filter((item) => ["serious", "critical"].includes(item.impact))
      });
    }
  } finally {
    if (browser) await browser.close();
    server.kill();
  }

  const status = checks.every((item) => item.passed) ? "pass" : "fail";
  const report = {
    validator: "axe_accessibility_probe.mjs",
    generated_at: new Date().toISOString(),
    status,
    check_count: checks.length,
    failure_count: checks.filter((item) => !item.passed).length,
    base_url: baseUrl,
    views: viewReports,
    checks,
    server_stderr_tail: stderr.slice(-2000)
  };
  await writeFile(OUT_JSON, JSON.stringify(report, null, 2), "utf8");
  console.log(`status=${status}`);
  console.log(`wrote=${path.relative(ROOT, OUT_JSON)}`);
  if (status !== "pass") process.exitCode = 1;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
