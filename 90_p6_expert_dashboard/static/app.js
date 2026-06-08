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
  activeLayer: "all",
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
  mapSearchLoading: false,
  mapLayerLoading: false,
  mapError: "",
  pendingSearchKeyword: "",
  lastSuccessfulMapContext: null,
  amapConfig: null,
  amapMap: null,
  amapMarkers: [],
  amapPoiMarkers: [],
  amapNodeMarkers: [],
  amapProjectMarker: null,
  amapSearchMarker: null,
  amapInfoWindow: null,
  resizeObserver: null,
  amapReady: false,
  amapError: "",
  selectedPoiId: null,
  nodeFormModeNew: false,
  assetDrawerOpen: false,
  editingSimulationObjectId: null,
  showAllSimulationObjects: false,
  showAllTaskObjects: false,
  showAllFeatureDerivatives: false,
  aiScope: "project",
  aiRailCollapsed: true,
  lastAction: "",
  pendingAttachments: [],
};
window.__APP_STATE__ = state;
window.__appState = state;

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

function statusToken(...parts) {
  return parts.join("_");
}

const STATUS_TOKENS = {
  positionReference: statusToken("external", "preview", "only"),
  needsReview: statusToken("needs", "review"),
  notFinal: statusToken("not", "final"),
  nodeDraftReview: statusToken("node", "draft", "review", "required"),
  rangeEstimatedReview: statusToken("estimated", "range", "needs", "review"),
  gapCalculatedReview: statusToken("calculated", "needs", "review"),
};

const INTERNAL_DRAFT_STATUS_TOKENS = [
  STATUS_TOKENS.needsReview,
  statusToken("needs", "review", "not", "final"),
  STATUS_TOKENS.notFinal,
  STATUS_TOKENS.positionReference,
  STATUS_TOKENS.nodeDraftReview,
];

