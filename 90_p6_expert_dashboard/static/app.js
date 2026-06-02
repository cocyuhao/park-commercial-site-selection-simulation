const state = {
  data: null,
  simulationJobs: [],
  latestSimulationResults: null,
  aiSessions: { projects: [], sessions: [] },
  activeAiSessionId: null,
  activeAiProjectId: null,
  aiBusy: false,
  selectedNodeId: null,
  chatHistory: [],
  currentView: "overview",
  mapMode: "risk",
  mapZoom: 1,
  mapNativeZoom: 15,
  mapCenter: null,
  mapPan: { x: 0, y: 0 },
  mapDragging: null,
  mapSuggestTimer: null,
  mapAutoLocateTimer: null,
  mapTipsSeq: 0,
  mapSuppressTipsUntil: 0,
  mapContextHistory: [],
  mapSelectedOnly: false,
  mapLoading: false,
  amapConfig: null,
  amapMap: null,
  amapMarkers: [],
  amapPoiMarkers: [],
  amapNodeMarkers: [],
  amapReady: false,
  amapError: "",
  assetDrawerOpen: false,
  aiScope: "project",
  lastAction: "",
  pendingAttachments: [],
};
window.__APP_STATE__ = state;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function valueText(value, fallback = "待补") {
  if (value === undefined || value === null || String(value).trim() === "") return fallback;
  return String(value);
}

