const state = {
  data: null,
  simulationJobs: [],
  latestSimulationResults: null,
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
  mapContextHistory: [],
  mapSelectedOnly: false,
  mapAddMode: false,
  manualNodes: [],
  lastAction: "",
  pendingAttachments: [],
};

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

function scoreOf(node) {
  const base = Number(node?.discussion_score || 0);
  const raw = Number.isFinite(base) ? base : 50;
  const context = state.data?.amap?.map_context || {};
  const contextText = `${context.keyword || ""}${context.matched_name || ""}`;
  const isOsen = contextText.includes("奥森") || contextText.includes("奥林匹克森林");
  if (!isOsen) return 0;
  const gates = state.data?.p3_gates || [];
  const blockedGateCount = gates.filter((gate) => {
    const status = String(gate.current_gate_status || "");
    return status.includes("blocked") || status.includes("pending") || status.includes("not_ready");
  }).length;
  const simRows = state.latestSimulationResults?.items || [];
  const simMissing = simRows.reduce((sum, row) => sum + Number(row.missing_business_field_count || 0), 0);
  const simBlocked = Number(simRows[0]?.blocked_gate_count || blockedGateCount || 0);
  const poiCount = Number(state.data?.amap?.status?.point_count || 0);
  const boundaryStatus = String(state.data?.amap?.boundary_status || "");
  let penalty = 0;
  penalty += Math.min(30, simBlocked * 5);
  penalty += Math.min(18, Math.ceil(simMissing / 8));
  if (!simRows.length) penalty += 8;
  if (poiCount < 20) penalty += 6;
  if (boundaryStatus.includes("estimated")) penalty += 8;
  return Math.max(0, Math.min(100, Math.round(raw - penalty)));
}

function scoreText(node) {
  const context = state.data?.amap?.map_context || {};
  const contextText = `${context.keyword || ""}${context.matched_name || ""}`;
  if (!(contextText.includes("奥森") || contextText.includes("奥林匹克森林"))) return "外部预览";
  return `${scoreOf(node)} 分`;
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
  state.selectedNodeId = state.selectedNodeId || state.data.nodes[0]?.node_id;
  renderAll();
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
  renderDataPage();
  renderSimulationPanel();
  renderAiContext();
  renderIntegrationStatus();
}