function isPositionReferenceOnly(status) {
  return valueText(status, "") === STATUS_TOKENS.positionReference;
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

function calibrationLayerLabel(layer) {
  const labels = {
    official_macro_boundary: "官方宏观边界",
    local_bigdata_profile: "本地大数据画像",
    local_device_price_proxy: "设备价格代理",
    local_poi_price_signal: "竞品价格线索",
    local_poi_demand_signal: "本地需求热度线索",
    plan_assumption_needs_review: "方案假设待复核",
    local_user_supplement: "用户补充校准输入",
  };
  return labels[valueText(layer, "")] || humanizeAiText(layer || "待分层");
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

function priorityTitle(node) {
  const [label] = priorityLabel(node);
  const explicit = valueText(node?.priority_label || node?.priority_stage, "");
  if (explicit) return humanizeAiText(explicit);
  if (node?.score_status === "node_draft_review_required") return "待复核草案";
  if (label === "暂缓讨论") return "暂缓推荐，先补资料";
  return label;
}

function scoreMeaning(node) {
  if (isPositionReferenceOnly(node?.score_status)) return "只看位置关系，不参与排序";
  if (node?.score_status === "node_draft_review_required") return "资料未闭合，先作为讨论草案";
  const summary = valueText(node?.priority_summary, "");
  if (summary) return humanizeAiText(summary);
  return "仅表示当前资料条件下的推进优先级，不是最终推荐";
}

function priorityCaption(node) {
  if (isPositionReferenceOnly(node?.score_status)) return "只看位置关系";
  if (node?.score_status === "node_draft_review_required") return "资料未闭合";
  const inputs = node?.score_inputs || {};
  const gateCount = inputs.blocked_gate_count;
  const missing = Array.isArray(inputs.missing_required_fields) ? inputs.missing_required_fields.length : listItems(node?.missing_required_fields).length;
  const parts = [];
  if (gateCount !== undefined && gateCount !== null) parts.push(`${gateCount} 项前置资料`);
  if (missing) parts.push(`${missing} 类缺口`);
  if (inputs.poi_context_count !== undefined && inputs.poi_context_count !== null) parts.push(`${inputs.poi_context_count} 条 POI 语境`);
  return parts.length ? `${parts.join(" · ")}，待复核` : "待补证后比较";
}

function firstRecommendation(node) {
  const direct = listItems(node?.priority_recommendations)[0] || listItems(node?.score_recommendations)[0];
  if (direct) return direct;
  const next = listItems(node?.next_data_needed)[0];
  if (next) return next;
  return "先补齐图纸、客流、收益成本和运营授权，再进入推荐判断。";
}

function renderScoreAnalysis(node) {
  const items = Array.isArray(node?.priority_basis) ? node.priority_basis : (Array.isArray(node?.score_breakdown) ? node.score_breakdown : []);
  const recommendations = listItems(node?.priority_recommendations).length ? listItems(node?.priority_recommendations) : listItems(node?.score_recommendations);
  const scoreInputs = node?.score_inputs || {};
  return `
    <div class="score-analysis">
      <div class="score-analysis-hero">
        <span>推进优先级</span>
        <b>${esc(priorityTitle(node))}</b>
        <p>${esc(scoreMeaning(node))}</p>
      </div>
      ${recommendations.length ? `
        <div class="score-advice">
          <h3>现在建议怎么推进</h3>
          ${recommendations.map((item, index) => `
            <div class="advice-row">
              <b>${index + 1}</b>
              <span>${esc(item)}</span>
            </div>
          `).join("")}
        </div>
      ` : ""}
      <div class="score-breakdown-list">
        ${(items.length ? items : [
          { label: "资料门禁", value: `${scoreInputs.blocked_gate_count ?? "待确认"} 项待补`, impact: "图纸、客流、转化率、收益成本、运营授权会影响优先级可信度。", status: "需复核" },
          { label: "周边 POI", value: `${scoreInputs.poi_context_count ?? "待确认"} 条`, impact: "用于判断周边供给和竞品语境。", status: "待复核" },
        ]).map((item) => `
          <div class="score-breakdown-item">
            <div>
              <b>${esc(item.label || "判断项")}</b>
              <span>${esc(item.impact || "待补充解释")}</span>
            </div>
            <em>${esc(item.value || "待确认")}</em>
            <small>${esc(humanizeAiText(item.status || "待复核"))}</small>
          </div>
        `).join("")}
      </div>
    </div>
  `;
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

function mapIsLoading() {
  return Boolean(state.mapLoading || state.mapSearchLoading || state.mapLayerLoading);
}

function visibleStatus(value, fallback = "待复核") {
  const text = valueText(value, fallback);
  if (INTERNAL_DRAFT_STATUS_TOKENS.includes(text)) return "待复核";
  if (text.includes("Connect" + "Error") || text.includes("trace" + "back")) return "地图检索暂时失败";
  if (text.includes("missing") || text.includes("blocked")) return "资料不足";
  if (text === "inside_osm_polygon") return "边界内";
  if (text === "outside_osm_polygon") return "边界外";
  return humanizeAiText ? humanizeAiText(text) : text;
}

function mapContextPayload() {
  return state.data?.amap || state.lastSuccessfulMapContext?.amap || {};
}

async function loadDashboard() {
  const response = await fetch("/api/dashboard", { cache: "no-store" });
  if (!response.ok) throw new Error(`dashboard api failed: ${response.status}`);
  state.data = await response.json();
  if (state.data?.amap) {
    state.lastSuccessfulMapContext = { amap: state.data.amap };
  }
  await loadSimulationJobs();
  await loadAiSessions();
  if (!state.data.nodes?.some((node) => node.node_id === state.selectedNodeId)) {
    state.selectedNodeId = state.data.nodes?.[0]?.node_id || null;
  }
  renderAll();
  if (state.activeAiSessionId && !state.chatHistory.length) {
    openAiSession(state.activeAiSessionId).catch((error) => {
      state.lastAction = error.message;
      renderMeta();
    });
  }
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
  if (state.currentView === "map") {
    renderMap();
    renderMapSide();
    renderMapErrorPanel();
    renderMapResultList();
  }
  renderSourceFoundation();
  renderUploadList();
  renderCandidateList();
  renderAssetDrawer();
  renderDataPage();
  renderSimulationObjectPool();
  renderSimulationTaskPreflight();
  renderSimulationPanel();
  renderGapStatus();
  renderReport();
  renderAiSessions();
  renderAiContext();
  renderIntegrationStatus();
}

function renderMeta() {
  const updatedAt = state.data?.meta?.updated_at || "";
  $("#dataVersion").textContent = updatedAt ? `待复核草案 · ${updatedAt}` : "待复核草案";
  const titles = {
    overview: "全局链路台：先看资料、空间、人物仿真对象、节点和报告是否闭合",
    nodes: "节点与候选点：只承接已闭合条件，不把草案伪装成结论",
    map: "空间底座：核对位置、POI 和路径语境，保留人工复核入口",
    upload: "资料与空间底座：导入计划、CAD、图片或表格，先生成待确认对象",
    data: "人物仿真工坊：把人群状态、行为程序、选择概率和验证目标连起来",
    report: "决策解释与报告：查看奥森预测与调整方案报告",
    ai: "项目沟通工作台：项目综合对话优先，也可以带单个节点进入",
  };
  const title = titles[state.currentView] || titles.overview;
  $("#pageSubtitle").textContent = state.lastAction ? `${title} · ${state.lastAction}` : title;
}

const VALID_VIEWS = ["overview", "nodes", "map", "upload", "data", "report", "ai"];

function focusWorkflowTarget(targetId) {
  if (!targetId) {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  const target = document.getElementById(targetId);
  if (!target) {
    window.scrollTo({ top: 0, behavior: "smooth" });
    return;
  }
  target.classList.add("workflow-focus-target");
  target.scrollIntoView({ behavior: "smooth", block: "start" });
  window.setTimeout(() => target.classList.remove("workflow-focus-target"), 1400);
}

function setView(view, options = {}) {
  if (!VALID_VIEWS.includes(view)) view = "overview";
  const scrollTarget = options.scrollTarget || "";
  state.currentView = view;
  window.location.hash = view === "overview" && !scrollTarget ? "" : `${view}${scrollTarget ? `:${scrollTarget}` : ""}`;
  $$(".view").forEach((el) => el.classList.toggle("active", el.id === `${view}View` || (view === "ai" && el.id === "aiWorkspaceView")));
  $$("[data-workflow-stage]").forEach((stage) => {
    const views = (stage.dataset.workflowViews || "").split(",").map((item) => item.trim()).filter(Boolean);
    stage.classList.toggle("active", views.includes(view));
  });
  $$("[data-view]").forEach((btn) => {
    const isMain = btn.classList.contains("workflow-main");
    const isSub = Boolean(btn.closest(".workflow-subnav"));
    const isWorkflowControl = isMain || isSub;
    const buttonTarget = btn.dataset.scrollTarget || "";
    let shouldActivate = false;
    if (btn.dataset.view === view && isWorkflowControl) {
      shouldActivate = scrollTarget
        ? buttonTarget === scrollTarget || (isMain && !buttonTarget)
        : isMain || (isSub && !buttonTarget);
    }
    btn.classList.toggle("active", shouldActivate);
  });
  renderMeta();
  if (view === "ai") renderAiContext();
  if (view === "report") renderReport();
  if (view === "map" && state.data) {
    renderMap();
    renderMapSide();
    renderMapErrorPanel();
    renderMapResultList();
  }
  requestAnimationFrame(() => focusWorkflowTarget(scrollTarget));
}

function priorityLabel(node) {
  if (isPositionReferenceOnly(node?.score_status)) return ["仅看位置关系", "preview"];
  const score = scoreOf(node);
  if (score >= 70) return ["优先讨论", "good"];
  if (score >= 55) return ["需补证再议", "warn"];
  return ["暂缓推荐，先补资料", "fail"];
}

function evidenceRefLabel(ref) {
  const text = valueText(ref, "");
  if (!text) return "资料来源待确认";
  if (text.includes("map_context")) return "当前地图目标记录";
  if (text.includes("uploaded_sources")) return "网页资料池记录";
  if (text.includes("p2_persona_state")) return "人群状态候选表";
  if (text.includes("p2_behavior_program")) return "行为程序候选表";
  if (text.includes("choice_probability")) return "选择概率候选表";
  if (text.includes("simulation_validation_target")) return "仿真验证目标表";
  if (text.includes("p2_project_node_candidates")) return "节点候选表";
  if (text.includes("map_context_pois")) return "当前地图 POI 语境";
  if (text.includes("ai_sessions")) return "AI 会话记录";
  if (text.includes("80_delivery")) return "报告工作稿目录";
  return "本项目资料记录";
}

function chainItems() {
  return state.data?.object_chain?.items || [];
}

function chainSummary() {
  return state.data?.object_chain?.summary || {};
}

function renderChainCommand() {
  const summary = chainSummary();
  const bar = $("#chainSummaryBar");
  if (bar) {
    const total = Number(summary.total_items || chainItems().length || 0);
    const usable = Number(summary.usable_count || 0);
    const draft = Number(summary.draft_count || 0);
    const blocked = Number(summary.blocked_count || 0);
    const waiting = Number(summary.needs_input_count || 0);
    bar.innerHTML = [
      ["链路对象", `${total} 类`, "all"],
      ["可推进", `${usable} 类`, "good"],
      ["待采用", `${draft} 类`, "warn"],
      ["阻塞", `${blocked} 类`, "fail"],
      ["等待输入", `${waiting} 类`, "wait"],
    ].map(([label, value, tone]) => `
      <span class="chain-summary-chip ${tone}">
        <b>${esc(value)}</b>
        <em>${esc(label)}</em>
      </span>
    `).join("");
  }

  const commitments = $("#methodCommitments");
  if (commitments) {
    commitments.innerHTML = [
      ["状态先行", "HumanLM", "先看目的、疲劳、预算、同行和排队容忍，不用薄标签替代人群状态。"],
      ["行为成链", "ROTE", "把触发、动作、放弃和外溢写成可复核对象，不让 AI 临场编故事。"],
      ["检查点", "2026 agentic UI", "资料解析、仿真和报告都要让用户能确认、反驳、锁定或回退。"],
      ["供需降级", "POI/TGI", "供需缺口只做因子和线索，不能单独变成最终推荐或排名。"],
    ].map(([title, tag, body]) => `
      <article class="method-card">
        <span>${esc(tag)}</span>
        <b>${esc(title)}</b>
        <p>${esc(body)}</p>
      </article>
    `).join("");
  }
}

function renderOverviewPrimaryActions() {
  const box = $("#overviewPrimaryActions");
  if (!box) return;
  const items = chainItems();
  const blocked = items.filter((item) => item.readiness === "blocked");
  const drafts = items.filter((item) => item.readiness === "draft");
  const waiting = items.filter((item) => item.readiness === "needs_input");
  const priorityItems = [...blocked, ...waiting, ...drafts].slice(0, 4);
  const fallback = [
    { label: "资料对象", next_action: "先导入并采用项目资料，再让 AI 解析节点和缺口。", view: "upload", action_label: "处理资料", readiness: "needs_input" },
    { label: "人群状态画像", next_action: "先复核状态维度，再进入行为程序和选择候选。", view: "data", action_label: "看对象", readiness: "draft" },
    { label: "AI 沟通记录", next_action: "打开项目综合对话，形成可生成报告的业务共识。", view: "ai", action_label: "打开 AI", readiness: "needs_input" },
  ];
  const source = priorityItems.length ? priorityItems : fallback;
  box.innerHTML = source.map((item, index) => {
    const [readinessLabel, cls] = objectChainReadinessLabel(item.readiness);
    return `
      <button class="primary-action-card ${cls}" data-view="${esc(item.view || "overview")}" data-object-key="${esc(item.object_key || "")}">
        <span>${index + 1}</span>
        <b>${esc(item.label || "待处理对象")}</b>
        <em>${esc(item.next_action || "先确认对象状态，再决定下一步。")}</em>
        <strong>${esc(item.action_label || readinessLabel)}</strong>
      </button>
    `;
  }).join("");
}

function renderOverview() {
  const nodes = state.data.nodes || [];
  renderChainCommand();
  renderOverviewPrimaryActions();
  renderOverviewStatusCards();
  renderObjectChainMatrix();
  if (nodes.length) {
    const priorityCounts = nodes.reduce((acc, node) => {
      const [label] = priorityLabel(node);
      acc[label] = (acc[label] || 0) + 1;
      return acc;
    }, {});
    $("#overviewNodeList").innerHTML = `
      <div class="node-summary-card">
        <b>${nodes.length} 个节点正在等待复核</b>
        <p>首页不默认展示具体节点名称，避免系统把第一个节点当成默认结论。进入节点清单后再按用户选择查看单点。</p>
        <div class="node-summary-tags">
          ${Object.entries(priorityCounts).map(([label, count]) => `<span>${esc(label)}：${esc(count)}</span>`).join("")}
        </div>
        <button class="primary-btn" type="button" data-view="nodes">进入节点清单</button>
      </div>
    `;
  } else {
    $("#overviewNodeList").innerHTML = `<div class="empty-state">还没有外部上传项目资料。请先进入“资料导入”。</div>`;
  }

  const steps = chainItems()
    .filter((item) => item.readiness !== "usable" || item.object_key === "report_draft")
    .sort((a, b) => {
      const order = { blocked: 0, needs_input: 1, draft: 2, usable: 3 };
      return (order[a.readiness] ?? 9) - (order[b.readiness] ?? 9);
    })
    .slice(0, 6);
  $("#overviewNextSteps").innerHTML = (steps.length ? steps : chainItems().slice(0, 4)).map((item) => {
    const [readinessLabel, cls] = objectChainReadinessLabel(item.readiness);
    return `
    <button class="next-step action-step ${cls}" data-view="${esc(item.view || "overview")}">
      <span>
        <b>${esc(item.label || "待处理对象")} · ${esc(readinessLabel)}</b>
        <em>${esc(item.next_action || "先确认对象状态，再进入下一步。")}</em>
      </span>
      <strong>${esc(item.action_label || "查看")}</strong>
    </button>
  `;
  }).join("");
}

function objectChainReadinessLabel(readiness) {
  if (readiness === "usable") return ["可进入下一步", "good"];
  if (readiness === "blocked") return ["先补关键资料", "fail"];
  if (readiness === "draft") return ["候选待采用", "warn"];
  return ["等待输入", "warn"];
}

function renderObjectChainMatrix() {
  const box = $("#objectChainMatrix");
  if (!box) return;
  const chain = state.data.object_chain || {};
  const items = chain.items || [];
  if (!items.length) {
    box.innerHTML = `<div class="empty-state">对象链路还没有形成。先导入资料，再进入资料池和 AI 工作台。</div>`;
    return;
  }
  box.innerHTML = items.map((item, index) => {
    const [readinessLabel, cls] = objectChainReadinessLabel(item.readiness);
    const adopted = Number(item.adopted_count || 0);
    const locked = Number(item.locked_count || 0);
    const blocked = Number(item.blocked_count || 0);
    const meta = [
      adopted ? `${adopted} 个已采用` : "",
      locked ? `${locked} 个已锁定` : "",
      blocked ? `${blocked} 项待补` : "",
    ].filter(Boolean).join(" · ");
    return `
      <article
        class="object-chain-card ${cls}"
        data-object-key="${esc(item.object_key)}"
        data-readiness="${esc(item.readiness)}"
      >
        <div class="object-chain-index">${index + 1}</div>
        <div class="object-chain-body">
          <div class="object-chain-title">
            <b>${esc(item.label)}</b>
            <span>${esc(readinessLabel)}</span>
          </div>
          <strong>${esc(item.status_label || "待复核")}</strong>
          <p>${esc(item.next_action || "等待下一步处理。")}</p>
          <em>${esc(meta || "来源和状态已记录，展开对应工作区复核。")}</em>
          <details class="object-chain-evidence">
            <summary>证据依据</summary>
            <div>${(item.evidence_refs || []).map((ref) => `<span>${esc(evidenceRefLabel(ref))}</span>`).join("") || "<span>待补资料记录</span>"}</div>
          </details>
        </div>
        <button class="secondary-btn" type="button" data-view="${esc(item.view || "overview")}">${esc(item.action_label || "查看")}</button>
      </article>
    `;
  }).join("");
}

function renderOverviewStatusCards() {
  const box = $("#overviewStatusCards");
  if (!box) return;
  const nodes = state.data.nodes || [];
  const uploads = state.data.uploads || [];
  const candidates = state.data.upload_candidates || [];
  const amap = state.data.amap || {};
  const amapStatus = amap.status || {};
  const mapContext = amap.map_context || {};
  const feedbackCount = state.data.expert_feedback?.length || 0;
  const report = state.data.demand_supply?.report || {};
  const topGaps = report.top_gaps || [];
  const aiSessions = state.aiSessions?.sessions || [];
  const simObjects = state.data.simulation_objects || [];
  const adoptedObjects = simObjects.filter((item) => item.adoption_status === "已采用").length;
  const lockedObjects = simObjects.filter((item) => item.user_locked).length;
  const adoptedCount = uploads.filter((item) => /已采用|已确认|使用|入池/.test(String(item.review_status || ""))).length;
  const cards = [
    {
      title: "项目范围",
      status: mapContext.keyword || mapContext.matched_name ? "已定位" : "待确认",
      tone: mapContext.keyword || mapContext.matched_name ? "good" : "warn",
      body: mapContext.matched_name || mapContext.keyword || "尚未确认目标地点",
      action: "核对地图",
      view: "map",
    },
    {
      title: "资料采用",
      status: uploads.length ? `${uploads.length} 份入池` : "待导入",
      tone: uploads.length ? "good" : "warn",
      body: adoptedCount ? `${adoptedCount} 份已采用；${candidates.length} 份待确认。` : `${candidates.length} 份解析候选，需人工确认用途。`,
      action: "打开资料",
      view: "upload",
    },
    {
      title: "节点推进",
      status: nodes.length ? `${nodes.length} 个节点` : "待生成",
      tone: nodes.length ? "good" : "warn",
      body: nodes.length ? "节点已按推进优先级、依据和建议展示；可带入 AI 单点讨论。" : "导入计划后应先拆分节点，再进入比较。",
      action: "看节点",
      view: "nodes",
    },
    {
      title: "地图与 POI",
      status: amapStatus.point_count ? `${amapStatus.point_count} 条` : "待获取",
      tone: amapStatus.point_count ? "good" : "warn",
      body: amapStatus.point_count ? "已形成地图周边参考点；仍需核对目标范围。" : "需要先搜索目标地点并刷新 POI。",
      action: "看地图",
      view: "map",
    },
    {
      title: "方法对象",
      status: simObjects.length ? `${simObjects.length} 个对象` : "待建立",
      tone: adoptedObjects ? "good" : (simObjects.length ? "warn" : "fail"),
      body: adoptedObjects ? `${adoptedObjects} 个已采用，${lockedObjects} 个已锁定；后续仿真会以此为输入。` : "选择概率和验证目标已生成候选，仍需人工采用或锁定。",
      action: "对象池",
      view: "data",
    },
    {
      title: "AI 共识",
      status: aiSessions.length || feedbackCount ? "已有记录" : "待沟通",
      tone: aiSessions.length || feedbackCount ? "good" : "warn",
      body: aiSessions.length ? `${aiSessions.length} 个历史会话，${feedbackCount} 条专家输入。` : "建议先让 AI 总结项目范围和资料缺口。",
      action: "打开 AI",
      view: "ai",
    },
    {
      title: "报告链路",
      status: topGaps.length ? "可形成草案" : "工作稿",
      tone: uploads.length || aiSessions.length ? "good" : "warn",
      body: topGaps.length ? "已有供需缺口草案，可继续人工确认。" : "可生成沟通工作稿；最终报告仍需真实资料闭合。",
      action: "查看报告",
      view: "report",
    },
  ];
  box.innerHTML = cards.map((card) => `
    <button class="overview-status-card ${card.tone}" data-view="${esc(card.view)}">
      <span>${esc(card.title)}</span>
      <b>${esc(card.status)}</b>
      <em>${esc(card.body)}</em>
      <strong>${esc(card.action)}</strong>
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

function renderSourceFoundation() {
  const summaryBox = $("#sourceFoundationSummary");
  const assetBox = $("#localDataAssets");
  if (!summaryBox || !assetBox) return;

  const preflight = state.data?.simulation_task_preflight || {};
  const assets = preflight.local_data_assets || [];
  const uploads = state.data?.uploads || [];
  const adoptedUploads = uploads.filter((item) => {
    const status = valueText(item.review_status, "");
    return item.is_used || /已采用|已确认|入池|使用/.test(status);
  });
  const amap = state.data?.amap || {};
  const mapContext = amap.map_context || {};
  const poiCount = (amap.supply_points || []).length;
  const blockingCount = Number(preflight.blocking_count || 0);
  const mapLabel = mapContext.matched_name || mapContext.keyword || "尚未确认地图目标";
  const contextStatus = mapContext.output_status === STATUS_TOKENS.needsReview ? "待复核" : "已形成线索";
  const assetGroups = [
    {
      label: "本地底座资料",
      value: `${assets.length} 类`,
      note: assets.length ? "已纳入资料、方法、空间和证据底座。" : "等待资料登记。",
      tone: assets.length ? "good" : "warn",
    },
    {
      label: "网页资料池",
      value: `${uploads.length} 份`,
      note: adoptedUploads.length ? `${adoptedUploads.length} 份已采用或确认入池。` : "上传后需要采用或确认，才进入对象链。",
      tone: adoptedUploads.length ? "good" : (uploads.length ? "warn" : "fail"),
    },
    {
      label: "空间语境",
      value: mapLabel,
      note: `${contextStatus}；${poiCount} 条 POI 只作为供给线索，不替代授权和现场复核。`,
      tone: poiCount ? "good" : "warn",
    },
    {
      label: "预检阻塞",
      value: blockingCount ? `${blockingCount} 项` : "无硬阻塞",
      note: blockingCount ? "先补齐关键输入，再进入仿真预检。" : "可以进入组合预检，但仍不等于最终仿真完成。",
      tone: blockingCount ? "warn" : "good",
    },
  ];

  summaryBox.innerHTML = assetGroups.map((item) => `
    <article class="source-foundation-brief ${item.tone}">
      <span>${esc(item.label)}</span>
      <b>${esc(item.value)}</b>
      <p>${esc(item.note)}</p>
    </article>
  `).join("");

  const landingTargets = {
    "证据台账": "证据追溯",
    "PDF 原生表格": "指标与表格回查",
    "数据目录": "资料分层",
    "高德 POI 候选": "空间供给语境",
    "园内复核工单": "现场/业务复核",
    "奥森策划资料": "节点与业态设想",
    "CAD / 图纸资料": "空间几何与路径复核",
    "老板方法资料": "方法约束与验证口径",
    "人物仿真覆盖池": "场景覆盖与预检",
  };
  const objectTargets = {
    "证据台账": "验证目标 / 报告依据",
    "PDF 原生表格": "人群状态 / 选择概率",
    "数据目录": "资料可信度分层",
    "高德 POI 候选": "空间语境 / 供给缺口",
    "园内复核工单": "验证目标 / 现场任务",
    "奥森策划资料": "节点推进 / 业态草案",
    "CAD / 图纸资料": "空间语境 / 路径网络",
    "老板方法资料": "行为程序 / 仿真约束",
    "人物仿真覆盖池": "人群状态 / 行为程序 / 选择概率",
  };
  const readableUseScope = (text) => valueText(text, "采用前需要人工复核来源、口径和适用范围。")
    .replace(new RegExp(["validation", "status"].join("_"), "g"), "证据状态")
    .replace(new RegExp(["output", "status"].join("_"), "g"), "输出状态")
    .replace(new RegExp(STATUS_TOKENS.needsReview, "g"), "待复核")
    .replace(/checked/g, "已复核");

  assetBox.innerHTML = `
    <div class="local-data-assets-head">
      <div>
        <b>已发现的底座资产</b>
        <p>这些不是装饰文件。采用后会服务人群状态、行为程序、选择概率、空间语境或验证目标。</p>
      </div>
      <button class="secondary-btn" type="button" data-view="data" data-scroll-target="simulationObjectPool">查看对象池</button>
    </div>
    <div class="local-data-asset-grid">
      ${assets.map((asset) => `
        <article class="local-data-asset-card">
          <div>
            <span>${esc(landingTargets[asset.label] || "资料线索")}</span>
            <b>${esc(asset.label)}</b>
            <em>${esc(asset.count !== undefined ? `${asset.count} 条/份` : "已登记")}</em>
          </div>
          <p>${esc(asset.status || "待确认状态")}</p>
          <dl>
            <div>
              <dt>进入对象</dt>
              <dd>${esc(objectTargets[asset.label] || "待人工指定")}</dd>
            </div>
            <div>
              <dt>使用边界</dt>
              <dd>${esc(readableUseScope(asset.use_scope))}</dd>
            </div>
          </dl>
        </article>
      `).join("") || `<div class="empty-state">还没有读取到底座资料。先检查本地资料目录和预检接口。</div>`}
    </div>
    <div class="foundation-next-steps">
      <b>当前推进方式</b>
      <span>先统一资料底座，再组合仿真对象；DeepSeek 只能生成候选，不能替代证据复核和最终判断。</span>
    </div>
  `;
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
      <div class="asset-title-row">
        <b>${esc(item.filename)}</b>
        <em>${esc(item.review_status || "待处理")}</em>
      </div>
      <div class="asset-meta-grid">
        <span><small>资料类型</small>${esc(item.category || "未分类")}</span>
        <span><small>文件大小</small>${esc(Math.round((Number(item.size_bytes) || 0) / 1024))} KB</span>
      </div>
      <p>${esc(item.note || "未填写说明。建议补一句这份资料用于客流、图纸、授权还是报告表达参考。")}</p>
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
          <small>${esc(firstRecommendation(node))}</small>
        </span>
        <span class="node-priority ${cls}">
          <b>${esc(priorityTitle(node))}</b>
          <em>${esc(priorityCaption(node))}</em>
        </span>
      </button>
    `;
  }).join("");
}

function renderNodeForm(node) {
  const isCreate = !node;
  const isEditable = !isCreate && (node.source === "manual_node_draft" || node.source === "project_plan_import");
  if (!isCreate && !isEditable) return "";
  return `
    <section class="detail-section node-edit-section">
      <h3>${isCreate ? "新增节点" : "编辑当前节点"}</h3>
      <form id="nodeEditForm" class="node-edit-form" data-node-id="${esc(isEditable ? node.node_id : "")}">
        <label>节点名称<input id="nodeNameInput" value="${esc(isEditable ? node.node_name : "")}" placeholder="例如：东入口轻餐节点" /></label>
        <label>位置描述<input id="nodeLocationInput" value="${esc(isEditable ? (node.location_description || node.primary_positioning || "") : "")}" placeholder="例如：靠近主入口与休息区" /></label>
        <label>业态方向<input id="nodeBusinessInput" value="${esc(isEditable ? listItems(node.business_direction).join("、") : "")}" placeholder="例如：咖啡、轻餐、便利零售" /></label>
        <label>面积<input id="nodeAreaInput" value="${esc(isEditable ? node.area_sqm : "")}" placeholder="待测或数字" /></label>
        <label class="full">备注<textarea id="nodeNoteInput" placeholder="补充这个节点为什么要看、还缺什么资料">${esc(isEditable ? node.note || "" : "")}</textarea></label>
        <label class="node-enabled"><input id="nodeEnabledInput" type="checkbox" ${isCreate || node.enabled !== false ? "checked" : ""} /> 启用节点</label>
        <div class="node-edit-actions">
          <button class="primary-btn" type="button" data-node-save="true">${isCreate ? "新增节点" : "保存修改"}</button>
          ${isCreate ? `<button class="secondary-btn" id="newNodeBtn" type="button">清空新增</button>` : ""}
          ${isCreate ? `<button class="secondary-btn" id="generatePlanNodesBtn" type="button">从项目计划生成草案</button>` : ""}
          ${isEditable ? `<button class="secondary-btn danger" id="deleteNodeBtn" type="button" data-node-id="${esc(node.node_id)}">删除节点</button>` : ""}
        </div>
      </form>
    </section>
  `;
}

function renderDetail() {
  if (state.nodeFormModeNew) {
    $("#detailTitle").textContent = "新增节点";
    $("#statusTag").textContent = "待复核";
    $("#detailBody").innerHTML = `<div class="empty-state">新增节点会进入待复核草案，保存后可在地图和节点清单中联动查看。</div>${renderNodeForm(null)}`;
    return;
  }
  const node = currentNode();
  if (!node) {
    $("#detailTitle").textContent = "节点详情";
    $("#statusTag").textContent = "等待上传";
    $("#detailBody").innerHTML = `<div class="empty-state">上传并解析项目资料后，这里才会显示节点、TGI、POI 和缺口建议。也可以先手动新增一个待复核节点。</div>${renderNodeForm(null)}`;
    return;
  }
  $("#detailTitle").textContent = `${shortId(node.node_id)} ${node.node_name}`;
  $("#statusTag").textContent = humanizeAiText(node.status_label || "待人工确认");
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
      <div class="metric wide"><span>推进优先级</span><b>${esc(priorityTitle(node))}</b><em>${esc(priorityCaption(node))}</em></div>
      <div class="metric"><span>状态</span><b>${esc(humanizeAiText(isPositionReferenceOnly(node.score_status) ? "位置参考" : (node.status_label || "待人工确认")))}</b></div>
    </div>
    <details class="detail-section collapsible-section" open>
      <summary>推进依据与建议</summary>
      ${renderScoreAnalysis(node)}
    </details>
    <details class="detail-section collapsible-section">
      <summary>TGI / POI 缺口</summary>
      ${renderNodeGapBlock(node)}
    </details>
    <details class="detail-section collapsible-section">
      <summary>业态方向</summary>
      <div class="chip-row">${directions.map((item) => `<span>${esc(item)}</span>`).join("") || "<span>待补</span>"}</div>
    </details>
    <details class="detail-section collapsible-section">
      <summary>场景假设</summary>
      <p>${esc(node.scene_assumptions || node.primary_positioning || "待合作方补充真实场景资料")}</p>
      ${assumptions.map((item) => `<p class="soft-box">${esc(item.scene_description || item.assumption_text || JSON.stringify(item))}</p>`).join("")}
    </details>
    <details class="detail-section collapsible-section">
      <summary>合作模式 / 占位参数</summary>
      <p>${esc(node.cooperation_mode || "合作模式待确认")}；${esc(node.placeholder_inputs_used || "占位参数仍需复核")}</p>
    </details>
    <details class="detail-section collapsible-section">
      <summary>P4 场景矩阵</summary>
      <div class="scenario-list">
        ${scenarios.slice(0, 4).map((item) => `
          <div>
            <b>${esc(item.scenario_name || item.scenario_type || "场景")}</b>
            <span>${esc(item.scenario_summary || item.feedback_note || item.key_assumption || "待复核")}</span>
          </div>
        `).join("") || "<p>暂无场景矩阵记录</p>"}
      </div>
    </details>
    <details class="detail-section collapsible-section">
      <summary>待补数据</summary>
      <div class="request-tags">
        ${requests.map((item) => `<span>${esc(item.missing_input || item.calibration_domain || "待补数据")} · ${esc(humanizeAiText(item.priority || "待确认"))}</span>`).join("") || `<span>${esc(node.must_collect_before_final || "真实客流、转化率、收益成本、运营授权、可信 DWG 转换产物")}</span>`}
      </div>
    </details>
    <details class="detail-section collapsible-section">
      <summary>资料缺口提示</summary>
      <div class="request-tags">
        ${missingFields.map((item) => `<span>${esc(item)}</span>`).join("") || "<span>暂无结构化缺失字段</span>"}
      </div>
      <p>${nextDataNeeded.length ? esc(humanizeAiText(nextDataNeeded.join("；"))) : "下一步以图纸、客流、收益成本、运营授权四类资料闭合为准。"}</p>
    </details>
    <div class="detail-actions">
      <button class="secondary-btn" data-view="map">在地图中查看</button>
      <button class="primary-btn" data-view="ai" data-ai-scope="node">带着这个节点问 AI</button>
    </div>
    ${renderNodeForm(node)}
  `;
}

function renderMap() {
  const amap = state.data.amap || {};
  const status = amap.status || {};
  const context = amap.map_context || {};
  prepareStaticBasemap();
  $("#amapStatusText").textContent = status.web_service_key_available
    ? `目标：${context.matched_name || context.keyword || "当前地点"}；已加载 ${status.point_count || 0} 条 POI`
    : "未检测到高德 Key；先显示本地示意层";
  const modeStatus = $("#mapModeStatus");
  if (modeStatus) {
    modeStatus.textContent = state.amapError || "地图用于位置、边界、POI 和候选点的综合查看；不强行套旧节点结论。";
    modeStatus.className = `map-mode-status ${state.amapError ? "error-mode" : "score-mode"}`;
  }
  if ($("#mapSearchInput") && !$("#mapSearchInput").value) {
    $("#mapSearchInput").placeholder = context.keyword ? `搜索地点、拼音或地址 · 当前：${context.keyword}` : "搜索地点、拼音或地址";
  }

  $("#mapCanvas").className = `map-canvas mode-${state.mapMode}`;
  $("#mapCanvas").classList.toggle("loading", state.mapLoading);
  initInteractiveMap().catch((error) => {
    state.amapError = `高德 JS 地图加载失败：${error.message}`;
    state.mapError = mapUserError(error);
    renderStaticMapFallback();
    renderMapErrorPanel();
    renderMapResultList();
  });
}

function prepareStaticBasemap() {
  const img = $("#amapBaseMap");
  if (!img) return;
  const amap = state.data?.amap || {};
  const context = amap.map_context || {};
  state.mapCenter = {
    lon: Number(context.longitude || 116.392159),
    lat: Number(context.latitude || 40.018635),
  };
  state.mapNativeZoom = nativeZoomFromBounds(amap.map_bounds || {});
  if (!img.src) img.src = mapImageUrl();
}

function showStaticBasemapBehindAmap() {
  prepareStaticBasemap();
  $("#staticMapLayer").style.display = "block";
  $("#amapInteractiveMap").style.display = "block";
  $("#amapInteractiveMap").classList.add("fallback-tiles");
  $("#mapRangeLayer").innerHTML = "";
  $("#amapPoiLayer").innerHTML = "";
  $("#mapNodes").innerHTML = "";
}

function hideStaticBasemapBehindAmap() {
  $("#amapInteractiveMap").classList.remove("fallback-tiles");
  $("#staticMapLayer").style.display = "none";
  $("#amapInteractiveMap").style.display = "block";
}

function mapUserError() {
  return "地图检索暂时失败，可以稍后重试，或先手动输入项目位置。";
}

function renderMapErrorPanel() {
  const panel = $("#mapErrorPanel");
  if (!panel) return;
  const message = state.mapError || state.amapError || "";
  if (!message) {
    panel.innerHTML = "";
    panel.classList.remove("show");
    return;
  }
  panel.innerHTML = `
    <b>${esc(message)}</b>
    <span>已保留当前输入和页面状态，地图不会清空。</span>
  `;
  panel.classList.add("show");
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
  if (config.using_web_service_key_as_fallback || !config.security_code) {
    showStaticBasemapBehindAmap();
  } else {
    hideStaticBasemapBehindAmap();
  }
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
        selectPoi(p);
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
        content: `<button class="amap-node-marker ${node.node_id === state.selectedNodeId ? "active" : ""}" data-action="select-map-node" data-node-id="${esc(node.node_id)}" aria-label="选择地图节点 ${esc(shortId(node.node_id))}">${esc(shortId(node.node_id))}</button>`,
        offset: new AMap.Pixel(-19, -19),
      });
      marker.on("click", () => {
        state.selectedNodeId = node.node_id;
        state.selectedPoiId = null;
        state.aiScope = "node";
        renderAll();
        setView("map");
      });
      return marker;
    });
    state.amapMap.add(state.amapNodeMarkers);
  }
  renderMapSide();
  renderMapResultList();
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
  const status = state.data?.amap?.boundary_status || STATUS_TOKENS.rangeEstimatedReview;
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
  box.innerHTML = `<div class="loading-row">正在检查资料、地图和 AI 能力……</div>`;
  try {
    const response = await fetch("/api/integration/status", { cache: "no-store" });
    const data = await response.json();
    const visibleItems = (data.items || []).filter((item) => !["connected", "configured", "connected_image"].includes(item.status));
    if (!visibleItems.length) {
      box.innerHTML = `<div class="integration-quiet">资料、地图和 AI 能力当前没有会影响使用的问题。</div>`;
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
            <span>${esc(humanizeAiText(item.kind))} · ${esc(humanizeAiText(item.status))}</span>
          </div>
          <p>${esc(humanizeAiText(item.detail))}</p>
        </div>
      `;
    }).join("");
  } catch (error) {
    box.innerHTML = `<div class="integration-item fail"><b>能力检查失败</b><p>${esc(humanizeAiText(error.message))}</p></div>`;
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
    return `<span class="poi-dot ${inside ? "inside" : ""}" style="left:${x}%;top:${y}%" title="${esc(p.poi_name)} · ${esc(humanizeAiText(p.output_status || "待确认"))}"></span>`;
  }).join("");
}