function esc(value) {
  return valueText(value, "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  })[ch]);
}

function shortId(nodeId) {
  return valueText(nodeId).replace("P2-NODE-", "N-");
}

const GATE_LABELS = {
  geometry: "几何图纸",
  visitor_flow: "客流数据",
  conversion_rate: "转化口径",
  revenue_cost: "收益成本",
  operation_authorization: "运营授权",
  model_gate: "模型综合",
};

function gateTitle(domain) {
  return GATE_LABELS[domain] || domain || "待确认闸门";
}

function listItems(value) {
  if (Array.isArray(value)) return value.filter((item) => valueText(item, "").trim());
  if (value === undefined || value === null || value === "") return [];
  return [String(value)];
}

function scoreOf(node) {
  const direct = Number(node?.discussion_score_draft);
  if (Number.isFinite(direct)) return Math.max(0, Math.min(100, Math.round(direct)));
  const fallback = Number(node?.discussion_score || 0);
  return Number.isFinite(fallback) ? Math.max(0, Math.min(100, Math.round(fallback))) : 0;
}

function scoreText(node) {
  if (node?.score_status === "external_preview_only") return "位置参考";
  return `${scoreOf(node)} 分`;
}

function invalidMapKeywordMessage(keyword) {
  if (!keyword) return "";
  if (/^\d+$/.test(keyword)) return "请输入地点名或完整地址，不要只输入数字。";
  const chineseCount = (keyword.match(/[\u4e00-\u9fff]/g) || []).length;
  if (keyword.length < 2 || (chineseCount > 0 && chineseCount < 2)) return "请输入更完整的地点名或地址。";
  return "";
}

function currentNode() {
  if (!state.data?.nodes?.length) return null;
  return state.data.nodes.find((node) => node.node_id === state.selectedNodeId) || state.data.nodes[0];
}

async function loadDashboard() {
  const response = await fetch("/api/dashboard", { cache: "no-store" });
  if (!response.ok) throw new Error(`dashboard api failed: ${response.status}`);
  state.data = await response.json();
  await loadSimulationJobs();
  await loadAiSessions();
  state.selectedNodeId = state.selectedNodeId || state.data.nodes[0]?.node_id;
  renderAll();
}

async function loadAiSessions() {
  try {
    const response = await fetch("/api/ai/sessions", { cache: "no-store" });
    if (!response.ok) throw new Error(`ai sessions api failed: ${response.status}`);
    state.aiSessions = await response.json();
    const currentProject = currentProjectInfo();
    const firstProject = state.aiSessions.projects?.[0];
    state.activeAiProjectId = state.activeAiProjectId || firstProject?.project_id || "current-project";
    if (state.activeAiProjectId === "current-project") state.activeAiProjectId = currentProject.project_id;
    if (!state.activeAiSessionId) {
      const firstSession = (state.aiSessions.sessions || []).find((item) => item.project_id === state.activeAiProjectId);
      state.activeAiSessionId = firstSession?.session_id || null;
    }
  } catch (error) {
    state.aiSessions = { projects: [], sessions: [], error: error.message };
  }
}

async function loadSimulationJobs() {
  try {
    const response = await fetch("/api/simulation/jobs", { cache: "no-store" });
    if (!response.ok) throw new Error(`simulation jobs api failed: ${response.status}`);
    const payload = await response.json();
    state.simulationJobs = payload.items || [];
    const latestJob = state.simulationJobs[0];
    if (latestJob?.job_id) {
      const resultResponse = await fetch(`/api/simulation/jobs/${encodeURIComponent(latestJob.job_id)}/results`, { cache: "no-store" });
      state.latestSimulationResults = resultResponse.ok ? await resultResponse.json() : null;
    } else {
      state.latestSimulationResults = null;
    }
  } catch (error) {
    state.simulationJobs = [];
    state.latestSimulationResults = { error: error.message };
  }
}

function renderAll() {
  if (!state.data) return;
  renderMeta();
  renderOverview();
  renderNodes();
  renderDetail();
  renderMap();
  renderMapSide();
  renderUploadList();
  renderCandidateList();
  renderAssetDrawer();
  renderDataPage();
  renderSimulationPanel();
  renderGapStatus();
  renderReport();
  renderAiSessions();
  renderAiContext();
  renderIntegrationStatus();
}

function renderMeta() {
  $("#dataVersion").textContent = `待复核草案 · ${state.data.meta?.updated_at || ""}`;
  const titles = {
    overview: "基于地图、资料、AI 反馈和仿真干跑，形成待复核选址方案",
    nodes: "查看节点细节，所有内容仍为反馈草案",
    map: "用地图讨论位置关系，底图文字只作参考",
    upload: "上传方案、图纸、图片和数据表，进入待解析资料池",
    data: "把资料缺口变成可执行任务",
    report: "查看 TGI、POI、供需缺口和节点改进报告",
    ai: "像网页 AI 一样对话、追问、记录专家意见",
  };
  const title = titles[state.currentView] || titles.overview;
  $("#pageSubtitle").textContent = state.lastAction ? `${title} · ${state.lastAction}` : title;
}

function setView(view) {
  state.currentView = view;
  window.location.hash = view === "overview" ? "" : view;
  $$(".view").forEach((el) => el.classList.toggle("active", el.id === `${view}View` || (view === "ai" && el.id === "aiWorkspaceView")));
  $$("[data-view]").forEach((btn) => btn.classList.toggle("active", btn.dataset.view === view && btn.classList.contains("side-nav-item")));
  renderMeta();
  if (view === "ai") renderAiContext();
  if (view === "report") renderReport();
  requestAnimationFrame(() => window.scrollTo(0, 0));
}

function priorityLabel(node) {
  if (node?.score_status === "external_preview_only") return ["仅看位置关系", "preview"];
  const score = scoreOf(node);
  if (score >= 70) return ["优先讨论", "good"];
  if (score >= 55) return ["需补证再议", "warn"];
  return ["暂缓讨论", "fail"];
}

function renderOverview() {
  const nodes = state.data.nodes || [];
  $("#overviewNodeList").innerHTML = nodes.length ? nodes.map((node) => {
    const [label, cls] = priorityLabel(node);
    return `
      <button class="overview-node ${node.node_id === state.selectedNodeId ? "active" : ""}" data-node-id="${esc(node.node_id)}" data-view="nodes">
        <b>${esc(shortId(node.node_id))} ${esc(node.node_name)}</b>
        <span class="${cls}">${label} · ${esc(scoreText(node))}</span>
      </button>
    `;
  }).join("") : `<div class="empty-state">还没有外部上传项目资料。请先进入“资料导入”。</div>`;

  const feedbackCount = state.data.expert_feedback?.length || 0;
  $("#overviewNextSteps").innerHTML = [
    ["上传项目资料", "方案、图纸、DOCX、PDF 和客流表都应由外部上传后再分析。", "upload", "上传资料"],
    ["补真实客流", "客流、转化率、收益成本等闸门仍不能作为 checked。", "data", "查看数据请求"],
    ["看供需缺口", "TGI 来自外部客流资料，POI 来自当前地图上下文。", "report", "打开报告"],
    ["专家录入意见", `当前已记录 ${feedbackCount} 条专家意见；继续写入后会自动刷新。`, "ai", "打开 AI 工作台"],
  ].map(([title, body, view, action]) => `
    <button class="next-step action-step" data-view="${view}">
      <span><b>${title}</b><em>${body}</em></span>
      <strong>${action}</strong>
    </button>
  `).join("");
}

function renderUploadList() {
  const box = $("#uploadList");
  if (!box) return;
  const uploads = state.data.uploads || [];
  if (!uploads.length) {
    box.innerHTML = `<div class="empty-state">还没有资料。请先上传 DWG、PDF、图片或表格。</div>`;
    return;
  }
  box.innerHTML = uploads.map((item) => `
    <div class="upload-item">
      <div>
        <b>${esc(item.filename)}</b>
        <span>${esc(item.category)} · ${esc(item.review_status || "待解析")}</span>
      </div>
      <p>${esc(item.note || "上传后先进入待解析资料池，不自动变成最终数据。")}</p>
      <div class="upload-flow">
        <span class="done">已上传</span>
        <span class="${item.review_status === "已确认入池" ? "done" : "active"}">AI 解析</span>
        <span class="${item.review_status === "已确认入池" ? "done" : ""}">确认入池</span>
        <span>关联资料缺口</span>
      </div>
      <div class="upload-actions">
        <button class="primary-btn parse-upload-btn" data-upload-id="${esc(item.upload_id)}">1. AI 解析</button>
        <button class="secondary-btn" data-view="data">2. 关联资料缺口</button>
        <button class="secondary-btn" data-view="ai" data-upload-name="${esc(item.filename)}">带入 AI 工作台</button>
      </div>
    </div>
  `).join("");
}

function renderCandidateList() {
  const box = $("#candidateList");
  if (!box) return;
  const candidates = state.data.upload_candidates || [];
  if (!candidates.length) {
    box.innerHTML = `<div class="candidate-empty">解析候选会出现在这里。先点资料卡片上的“AI 解析”。</div>`;
    return;
  }
  box.innerHTML = `
    <div class="candidate-title">待复核解析候选</div>
    ${candidates.slice().reverse().map((item) => `
      <div class="candidate-item ${item.review_status === "已确认入池" ? "confirmed" : ""}">
        <div>
          <b>${esc(item.filename)}</b>
          <span>${esc(item.review_status)} · ${esc(item.generated_by === "local_rules" ? "本地规则" : item.generated_by || "本地规则")}</span>
        </div>
        <p>${esc(item.summary || "已生成待复核资料候选。")}</p>
        <div class="request-tags">${(item.related_gates || []).map((gate) => `<span>${esc(gateTitle(gate))}</span>`).join("")}</div>
        <div class="candidate-next">${esc(item.review_status === "已确认入池" ? "已进入资料闭合中心，可继续查看缺口状态。" : "下一步：确认资料是否真实对应当前项目，再入池。")}</div>
        <div class="candidate-actions">
          <button class="secondary-btn" data-view="data">查看资料闭合</button>
          ${item.review_status === "已确认入池" ? "" : `<button class="primary-btn confirm-candidate-btn" data-candidate-id="${esc(item.candidate_id)}">确认入池</button>`}
        </div>
      </div>
    `).join("")}
  `;
}

function renderAssetDrawer() {
  const drawer = $("#assetDrawer");
  const list = $("#assetDrawerList");
  if (!drawer || !list) return;
  drawer.classList.toggle("open", state.assetDrawerOpen);
  const uploads = state.data?.uploads || [];
  if (!uploads.length) {
    list.innerHTML = `<div class="empty-state">还没有上传资料。可以从“资料导入”或 AI 工作台的 + 上传。</div>`;
    return;
  }
  list.innerHTML = uploads.slice().reverse().map((item) => `
    <article class="asset-item">
      <b>${esc(item.filename)}</b>
      <span>${esc(item.category)} · ${esc(item.review_status || "待处理")} · ${esc(Math.round((Number(item.size_bytes) || 0) / 1024))} KB</span>
      <span>${esc(item.note || "未填写说明")}</span>
      <div class="asset-actions">
        <button type="button" data-upload-action="use" data-upload-id="${esc(item.upload_id)}">使用</button>
        <button type="button" data-upload-action="discard" data-upload-id="${esc(item.upload_id)}">放弃使用</button>
        <button type="button" class="parse-upload-btn" data-upload-id="${esc(item.upload_id)}">AI 解析</button>
        <button type="button" class="danger" data-upload-action="delete" data-upload-id="${esc(item.upload_id)}">删除</button>
      </div>
    </article>
  `).join("");
}

async function updateUploadAction(uploadId, action) {
  if (action === "delete") {
    if (!window.confirm("确定删除这份上传资料吗？只删除网页资料池副本，不会删除项目原始文件。")) return;
    const response = await fetch(`/api/uploads/${encodeURIComponent(uploadId)}`, { method: "DELETE" });
    if (!response.ok) throw new Error(`delete upload failed: ${response.status}`);
    state.lastAction = "资料已从资料池删除";
  } else {
    const response = await fetch(`/api/uploads/${encodeURIComponent(uploadId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    if (!response.ok) throw new Error(`update upload failed: ${response.status}`);
    state.lastAction = action === "use" ? "资料已标记为使用" : "资料已标记为放弃使用";
  }
  await loadDashboard();
  state.assetDrawerOpen = true;
  renderAssetDrawer();
}

function nodeSearchKeyword() {
  const input = $("#nodeSearch");
  return input ? input.value.trim().toLowerCase() : "";
}

function renderNodes() {
  const keyword = nodeSearchKeyword();
  const nodes = (state.data.nodes || []).filter((node) => {
    const haystack = [
      node.node_id,
      node.node_name,
      node.primary_positioning,
      (node.business_direction || []).join(" "),
    ].join(" ").toLowerCase();
    return !keyword || haystack.includes(keyword);
  });

  if (!nodes.length) {
    $("#nodeList").innerHTML = `<div class="empty-state">还没有外部上传项目资料，节点方案暂为空。</div>`;
    return;
  }
  $("#nodeList").innerHTML = nodes.map((node) => {
    const [label, cls] = priorityLabel(node);
    return `
      <button class="node-row ${node.node_id === state.selectedNodeId ? "active" : ""}" data-node-id="${esc(node.node_id)}">
        <span class="node-code">${esc(shortId(node.node_id))}</span>
        <span class="node-main">
          <b>${esc(node.node_name)}</b>
          <em>${esc(node.primary_positioning || "待补场景描述")}</em>
        </span>
        <span class="node-score ${cls}">${esc(scoreText(node))}</span>
        <span class="node-status ${cls}">${label}</span>
      </button>
    `;
  }).join("");
}

function renderDetail() {
  const node = currentNode();
  if (!node) {
    $("#detailTitle").textContent = "节点详情";
    $("#statusTag").textContent = "等待上传";
    $("#detailBody").innerHTML = `<div class="empty-state">上传并解析项目资料后，这里才会显示节点、TGI、POI 和缺口建议。</div>`;
    return;
  }
  $("#detailTitle").textContent = `${shortId(node.node_id)} ${node.node_name}`;
  $("#statusTag").textContent = node.status_label || "待复核 / 非最终";
  const directions = node.business_direction?.length ? node.business_direction : node.candidate_business_formats || [];
  const scenarios = node.feedback_scenarios?.length ? node.feedback_scenarios : [];
  const requests = node.data_requests?.length ? node.data_requests : [];
  const assumptions = node.assumption_refs?.slice(0, 3) || [];
  const missingFields = listItems(node.missing_required_fields);
  const nextDataNeeded = listItems(node.next_data_needed);
  const scoreInputs = node.score_inputs || {};

  $("#detailBody").innerHTML = `
    <div class="detail-top">
      <div class="metric"><span>面积</span><b>${esc(node.area_sqm)} m²</b></div>
      <div class="metric"><span>草案分</span><b>${esc(scoreText(node))}</b></div>
      <div class="metric"><span>状态</span><b>${esc(node.score_status === "external_preview_only" ? "位置参考" : (node.score_label || node.status_label || "待复核"))}</b></div>
    </div>
    <section class="detail-section">
      <h3>评分解释</h3>
      <p>${esc(node.score_explanation || "后端暂未返回评分解释；当前仍按待复核草案展示。")}</p>
      <details class="tech-trace">
        <summary>技术追踪</summary>
        <div class="request-tags">
          <span>score_status: ${esc(node.score_status || "needs_review_not_final")}</span>
          <span>blocked_gate: ${esc(scoreInputs.blocked_gate_count ?? "待复核")}</span>
          <span>missing_fields: ${esc(scoreInputs.missing_field_count ?? missingFields.length)}</span>
          <span>poi_count: ${esc(scoreInputs.poi_count ?? "待复核")}</span>
        </div>
      </details>
    </section>
    <section class="detail-section">
      <h3>TGI / POI 缺口</h3>
      ${renderNodeGapBlock(node)}
    </section>
    <section class="detail-section">
      <h3>业态方向</h3>
      <div class="chip-row">${directions.map((item) => `<span>${esc(item)}</span>`).join("") || "<span>待补</span>"}</div>
    </section>
    <section class="detail-section">
      <h3>场景假设</h3>
      <p>${esc(node.scene_assumptions || node.primary_positioning || "待合作方补充真实场景资料")}</p>
      ${assumptions.map((item) => `<p class="soft-box">${esc(item.scene_description || item.assumption_text || JSON.stringify(item))}</p>`).join("")}
    </section>
    <section class="detail-section">
      <h3>合作模式 / 占位参数</h3>
      <p>${esc(node.cooperation_mode || "合作模式待确认")}；${esc(node.placeholder_inputs_used || "占位参数仍需复核")}</p>
    </section>
    <section class="detail-section">
      <h3>P4 场景矩阵</h3>
      <div class="scenario-list">
        ${scenarios.slice(0, 4).map((item) => `
          <div>
            <b>${esc(item.scenario_name || item.scenario_type || "场景")}</b>
            <span>${esc(item.scenario_summary || item.feedback_note || item.key_assumption || "待复核")}</span>
          </div>
        `).join("") || "<p>暂无场景矩阵记录</p>"}
      </div>
    </section>
    <section class="detail-section">
      <h3>待补数据</h3>
      <div class="request-tags">
        ${requests.map((item) => `<span>${esc(item.missing_input || item.calibration_domain || "待补数据")} · ${esc(item.priority || "needs_review")}</span>`).join("") || `<span>${esc(node.must_collect_before_final || "真实客流、转化率、收益成本、运营授权、可信 DWG 转换产物")}</span>`}
      </div>
    </section>
    <section class="detail-section">
      <h3>后端缺口提示</h3>
      <div class="request-tags">
        ${missingFields.map((item) => `<span>${esc(item)}</span>`).join("") || "<span>暂无结构化缺失字段</span>"}
      </div>
      <p>${nextDataNeeded.length ? esc(nextDataNeeded.join("；")) : "下一步仍以 P3 gate 和资料闭合清单为准。"}</p>
    </section>
    <div class="detail-actions">
      <button class="secondary-btn" data-view="map">在地图中查看</button>
      <button class="primary-btn" data-view="ai" data-ai-scope="node">带着这个节点问 AI</button>
    </div>
  `;
}

function renderMap() {
  const amap = state.data.amap || {};
  const status = amap.status || {};
  const context = amap.map_context || {};
  $("#amapStatusText").textContent = status.web_service_key_available
    ? `目标：${context.matched_name || context.keyword || "当前地点"}；已加载 ${status.point_count || 0} 条 POI`
    : "未检测到高德 Key；先显示本地示意层";
  const modeStatus = $("#mapModeStatus");
  if (modeStatus) {
    modeStatus.textContent = state.amapError || "地图用于位置、边界、POI 和候选点的综合查看；不按某一个公园强行套评分。";
    modeStatus.className = `map-mode-status ${state.amapError ? "error-mode" : "score-mode"}`;
  }
  if ($("#mapSearchInput") && !$("#mapSearchInput").value) {
    $("#mapSearchInput").placeholder = context.keyword ? `搜索地点、拼音或地址 · 当前：${context.keyword}` : "搜索地点、拼音或地址";
  }

  $("#mapCanvas").className = `map-canvas mode-${state.mapMode}`;
  $("#mapCanvas").classList.toggle("loading", state.mapLoading);
  initInteractiveMap().catch((error) => {
    state.amapError = `高德 JS 地图加载失败：${error.message}`;
    renderStaticMapFallback();
  });
}

async function fetchAmapConfig() {
  if (state.amapConfig) return state.amapConfig;
  const response = await fetch("/api/amap/js-config", { cache: "no-store" });
  if (!response.ok) throw new Error(`js-config ${response.status}`);
  state.amapConfig = await response.json();
  return state.amapConfig;
}

function loadAmapScript(config) {
  if (window.AMap) return Promise.resolve();
  if (!config.available || !config.key) throw new Error(config.message || "缺少高德 JS API Key");
  if (config.security_code) {
    window._AMapSecurityConfig = { securityJsCode: config.security_code };
  }
  return new Promise((resolve, reject) => {
    const existing = document.querySelector("script[data-amap-js='true']");
    if (existing) {
      existing.addEventListener("load", resolve, { once: true });
      existing.addEventListener("error", () => reject(new Error("高德脚本加载失败")), { once: true });
      return;
    }
    const script = document.createElement("script");
    script.dataset.amapJs = "true";
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(config.key)}&plugin=AMap.AutoComplete,AMap.PlaceSearch,AMap.Scale,AMap.ToolBar,AMap.Geolocation`;
    script.onload = resolve;
    script.onerror = () => reject(new Error("高德脚本加载失败"));
    document.head.appendChild(script);
  });
}

async function initInteractiveMap() {
  const amap = state.data.amap || {};
  const context = amap.map_context || {};
  const config = await fetchAmapConfig();
  await loadAmapScript(config);
  const center = [Number(context.longitude || 116.392159), Number(context.latitude || 40.018635)];
  if (!state.amapMap) {
    state.amapMap = new AMap.Map("amapInteractiveMap", {
      center,
      zoom: nativeZoomFromBounds(amap.map_bounds || {}),
      resizeEnable: true,
      dragEnable: true,
      zoomEnable: true,
      viewMode: "2D",
      mapStyle: "amap://styles/normal",
    });
    state.amapMap.addControl(new AMap.Scale());
    state.amapMap.addControl(new AMap.ToolBar({ position: "RB" }));
    state.amapReady = true;
  } else {
    state.amapMap.setZoomAndCenter(nativeZoomFromBounds(amap.map_bounds || {}), center, false, 700);
  }
  state.amapError = "";
  $("#staticMapLayer").style.display = "none";
  $("#amapInteractiveMap").style.display = "block";
  state.mapLoading = false;
  $("#mapCanvas").classList.remove("loading");
  renderAmapMarkers();
}

function clearAmapMarkers() {
  if (!state.amapMap) return;
  [...state.amapPoiMarkers, ...state.amapNodeMarkers].forEach((marker) => state.amapMap.remove(marker));
  state.amapPoiMarkers = [];
  state.amapNodeMarkers = [];
}

function renderAmapMarkers() {
  if (!state.amapMap || !window.AMap) return;
  clearAmapMarkers();
  const amap = state.data.amap || {};
  if (state.mapMode !== "nodes") {
    state.amapPoiMarkers = (amap.supply_points || []).slice(0, 80).map((p) => {
      const marker = new AMap.Marker({
        position: [Number(p.longitude), Number(p.latitude)],
        title: p.poi_name || "POI",
        content: `<div class="amap-poi-marker ${p.boundary_filter_status === "inside_osm_polygon" ? "inside" : ""}"></div>`,
        offset: new AMap.Pixel(-6, -6),
      });
      marker.on("click", () => {
        $("#mapSideDetail").innerHTML = `
          <h3>${esc(p.poi_name || "周边 POI")}</h3>
          <div class="map-score preview">${esc(p.category || p.amap_keywords || "商业/服务点位")}</div>
          <p>${esc(p.boundary_filter_status || "位置关系待复核")}</p>
          <div class="mini-kv"><span>距离</span><b>${esc(p.distance_m || "待测")} m</b></div>
          <div class="mini-kv"><span>状态</span><b>仅作供给参考</b></div>
        `;
      });
      return marker;
    });
    state.amapMap.add(state.amapPoiMarkers);
  }
  if (state.mapMode !== "poi") {
    const nodeRows = state.mapSelectedOnly
      ? (amap.context_nodes || []).filter((item) => item.node_id === state.selectedNodeId)
      : (amap.context_nodes || []);
    state.amapNodeMarkers = nodeRows.map((mapNode) => {
      const node = (state.data.nodes || []).find((item) => item.node_id === mapNode.node_id) || mapNode;
      const marker = new AMap.Marker({
        position: [Number(mapNode.longitude), Number(mapNode.latitude)],
        title: node.node_name || node.node_id,
        content: `<button class="amap-node-marker ${node.node_id === state.selectedNodeId ? "active" : ""}">${esc(shortId(node.node_id))}</button>`,
        offset: new AMap.Pixel(-19, -19),
      });
      marker.on("click", () => {
        state.selectedNodeId = node.node_id;
        state.aiScope = "node";
        renderAll();
        setView("map");
      });
      return marker;
    });
    state.amapMap.add(state.amapNodeMarkers);
  }
  renderMapSide();
}

function renderStaticMapFallback() {
  const active = currentNode();
  const amap = state.data.amap || {};
  const context = amap.map_context || {};
  const img = $("#amapBaseMap");
  $("#staticMapLayer").style.display = "block";
  $("#amapInteractiveMap").style.display = "none";
  if (!state.amapReady) $("#mapCanvas").classList.add("loading");
  img.onload = () => $("#mapCanvas").classList.remove("loading");
  state.mapCenter = {
    lon: Number(context.longitude || 116.392159),
    lat: Number(context.latitude || 40.018635),
  };
  state.mapNativeZoom = nativeZoomFromBounds(amap.map_bounds || {});
  img.src = mapImageUrl();
  img.onerror = () => {
    $("#amapStatusText").textContent = "地图底图加载失败，仅保留节点示意层";
  };

  renderPoiLayer(amap.supply_points || []);
  renderRangeLayer();

  const contextNodes = state.mapSelectedOnly
    ? (amap.context_nodes || []).filter((item) => item.node_id === state.selectedNodeId)
    : (amap.context_nodes || []);
  $("#mapNodes").innerHTML = contextNodes.map((mapNode, index) => {
    const node = (state.data.nodes || []).find((item) => item.node_id === mapNode.node_id) || mapNode;
    const [, cls] = priorityLabel(node);
    const pos = projectLonLat(mapNode.longitude, mapNode.latitude);
    return `
      <button class="map-pin ${cls} ${node.node_id === active?.node_id ? "active" : ""}" data-node-id="${esc(node.node_id)}" style="left:${pos[0]}%;top:${pos[1]}%">
        ${esc(shortId(node.node_id))}
      </button>
    `;
  }).join("");

  applyMapTransform();
}

function applyMapTransform() {
  const transform = `translate(${state.mapPan.x}px, ${state.mapPan.y}px) scale(${state.mapZoom})`;
  ["#amapBaseMap", "#mapRangeLayer", "#amapPoiLayer", "#mapNodes"].forEach((selector) => {
    const el = $(selector);
    if (el) el.style.transform = transform;
  });
}

function nativeZoomFromBounds(bounds = {}) {
  const lonSpan = Math.max(Number(bounds.max_lon) - Number(bounds.min_lon), 0.001);
  const latSpan = Math.max(Number(bounds.max_lat) - Number(bounds.min_lat), 0.001);
  const span = Math.max(lonSpan, latSpan);
  if (!Number.isFinite(span)) return 15;
  if (span > 0.09) return 12;
  if (span > 0.045) return 13;
  if (span > 0.022) return 14;
  if (span > 0.011) return 15;
  return 16;
}

function mapImageUrl() {
  const center = state.mapCenter || {};
  const params = new URLSearchParams({
    t: String(Date.now()),
    zoom: String(Math.max(3, Math.min(20, Math.round(state.mapNativeZoom || 15)))),
  });
  if (Number.isFinite(center.lon) && Number.isFinite(center.lat)) {
    params.set("lon", String(center.lon));
    params.set("lat", String(center.lat));
  }
  return `/api/amap/static-map?${params.toString()}`;
}

function refreshMapImage() {
  const img = $("#amapBaseMap");
  if (!img) return;
  $("#mapCanvas").classList.add("loading");
  img.src = mapImageUrl();
}

function changeMapZoom(delta) {
  if (state.amapMap) {
    const nextZoom = Math.max(3, Math.min(20, state.amapMap.getZoom() + delta * 4));
    state.amapMap.setZoom(nextZoom, false, 350);
    return;
  }
  state.mapNativeZoom = Math.max(3, Math.min(20, Number((state.mapNativeZoom + delta).toFixed(2))));
  state.mapZoom = 1;
  state.mapPan = { x: 0, y: 0 };
  applyMapTransform();
  refreshMapImage();
}

function resetMapView() {
  if (state.amapMap) {
    const context = state.data?.amap?.map_context || {};
    state.amapMap.setZoomAndCenter(
      nativeZoomFromBounds(state.data?.amap?.map_bounds || {}),
      [Number(context.longitude || 116.392159), Number(context.latitude || 40.018635)],
      false,
      500,
    );
    return;
  }
  state.mapZoom = 1;
  state.mapPan = { x: 0, y: 0 };
  state.mapNativeZoom = nativeZoomFromBounds(state.data?.amap?.map_bounds || {});
  applyMapTransform();
  refreshMapImage();
}

function shouldAutoLocateMap(q, item) {
  const text = q.trim().toLowerCase();
  if (!item?.longitude || !item?.latitude) return false;
  if (["aosen", "osen", "as", "dongba", "db"].includes(text)) return true;
  const name = String(item.name || "").toLowerCase();
  return text.length >= 3 && (name.includes(text) || text.includes(name));
}

function panMapNative(dx, dy) {
  const center = state.mapCenter;
  if (!center) return;
  const factor = 360 / (256 * Math.pow(2, state.mapNativeZoom || 15));
  const latFactor = factor * Math.max(0.3, Math.cos((center.lat * Math.PI) / 180));
  state.mapCenter = {
    lon: center.lon - dx * latFactor,
    lat: center.lat + dy * factor,
  };
  state.mapZoom = 1;
  state.mapPan = { x: 0, y: 0 };
  applyMapTransform();
  refreshMapImage();
}

function projectLonLat(lonValue, latValue) {
  const bounds = state.data?.amap?.map_bounds || {};
  const lon = Number(lonValue);
  const lat = Number(latValue);
  const minLon = Number(bounds.min_lon);
  const maxLon = Number(bounds.max_lon);
  const minLat = Number(bounds.min_lat);
  const maxLat = Number(bounds.max_lat);
  if (![lon, lat, minLon, maxLon, minLat, maxLat].every(Number.isFinite) || maxLon === minLon || maxLat === minLat) {
    return [50, 50];
  }
  const x = ((lon - minLon) / (maxLon - minLon)) * 100;
  const y = (1 - ((lat - minLat) / (maxLat - minLat))) * 100;
  return [Math.max(-20, Math.min(120, x)), Math.max(-20, Math.min(120, y))];
}

function renderRangeLayer() {
  const context = state.data?.amap?.map_context || {};
  const polygon = state.data?.amap?.boundary_polygon || [];
  const points = polygon.map((point) => projectLonLat(point.longitude, point.latitude));
  const polygonPoints = points.map(([x, y]) => `${x},${y}`).join(" ");
  const status = state.data?.amap?.boundary_status || "estimated_range_needs_review";
  const source = state.data?.amap?.boundary_source || "computed_from_visible_points";
  const isEstimated = status.includes("estimated") || source.includes("computed") || source.includes("convex hull");
  const label = isEstimated ? "讨论范围外包线 · 待复核" : "公开轮廓 · 待复核";
  $("#mapRangeLayer").innerHTML = `
    <svg class="range-shape ${isEstimated ? "estimated" : "public-polygon"}" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
      <polygon points="${esc(polygonPoints)}"></polygon>
    </svg>
    <div class="range-label">${esc(context.matched_name || context.keyword || "当前范围")} · ${esc(label)}</div>
  `;
}

async function renderIntegrationStatus() {
  const box = $("#integrationStatus");
  if (!box) return;
  box.innerHTML = `<div class="loading-row">正在检查接口与数据状态……</div>`;
  try {
    const response = await fetch("/api/integration/status", { cache: "no-store" });
    const data = await response.json();
    const visibleItems = (data.items || []).filter((item) => !["connected", "configured", "connected_image"].includes(item.status));
    if (!visibleItems.length) {
      box.innerHTML = `<div class="integration-quiet">后台接口与数据源当前无失败项。</div>`;
      return;
    }
    box.innerHTML = visibleItems.map((item) => {
      const cls = item.status === "connected" || item.status === "configured" || item.status === "connected_image"
        ? "good"
        : item.status === "missing_key"
          ? "fail"
          : "warn";
      return `
        <div class="integration-item ${cls}">
          <div>
            <b>${esc(item.name)}</b>
            <span>${esc(item.kind)} · ${esc(item.status)}</span>
          </div>
          <p>${esc(item.detail)}</p>
        </div>
      `;
    }).join("");
  } catch (error) {
    box.innerHTML = `<div class="integration-item fail"><b>状态检查失败</b><p>${esc(error.message)}</p></div>`;
  }
}

function renderPoiLayer(points) {
  const visiblePoints = state.mapSelectedOnly
    ? []
    : points;
  if (!visiblePoints.length) {
    $("#amapPoiLayer").innerHTML = "";
    return;
  }
  $("#amapPoiLayer").innerHTML = visiblePoints.slice(0, 60).map((p) => {
    const [x, y] = projectLonLat(p.longitude, p.latitude);
    const inside = p.boundary_filter_status === "inside_osm_polygon";
    return `<span class="poi-dot ${inside ? "inside" : ""}" style="left:${x}%;top:${y}%" title="${esc(p.poi_name)} · ${esc(p.output_status)}"></span>`;
  }).join("");
}

function renderMapSide() {
  const contextNode = (state.data?.amap?.context_nodes || []).find((item) => item.node_id === state.selectedNodeId);
  const node = contextNode || currentNode();
  if (!node) return;
  const [label, cls] = priorityLabel(node);
  const nextDataNeeded = listItems(node.next_data_needed);
  const scoreLine = node?.score_status === "external_preview_only" ? "位置参考 · 不生成评分" : `${label} · ${scoreText(node)}`;
  $("#mapSideDetail").innerHTML = `
    <h3>${esc(shortId(node.node_id))} ${esc(node.node_name)}</h3>
    <div class="map-score ${cls}">${esc(scoreLine)}</div>
    <p>${esc(node.primary_positioning || node.scene_assumptions || "待补场景")}</p>
    <div class="mini-kv"><span>面积</span><b>${esc(node.area_sqm === "待测" ? "待测" : `${node.area_sqm} m²`)}</b></div>
    <div class="mini-kv"><span>状态</span><b>${esc(node.status_label || "待复核 / 非最终")}</b></div>
    <div class="mini-kv"><span>评分说明</span><b>${esc(node.score_explanation || "仅作讨论草案")}</b></div>
    <div class="mini-kv"><span>地图边界</span><b>示意层，非 DWG</b></div>
    ${nextDataNeeded.length ? `<div class="mini-kv"><span>下一步</span><b>${esc(nextDataNeeded.slice(0, 2).join("；"))}</b></div>` : ""}
    ${node.source_node_name ? `<div class="mini-kv"><span>来源草案</span><b>${esc(node.source_node_name)}</b></div>` : ""}
  `;
}

function renderNodeGapBlock(node) {
  const gap = node?.supply_gap_match || {};
  if (!gap.business_type) {
    return `<p>当前节点还没有匹配到可计算缺口。请先上传客流/TGI资料，并确认当前地图 POI。</p>`;
  }
  const examples = listItems(gap.poi_examples).slice(0, 4).join("、");
  return `
    <div class="gap-mini-grid">
      <span><b>${esc(gap.business_type)}</b><em>匹配业态</em></span>
      <span><b>${esc(gap.tgi)}</b><em>TGI</em></span>
      <span><b>${esc(gap.poi_count)}</b><em>POI 数</em></span>
      <span><b>${esc(gap.gap_index)}</b><em>缺口指数</em></span>
    </div>
    <p>${esc(gap.priority)}；${examples ? `参考 POI：${examples}` : "暂无 POI 示例"}</p>
  `;
}

function gateClass(status = "") {
  if (status.includes("pending_conversion")) return "fail";
  if (status.includes("blocked")) return "warn";
  if (status.includes("pass") || status.includes("ready")) return "good";
  return "warn";
}

function gateText(status = "") {
  if (status.includes("pending_conversion")) return "待转换";
  if (status.includes("blocked")) return "待来源数据";
  if (status.includes("pass") || status.includes("ready")) return "通过";
  return "未决";
}

function renderDataPage() {
  const uploadsByGate = {};
  (state.data.uploads || []).forEach((item) => {
    const key = item.target_gate || item.category || "other";
    uploadsByGate[key] = (uploadsByGate[key] || 0) + 1;
  });
  $("#gateList").innerHTML = (state.data.p3_gates || []).map((gate) => {
    const cls = gateClass(gate.current_gate_status);
    const uploadCount = uploadsByGate[gate.calibration_domain] || 0;
    const actionMap = {
      geometry: "上传 DWG/DXF/PDF，并说明图纸对应北园或南园",
      visitor_flow: "上传客流表、时段图、票务/运营记录",
      conversion_rate: "填写入口客流到消费转化的口径或上传历史经营表",
      revenue_cost: "上传租金、分成、装修、人工、运营成本表",
      operation_authorization: "上传授权、消防、业态限制、审批口径文件",
      model_gate: "等待前面资料闭合后再复核模型",
    };
    return `
      <div class="gate-item ${cls}">
        <div>
          <b>${esc(gateTitle(gate.calibration_domain))}</b>
          <span>${esc(gate.calibration_domain)} · ${uploadCount ? `已关联 ${uploadCount} 份资料` : "尚未关联资料"}</span>
        </div>
        <p>${esc(actionMap[gate.calibration_domain] || gate.blocking_reason || "需要补充来源数据后复核")}</p>
        <div class="gate-actions">
          <button class="secondary-btn" data-view="upload">上传资料</button>
          <button class="secondary-btn gate-note-btn" data-gate="${esc(gate.calibration_domain)}">填写说明</button>
          <button class="secondary-btn" data-view="ai">问 AI 怎么补</button>
        </div>
      </div>
    `;
  }).join("");

  const rows = state.data.p4_feedback?.data_requests || [];
  $("#dataNeeds").innerHTML = `
    <table>
      <thead><tr><th>节点</th><th>要补什么</th><th>用途</th><th>状态</th></tr></thead>
      <tbody>
        ${rows.map((row) => `
          <tr>
            <td>${esc(shortId(row.node_id))}</td>
            <td>${esc(row.missing_input || row.calibration_domain)}</td>
            <td>${esc(row.why_needed || row.request_reason || "用于后续校准")}</td>
            <td><span class="status-pill danger">待复核</span></td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}

function renderGapStatus() {
  const box = $("#gapStatus");
  if (!box) return;
  const payload = state.data?.demand_supply || {};
  const tgi = payload.tgi || {};
  const supply = payload.supply || {};
  const gap = payload.gap || {};
  if (gap.status !== "calculated_needs_review") {
    box.innerHTML = `
      <div class="gap-blocked">
        <b>暂不能计算</b>
        <p>${esc(gap.message || "请上传客流/TGI资料，并确认当前地图 POI。")}</p>
        <div class="request-tags">
          <span>客流资料：${payload.visitor_sources?.count || 0} 份</span>
          <span>TGI：${esc(tgi.status || "未生成")}</span>
          <span>POI：${esc(supply.status || "未生成")}</span>
        </div>
      </div>
    `;
    return;
  }
  box.innerHTML = `
    <div class="gap-summary">
      <span><b>${esc(payload.visitor_sources?.count || 0)}</b><em>客流资料</em></span>
      <span><b>${esc(Object.keys(tgi.tgi_profile || {}).length)}</b><em>TGI 业态</em></span>
      <span><b>${esc(Object.keys(supply.poi_counts || {}).length)}</b><em>POI 业态</em></span>
    </div>
    <div class="gap-table">
      <table>
        <thead><tr><th>业态</th><th>TGI</th><th>POI</th><th>缺口指数</th><th>建议</th></tr></thead>
        <tbody>
          ${(gap.items || []).slice(0, 8).map((item) => `
            <tr>
              <td>${esc(item.business_type)}</td>
              <td>${esc(item.tgi)}</td>
              <td>${esc(item.poi_count)}</td>
              <td>${esc(item.gap_index)}</td>
              <td>${esc(item.priority)}</td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderReport() {
  const box = $("#reportBody");
  if (!box) return;
  const report = state.data?.demand_supply?.report || {};
  const topGaps = report.top_gaps || [];
  const nodes = report.nodes || [];
  box.innerHTML = `
    <section class="report-summary">
      <div><span>状态</span><b>待复核 / 非最终</b></div>
      <div><span>上传资料</span><b>${esc(report.source_upload_count || 0)} 份</b></div>
      <div><span>缺口状态</span><b>${esc(report.gap_status || "未计算")}</b></div>
    </section>
    <section class="report-section">
      <h3>主要供需缺口</h3>
      ${topGaps.length ? `
        <table>
          <thead><tr><th>业态</th><th>TGI</th><th>POI</th><th>缺口</th><th>建议</th></tr></thead>
          <tbody>${topGaps.map((item) => `
            <tr>
              <td>${esc(item.business_type)}</td>
              <td>${esc(item.tgi)}</td>
              <td>${esc(item.poi_count)}</td>
              <td>${esc(item.gap_index)}</td>
              <td>${esc(item.priority)}</td>
            </tr>
          `).join("")}</tbody>
        </table>
      ` : `<p>${esc(report.summary || "请先上传外部客流/TGI资料。")}</p>`}
    </section>
    <section class="report-section">
      <h3>节点改进建议</h3>
      <div class="report-node-list">
        ${nodes.map((node) => `
          <div class="report-node">
            <b>${esc(shortId(node.node_id))} ${esc(node.node_name)}</b>
            <p>${esc(node.improvement)}</p>
          </div>
        `).join("")}
      </div>
    </section>
  `;
}

function renderSimulationPanel() {
  const box = $("#simulationStatus");
  if (!box) return;
  const latestJob = state.simulationJobs?.[0];
  const resultItems = state.latestSimulationResults?.items || [];
  if (state.latestSimulationResults?.error) {
    box.innerHTML = `<div class="simulation-empty">仿真任务接口暂不可用：${esc(state.latestSimulationResults.error)}</div>`;
    return;
  }
  if (!latestJob) {
    box.innerHTML = `
      <div class="simulation-empty">
        还没有仿真检查任务。点击“运行检查”会创建一个待复核任务，用当前 POI 和资料门禁检查数据闭环。
      </div>
    `;
    return;
  }
  const blocked = resultItems[0]?.blocked_gate_count ?? 0;
  const missingFields = resultItems.reduce((sum, row) => sum + Number(row.missing_business_field_count || 0), 0);
  const categories = resultItems.slice(0, 6).map((row) => `
    <tr>
      <td>${esc(row.park_id)}</td>
      <td>${esc(row.category)}</td>
      <td>${esc(row.candidate_count)}</td>
      <td>${esc(row.inside_osm_polygon_count)}</td>
      <td>${esc(listItems(row.why_blocked).slice(0, 2).join("；") || "待复核")}</td>
      <td>${esc(listItems(row.next_data_needed).slice(0, 2).join("；") || "待补资料")}</td>
    </tr>
  `).join("");
  box.innerHTML = `
    <div class="simulation-summary">
      <div><b>${esc(latestJob.job_id)}</b><span>${esc(latestJob.scenario_name)} · seed ${esc(latestJob.seed)} · ${esc(latestJob.iterations)} 次</span></div>
      <span class="status-pill danger">待复核 / 非最终</span>
    </div>
    <div class="simulation-metrics">
      <span><b>${esc(resultItems.length)}</b><em>结果行</em></span>
      <span><b>${esc(blocked)}</b><em>资料门禁未闭合</em></span>
      <span><b>${esc(missingFields)}</b><em>经营字段缺失</em></span>
    </div>
    <div class="simulation-actions">
      <button class="secondary-btn" id="refreshSimulationBtn">刷新任务</button>
      <a class="secondary-btn" href="/api/simulation/jobs/${encodeURIComponent(latestJob.job_id)}/export?format=csv">导出 CSV</a>
      <a class="secondary-btn" href="/api/simulation/jobs/${encodeURIComponent(latestJob.job_id)}/export?format=json">导出 JSON</a>
    </div>
    <div class="simulation-table">
      <table>
        <thead><tr><th>公园</th><th>业态</th><th>候选</th><th>边界内</th><th>为什么卡住</th><th>下一步资料</th></tr></thead>
        <tbody>${categories}</tbody>
      </table>
    </div>
  `;
}

async function runSimulationDryRun() {
  const button = $("#runSimulationBtn");
  button.disabled = true;
  button.textContent = "运行中";
  state.lastAction = "正在运行仿真检查";
  renderMeta();
  try {
    const response = await fetch("/api/simulation/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_name: "frontend_simulation_check",
        seed: 20260601,
        iterations: 100,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `simulation failed: ${response.status}`);
    state.lastAction = `已生成 ${payload.result_count || 0} 行待复核检查结果`;
    await loadSimulationJobs();
    renderSimulationPanel();
    renderMeta();
  } catch (error) {
    state.lastAction = error.message;
    renderMeta();
  } finally {
    button.disabled = false;
    button.textContent = "运行检查";
  }
}

async function submitUpload(event) {
  event.preventDefault();
  const fileInput = $("#sourceFile");
  if (!fileInput.files.length) {
    state.lastAction = "请先选择一个文件";
    renderMeta();
    return;
  }
  const form = new FormData();
  form.append("file", fileInput.files[0]);
  form.append("category", $("#uploadCategory").value);
  form.append("target_gate", $("#uploadGate").value);
  form.append("note", $("#uploadNote").value);
  const response = await fetch("/api/uploads", { method: "POST", body: form });
  const data = await response.json();
  state.lastAction = `已上传 ${data.filename}，进入待解析资料池`;
  fileInput.value = "";
  $("#uploadNote").value = "";
  await loadDashboard();
  setView("upload");
}

async function parseUpload(uploadId) {
  state.lastAction = "正在解析资料，请稍等";
  renderMeta();
  const response = await fetch(`/api/uploads/${encodeURIComponent(uploadId)}/parse`, { method: "POST" });
  if (!response.ok) throw new Error(`parse failed: ${response.status}`);
  const data = await response.json();
  state.lastAction = `已生成 ${data.filename} 的待复核候选`;
  await loadDashboard();
  setView("upload");
}

async function confirmCandidate(candidateId) {
  const reviewerNote = window.prompt("确认入池说明，例如：这份资料确实对应南园图纸/客流表/授权材料。");
  if (reviewerNote === null) return;
  const response = await fetch(`/api/upload-candidates/${encodeURIComponent(candidateId)}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reviewer_note: reviewerNote }),
  });
  if (!response.ok) throw new Error(`confirm failed: ${response.status}`);
  const data = await response.json();
  state.lastAction = `已确认 ${data.filename} 入待复核资料池`;
  await loadDashboard();
  setView("upload");
}

async function updateMapContext(event) {
  if (event) event.preventDefault();
  const input = $("#mapSearchInput");
  const keyword = input.value.trim();
  if (!keyword) return;
  const invalidMessage = invalidMapKeywordMessage(keyword);
  if (invalidMessage) {
    state.lastAction = invalidMessage;
    renderMeta();
    return;
  }
  state.lastAction = `正在定位：${keyword}`;
  state.mapLoading = true;
  state.mapTipsSeq += 1;
  state.mapSuppressTipsUntil = Date.now() + 2500;
  if (!state.amapReady) $("#mapCanvas").classList.add("loading");
  $("#mapSuggest").innerHTML = "";
  renderMeta();
  try {
    const response = await fetch("/api/amap/context", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ keyword }),
    });
    if (!response.ok) {
      const text = await response.text();
      throw new Error(`地图定位失败：${text}`);
    }
    const data = await response.json();
    pushMapHistory(state.data?.amap?.map_context);
    state.lastAction = `地图目标已更新：${data.matched_name || data.keyword}`;
    input.value = "";
    $("#mapSuggest").innerHTML = "";
    await loadDashboard();
    if (state.amapMap) state.amapMap.setZoomAndCenter(15, [Number(data.longitude), Number(data.latitude)], false, 500);
    setView("map");
  } finally {
    state.mapLoading = false;
    $("#mapCanvas").classList.remove("loading");
    $("#mapSuggest").innerHTML = "";
  }
}

async function updateMapContextFromSuggestion(tip) {
  $("#mapSearchInput").value = tip.name;
  $("#mapSuggest").innerHTML = "";
  state.lastAction = `正在定位：${tip.name}`;
  state.mapLoading = true;
  state.mapTipsSeq += 1;
  state.mapSuppressTipsUntil = Date.now() + 2500;
  $("#mapCanvas").classList.add("loading");
  renderMeta();
  try {
    const response = await fetch("/api/amap/context", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        keyword: tip.name,
        matched_name: tip.name,
        address: tip.address || tip.district || "",
        longitude: tip.longitude || "",
        latitude: tip.latitude || "",
      }),
    });
    if (!response.ok) throw new Error(`地图定位失败：${await response.text()}`);
    const data = await response.json();
    pushMapHistory(state.data?.amap?.map_context);
    state.lastAction = `地图目标已更新：${data.matched_name || data.keyword}`;
    $("#mapSearchInput").value = "";
    $("#mapSuggest").innerHTML = "";
    await loadDashboard();
    if (state.amapMap) state.amapMap.setZoomAndCenter(16, [Number(data.longitude), Number(data.latitude)], false, 500);
    setView("map");
  } finally {
    state.mapLoading = false;
    $("#mapCanvas").classList.remove("loading");
    $("#mapSuggest").innerHTML = "";
  }
}

async function fetchMapTips() {
  if (Date.now() < state.mapSuppressTipsUntil) return;
  const q = $("#mapSearchInput").value.trim();
  if (!q) {
    $("#mapSuggest").innerHTML = "";
    return;
  }
  const invalidMessage = invalidMapKeywordMessage(q);
  if (invalidMessage) {
    $("#mapSuggest").innerHTML = `<div class="map-suggest-empty">${esc(invalidMessage)}</div>`;
    return;
  }
  const seq = ++state.mapTipsSeq;
  $("#mapSuggest").innerHTML = `<div class="map-suggest-empty">正在搜索“${esc(q)}”……</div>`;
  let items = [];
  try {
    const response = await fetch(`/api/amap/tips?q=${encodeURIComponent(q)}`, { cache: "no-store" });
    const data = await response.json();
    items = Array.isArray(data.items) ? data.items : [];
  } catch (error) {
    state.lastAction = `地图提示暂未返回：${error.message}`;
    renderMeta();
  }
  if (seq !== state.mapTipsSeq) return;
  if (!items.length) {
    items = [{
      name: q,
      district: "按当前输入定位",
      address: "点击后由高德地点检索继续解析",
      longitude: "",
      latitude: "",
      output_status: "needs_review",
    }];
  }
  $("#mapSuggest").innerHTML = items.length ? items.map((item) => `
    <button type="button" class="map-suggest-item"
      data-tip='${esc(JSON.stringify(item))}'>
      <b>${esc(item.name)}</b>
      <span>${esc(item.district || "")} ${esc(item.address || "")}</span>
    </button>
  `).join("") : `<div class="map-suggest-empty">没有直接结果，换个关键词、拼音或更完整地址。</div>`;
  clearTimeout(state.mapAutoLocateTimer);
  if (shouldAutoLocateMap(q, items[0])) {
    state.mapAutoLocateTimer = setTimeout(() => {
      if ($("#mapSearchInput").value.trim() === q) {
        updateMapContextFromSuggestion(items[0]).catch((error) => {
          state.lastAction = error.message;
          renderMeta();
        });
      }
    }, 850);
  }
}

function pushMapHistory(context) {
  if (!context?.keyword) return;
  const last = state.mapContextHistory[state.mapContextHistory.length - 1];
  if (last && last.keyword === context.keyword && last.longitude === context.longitude && last.latitude === context.latitude) return;
  state.mapContextHistory.push({ ...context });
  state.mapContextHistory = state.mapContextHistory.slice(-8);
}

async function undoMapContext() {
  const previous = state.mapContextHistory.pop();
  if (!previous) {
    state.lastAction = "暂无可撤回的地图搜索";
    renderMeta();
    return;
  }
  $("#mapSearchInput").value = previous.keyword || previous.matched_name || "";
  await updateMapContextFromSuggestion({
    name: previous.keyword || previous.matched_name,
    address: previous.address,
    longitude: previous.longitude,
    latitude: previous.latitude,
  });
}

async function saveGateNote(domain) {
  const note = window.prompt("请填写这项资料缺口的补充说明，例如资料在哪、谁负责、下一步要问谁：");
  if (!note) return;
  const response = await fetch("/api/gate-inputs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ calibration_domain: domain, note }),
  });
  const data = await response.json();
  state.lastAction = `已记录 ${domain} 的补充说明 ${data.input_id}`;
  await loadDashboard();
  setView("data");
}

function fallbackAiIntro(node) {
  if (state.aiScope !== "node") {
    const uploadCount = state.data?.uploads?.length || 0;
    const nodeCount = state.data?.nodes?.length || 0;
    return `请从全局看这个项目：当前有 ${uploadCount} 份上传资料、${nodeCount} 个待复核节点。先综合判断资料缺口、地图位置、POI 供给和下一步工作，不要直接给最终推荐。`;
  }
  if (!node) {
    return "当前还没有外部上传项目资料。请先上传 DWG/DOCX/PDF/客流表等资料，AI 只能生成待复核解析建议。";
  }
  const missing = node.data_requests?.map((item) => item.missing_input).filter(Boolean).join("、")
    || node.must_collect_before_final
    || "真实客流、转化率、收益成本、运营授权、可信 DWG 转换产物";
  return `当前节点是 ${node.node_name}。它只能作为待复核草案讨论：几何、客流、转化率、收益成本、运营授权仍未闭合。下一步应向合作方补充：${missing}。`;
}

function currentProjectInfo() {
  const context = state.data?.amap?.map_context || {};
  const name = context.matched_name || context.keyword || "当前选址项目";
  const id = name.replace(/[^\w\u4e00-\u9fff-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 48) || "current-project";
  return { project_id: id, project_name: name };
}

function renderAiSessions() {
  if (!$("#aiProjectList") || !$("#aiSessionList")) return;
  const currentProject = currentProjectInfo();
  const projects = [...(state.aiSessions.projects || [])];
  if (!projects.some((item) => item.project_id === currentProject.project_id)) {
    projects.unshift({ ...currentProject, count: 0, updated_at: "" });
  }
  if (!state.activeAiProjectId) state.activeAiProjectId = projects[0]?.project_id || currentProject.project_id;
  $("#aiProjectList").innerHTML = projects.map((project) => `
    <button type="button" class="ai-project-item ${project.project_id === state.activeAiProjectId ? "active" : ""}" data-ai-project-id="${esc(project.project_id)}">
      <b>${esc(project.project_name || project.project_id)}</b>
      <span>${esc(project.count || 0)} 个对话</span>
    </button>
  `).join("");
  const sessions = (state.aiSessions.sessions || []).filter((item) => item.project_id === state.activeAiProjectId);
  $("#aiSessionList").innerHTML = sessions.length ? sessions.map((session) => `
    <button type="button" class="ai-session-item ${session.session_id === state.activeAiSessionId ? "active" : ""}" data-ai-session-id="${esc(session.session_id)}">
      <b>${esc(session.title || "未命名对话")}</b>
      <span>${esc(session.message_count || 0)} 条 · ${esc(session.updated_at || session.created_at || "")}</span>
    </button>
  `).join("") : `<div class="ai-rail-empty">这个项目还没有对话。点“新对话”开始。</div>`;
}

function renderChatMessagesFromSession(session) {
  const box = $("#chatMessages");
  box.innerHTML = "";
  const messages = session?.messages || [];
  if (!messages.length) {
    box.innerHTML = `
      <div class="chat-empty-state">
        <h2>项目综合回聊</h2>
        <p>上传资料、描述位置或直接说问题。系统会按全局资料、当前地图和节点缺口一起看。</p>
      </div>
    `;
    return;
  }
  messages.forEach((item) => addChatMessage(item.role === "user" ? "user" : "assistant", item.content || "", item.created_at || ""));
}

async function openAiSession(sessionId) {
  const response = await fetch(`/api/ai/sessions/${encodeURIComponent(sessionId)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`会话读取失败：${response.status}`);
  const data = await response.json();
  const session = data.session;
  state.activeAiSessionId = session.session_id;
  state.activeAiProjectId = session.project_id || state.activeAiProjectId;
  state.chatHistory = (session.messages || []).map((item) => ({ role: item.role, content: item.content }));
  renderAiSessions();
  renderChatMessagesFromSession(session);
  renderAiContext();
}

async function createAiSession() {
  const project = currentProjectInfo();
  const response = await fetch("/api/ai/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      project_id: project.project_id,
      project_name: project.project_name,
      title: "新对话",
      node_id: state.aiScope === "node" ? state.selectedNodeId : null,
    }),
  });
  if (!response.ok) throw new Error(`新建对话失败：${response.status}`);
  const data = await response.json();
  await loadAiSessions();
  await openAiSession(data.session.session_id);
  state.lastAction = "已开启新对话";
  renderMeta();
}