function renderMeta() {
  $("#dataVersion").textContent = `待复核草案 · ${state.data.meta?.updated_at || ""}`;
  const titles = {
    overview: "先选任务，再进入地图、节点或 AI 工作台",
    nodes: "查看节点细节，所有内容仍为 feedback draft",
    map: "用地图讨论位置关系，不生成 DWG 几何结论",
    upload: "上传方案、图纸、图片和数据表，进入待解析资料池",
    data: "把资料缺口变成可执行任务",
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
  requestAnimationFrame(() => window.scrollTo(0, 0));
}

function priorityLabel(node) {
  const score = scoreOf(node);
  const context = state.data?.amap?.map_context || {};
  const contextText = `${context.keyword || ""}${context.matched_name || ""}`;
  if (!(contextText.includes("奥森") || contextText.includes("奥林匹克森林"))) return ["仅地图预览", "fail"];
  if (score >= 70) return ["优先讨论", "good"];
  if (score >= 55) return ["需补证再议", "warn"];
  return ["暂缓讨论", "fail"];
}

function renderOverview() {
  const nodes = state.data.nodes || [];
  $("#overviewNodeList").innerHTML = nodes.map((node) => {
    const [label, cls] = priorityLabel(node);
    return `
      <button class="overview-node ${node.node_id === state.selectedNodeId ? "active" : ""}" data-node-id="${esc(node.node_id)}" data-view="nodes">
        <b>${esc(shortId(node.node_id))} ${esc(node.node_name)}</b>
        <span class="${cls}">${label} · ${esc(scoreText(node))}</span>
      </button>
    `;
  }).join("");

  const feedbackCount = state.data.expert_feedback?.length || 0;
  $("#overviewNextSteps").innerHTML = [
    ["补齐几何", "已有 CAD图及其计划 资料，但需要上传/选择后进入解析流程。", "upload", "上传或选择图纸"],
    ["补真实客流", "客流、转化率、收益成本等闸门仍不能作为 checked。", "data", "查看数据请求"],
    ["专家录入意见", `当前已记录 ${feedbackCount} 条专家意见；继续写入后会自动刷新。`, "ai", "打开 AI 工作台"],
    ["留给员工 A 的接口", "可继续接正式地图底图、导出报告、图片上传和 Figma 视觉细化。", "map", "查看地图接口"],
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
      <div class="upload-actions">
        <button class="secondary-btn parse-upload-btn" data-upload-id="${esc(item.upload_id)}">AI 解析</button>
        <button class="secondary-btn" data-view="ai" data-upload-name="${esc(item.filename)}">带入 AI 对话</button>
        <button class="secondary-btn" data-view="data">关联资料缺口</button>
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
          <span>${esc(item.review_status)} · ${esc(item.generated_by || "local_rules")}</span>
        </div>
        <p>${esc(item.summary || "已生成待复核资料候选。")}</p>
        <div class="request-tags">${(item.related_gates || []).map((gate) => `<span>${esc(gateTitle(gate))}</span>`).join("")}</div>
        <div class="candidate-actions">
          <button class="secondary-btn" data-view="data">查看资料闭合</button>
          ${item.review_status === "已确认入池" ? "" : `<button class="primary-btn confirm-candidate-btn" data-candidate-id="${esc(item.candidate_id)}">确认入池</button>`}
        </div>
      </div>
    `).join("")}
  `;
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
  if (!node) return;
  $("#detailTitle").textContent = `${shortId(node.node_id)} ${node.node_name}`;
  $("#statusTag").textContent = "待复核 / 非最终";
  const directions = node.business_direction?.length ? node.business_direction : node.candidate_business_formats || [];
  const scenarios = node.feedback_scenarios?.length ? node.feedback_scenarios : [];
  const requests = node.data_requests?.length ? node.data_requests : [];
  const assumptions = node.assumption_refs?.slice(0, 3) || [];

  $("#detailBody").innerHTML = `
    <div class="detail-top">
      <div class="metric"><span>面积</span><b>${esc(node.area_sqm)} m²</b></div>
      <div class="metric"><span>实时草案分</span><b>${esc(scoreText(node))}</b></div>
      <div class="metric"><span>边界</span><b>反馈草案</b></div>
    </div>
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
    <div class="detail-actions">
      <button class="secondary-btn" data-view="map">在地图中查看</button>
      <button class="primary-btn" data-view="ai">带着这个节点问 AI</button>
    </div>
  `;
}

function renderMap() {
  const active = currentNode();
  const amap = state.data.amap || {};
  const status = amap.status || {};
  const context = amap.map_context || {};
  const contextName = `${context.keyword || ""}${context.matched_name || ""}`;
  const isOsenContext = contextName.includes("奥森") || contextName.includes("奥林匹克森林");
  $("#amapStatusText").textContent = status.web_service_key_available
    ? `高德后端读取；目标：${context.matched_name || context.keyword || "默认项目"}；${isOsenContext ? "奥森项目上下文" : "外部地点仅作地图预览，不套用奥森评分"}；已加载 ${status.point_count || 0} 条 POI`
    : "未检测到高德 Key；显示本地示意层；前端不会暴露 Key";
  if ($("#mapSearchInput") && !$("#mapSearchInput").value) {
    $("#mapSearchInput").placeholder = context.keyword ? `搜索地点、拼音或地址 · 当前：${context.keyword}` : "搜索地点、拼音或地址";
  }

  const img = $("#amapBaseMap");
  $("#mapCanvas").classList.add("loading");
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
  }).join("") + state.manualNodes.map((node, index) => `
    <button class="map-pin manual" style="left:${node.x}%;top:${node.y}%" title="人工新增待复核节点">M-${index + 1}</button>
  `).join("");

  $("#mapCanvas").className = `map-canvas mode-${state.mapMode}`;
  if (state.mapAddMode) $("#mapCanvas").classList.add("add-mode");
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
  state.mapNativeZoom = Math.max(3, Math.min(20, Number((state.mapNativeZoom + delta).toFixed(2))));
  state.mapZoom = 1;
  state.mapPan = { x: 0, y: 0 };
  applyMapTransform();
  refreshMapImage();
}