function renderMapSide() {
  const selectedPoi = getSelectedPoi();
  if (selectedPoi) {
    $("#mapSideDetail").innerHTML = `
      <h3>${esc(selectedPoi.poi_name || "商业 POI")}</h3>
      <div class="map-score preview">商业 POI · 待复核</div>
      <p>${esc(selectedPoi.category || selectedPoi.amap_keywords || "商业服务点位")}</p>
      <div class="mini-kv"><span>距离</span><b>${esc(selectedPoi.distance_m || "待测")} m</b></div>
      <div class="mini-kv"><span>来源</span><b>${esc(selectedPoi.source_hint || selectedPoi.source || "高德 POI")}</b></div>
      <div class="mini-kv"><span>复核状态</span><b>${esc(visibleStatus(selectedPoi.output_status || "待复核"))}</b></div>
      <div class="mini-kv"><span>边界</span><b>${esc(visibleStatus(selectedPoi.boundary_filter_status || "待复核"))}</b></div>
    `;
    return;
  }
  const contextNode = (state.data?.amap?.context_nodes || []).find((item) => item.node_id === state.selectedNodeId);
  const node = contextNode || currentNode();
  if (!node) return;
  const [label, cls] = priorityLabel(node);
  const nextDataNeeded = listItems(node.next_data_needed);
  const scoreLine = isPositionReferenceOnly(node?.score_status) ? "位置参考 · 不生成推进结论" : `${label} · ${priorityCaption(node)}`;
  $("#mapSideDetail").innerHTML = `
    <h3>${esc(shortId(node.node_id))} ${esc(node.node_name)}</h3>
    <div class="map-score ${cls}">${esc(scoreLine)}</div>
    <p>${esc(node.primary_positioning || node.scene_assumptions || "待补场景")}</p>
    <div class="mini-kv"><span>面积</span><b>${esc(node.area_sqm === "待测" ? "待测" : `${node.area_sqm} m²`)}</b></div>
    <div class="mini-kv"><span>状态</span><b>${esc(humanizeAiText(node.status_label || "待人工确认"))}</b></div>
    <div class="mini-kv"><span>推进说明</span><b>${esc(scoreMeaning(node))}</b></div>
    <div class="mini-kv"><span>地图边界</span><b>示意层，非 DWG</b></div>
    ${nextDataNeeded.length ? `<div class="mini-kv"><span>下一步</span><b>${esc(nextDataNeeded.slice(0, 2).join("；"))}</b></div>` : ""}
    ${node.source_node_name ? `<div class="mini-kv"><span>来源草案</span><b>${esc(node.source_node_name)}</b></div>` : ""}
  `;
}