async function generateChatReport() {
  if (state.aiBusy) {
    state.lastAction = "AI 还在整理当前回复，等回复完成后再生成报告";
    renderMeta();
    return;
  }
  if (!state.activeAiSessionId) await createAiSession();
  const response = await fetch(`/api/ai/sessions/${encodeURIComponent(state.activeAiSessionId)}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ instruction: "根据当前会话，整理为给同事/客户看的待复核选址沟通报告。" }),
  });
  if (!response.ok) throw new Error(`生成报告失败：${response.status}`);
  const data = await response.json();
  state.lastAction = `AI 会话报告已生成：${data.report_path}`;
  renderMeta();
  addChatMessage("assistant", `报告已生成，可下载查看：${data.report_path}`, "needs_review / not_final");
  window.open(data.download_url, "_blank");
}

function renderAiContext() {
  const node = currentNode();
  const uploadCount = state.data?.uploads?.length || 0;
  const nodeCount = state.data?.nodes?.length || 0;
  if (state.aiScope !== "node") {
    $("#aiContext").innerHTML = `
      <details open class="ai-context-details">
        <summary>项目综合分析</summary>
        <div>
          <b>全局视角</b>
          <span>综合 ${nodeCount} 个节点、${uploadCount} 份上传资料、当前地图 POI 和资料缺口；默认不锁定任何单个节点。</span>
        </div>
        <div>
          <b>输出边界</b>
          <span>写给人看：先说判断，再说依据和下一步；不输出最终排名、收益预测或 ROI。</span>
        </div>
      </details>
      <button class="secondary-btn" type="button" id="aiUseNodeBtn">改为分析当前节点</button>
    `;
    return;
  }
  if (!node) {
    $("#aiContext").innerHTML = `
      <div>
        <b>等待外部上传资料</b>
        <span>当前没有可分析节点，先上传项目文件或客流数据。</span>
      </div>
      <div>
        <b>边界</b>
        <span>只生成待复核草案，不输出最终推荐。</span>
      </div>
    `;
    return;
  }
  $("#aiContext").innerHTML = `
    <div>
      <b>${esc(shortId(node.node_id))} ${esc(node.node_name)}</b>
      <span>${esc(node.primary_positioning || "待补场景")}</span>
    </div>
    <div>
      <b>边界</b>
      <span>只生成待复核草案，不输出最终推荐。</span>
    </div>
  `;
}

function addChatMessage(role, text, meta = "") {
  const box = $("#chatMessages");
  box.querySelector(".chat-empty-state")?.remove();
  const item = document.createElement("div");
  item.className = `chat-message ${role}`;
  item.innerHTML = `<div>${esc(text)}</div>${meta ? `<span>${esc(meta)}</span>` : ""}`;
  box.appendChild(item);
  box.scrollTop = box.scrollHeight;
  return item;
}

async function sendChat() {
  const input = $("#chatInput");
  const message = input.value.trim();
  if (!message && !state.pendingAttachments.length) return;
  const node = state.aiScope === "node" ? currentNode() : null;
  const project = currentProjectInfo();
  state.aiBusy = true;
  if ($("#generateChatReportBtn")) $("#generateChatReportBtn").disabled = true;
  input.value = "";
  autoResizeComposer();
  const uploaded = await uploadComposerAttachments(message);
  const attachmentText = uploaded.length
    ? `\n\n已附资料：${uploaded.map((item) => `${item.filename}（${item.category}，${item.review_status}）`).join("；")}`
    : "";
  const composedMessage = `${message || "请先查看我上传的资料，并说明下一步怎么进入待复核解析。"}${attachmentText}`;
  addChatMessage("user", composedMessage);
  const thinking = addChatMessage("assistant thinking", "正在思考，请稍等……", "DeepSeek 深度分析中");
  thinking.querySelector("div").textContent = "正在读取上下文、整理资料缺口、调用 DeepSeek，并自动登记专家输入……";
  await saveFeedbackDraft(node, composedMessage, uploaded);
  try {
    const response = await fetch("/api/ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.activeAiSessionId,
        project_id: project.project_id,
        project_name: project.project_name,
        node_id: node?.node_id,
        message: composedMessage,
        upload_refs: uploaded,
        history: state.chatHistory.slice(-8),
      }),
    });
    const data = await response.json();
    thinking.remove();
    state.activeAiSessionId = data.session?.session_id || state.activeAiSessionId;
    state.activeAiProjectId = data.session?.project_id || state.activeAiProjectId;
    state.chatHistory.push({ role: "user", content: composedMessage });
    state.chatHistory.push({ role: "assistant", content: data.message || "" });
    addChatMessage("assistant", data.message || "DeepSeek 未返回内容", `${data.generated_by || "deepseek"} · 待复核`);
    state.lastAction = "AI 对话已更新，专家输入已登记为待复核";
    await loadAiSessions();
    renderAiSessions();
    await loadDashboard();
    setView("ai");
  } finally {
    state.aiBusy = false;
    if ($("#generateChatReportBtn")) $("#generateChatReportBtn").disabled = false;
  }
}

async function saveFeedbackDraft(node, comment, uploaded = []) {
  if (!comment) return;
  const response = await fetch("/api/expert-feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      node_id: node?.node_id || "PROJECT-UPLOAD",
      comment,
      position_note: uploaded.map((item) => item.filename).join("；"),
      data_hint: uploaded.length ? "uploaded_source_needs_review" : "needs_review",
    }),
  });
  return response.json();
}

async function uploadComposerAttachments(note) {
  if (!state.pendingAttachments.length) return [];
  const uploaded = [];
  for (const file of state.pendingAttachments) {
    const form = new FormData();
    form.append("file", file);
    form.append("category", "auto");
    form.append("target_gate", "");
    form.append("note", note || "通过专家 AI 工作台随对话上传，待 AI 解析。");
    const response = await fetch("/api/uploads", { method: "POST", body: form });
    uploaded.push(await response.json());
  }
  state.pendingAttachments = [];
  renderAttachmentTray();
  return uploaded;
}

function renderAttachmentTray() {
  const tray = $("#attachmentTray");
  if (!tray) return;
  tray.innerHTML = state.pendingAttachments.map((file, index) => `
    <span class="attachment-chip">
      ${esc(file.name)}
      <button type="button" data-remove-attachment="${index}" aria-label="移除附件">×</button>
    </span>
  `).join("");
}

function autoResizeComposer() {
  const input = $("#chatInput");
  if (!input) return;
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
}

function bindEvents() {
document.body.addEventListener("click", (event) => {
    const nodeBtn = event.target.closest("[data-node-id]");
    if (nodeBtn) {
      state.selectedNodeId = nodeBtn.dataset.nodeId;
      state.aiScope = "node";
      renderAll();
      if (nodeBtn.classList.contains("map-pin")) {
        setView("map");
      } else if (nodeBtn.dataset.view) {
        setView(nodeBtn.dataset.view);
      }
      return;
    }
    const viewBtn = event.target.closest("[data-view]");
    if (viewBtn) {
      if (viewBtn.dataset.view === "ai") {
        state.aiScope = viewBtn.dataset.aiScope || "project";
      }
      setView(viewBtn.dataset.view);
      return;
    }
    const aiPromptBtn = event.target.closest("[data-ai-prompt]");
    if (aiPromptBtn) {
      const input = $("#chatInput");
      input.value = aiPromptBtn.dataset.aiPrompt || "";
      input.focus();
      autoResizeComposer();
      return;
    }
    const newAiSessionBtn = event.target.closest("#newAiSessionBtn");
    if (newAiSessionBtn) {
      createAiSession().catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const aiProjectBtn = event.target.closest("[data-ai-project-id]");
    if (aiProjectBtn) {
      state.activeAiProjectId = aiProjectBtn.dataset.aiProjectId;
      const firstSession = (state.aiSessions.sessions || []).find((item) => item.project_id === state.activeAiProjectId);
      state.activeAiSessionId = firstSession?.session_id || null;
      state.chatHistory = [];
      renderAiSessions();
      renderChatMessagesFromSession(null);
      return;
    }
    const aiSessionBtn = event.target.closest("[data-ai-session-id]");
    if (aiSessionBtn) {
      openAiSession(aiSessionBtn.dataset.aiSessionId).catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const reportBtn = event.target.closest("#generateChatReportBtn");
    if (reportBtn) {
      generateChatReport().catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const aiUseNodeBtn = event.target.closest("#aiUseNodeBtn");
    if (aiUseNodeBtn) {
      state.aiScope = "node";
      renderAiContext();
      return;
    }
    const modeBtn = event.target.closest("[data-map-mode]");
    if (modeBtn) {
      state.mapMode = modeBtn.dataset.mapMode;
      $$("[data-map-mode]").forEach((btn) => btn.classList.toggle("active", btn === modeBtn));
      renderMap();
      return;
    }
    const gateNoteBtn = event.target.closest(".gate-note-btn");
    if (gateNoteBtn) saveGateNote(gateNoteBtn.dataset.gate);
    const parseBtn = event.target.closest(".parse-upload-btn");
    if (parseBtn) parseUpload(parseBtn.dataset.uploadId).catch((error) => {
      state.lastAction = error.message;
      renderMeta();
    });
    const confirmBtn = event.target.closest(".confirm-candidate-btn");
    if (confirmBtn) confirmCandidate(confirmBtn.dataset.candidateId).catch((error) => {
      state.lastAction = error.message;
      renderMeta();
    });
    const refreshSimulationBtn = event.target.closest("#refreshSimulationBtn");
    if (refreshSimulationBtn) loadSimulationJobs().then(() => {
      state.lastAction = "仿真检查任务已刷新";
      renderSimulationPanel();
      renderMeta();
    }).catch((error) => {
      state.lastAction = error.message;
      renderMeta();
    });
    const suggestBtn = event.target.closest(".map-suggest-item");
    if (suggestBtn) {
      updateMapContextFromSuggestion(JSON.parse(suggestBtn.dataset.tip)).catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
    }
    const removeAttachmentBtn = event.target.closest("[data-remove-attachment]");
    if (removeAttachmentBtn) {
      state.pendingAttachments.splice(Number(removeAttachmentBtn.dataset.removeAttachment), 1);
      renderAttachmentTray();
    }
    const uploadActionBtn = event.target.closest("[data-upload-action]");
    if (uploadActionBtn) {
      updateUploadAction(uploadActionBtn.dataset.uploadId, uploadActionBtn.dataset.uploadAction).catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
    }
  });

  $("#nodeSearch").addEventListener("input", renderNodes);
  $("#uploadForm").addEventListener("submit", submitUpload);
  $("#assetDrawerBtn").addEventListener("click", () => {
    state.assetDrawerOpen = !state.assetDrawerOpen;
    renderAssetDrawer();
  });
  $("#assetDrawerClose").addEventListener("click", () => {
    state.assetDrawerOpen = false;
    renderAssetDrawer();
  });
  $("#headerAiBtn").addEventListener("click", () => {
    state.aiScope = "project";
    setView("ai");
  });
  $("#headerDataBtn").addEventListener("click", () => setView("data"));
  $("#mapAskAiBtn").addEventListener("click", () => {
    state.aiScope = "node";
    setView("ai");
  });
  $("#aiComposer").addEventListener("submit", (event) => {
    event.preventDefault();
    sendChat();
  });
  $("#attachBtn").addEventListener("click", () => $("#aiFileInput").click());
  $("#aiFileInput").addEventListener("change", (event) => {
    state.pendingAttachments.push(...Array.from(event.target.files || []));
    event.target.value = "";
    renderAttachmentTray();
  });
  $("#chatInput").addEventListener("input", autoResizeComposer);
  $("#chatInput").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendChat();
    }
  });
  $("#refreshIntegrationBtn").addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    renderIntegrationStatus();
  });
  $("#runSimulationBtn").addEventListener("click", () => {
    runSimulationDryRun().catch((error) => {
      state.lastAction = error.message;
      renderMeta();
    });
  });
  $("#mapSearchForm").addEventListener("submit", (event) => {
    updateMapContext(event).catch((error) => {
      state.lastAction = error.message;
      renderMeta();
    });
  });
  $("#mapSearchInput").addEventListener("input", () => {
    clearTimeout(state.mapSuggestTimer);
    state.mapSuggestTimer = setTimeout(() => fetchMapTips().catch(() => {}), 250);
  });
  $("#mapZoomIn").addEventListener("click", () => changeMapZoom(0.25));
  $("#mapZoomOut").addEventListener("click", () => changeMapZoom(-0.25));
  $("#mapReset").addEventListener("click", resetMapView);
  $("#mapUndo").addEventListener("click", () => undoMapContext().catch((error) => {
    state.lastAction = error.message;
    renderMeta();
  }));
  $("#mapSelectedOnly").addEventListener("click", () => {
    state.mapSelectedOnly = !state.mapSelectedOnly;
    $("#mapSelectedOnly").classList.toggle("active", state.mapSelectedOnly);
    state.lastAction = state.mapSelectedOnly ? "已切换为只看所选节点" : "已恢复显示全部节点和 POI";
    renderMeta();
    renderMap();
  });
  $("#mapCanvas").addEventListener("wheel", (event) => {
    event.preventDefault();
    changeMapZoom(event.deltaY < 0 ? 0.15 : -0.15);
  }, { passive: false });
  $("#mapCanvas").addEventListener("pointerdown", (event) => {
    if (event.target.closest("button")) return;
    $("#mapCanvas").setPointerCapture(event.pointerId);
    state.mapDragging = { id: event.pointerId, x: event.clientX, y: event.clientY, pan: { ...state.mapPan } };
  });
  $("#mapCanvas").addEventListener("pointermove", (event) => {
    if (!state.mapDragging || state.mapDragging.id !== event.pointerId) return;
    state.mapPan = {
      x: state.mapDragging.pan.x + event.clientX - state.mapDragging.x,
      y: state.mapDragging.pan.y + event.clientY - state.mapDragging.y,
    };
    applyMapTransform();
  });
  $("#mapCanvas").addEventListener("pointerup", () => {
    if (state.mapDragging && (Math.abs(state.mapPan.x) > 6 || Math.abs(state.mapPan.y) > 6)) {
      panMapNative(state.mapPan.x, state.mapPan.y);
    }
    state.mapDragging = null;
  });
  $("#mapCanvas").addEventListener("pointercancel", () => { state.mapDragging = null; });
}

function initFromHash() {
  const hash = window.location.hash.replace("#", "");
  if (["nodes", "map", "upload", "data", "report", "ai"].includes(hash)) setView(hash);
}

bindEvents();
loadDashboard()
  .then(initFromHash)
  .catch((error) => {
    document.body.innerHTML = `<main class="fatal-error"><h1>页面加载失败</h1><p>${esc(error.message)}</p></main>`;
  });

setInterval(() => {
  if (document.visibilityState === "visible") {
    loadDashboard().catch(() => {});
  }
}, 60000);