function resetMapView() {
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
    box.innerHTML = (data.items || []).map((item) => {
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
  $("#mapSideDetail").innerHTML = `
    <h3>${esc(shortId(node.node_id))} ${esc(node.node_name)}</h3>
    <div class="map-score ${cls}">${label} · ${esc(scoreText(node))}</div>
    <p>${esc(node.primary_positioning || node.scene_assumptions || "待补场景")}</p>
    <div class="mini-kv"><span>面积</span><b>${esc(node.area_sqm === "待测" ? "待测" : `${node.area_sqm} m²`)}</b></div>
    <div class="mini-kv"><span>状态</span><b>待复核 / 非最终</b></div>
    <div class="mini-kv"><span>地图边界</span><b>示意层，非 DWG</b></div>
    ${node.source_node_name ? `<div class="mini-kv"><span>来源草案</span><b>${esc(node.source_node_name)}</b></div>` : ""}
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
        还没有仿真任务。点击“运行干跑”会创建一个待复核任务，用当前 POI 和 P3 gate 检查后端闭环。
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
      <td>${esc(row.missing_business_field_count)}</td>
    </tr>
  `).join("");
  box.innerHTML = `
    <div class="simulation-summary">
      <div><b>${esc(latestJob.job_id)}</b><span>${esc(latestJob.scenario_name)} · seed ${esc(latestJob.seed)} · ${esc(latestJob.iterations)} 次</span></div>
      <span class="status-pill danger">待复核 / 非最终</span>
    </div>
    <div class="simulation-metrics">
      <span><b>${esc(resultItems.length)}</b><em>结果行</em></span>
      <span><b>${esc(blocked)}</b><em>P3 未闭合 gate</em></span>
      <span><b>${esc(missingFields)}</b><em>经营字段缺失</em></span>
    </div>
    <div class="simulation-actions">
      <button class="secondary-btn" id="refreshSimulationBtn">刷新任务</button>
      <a class="secondary-btn" href="/api/simulation/jobs/${encodeURIComponent(latestJob.job_id)}/export?format=csv">导出 CSV</a>
      <a class="secondary-btn" href="/api/simulation/jobs/${encodeURIComponent(latestJob.job_id)}/export?format=json">导出 JSON</a>
    </div>
    <div class="simulation-table">
      <table>
        <thead><tr><th>公园</th><th>业态</th><th>候选</th><th>边界内</th><th>缺字段</th></tr></thead>
        <tbody>${categories}</tbody>
      </table>
    </div>
  `;
}

async function runSimulationDryRun() {
  const button = $("#runSimulationBtn");
  button.disabled = true;
  button.textContent = "运行中";
  state.lastAction = "正在运行结构化仿真干跑";
  renderMeta();
  try {
    const response = await fetch("/api/simulation/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scenario_name: "frontend_structural_dry_run",
        seed: 20260601,
        iterations: 100,
      }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `simulation failed: ${response.status}`);
    state.lastAction = `已生成 ${payload.result_count || 0} 行待复核干跑结果`;
    await loadSimulationJobs();
    renderSimulationPanel();
    renderMeta();
  } catch (error) {
    state.lastAction = error.message;
    renderMeta();
  } finally {
    button.disabled = false;
    button.textContent = "运行干跑";
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
  state.lastAction = `正在定位：${keyword}`;
  $("#mapCanvas").classList.add("loading");
  $("#mapSuggest").innerHTML = "";
  renderMeta();
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
  resetMapView();
  await loadDashboard();
  setView("map");
}

async function updateMapContextFromSuggestion(tip) {
  $("#mapSearchInput").value = tip.name;
  $("#mapSuggest").innerHTML = "";
  state.lastAction = `正在定位：${tip.name}`;
  $("#mapCanvas").classList.add("loading");
  renderMeta();
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
  resetMapView();
  await loadDashboard();
  setView("map");
}

async function fetchMapTips() {
  const q = $("#mapSearchInput").value.trim();
  if (!q) {
    $("#mapSuggest").innerHTML = "";
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
  const missing = node.data_requests?.map((item) => item.missing_input).filter(Boolean).join("、")
    || node.must_collect_before_final
    || "真实客流、转化率、收益成本、运营授权、可信 DWG 转换产物";
  return `当前节点是 ${node.node_name}。它只能作为待复核草案讨论：几何、客流、转化率、收益成本、运营授权仍未闭合。下一步应向合作方补充：${missing}。`;
}

function renderAiContext() {
  const node = currentNode();
  if (!node) return;
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
  const item = document.createElement("div");
  item.className = `chat-message ${role}`;
  item.innerHTML = `<div>${esc(text)}</div>${meta ? `<span>${esc(meta)}</span>` : ""}`;
  box.appendChild(item);
  box.scrollTop = box.scrollHeight;
  return item;
}

async function requestAiReview(mode = "node") {
  const node = currentNode();
  addChatMessage("assistant", "正在请求 DeepSeek 生成待复核草稿……", "非最终");
  const response = await fetch("/api/ai/review", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, node_id: node?.node_id }),
  });
  const data = await response.json();
  const text = data.node_explanation || data.priority_discussion || data.why_feedback_draft || data.raw_text || JSON.stringify(data, null, 2);
  addChatMessage("assistant", text, data.generated_by || "deepseek");
}