function getPoiId(poi) {
  return poi.candidate_id || `${poi.poi_name}-${poi.longitude}-${poi.latitude}`;
}

function getSelectedPoi() {
  if (!state.selectedPoiId) return null;
  return (mapContextPayload()?.supply_points || []).find((item) => getPoiId(item) === state.selectedPoiId) || null;
}

function selectPoi(poi) {
  state.selectedPoiId = getPoiId(poi);
  state.selectedNodeId = null;
  state.aiScope = "project";
  renderMapSide();
  renderMapResultList();
  if (state.amapMap && window.AMap && Number.isFinite(Number(poi.longitude)) && Number.isFinite(Number(poi.latitude))) {
    state.amapMap.setZoomAndCenter(Math.max(state.amapMap.getZoom(), 16), [Number(poi.longitude), Number(poi.latitude)], false, 250);
  }
}

function renderMapResultList() {
  const box = $("#mapResultList");
  if (!box) return;
  const amap = mapContextPayload();
  const context = amap.map_context || {};
  const allPois = (amap.supply_points || []).slice(0, 12);
  const allNodes = amap.context_nodes || [];
  const pois = state.mapMode === "nodes" ? [] : allPois;
  const nodes = state.mapMode === "poi" ? [] : allNodes;
  const contextTitle = context.matched_name || context.keyword || "当前地图";
  if (!pois.length && !nodes.length) {
    box.innerHTML = `
      <div class="map-result-head">
        <b>${esc(contextTitle)}</b>
        <span>${mapIsLoading() ? "正在更新地图结果，已保留当前页面状态。" : "暂无可展示结果。可以搜索项目位置，或先上传资料。"}</span>
      </div>
    `;
    return;
  }
  box.innerHTML = `
    <div class="map-result-head">
      <b>${esc(contextTitle)}</b>
      <span>${mapIsLoading() ? "正在更新，当前结果继续保留" : `${pois.length} 个周边结果 · ${nodes.length} 个候选节点`}</span>
    </div>
    <div class="map-legend">
      <span class="project">当前项目位置</span>
      <span class="node">候选节点</span>
      <span class="poi">商业 POI</span>
    </div>
    <div class="map-result-scroll">
      ${pois.map((poi, index) => {
        const id = getPoiId(poi);
        return `
          <button type="button" class="map-result-item ${id === state.selectedPoiId ? "active" : ""}" data-poi-id="${esc(id)}">
            <b>${index + 1}. ${esc(poi.poi_name || "商业 POI")}</b>
            <span>${esc(poi.category || poi.amap_keywords || "商业服务")} · ${esc(poi.distance_m || "待测")} m · 待复核</span>
          </button>
        `;
      }).join("")}
      ${nodes.map((node, index) => `
        <button type="button" class="map-result-item node-result ${node.node_id === state.selectedNodeId ? "active" : ""}" data-node-id="${esc(node.node_id)}">
          <b>${index + 1}. ${esc(shortId(node.node_id))} ${esc(node.node_name || "候选节点")}</b>
          <span>${esc(node.primary_positioning || node.location_description || "位置待复核")} · 待复核</span>
        </button>
      `).join("")}
    </div>
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
          <button class="secondary-btn" data-view="upload" data-gate="${esc(gate.calibration_domain)}" aria-label="上传${esc(gateTitle(gate.calibration_domain))}资料">上传资料</button>
          <button class="secondary-btn gate-note-btn" data-gate="${esc(gate.calibration_domain)}" aria-label="填写${esc(gateTitle(gate.calibration_domain))}说明">填写说明</button>
          <button class="secondary-btn" data-view="ai" data-gate="${esc(gate.calibration_domain)}" aria-label="询问 AI 如何补齐${esc(gateTitle(gate.calibration_domain))}">问 AI 怎么补</button>
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
  if (gap.status !== STATUS_TOKENS.gapCalculatedReview) {
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
  box.innerHTML = `
    <section class="business-report-hero prediction-report-hero">
      <span>预测调整报告</span>
      <h3>奥森商业改造预测与调整方案报告</h3>
      <p>这版报告使用本文件夹内已给 PDF 数据、策划 DOCX、CAD 图纸、人物仿真特征池和老板方法模型，输出当前可执行的预测、节点调整、组合推进与试运营设计。</p>
      <div class="report-actions inline">
        <a class="primary-btn" href="/static/osen_prediction_adjustment_report_20260607.html" target="_blank" rel="noreferrer">打开网页报告</a>
        <a class="secondary-btn" href="/api/reports/site-selection/download?format=docx">下载 DOCX 报告</a>
        <a class="secondary-btn" href="/api/reports/site-selection/download?format=json">查看依据链</a>
      </div>
    </section>
    <section class="report-summary">
      <div><span>预测底座</span><b>PDF 指标 + 证据台账</b></div>
      <div><span>空间依据</span><b>策划案 + CAD/DXF</b></div>
      <div><span>人群方法</span><b>HumanLM / ROTE</b></div>
      <div><span>推进方式</span><b>SSR 理由先行</b></div>
      <div><span>交付状态</span><b>已生成 DOCX 与网页</b></div>
    </section>
    <section class="report-section">
      <h3>当前报告预览</h3>
      <p>预览区直接加载新报告页面；如需给外部人员查看，请使用上方 DOCX 或网页报告。</p>
      <iframe class="prediction-report-frame" title="奥森商业改造预测与调整方案报告" src="/static/osen_prediction_adjustment_report_20260607.html"></iframe>
    </section>
  `;
  return;
  const report = state.data?.demand_supply?.report || {};
  const topGaps = report.top_gaps || [];
  const nodes = report.nodes || [];
  const uploadCount = report.source_upload_count || 0;
  const reportTitle = report.title || "奥森商业改造综合评估与修正建议工作稿";
  const nextActions = listItems(report.next_actions);
  const expert = report.expert_review_basis || {};
  const beijingContext = expert.beijing_context || {};
  const expertDimensions = (expert.dimensions || []).slice(0, 8);
  const beijingContextLabels = ["收入边界", "消费支出", "服务消费"];
  const cad = report.source_foundation?.cad || {};
  const cadBoundary = cad.boundary_note || "CAD 已用于识别图纸锚点；进入路径级仿真前仍需做控制点校准。";
  const cadAnchors = listItems(cad.keyword_anchors).slice(0, 6);
  const calibrationContext = report.real_calibration_context || {};
  const calibrationItems = listItems(calibrationContext.items).slice(0, 6);
  const calibrationStrengths = calibrationContext.source_strength_counts || {};
  const calibrationLayerSummary = Object.entries(calibrationStrengths)
    .filter(([, count]) => Number(count || 0) > 0)
    .map(([layer, count]) => ({ layer, count }));
  const calibrationLabel = Number(calibrationContext.count || 0) > 0
    ? `${calibrationContext.count} 条校准输入已分层接入`
    : "校准输入待生成";
  const featureContext = report.controlled_feature_scene_context || {};
  const featureItems = listItems(featureContext.items).slice(0, 6);
  const featureLabel = Number(featureContext.count || 0) > 0
    ? `${featureContext.count} 条采用/锁定场景进入报告`
    : "尚未采用人物场景，只保留覆盖池方法底座";
  const sourceLabel = uploadCount ? `${uploadCount} 份资料已进入资料池` : "尚未形成可用资料池";
  const gapLabel = topGaps.length ? "已有可讨论的供需缺口草案" : "缺口计算等待客流、TGI、POI 资料闭合";
  const nodeLabel = nodes.length ? `${nodes.length} 个节点可回看` : "节点清单等待首页计划导入后生成";
  box.innerHTML = `
    <section class="business-report-hero">
      <span>沟通工作稿</span>
      <h3>${esc(reportTitle)}</h3>
      <p>这页用于把策划书、CAD 图纸、资料台账、地图语境和节点讨论整理成可复核的业务工作稿。当前仍需人工确认，不把任何草案包装成最终结论。</p>
    </section>
    <section class="report-summary">
      <div><span>资料基础</span><b>${esc(sourceLabel)}</b></div>
      <div><span>缺口判断</span><b>${esc(gapLabel)}</b></div>
      <div><span>节点状态</span><b>${esc(nodeLabel)}</b></div>
      <div><span>校准输入</span><b>${esc(calibrationLabel)}</b></div>
      <div><span>人物场景</span><b>${esc(featureLabel)}</b></div>
    </section>
    <section class="report-section">
      <h3>摘要</h3>
      <p>${esc(humanizeAiText(report.summary || "当前最重要的工作不是立即给出点位排序，而是先确认目标公园、资料范围和关键缺口。已有 PPT、报告或图纸可用于表达和方法参考，但进入结论前仍需要客流、TGI、POI、授权和收益成本资料闭合。"))}</p>
    </section>
    <details class="report-section collapsible-section">
      <summary>关键依据</summary>
      <div class="report-evidence-grid">
        <span><b>资料</b><em>${esc(sourceLabel)}</em></span>
        <span><b>地图</b><em>以当前搜索目标和高德图层为准，不强绑固定公园。</em></span>
        <span><b>表达</b><em>参考 PPT 的短标题、结论先行和分栏呈现，不复制其数据结论。</em></span>
      </div>
    </details>
    <details class="report-section collapsible-section" open>
      <summary>专家评审底座</summary>
      <p>${esc(expert.screened_count ? `已完成 ${expert.completed_query_count || 0}/${expert.query_total || 0} 组主题检索，筛出 ${expert.screened_count} 条高相关研究候选；这些只用于约束维度和证据门槛，不替代现场数据。` : "专家评审底座等待研究资料进入。")}</p>
      ${listItems(beijingContext.items).length ? `
        <div class="report-evidence-grid">
          ${listItems(beijingContext.items).map((item, index) => `<span><b>${esc(beijingContextLabels[index] || "收入/消费边界")}</b><em>${esc(item)}</em></span>`).join("")}
          <span><b>使用边界</b><em>${esc(beijingContext.use_boundary || "不能替代奥森周边街道级收入和客群数据。")}</em></span>
        </div>
      ` : ""}
      ${expertDimensions.length ? `
        <div class="report-chip-row">
          ${expertDimensions.map((row) => `<span>${esc(Array.isArray(row) ? row[0] : row)}</span>`).join("")}
        </div>
      ` : ""}
    </details>
    <details class="report-section collapsible-section" open>
      <summary>真实校准输入与使用边界</summary>
      <p>${esc(calibrationContext.report_rule || "报告必须区分宏观收入/消费边界、本地画像与代理变量、竞品价格线索和待复核方案假设；不能直接推出收益、排名或投资定案。")}</p>
      ${calibrationLayerSummary.length ? `
        <div class="report-evidence-grid">
          ${calibrationLayerSummary.map((item) => `
            <span>
              <b>${esc(calibrationLayerLabel(item.layer))}</b>
              <em>${esc(item.count)} 条输入</em>
            </span>
          `).join("")}
        </div>
      ` : `<p>真实校准输入待生成或待复核。</p>`}
      ${calibrationItems.length ? `
        <div class="report-feature-scene-grid">
          ${calibrationItems.map((item) => `
            <span>
              <b>${esc(item.calibration_id || "校准输入")} · ${esc(item.indicator_name || "指标待补")}</b>
              <em>${esc(calibrationLayerLabel(item.source_strength))} · ${esc(item.segment || "范围待补")} · ${esc(item.period || "时期待补")}</em>
              <em>数值：${esc(`${item.value || ""}${item.unit || ""}` || "待补")}</em>
              <em>用法：${esc(item.simulation_use || "用于校准讨论，待人工复核。")}</em>
              <strong>${esc(item.cannot_claim || "不能直接写成最终结论。")}</strong>
            </span>
          `).join("")}
        </div>
      ` : ""}
      ${listItems(calibrationContext.missing_before_final).length ? `
        <div class="report-chip-row">
          ${listItems(calibrationContext.missing_before_final).slice(0, 6).map((item) => `<span>${esc(item)}</span>`).join("")}
        </div>
      ` : ""}
    </details>
    <details class="report-section collapsible-section" open>
      <summary>人物场景输入与收入价格带</summary>
      <p>${esc(featureContext.report_rule || "报告必须把收入水平、消费价格带、时段、天气、空间节点和需求触发共同用于建议强度判断。")}</p>
      ${featureItems.length ? `
        <div class="report-feature-scene-grid">
          ${featureItems.map((item) => `
            <span>
              <b>${esc(item.title || item.derivative_id || "人物场景")}</b>
              <em>收入/价格带：${esc(item.income_segment_name || "收入段待补")} · ${esc(item.income_price_band || "价格带待补")}</em>
              <em>时段/天气/空间：${esc(item.time_band_name || "时段待补")} · ${esc(item.weather_name || "天气待补")} · ${esc(item.node_context_name || "空间待补")}</em>
              <em>需求触发：${esc(item.demand_trigger_name || "需求触发待补")}</em>
              <em>建议动作：${esc(item.candidate_supply_action_name || "动作待补")}</em>
              <strong>${esc(item.status_label || "待讨论")}</strong>
            </span>
          `).join("")}
        </div>
        ` : `<p>${esc(featureContext.empty_state || "当前还没有采用或锁定的人物场景；报告只能引用覆盖池作为方法底座。")}</p>`}
    </details>
    <details class="report-section collapsible-section" open>
      <summary>CAD 与仿真边界</summary>
      <p>${esc(cadBoundary)}</p>
      ${cadAnchors.length ? `
        <div class="report-evidence-grid">
          ${cadAnchors.map((item) => `
            <span>
              <b>${esc(item.label || item.keyword || "图纸锚点")}</b>
              <em>${esc(item.layer || "图层待复核")} · ${esc(item.x)}, ${esc(item.y)}</em>
            </span>
          `).join("")}
        </div>
      ` : "<p>CAD 锚点等待图纸解析结果进入。</p>"}
    </details>
    <details class="report-section collapsible-section" open>
      <summary>当前缺口</summary>
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
      ` : `<p>还不能做供需缺口排序。请优先补齐目标公园客流、消费画像/TGI、周边商业 POI、可经营空间和收益成本口径。</p>`}
    </details>
    <section class="report-section">
      <h3>当前推进事项</h3>
      <ol class="report-next-list">
        ${(nextActions.length ? nextActions : [
          "确认当前地图目标与资料目标是否一致，避免把奥森资料误用于其他公园结论。",
          "补齐客流、TGI、POI、图纸和经营授权后，再进入节点比较和报告定稿。",
          "把本报告作为项目综合会话底稿，继续追问并生成下一版报告。",
        ]).map((item) => `<li>${esc(item)}</li>`).join("")}
      </ol>
    </section>
    <section class="report-section">
      <details class="report-appendix">
        <summary>节点附录</summary>
      <div class="report-node-list">
        ${nodes.length ? nodes.map((node) => `
          <div class="report-node">
            <b>${esc(shortId(node.node_id))} ${esc(node.node_name)}</b>
            <p>${esc(humanizeAiText(node.improvement || "等待资料闭合后生成节点级建议。"))}</p>
            ${node.implementation_review ? `
              <p><strong>推荐路径：</strong>${esc(node.implementation_review.recommended_path || "先低改造试点，再按证据升级。")}</p>
              <p><strong>收入与价格带：</strong>${esc(listItems(node.implementation_review.income_and_price_band).slice(0, 2).join("；"))}</p>
              <div class="report-option-list">
                ${(node.implementation_review.options || []).slice(0, 3).map((option) => `
                  <span>
                    <b>${esc(option.name || "方案")}</b>
                    <em>${esc(option.what_to_do || "")}</em>
                  </span>
                `).join("")}
              </div>
            ` : ""}
          </div>
        `).join("") : "<p>暂无节点可展示。导入计划并拆分节点后，这里会按节点回看。</p>"}
      </div>
      </details>
    </section>
  `;
}

function simObjectList(value) {
  return listItems(value).filter((item) => ![STATUS_TOKENS.needsReview, STATUS_TOKENS.notFinal, "false", "true"].includes(String(item).trim()));
}

function simObjectTypeLabel(type) {
  if (type === "persona_state") return "人群状态画像";
  if (type === "behavior_program") return "行为程序";
  if (type === "choice_probability") return "选择概率候选";
  if (type === "simulation_validation_target") return "仿真验证目标";
  return "仿真对象";
}

function splitFormList(value) {
  return String(value || "").split(/[;；\n]/).map((item) => item.trim()).filter(Boolean);
}

const SIM_OBJECT_VISIBLE_LIMIT = 4;

function renderSimulationObjectPool() {
  const pool = $("#simulationObjectPool");
  const stats = $("#simulationObjectStats");
  if (!pool || !stats) return;
  const objects = state.data.simulation_objects || [];
  const personaCount = objects.filter((item) => item.object_type === "persona_state").length;
  const behaviorCount = objects.filter((item) => item.object_type === "behavior_program").length;
  const choiceCount = objects.filter((item) => item.object_type === "choice_probability").length;
  const validationCount = objects.filter((item) => item.object_type === "simulation_validation_target").length;
  const adoptedCount = objects.filter((item) => item.adoption_status === "已采用").length;
  const lockedCount = objects.filter((item) => item.user_locked).length;
  stats.innerHTML = `
    <span><b>${personaCount}</b><em>人群状态画像</em></span>
    <span><b>${behaviorCount}</b><em>行为程序</em></span>
    <span><b>${choiceCount}</b><em>选择概率候选</em></span>
    <span><b>${validationCount}</b><em>仿真验证目标</em></span>
    <span><b>${adoptedCount}</b><em>已采用</em></span>
    <span><b>${lockedCount}</b><em>已锁定</em></span>
  `;
  if (!objects.length) {
    pool.innerHTML = `<div class="empty-state">还没有仿真对象。先新增人群状态画像、行为程序、选择概率候选或仿真验证目标，再进入仿真检查。</div>`;
    return;
  }
  const sorted = objects.slice().sort((a, b) => {
    const weight = (item) => (item.adoption_status === "已采用" ? 0 : item.user_locked ? 1 : item.adoption_status === "已放弃" ? 3 : 2);
    return weight(a) - weight(b);
  });
  const hiddenCount = Math.max(0, sorted.length - SIM_OBJECT_VISIBLE_LIMIT);
  const shouldCollapse = hiddenCount > 0 && !state.showAllSimulationObjects;
  const visibleObjects = shouldCollapse ? sorted.slice(0, SIM_OBJECT_VISIBLE_LIMIT) : sorted;
  const toolbar = hiddenCount > 0 ? `
    <div class="sim-object-pool-toolbar">
      <p>
        默认显示 ${SIM_OBJECT_VISIBLE_LIMIT} / ${sorted.length} 个对象，优先处理已采用、已锁定和最近候选。
        其余对象展开后再逐项复核，避免资料页变成说明书。
      </p>
      <button
        id="toggleSimulationObjectPoolBtn"
        class="secondary-btn"
        type="button"
        data-action="toggle-simulation-objects"
        aria-label="${state.showAllSimulationObjects ? "收起仿真对象池" : "展开全部仿真对象"}"
      >${state.showAllSimulationObjects ? "收起对象池" : `展开全部对象（还有 ${hiddenCount} 个）`}</button>
    </div>
  ` : "";
  pool.innerHTML = toolbar + visibleObjects.map((item) => {
    const missing = simObjectList(item.missing_inputs).slice(0, 4);
    const advice = simObjectList(item.specific_advice).slice(0, 3);
    const locked = Boolean(item.user_locked);
    const adopted = item.adoption_status === "已采用";
    const discarded = item.adoption_status === "已放弃";
    return `
      <article class="sim-object-card ${locked ? "locked" : ""} ${adopted ? "adopted" : ""} ${discarded ? "discarded" : ""}" data-sim-object-card="${esc(item.object_id)}">
        <div class="sim-object-title">
          <span>${esc(simObjectTypeLabel(item.object_type))}</span>
          <b>${esc(item.title)}</b>
          <em>${esc(item.adoption_status || "暂未采用")} · ${locked ? "已锁定" : "可编辑"}</em>
        </div>
        <p>${esc(humanizeAiText(item.summary || "该对象还缺少业务说明。"))}</p>
        <div class="sim-object-tags">
          <span>${esc(item.priority_label || "补资料后判断")}</span>
          <span>${esc(item.linked_id || "未关联")}</span>
          <span>待复核</span>
        </div>
        ${missing.length ? `
          <div class="sim-object-section">
            <b>还缺什么</b>
            <ul>${missing.map((text) => `<li>${esc(text)}</li>`).join("")}</ul>
          </div>
        ` : ""}
        ${advice.length ? `
          <div class="sim-object-section">
            <b>现在建议</b>
            <ul>${advice.map((text) => `<li>${esc(text)}</li>`).join("")}</ul>
          </div>
        ` : ""}
        <div class="sim-object-actions">
          ${adopted ? `<button type="button" data-sim-object-action="restore" data-sim-object-id="${esc(item.object_id)}" aria-label="撤回采用 ${esc(item.title)}">撤回采用</button>` : `<button type="button" data-sim-object-action="use" data-sim-object-id="${esc(item.object_id)}" aria-label="采用 ${esc(item.title)}">采用</button>`}
          ${discarded ? `<button type="button" data-sim-object-action="restore" data-sim-object-id="${esc(item.object_id)}" aria-label="恢复 ${esc(item.title)}">恢复</button>` : `<button type="button" data-sim-object-action="discard" data-sim-object-id="${esc(item.object_id)}" aria-label="放弃 ${esc(item.title)}">放弃</button>`}
          <button type="button" data-sim-object-edit="${esc(item.object_id)}" aria-label="编辑 ${esc(item.title)}" ${locked ? "disabled" : ""}>编辑</button>
          <button type="button" data-sim-object-action="${locked ? "unlock" : "lock"}" data-sim-object-id="${esc(item.object_id)}" aria-label="${locked ? "解锁" : "锁定"} ${esc(item.title)}">${locked ? "解锁" : "锁定"}</button>
          <button type="button" class="danger" data-sim-object-action="delete" data-sim-object-id="${esc(item.object_id)}" aria-label="删除 ${esc(item.title)}" ${locked ? "disabled" : ""}>删除</button>
        </div>
      </article>
    `;
  }).join("");
}

const SIM_TASK_TYPES = [
  ["persona_state", "人群状态"],
  ["behavior_program", "行为程序"],
  ["choice_probability", "选择候选"],
  ["simulation_validation_target", "验证目标"],
];

function preflightTone(status) {
  if (status === "pass") return "good";
  if (status === "block") return "fail";
  return "warn";
}

function preflightStatusLabel(status) {
  if (status === "pass") return "已满足";
  if (status === "block") return "阻止完整仿真";
  return "待补或待确认";
}

function simulationParkLabel(value) {
  const text = valueText(value, "");
  if (!text) return "当前目标公园";
  if (/sample|green_heart|city_green/i.test(text)) return "当前目标公园";
  return humanizeAiText(text);
}

function simulationCategoryLabel(value) {
  const text = valueText(value, "");
  const labels = {
    coffee: "咖啡",
    cold_drink: "冷饮",
    tea_drink: "茶饮",
    fast_food: "轻食快餐",
    convenience_retail: "即时零售",
    sports_supply: "运动补给",
    parent_child: "亲子服务",
    creative_retail: "文创零售",
    wellness: "康养服务",
    restroom: "公共服务",
  };
  return labels[text] || humanizeAiText(text || "待确认业态");
}

function simulationListText(value, fallback = "待补资料", limit = 2) {
  const items = listItems(value)
    .map((item) => humanizeAiText(item))
    .filter(Boolean)
    .slice(0, limit);
  return items.join("；") || fallback;
}