async function sendChat() {
  const input = $("#chatInput");
  const message = input.value.trim();
  if (!message && !state.pendingAttachments.length) return;
  const node = currentNode();
  input.value = "";
  autoResizeComposer();
  const uploaded = await uploadComposerAttachments(message);
  const attachmentText = uploaded.length
    ? `\n\n已附资料：${uploaded.map((item) => `${item.filename}（${item.category}，${item.review_status}）`).join("；")}`
    : "";
  const composedMessage = `${message || "请先查看我上传的资料，并说明下一步怎么进入待复核解析。"}${attachmentText}`;
  addChatMessage("user", composedMessage);
  const thinking = addChatMessage("assistant thinking", "正在思考，请稍等……", "DeepSeek 深度分析中");
  thinking.querySelector("div").textContent = "正在读取上下文、整理资料缺口、调用 DeepSeek……";
  await saveFeedbackDraft(node, composedMessage, uploaded);
  const response = await fetch("/api/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      node_id: node?.node_id,
      message: composedMessage,
      upload_refs: uploaded,
      history: state.chatHistory.slice(-8),
    }),
  });
  const data = await response.json();
  thinking.remove();
  state.chatHistory.push({ role: "user", content: composedMessage });
  state.chatHistory.push({ role: "assistant", content: data.message || "" });
  addChatMessage("assistant", data.message || "DeepSeek 未返回内容", `${data.generated_by || "deepseek"} · 待复核`);
  state.lastAction = "AI 对话已更新";
  await loadDashboard();
  setView("ai");
}

async function saveFeedbackDraft(node, comment, uploaded = []) {
  if (!comment) return;
  const response = await fetch("/api/expert-feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      node_id: node?.node_id,
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
    const viewBtn = event.target.closest("[data-view]");
    if (viewBtn) {
      setView(viewBtn.dataset.view);
      return;
    }
    const nodeBtn = event.target.closest("[data-node-id]");
    if (nodeBtn) {
      state.selectedNodeId = nodeBtn.dataset.nodeId;
      renderAll();
      if (nodeBtn.classList.contains("map-pin")) setView("map");
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
      state.lastAction = "?????????";
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
  });

  $("#nodeSearch").addEventListener("input", renderNodes);
  $("#uploadForm").addEventListener("submit", submitUpload);
  $("#headerAiBtn").addEventListener("click", () => setView("ai"));
  $("#headerDataBtn").addEventListener("click", () => setView("data"));
  $("#mapAskAiBtn").addEventListener("click", () => setView("ai"));
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
  $("#refreshIntegrationBtn").addEventListener("click", renderIntegrationStatus);
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
  $("#mapAddNode").addEventListener("click", () => {
    state.mapAddMode = !state.mapAddMode;
    state.lastAction = state.mapAddMode ? "设点模式：在地图上点击新增待复核节点" : "已退出设点模式";
    renderMeta();
    renderMap();
  });
  $("#mapCanvas").addEventListener("wheel", (event) => {
    event.preventDefault();
    changeMapZoom(event.deltaY < 0 ? 0.15 : -0.15);
  }, { passive: false });
  $("#mapCanvas").addEventListener("pointerdown", (event) => {
    if (event.target.closest("button")) return;
    if (state.mapAddMode) {
      const rect = $("#mapCanvas").getBoundingClientRect();
      state.manualNodes.push({
        x: Number((((event.clientX - rect.left) / rect.width) * 100).toFixed(2)),
        y: Number((((event.clientY - rect.top) / rect.height) * 100).toFixed(2)),
      });
      state.mapAddMode = false;
      state.lastAction = "已新增 1 个待复核人工节点";
      renderMeta();
      renderMap();
      return;
    }
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
  if (["nodes", "map", "upload", "data", "ai"].includes(hash)) setView(hash);
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