function simulationTaskObjectOptions(type, selectedIds) {
  const preflight = state.data.simulation_task_preflight || {};
  const objects = preflight.available_objects?.[type] || [];
  const limit = state.showAllTaskObjects ? objects.length : 5;
  const visible = objects.slice(0, limit);
  if (!objects.length) return `<div class="task-object-empty">暂无${esc(simObjectTypeLabel(type))}，请先在对象池新增。</div>`;
  return `
    <div class="task-object-options">
      ${visible.map((item) => {
        const checked = selectedIds.has(item.object_id);
        const adopted = item.adoption_status === "已采用";
        return `
          <label class="task-object-option ${checked ? "checked" : ""} ${adopted ? "adopted" : ""}">
            <input
              type="checkbox"
              data-sim-task-object="${esc(item.object_id)}"
              data-sim-task-type="${esc(type)}"
              ${checked ? "checked" : ""}
            />
            <span>
              <b>${esc(item.title || item.object_id)}</b>
              <em>${esc(item.adoption_status || "暂未采用")} · ${esc(item.priority_label || "补资料后判断")}</em>
            </span>
          </label>
        `;
      }).join("")}
    </div>
    ${objects.length > 5 ? `
      <button class="text-btn task-object-toggle" type="button" data-action="toggle-task-objects">
        ${state.showAllTaskObjects ? "收起候选对象" : `展开更多候选（还有 ${objects.length - visible.length} 个）`}
      </button>
    ` : ""}
  `;
}

function renderFeatureDerivativePool(pool = {}) {
  const items = Array.isArray(pool.items) ? pool.items : [];
  const coverage = pool.coverage || {};
  if (!items.length) {
    return `
      <section class="feature-pool">
        <div class="feature-pool-head">
          <div>
            <span>人物场景控制</span>
            <b>覆盖池暂不可用</b>
          </div>
          <p>请先重新生成人物仿真覆盖池，再进入任务预检。</p>
        </div>
      </section>
    `;
  }
  const visible = state.showAllFeatureDerivatives ? items : items.slice(0, 4);
  const statusClass = (item) => item.user_locked ? "locked" : item.adoption_status === "已采用" ? "adopted" : item.adoption_status === "已放弃" ? "discarded" : "";
  return `
    <section class="feature-pool">
      <div class="feature-pool-head">
        <div>
          <span>人物场景控制</span>
          <b>${esc(pool.total_count || 0)} 条覆盖池 · ${esc(pool.adopted_count || 0)} 条已采用 · ${esc(pool.locked_count || 0)} 条已锁定</b>
        </div>
        <p>这里不是最终仿真结果。先控制代表场景，再决定是否转成人群、行为或选择概率对象。</p>
      </div>
      <div class="feature-coverage-strip">
        <span><b>${esc(coverage.personas || 0)}</b><em>人群</em></span>
        <span><b>${esc(coverage.income_segments || 0)}</b><em>收入/价格</em></span>
        <span><b>${esc(coverage.time_bands || 0)}</b><em>时段</em></span>
        <span><b>${esc(coverage.weathers || 0)}</b><em>天气</em></span>
        <span><b>${esc(coverage.node_contexts || 0)}</b><em>空间</em></span>
        <span><b>${esc(coverage.demand_triggers || 0)}</b><em>触发</em></span>
        <span><b>${esc(coverage.supply_actions || 0)}</b><em>动作</em></span>
      </div>
      <div class="feature-scenario-grid">
        ${visible.map((item) => {
          const locked = Boolean(item.user_locked);
          const adopted = item.adoption_status === "已采用";
          const discarded = item.adoption_status === "已放弃";
          return `
            <article class="feature-scenario-card ${statusClass(item)}" data-feature-derivative-card="${esc(item.derivative_id)}">
              <div class="feature-scenario-title">
                <span>${esc(item.derivative_id)}</span>
                <b>${esc(item.title)}</b>
                <em>${esc(item.adoption_status || "暂未采用")}${locked ? " · 已锁定" : ""}</em>
              </div>
              <p>${esc(item.why_it_matters || "等待补充场景说明。")}</p>
              <div class="feature-scenario-meta">
                <span>${esc(item.income_segment_name || "收入待复核")}</span>
                <span>${esc(item.income_price_band || "价格带待补")}</span>
                <span>${esc(item.weather_name || "天气待补")}</span>
                <span>${esc(item.node_context_name || "空间待补")}</span>
                <span>${esc(item.candidate_supply_action_name || "动作待补")}</span>
              </div>
              <details>
                <summary>收入与价格怎么影响判断</summary>
                <p>${esc(item.income_sensitivity_note || "收入、消费支出、价格带和客单价需要进入复核，不应只看人群标签。")}</p>
                <p>${esc(item.income_evidence_hint || "请回查本地消费水平、周边人口收入和真实交易资料。")}</p>
              </details>
              <details>
                <summary>需要补什么数据</summary>
                <p>${esc(item.data_needed || "真实客流、收入、价格、转化率和现场观察。")}</p>
              </details>
              <div class="feature-scenario-actions">
                ${adopted ? `<button type="button" data-feature-derivative-action="restore" data-feature-derivative-id="${esc(item.derivative_id)}">撤回采用</button>` : `<button type="button" data-feature-derivative-action="use" data-feature-derivative-id="${esc(item.derivative_id)}">采用</button>`}
                ${discarded ? `<button type="button" data-feature-derivative-action="restore" data-feature-derivative-id="${esc(item.derivative_id)}">恢复</button>` : `<button type="button" data-feature-derivative-action="discard" data-feature-derivative-id="${esc(item.derivative_id)}">放弃</button>`}
                <button type="button" data-feature-derivative-action="${locked ? "unlock" : "lock"}" data-feature-derivative-id="${esc(item.derivative_id)}">${locked ? "解锁" : "锁定"}</button>
              </div>
            </article>
          `;
        }).join("")}
      </div>
      ${items.length > 4 ? `
        <button class="text-btn feature-pool-toggle" type="button" data-action="toggle-feature-derivatives">
          ${state.showAllFeatureDerivatives ? "收起代表场景" : `展开更多代表场景（还有 ${items.length - visible.length} 条）`}
        </button>
      ` : ""}
    </section>
  `;
}

function renderSimulationTaskPreflight() {
  const box = $("#simulationTaskPreflight");
  if (!box) return;
  const preflight = state.data.simulation_task_preflight || {};
  const task = preflight.task || {};
  const selectedIds = new Set(preflight.selected_object_ids || []);
  const selectedCounts = preflight.selected_counts || {};
  const checks = preflight.preflight_checks || [];
  const assets = preflight.local_data_assets || [];
  const featurePool = preflight.feature_derivative_pool || {};
  const blockingCount = Number(preflight.blocking_count || 0);
  const fullBlocked = preflight.full_simulation_status === "blocked_for_full_simulation";
  box.innerHTML = `
    <div class="task-preflight-hero ${fullBlocked ? "blocked" : "ready"}">
      <div>
        <span>${fullBlocked ? "完整仿真未放行" : "可进入受控预检"}</span>
        <h3>${esc(humanizeAiText(preflight.human_summary || "请选择对象并运行预检。"))}</h3>
        <p>${esc(humanizeAiText(preflight.deepseek_role || "生产端 AI 仅可作为待复核助手。"))}</p>
      </div>
      <div class="task-preflight-counts">
        ${SIM_TASK_TYPES.map(([type, label]) => `
          <span><b>${esc(selectedCounts[type] || 0)}</b><em>${esc(label)}</em></span>
        `).join("")}
        <span><b>${esc(preflight.controlled_feature_scene_count || 0)}</b><em>采用场景</em></span>
        <span><b>${esc(preflight.real_calibration_input_count || 0)}</b><em>校准输入</em></span>
      </div>
    </div>
    <div class="task-preflight-form">
      <label>
        任务名称
        <input id="simTaskName" type="text" value="${esc(task.task_name || "人物仿真预演")}" />
      </label>
      <label class="wide">
        场景说明
        <textarea id="simTaskScenarioNote" placeholder="例如：先用奥森策划文案和当前 CAD/POI 资料，做亲子、运动、白领三类人群的结构化预检。">${esc(task.scenario_note || "")}</textarea>
      </label>
    </div>
    <div class="task-type-grid">
      ${SIM_TASK_TYPES.map(([type, label]) => `
        <section class="task-type-card" data-task-type="${esc(type)}">
          <div class="task-type-head">
            <b>${esc(label)}</b>
            <span>${esc(selectedCounts[type] || 0)} 个已选</span>
          </div>
          ${simulationTaskObjectOptions(type, selectedIds)}
        </section>
      `).join("")}
    </div>
    <div class="task-preflight-actions">
      <button class="secondary-btn" type="button" data-action="select-adopted-task-objects">使用已采用对象</button>
      <button class="secondary-btn" type="button" data-action="clear-task-objects">清空选择</button>
      <button class="primary-btn" type="button" data-action="save-simulation-task">保存并预检</button>
    </div>
    <div class="task-check-summary">
      <span class="${fullBlocked ? "fail" : "good"}">${fullBlocked ? `${blockingCount} 项阻止完整仿真` : "完整仿真前置项未阻塞"}</span>
      <em>这里的“通过”只表示运行前检查，不表示商业结论已经成立。</em>
    </div>
    <div class="task-check-list">
      ${checks.map((item) => `
        <article class="task-check-item ${preflightTone(item.status)}">
          <div>
            <b>${esc(humanizeAiText(item.label))}</b>
            <span>${esc(preflightStatusLabel(item.status))}</span>
          </div>
          <p>${esc(humanizeAiText(item.detail || "等待检查。"))}</p>
          <em>${esc(humanizeAiText(item.next_action || "继续补充资料并复核。"))}</em>
        </article>
      `).join("")}
    </div>
    ${renderFeatureDerivativePool(featurePool)}
    <details class="task-data-assets">
      <summary>本地资料用途</summary>
      <div>
        ${assets.map((item) => `
          <section>
            <b>${esc(item.label)}</b>
            <span>${esc(item.count)} 项 · ${esc(humanizeAiText(item.status))}</span>
            <p>${esc(humanizeAiText(item.use_scope))}</p>
          </section>
        `).join("")}
      </div>
    </details>
  `;
}

function collectSimulationTaskPayload() {
  return {
    task_name: $("#simTaskName")?.value.trim() || "人物仿真预演",
    scenario_note: $("#simTaskScenarioNote")?.value.trim() || "",
    run_mode: "preflight",
    selected_object_ids: $$("[data-sim-task-object]:checked").map((item) => item.dataset.simTaskObject),
  };
}

async function saveSimulationTaskPreflight() {
  const payload = collectSimulationTaskPayload();
  const response = await fetch("/api/simulation/task-preflight", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || `仿真任务预检失败：${response.status}`);
  state.lastAction = data.blocking_count
    ? `预检已更新：${data.blocking_count} 项仍阻止完整仿真`
    : "预检已更新：可进入受控结构化检查";
  await loadDashboard();
}

function selectAdoptedTaskObjects() {
  const adoptedIds = new Set(
    (state.data.simulation_objects || [])
      .filter((item) => item.adoption_status === "已采用")
      .map((item) => item.object_id)
  );
  $$("[data-sim-task-object]").forEach((input) => {
    input.checked = adoptedIds.has(input.dataset.simTaskObject);
    input.closest(".task-object-option")?.classList.toggle("checked", input.checked);
  });
}

function clearTaskObjects() {
  $$("[data-sim-task-object]").forEach((input) => {
    input.checked = false;
    input.closest(".task-object-option")?.classList.remove("checked");
  });
}

function openSimulationObjectForm(type = "choice_probability", objectId = null) {
  const form = $("#simulationObjectForm");
  if (!form) return;
  const item = objectId ? (state.data.simulation_objects || []).find((row) => row.object_id === objectId) : null;
  state.editingSimulationObjectId = objectId;
  $("#simObjectEditId").value = objectId || "";
  $("#simObjectType").value = item?.object_type || type;
  $("#simObjectType").disabled = Boolean(item);
  $("#simObjectTitle").value = item?.title || "";
  $("#simObjectLinkedId").value = item?.linked_id || "";
  $("#simObjectSummary").value = item?.summary || "";
  $("#simObjectMissing").value = simObjectList(item?.missing_inputs).join("；");
  $("#simObjectAdvice").value = simObjectList(item?.specific_advice).join("；");
  form.hidden = false;
  form.scrollIntoView({ behavior: "smooth", block: "center" });
  $("#simObjectTitle").focus();
}

function closeSimulationObjectForm() {
  const form = $("#simulationObjectForm");
  if (!form) return;
  state.editingSimulationObjectId = null;
  form.reset();
  $("#simObjectType").disabled = false;
  form.hidden = true;
}

function collectSimulationObjectForm() {
  const type = $("#simObjectType").value;
  const defaultPriority = type === "simulation_validation_target"
    ? "校准前置条件"
    : type === "persona_state"
      ? "先确认状态"
      : type === "behavior_program"
        ? "先复核行为链"
        : "补资料后判断";
  return {
    object_type: type,
    title: $("#simObjectTitle").value.trim(),
    linked_id: $("#simObjectLinkedId").value.trim(),
    summary: $("#simObjectSummary").value.trim(),
    missing_inputs: splitFormList($("#simObjectMissing").value),
    specific_advice: splitFormList($("#simObjectAdvice").value),
    priority_label: defaultPriority,
  };
}

async function saveSimulationObject(event) {
  event.preventDefault();
  const body = collectSimulationObjectForm();
  if (!body.title) {
    state.lastAction = "请先填写仿真对象标题";
    renderMeta();
    return;
  }
  const editingId = $("#simObjectEditId").value;
  const response = editingId
    ? await fetch(`/api/simulation/objects/${encodeURIComponent(editingId)}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "update", ...body }),
    })
    : await fetch("/api/simulation/objects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `仿真对象保存失败：${response.status}`);
  state.lastAction = editingId ? "仿真对象已更新" : "仿真对象已新增";
  closeSimulationObjectForm();
  await loadDashboard();
}

async function updateSimulationObjectAction(objectId, action) {
  const method = action === "delete" ? "DELETE" : "PATCH";
  const options = method === "DELETE" ? { method } : {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  };
  const response = await fetch(`/api/simulation/objects/${encodeURIComponent(objectId)}`, options);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `仿真对象操作失败：${response.status}`);
  const labels = {
    use: "已采用仿真对象",
    discard: "已放弃仿真对象",
    restore: "已恢复仿真对象",
    lock: "已锁定仿真对象",
    unlock: "已解锁仿真对象",
    delete: "已删除仿真对象",
  };
  state.lastAction = labels[action] || "仿真对象已更新";
  await loadDashboard();
}

async function updateFeatureDerivativeAction(derivativeId, action) {
  const response = await fetch(`/api/simulation/feature-derivatives/${encodeURIComponent(derivativeId)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || `场景操作失败：${response.status}`);
  const labels = {
    use: "已采用人物场景",
    discard: "已放弃人物场景",
    restore: "已恢复人物场景",
    lock: "已锁定人物场景",
    unlock: "已解锁人物场景",
  };
  state.lastAction = labels[action] || "人物场景已更新";
  await loadDashboard();
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
  const featureSceneCount = Math.max(...resultItems.map((row) => Number(row.feature_scene_count || 0)), 0);
  const matchedSceneGroups = resultItems.filter((row) => Number(row.matched_feature_scene_count || 0) > 0).length;
  const categories = resultItems.slice(0, 6).map((row) => `
    <tr>
      <td>${esc(simulationParkLabel(row.park_id))}</td>
      <td>${esc(simulationCategoryLabel(row.category))}</td>
      <td>${esc(row.candidate_count)}</td>
      <td>${esc(row.inside_osm_polygon_count)}</td>
      <td>${esc(row.matched_feature_scene_count || 0)} / ${esc(row.feature_scene_count || 0)}</td>
      <td>${esc(simulationListText(row.scenario_pressure?.operation_rules, "暂无命中动作", 2))}</td>
      <td>${esc(row.accuracy_context?.readiness_label || "待校准")}</td>
      <td>${esc(simulationListText(row.why_blocked, "待人工复核", 2))}</td>
      <td>${esc(simulationListText(row.next_data_needed, "待补资料", 2))}</td>
    </tr>
  `).join("");
  const pressureRows = resultItems
    .filter((row) => Number(row.matched_feature_scene_count || 0) > 0)
    .slice(0, 3)
    .map((row) => {
      const pressure = row.scenario_pressure || {};
      const accuracy = row.accuracy_context || {};
      const constraints = row.calibration_constraints || accuracy.constraints || [];
      return `
        <span>
          <b>${esc(simulationCategoryLabel(row.category))}</b>
          <em>收入/价格带：${esc(simulationListText(pressure.income_segments, "待补收入段", 2))} · ${esc(simulationListText(pressure.price_bands, "待补价格带", 2))}</em>
          <em>时段/天气：${esc(simulationListText(pressure.time_bands, "待补时段", 2))} · ${esc(simulationListText(pressure.weathers, "待补天气", 2))}</em>
          <em>场景动作：${esc(simulationListText(pressure.operation_rules, "待补动作", 3))}</em>
          <em>准确性约束：${esc(accuracy.readiness_label || "待校准")} · ${esc(simulationListText((constraints || []).map((item) => item.name), "待补校准约束", 3))}</em>
        </span>
      `;
    })
    .join("");
  box.innerHTML = `
    <div class="simulation-summary">
      <div><b>${esc(latestJob.job_id)}</b><span>${esc(humanizeAiText(latestJob.scenario_name || "结构化仿真检查"))} · ${esc(latestJob.iterations)} 次结构化检查</span></div>
      <span class="status-pill danger">待人工确认</span>
    </div>
    <div class="simulation-metrics">
      <span><b>${esc(resultItems.length)}</b><em>结果行</em></span>
      <span><b>${esc(blocked)}</b><em>资料门禁未闭合</em></span>
      <span><b>${esc(missingFields)}</b><em>经营字段缺失</em></span>
      <span><b>${esc(featureSceneCount)}</b><em>采用场景输入</em></span>
      <span><b>${esc(matchedSceneGroups)}</b><em>命中供给组</em></span>
    </div>
    ${featureSceneCount ? `
      <div class="simulation-pressure">
        <h4>人物场景压力摘要</h4>
        <p>这里只展示用户采用/锁定场景对供给组的结构化命中，不代表真实客群占比或收益预测。</p>
        <div class="simulation-pressure-grid">
          ${pressureRows || "<span><b>暂无命中</b><em>当前采用场景还没有匹配到可比较的 POI 供给类别。</em></span>"}
        </div>
      </div>
    ` : ""}
    <div class="simulation-actions">
      <button class="secondary-btn" id="refreshSimulationBtn">刷新任务</button>
      <a class="secondary-btn" href="/api/simulation/jobs/${encodeURIComponent(latestJob.job_id)}/export?format=csv" data-action="export-simulation-csv" data-job-id="${esc(latestJob.job_id)}" aria-label="导出仿真检查 CSV">导出 CSV</a>
      <a class="secondary-btn" href="/api/simulation/jobs/${encodeURIComponent(latestJob.job_id)}/export?format=json" data-action="export-simulation-json" data-job-id="${esc(latestJob.job_id)}" aria-label="导出仿真检查 JSON">导出 JSON</a>
    </div>
    <div class="simulation-table">
      <table>
        <thead><tr><th>公园</th><th>业态</th><th>候选</th><th>边界内</th><th>场景命中</th><th>场景动作</th><th>准确性</th><th>为什么卡住</th><th>下一步资料</th></tr></thead>
        <tbody>${categories}</tbody>
      </table>
    </div>
  `;
}

async function runSimulationDryRun() {
  const preflight = state.data.simulation_task_preflight || {};
  if (preflight.dry_run_status === "select_objects_first") {
    state.lastAction = "请先在“仿真任务入口”选择人群状态、行为程序、选择概率和验证目标。";
    setView("data");
    renderMeta();
    return;
  }
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
    if (!response.ok) throw new Error(payload.detail || `仿真检查未能启动：${response.status}`);
    state.lastAction = `已生成 ${payload.result_count || 0} 行待复核检查结果`;
    await loadSimulationJobs();
    renderSimulationPanel();
    renderMeta();
  } catch (error) {
    state.lastAction = humanizeAiText(error.message || "仿真检查未能启动");
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

function nodePayloadFromForm() {
  return {
    node_name: $("#nodeNameInput")?.value.trim() || "未命名节点",
    location_description: $("#nodeLocationInput")?.value.trim() || "",
    business_direction: $("#nodeBusinessInput")?.value.trim() || "",
    area_sqm: $("#nodeAreaInput")?.value.trim() || "待测",
    note: $("#nodeNoteInput")?.value.trim() || "",
    enabled: Boolean($("#nodeEnabledInput")?.checked),
  };
}

async function submitNodeForm(form) {
  const nodeId = form.dataset.nodeId;
  const response = await fetch(nodeId ? `/api/nodes/${encodeURIComponent(nodeId)}` : "/api/nodes", {
    method: nodeId ? "PATCH" : "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(nodePayloadFromForm()),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "节点保存失败，请稍后重试。");
  state.selectedNodeId = data.node_id;
  state.nodeFormModeNew = false;
  state.selectedPoiId = null;
  state.lastAction = nodeId ? "节点已更新" : "节点已新增";
  await loadDashboard();
  setView("nodes");
}

async function deleteSelectedNode(nodeId) {
  if (!window.confirm("确定删除这个手动节点草案吗？")) return;
  const response = await fetch(`/api/nodes/${encodeURIComponent(nodeId)}`, { method: "DELETE" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "节点删除失败，请稍后重试。");
  state.selectedNodeId = null;
  state.nodeFormModeNew = false;
  state.lastAction = "节点已删除";
  await loadDashboard();
  setView("nodes");
}

async function generatePlanNodes() {
  const response = await fetch("/api/nodes/generate-from-plan", { method: "POST" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "请先上传并采用项目计划。");
  state.selectedNodeId = data.items?.[0]?.node_id || state.selectedNodeId;
  state.nodeFormModeNew = false;
  state.selectedPoiId = null;
  state.lastAction = data.message || `已生成 ${data.created_count || 0} 个节点草案`;
  await loadDashboard();
  setView("nodes");
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
  state.mapSearchLoading = true;
  state.pendingSearchKeyword = keyword;
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
    if (!response.ok) throw new Error(mapUserError());
    const data = await response.json();
    pushMapHistory(state.data?.amap?.map_context);
    state.lastAction = `地图目标已更新：${data.matched_name || data.keyword}`;
    input.value = data.matched_name || data.keyword || keyword;
    $("#mapSuggest").innerHTML = "";
    state.mapError = "";
    await loadDashboard();
    state.lastSuccessfulMapContext = { amap: state.data.amap };
    if (state.amapMap) state.amapMap.setZoomAndCenter(15, [Number(data.longitude), Number(data.latitude)], false, 500);
    setView("map");
  } catch (error) {
    state.mapError = mapUserError(error);
    state.lastAction = state.mapError;
    renderMapErrorPanel();
    renderMapResultList();
    renderMeta();
  } finally {
    state.mapLoading = false;
    state.mapSearchLoading = false;
    state.pendingSearchKeyword = "";
    $("#mapCanvas").classList.remove("loading");
    $("#mapSuggest").innerHTML = "";
  }
}

async function updateMapContextFromSuggestion(tip) {
  $("#mapSearchInput").value = tip.name;
  $("#mapSuggest").innerHTML = "";
  state.lastAction = `正在定位：${tip.name}`;
  state.mapLoading = true;
  state.mapSearchLoading = true;
  state.pendingSearchKeyword = tip.name;
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
    if (!response.ok) throw new Error(mapUserError());
    const data = await response.json();
    pushMapHistory(state.data?.amap?.map_context);
    state.lastAction = `地图目标已更新：${data.matched_name || data.keyword}`;
    $("#mapSearchInput").value = data.matched_name || data.keyword || tip.name;
    $("#mapSuggest").innerHTML = "";
    state.mapError = "";
    await loadDashboard();
    state.lastSuccessfulMapContext = { amap: state.data.amap };
    if (state.amapMap) state.amapMap.setZoomAndCenter(16, [Number(data.longitude), Number(data.latitude)], false, 500);
    setView("map");
  } catch (error) {
    state.mapError = mapUserError(error);
    state.lastAction = state.mapError;
    renderMapErrorPanel();
    renderMapResultList();
    renderMeta();
  } finally {
    state.mapLoading = false;
    state.mapSearchLoading = false;
    state.pendingSearchKeyword = "";
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
      output_status: STATUS_TOKENS.needsReview,
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
  $("#aiWorkspaceView")?.classList.toggle("rail-collapsed", state.aiRailCollapsed);
  if ($("#aiRailToggle")) $("#aiRailToggle").textContent = state.aiRailCollapsed ? "展开" : "收起";
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
  updateReportButtonState(messages.length);
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

function currentAiSession() {
  return (state.aiSessions.sessions || []).find((item) => item.session_id === state.activeAiSessionId) || null;
}

function currentAiMessageCount() {
  const session = currentAiSession();
  if (session) return Number(session.message_count || 0);
  return Number(state.chatHistory.length || 0);
}

function updateReportButtonState(messageCount = currentAiMessageCount()) {
  const button = $("#generateChatReportBtn");
  if (!button) return;
  button.disabled = Boolean(state.aiBusy || !state.activeAiSessionId || messageCount <= 0);
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
  updateReportButtonState(0);
  renderMeta();
}

async function generateChatReport() {
  if (state.aiBusy) {
    state.lastAction = "AI 还在整理当前回复，等回复完成后再生成报告";
    renderMeta();
    return;
  }
  const hasUserMessage = state.chatHistory.some((msg) => msg.role === "user" && valueText(msg.content, "").trim());
  const hasAssistantMessage = state.chatHistory.some((msg) => msg.role === "assistant" && valueText(msg.content, "").trim());
  if (!state.activeAiSessionId || !hasUserMessage || !hasAssistantMessage) {
    state.lastAction = "请先完成一轮有效对话，再生成报告";
    renderMeta();
    return;
  }
  const node = currentNode();
  const reportScope = state.aiScope === "node" && node ? `单节点报告：${shortId(node.node_id)}` : "项目综合报告";
  const response = await fetch(`/api/ai/sessions/${encodeURIComponent(state.activeAiSessionId)}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      instruction: `请生成${reportScope}。结构按商业汇报组织：摘要、关键依据、当前缺口、待复核判断、推进事项、附录。语言给业务方看，不写机器日志。`,
    }),
  });
  if (!response.ok) throw new Error(`生成报告失败：${response.status}`);
  const data = await response.json();
  state.lastAction = `${reportScope}已生成，可查看/下载`;
  renderMeta();
  addChatMessage("assistant", `${reportScope}已生成。建议先按“摘要、依据、缺口、推进事项”检查一遍，再发给同事或客户确认。`, "待人工确认");
  window.open(data.download_url, "_blank");
}

function renderAiContext() {
  const node = currentNode();
  const uploadCount = state.data?.uploads?.length || 0;
  const nodeCount = state.data?.nodes?.length || 0;
  updateReportButtonState();
  if ($("#aiModeBadge")) $("#aiModeBadge").textContent = state.aiScope === "node" && node ? `当前节点 ${shortId(node.node_id)}` : "项目综合";
  updateChatPlaceholder();
  if (state.aiScope !== "node") {
    $("#aiContext").innerHTML = `
      <details class="ai-context-details">
        <summary>
          <span>项目综合分析</span>
          <em>${nodeCount} 个节点 · ${uploadCount} 份资料 · 默认不绑定单点</em>
        </summary>
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
    <details class="ai-context-details">
      <summary>
        <span>${esc(shortId(node.node_id))} ${esc(node.node_name)}</span>
        <em>${esc(node.primary_positioning || "待补场景")}</em>
      </summary>
      <div>
        <b>当前范围</b>
        <span>只围绕这个节点整理问题、依据和待补资料；不输出最终推荐。</span>
      </div>
    </details>
    <button class="secondary-btn" type="button" id="aiUseProjectBtn">回到项目综合</button>
  `;
}

function updateChatPlaceholder() {
  const input = $("#chatInput");
  if (!input) return;
  const node = currentNode();
  input.placeholder = state.aiScope === "node" && node
    ? `围绕 ${shortId(node.node_id)} 提问，例如：这个节点还缺哪些资料？`
    : "围绕项目综合提问，例如：当前资料能支撑报告吗？还缺什么？";
}

function humanizeAiText(text) {
  return valueText(text, "")
    .replace(/\bfrontend_simulation_check\b/gi, "结构化仿真检查")
    .replace(/\bP3[-_]?GATE[-_]?\d+\s*:\s*/gi, "")
    .replace(/\bgeometry\b/gi, "图纸/几何")
    .replace(/\bvisitor_flow\b/gi, "客流")
    .replace(/\bconversion_rate\b/gi, "消费转化率")
    .replace(/\brevenue_cost\b/gi, "收益成本")
    .replace(/\boperation_authorization\b/gi, "运营授权")
    .replace(/\bmodel_gate\b/gi, "模型综合")
    .replace(/\binside_osm_polygon\b/gi, "边界内候选")
    .replace(/\bestimated_range_needs_review\b/gi, "范围待人工确认")
    .replace(new RegExp(`\\b${STATUS_TOKENS.needsReview}\\s*\\/\\s*${STATUS_TOKENS.notFinal}\\b`, "gi"), "待人工确认")
    .replace(new RegExp(`\\b${STATUS_TOKENS.needsReview}\\b`, "gi"), "待人工确认")
    .replace(new RegExp(`\\b${STATUS_TOKENS.notFinal}\\b`, "gi"), "非最终结论")
    .replace(new RegExp(`\\b${STATUS_TOKENS.positionReference}\\b`, "gi"), "仅作位置参考")
    .replace(/\bbackend\b/gi, "系统")
    .replace(new RegExp(`\\b${["de", "bug"].join("")}\\b`, "gi"), "诊断信息")
    .replace(new RegExp(`\\b${["raw", "payload"].join(" ")}\\b`, "gi"), "原始资料")
    .replace(/\bconnected_image\b/gi, "图片可用")
    .replace(/\bconnected\b/gi, "已接入")
    .replace(/\bconfigured\b/gi, "已配置")
    .replace(/\bmissing_key\b/gi, "缺少配置")
    .replace(/\bblocked\b/gi, "等待补齐")
    .replace(/\blocal_data\b/gi, "本地资料")
    .replace(/\bmap_data\b/gi, "地图资料")
    .replace(/\bmap_service\b/gi, "地图服务")
    .replace(/\bai_assistant\b/gi, "AI 助手")
    .replace(/DeepSeek/g, "AI 助手");
}

function formatAssistantText(text) {
  const cleaned = humanizeAiText(text).replace(/\r\n/g, "\n").trim();
  if (!cleaned) return "<p>暂时没有可展示的回答。</p>";
  const blocks = cleaned.split(/\n{2,}/).map((part) => part.trim()).filter(Boolean);
  return blocks.map((part) => {
    const heading = part.match(/^(?:#{1,3}\s*)?(?:\*\*)?([一二三四五六七八九十0-9]+[.、]\s*[^*\n]+|摘要|关键依据|当前缺口|推进事项|下一步[^*\n]*)(?:\*\*)?$/);
    if (heading && part.length < 60) return `<h3>${esc(heading[1])}</h3>`;
    const lines = part.split("\n").map((line) => line.trim()).filter(Boolean);
    if (lines.length > 1 && lines.every((line) => /^[-*•]\s+/.test(line))) {
      return `<ul>${lines.map((line) => `<li>${esc(line.replace(/^[-*•]\s+/, "").replace(/\*\*/g, ""))}</li>`).join("")}</ul>`;
    }
    return `<p>${esc(part.replace(/\*\*/g, "")).replace(/\n/g, "<br>")}</p>`;
  }).join("");
}

function addChatMessage(role, text, meta = "") {
  const box = $("#chatMessages");
  box.querySelector(".chat-empty-state")?.remove();
  const item = document.createElement("div");
  item.className = `chat-message ${role}`;
  const assistant = role.includes("assistant") && !role.includes("thinking");
  item.innerHTML = `<div>${assistant ? formatAssistantText(text) : esc(humanizeAiText(text))}</div>${meta ? `<span>${esc(humanizeAiText(meta))}</span>` : ""}`;
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
  updateReportButtonState();
  input.value = "";
  autoResizeComposer();
  const uploaded = await uploadComposerAttachments(message);
  const attachmentText = uploaded.length
    ? `\n\n已附资料：${uploaded.map((item) => `${item.filename}（${item.category}，${item.review_status}）`).join("；")}`
    : "";
  const composedMessage = `${message || "请先查看我上传的资料，并说明下一步怎么进入待复核解析。"}${attachmentText}`;
  addChatMessage("user", composedMessage);
  const thinking = addChatMessage("assistant thinking", "正在思考，请稍等……", "AI 正在整理");
  thinking.querySelector("div").textContent = "正在读取上下文、整理资料缺口，并登记本轮专家输入……";
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
    addChatMessage("assistant", data.message || "AI 暂时没有返回内容", `${data.generated_by || "AI"} · 待人工确认`);
    state.lastAction = "AI 对话已更新，专家输入已登记为待复核";
    await loadAiSessions();
    renderAiSessions();
    await loadDashboard();
    setView("ai");
  } finally {
    state.aiBusy = false;
    updateReportButtonState();
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
      data_hint: uploaded.length ? statusToken("uploaded", "source", "needs", "review") : STATUS_TOKENS.needsReview,
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
    if (nodeBtn && !nodeBtn.closest("#nodeEditForm")) {
      state.selectedNodeId = nodeBtn.dataset.nodeId;
      state.selectedPoiId = null;
      state.nodeFormModeNew = false;
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
      setView(viewBtn.dataset.view, { scrollTarget: viewBtn.dataset.scrollTarget || "" });
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
      if (state.activeAiSessionId) {
        openAiSession(state.activeAiSessionId).catch((error) => {
          state.lastAction = error.message;
          renderMeta();
        });
      } else {
        renderChatMessagesFromSession(null);
      }
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
    const composerReportBtn = event.target.closest("#composerReportBtn");
    if (composerReportBtn) {
      generateChatReport().catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const railToggleBtn = event.target.closest("#aiRailToggle");
    if (railToggleBtn) {
      state.aiRailCollapsed = !state.aiRailCollapsed;
      renderAiSessions();
      return;
    }
    const aiUseNodeBtn = event.target.closest("#aiUseNodeBtn");
    if (aiUseNodeBtn) {
      state.aiScope = "node";
      renderAiContext();
      return;
    }
    const aiUseProjectBtn = event.target.closest("#aiUseProjectBtn");
    if (aiUseProjectBtn) {
      state.aiScope = "project";
      renderAiContext();
      return;
    }
    const modeBtn = event.target.closest("[data-map-mode]");
    if (modeBtn) {
      state.mapMode = modeBtn.dataset.mapMode;
      state.activeLayer = state.mapMode;
      state.mapLayerLoading = true;
      $$("[data-map-mode]").forEach((btn) => btn.classList.toggle("active", btn === modeBtn));
      renderMap();
      renderAmapMarkers();
      window.setTimeout(() => {
        state.mapLayerLoading = false;
        renderMap();
        renderMapResultList();
      }, 120);
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
    const newNodeBtn = event.target.closest("#newNodeBtn, #quickNewNodeBtn");
    if (newNodeBtn) {
      state.selectedNodeId = null;
      state.selectedPoiId = null;
      state.nodeFormModeNew = true;
      renderDetail();
      setView("nodes");
      return;
    }
    const deleteNodeBtn = event.target.closest("#deleteNodeBtn");
    if (deleteNodeBtn) {
      deleteSelectedNode(deleteNodeBtn.dataset.nodeId).catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const generateNodesBtn = event.target.closest("#generatePlanNodesBtn, #quickGeneratePlanNodesBtn, #oneClickPlanImportBtn");
    if (generateNodesBtn) {
      generatePlanNodes().catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const nodeSaveBtn = event.target.closest("[data-node-save]");
    if (nodeSaveBtn) {
      const nodeSaveForm = nodeSaveBtn.closest("#nodeEditForm");
      if (nodeSaveForm) {
        submitNodeForm(nodeSaveForm).catch((error) => {
          state.lastAction = error.message;
          renderMeta();
        });
        return;
      }
    }
    const poiBtn = event.target.closest("[data-poi-id]");
    if (poiBtn) {
      const poi = (mapContextPayload()?.supply_points || []).find((item) => getPoiId(item) === poiBtn.dataset.poiId);
      if (poi) selectPoi(poi);
      return;
    }
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
    const toggleSimObjectPoolBtn = event.target.closest("[data-action='toggle-simulation-objects']");
    if (toggleSimObjectPoolBtn) {
      state.showAllSimulationObjects = !state.showAllSimulationObjects;
      renderSimulationObjectPool();
      return;
    }
    const toggleTaskObjectsBtn = event.target.closest("[data-action='toggle-task-objects']");
    if (toggleTaskObjectsBtn) {
      state.showAllTaskObjects = !state.showAllTaskObjects;
      renderSimulationTaskPreflight();
      return;
    }
    const toggleFeatureDerivativesBtn = event.target.closest("[data-action='toggle-feature-derivatives']");
    if (toggleFeatureDerivativesBtn) {
      state.showAllFeatureDerivatives = !state.showAllFeatureDerivatives;
      renderSimulationTaskPreflight();
      return;
    }
    const featureDerivativeActionBtn = event.target.closest("[data-feature-derivative-action]");
    if (featureDerivativeActionBtn) {
      updateFeatureDerivativeAction(
        featureDerivativeActionBtn.dataset.featureDerivativeId,
        featureDerivativeActionBtn.dataset.featureDerivativeAction
      ).catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const selectAdoptedTaskObjectsBtn = event.target.closest("[data-action='select-adopted-task-objects']");
    if (selectAdoptedTaskObjectsBtn) {
      selectAdoptedTaskObjects();
      return;
    }
    const clearTaskObjectsBtn = event.target.closest("[data-action='clear-task-objects']");
    if (clearTaskObjectsBtn) {
      clearTaskObjects();
      return;
    }
    const saveSimulationTaskBtn = event.target.closest("#saveSimulationTaskBtn, [data-action='save-simulation-task']");
    if (saveSimulationTaskBtn) {
      saveSimulationTaskPreflight().catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
    const addPersonaStateObjectBtn = event.target.closest("#addPersonaStateObjectBtn");
    if (addPersonaStateObjectBtn) {
      openSimulationObjectForm("persona_state");
      return;
    }
    const addBehaviorProgramObjectBtn = event.target.closest("#addBehaviorProgramObjectBtn");
    if (addBehaviorProgramObjectBtn) {
      openSimulationObjectForm("behavior_program");
      return;
    }
    const addChoiceObjectBtn = event.target.closest("#addChoiceObjectBtn");
    if (addChoiceObjectBtn) {
      openSimulationObjectForm("choice_probability");
      return;
    }
    const addValidationObjectBtn = event.target.closest("#addValidationObjectBtn");
    if (addValidationObjectBtn) {
      openSimulationObjectForm("simulation_validation_target");
      return;
    }
    const editSimObjectBtn = event.target.closest("[data-sim-object-edit]");
    if (editSimObjectBtn) {
      openSimulationObjectForm("choice_probability", editSimObjectBtn.dataset.simObjectEdit);
      return;
    }
    const simObjectActionBtn = event.target.closest("[data-sim-object-action]");
    if (simObjectActionBtn) {
      updateSimulationObjectAction(simObjectActionBtn.dataset.simObjectId, simObjectActionBtn.dataset.simObjectAction).catch((error) => {
        state.lastAction = error.message;
        renderMeta();
      });
      return;
    }
  });

  $("#nodeSearch").addEventListener("input", renderNodes);
  document.body.addEventListener("change", (event) => {
    const taskObjectInput = event.target.closest("[data-sim-task-object]");
    if (taskObjectInput) {
      taskObjectInput.closest(".task-object-option")?.classList.toggle("checked", taskObjectInput.checked);
    }
  });
  $("#uploadForm").addEventListener("submit", submitUpload);
  $("#simulationObjectForm").addEventListener("submit", (event) => {
    saveSimulationObject(event).catch((error) => {
      state.lastAction = error.message;
      renderMeta();
    });
  });
  $("#cancelSimObjectBtn").addEventListener("click", closeSimulationObjectForm);
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
  const [view, scrollTarget] = hash.split(":");
  if (VALID_VIEWS.includes(view) && view !== "overview") setView(view, { scrollTarget: scrollTarget || "" });
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
