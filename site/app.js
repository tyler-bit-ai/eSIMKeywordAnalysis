const DEFAULT_DATA_PATH = "./data/dashboard_data.json";
const DEFAULT_MANIFEST_PATH = "./data/dashboard_manifest.json";

const state = {
  manifest: null,
  manifestUrl: null,
  payload: null,
  activeDatasetId: "",
  activeSnapshotTab: "new_keywords",
  targetTablePage: 1,
  modifierSummaryPage: 1,
  pageSize: 10,
};

const elements = {
  datasetSelect: document.querySelector("#dataset-select"),
  datasetSummary: document.querySelector("#dataset-summary"),
  generatedAt: document.querySelector("#generated-at"),
  sourceReportDir: document.querySelector("#source-report-dir"),
  helpButton: document.querySelector("#help-button"),
  helpDialog: document.querySelector("#help-dialog"),
  helpClose: document.querySelector("#help-close"),
  helpScoreTitle: document.querySelector("#help-score-title"),
  helpScoreSummary: document.querySelector("#help-score-summary"),
  helpFormulaList: document.querySelector("#help-formula-list"),
  helpSignalWeights: document.querySelector("#help-signal-weights"),
  helpPriorityRules: document.querySelector("#help-priority-rules"),
  helpBucketRules: document.querySelector("#help-bucket-rules"),
  helpSections: document.querySelector("#help-sections"),
  statusText: document.querySelector("#status-text"),
  searchInput: document.querySelector("#search-input"),
  priorityFilter: document.querySelector("#priority-filter"),
  signalFilter: document.querySelector("#signal-filter"),
  hideNoisyFilter: document.querySelector("#hide-noisy-filter"),
  kpiGrid: document.querySelector("#kpi-grid"),
  kpiExport: document.querySelector("#kpi-export"),
  tableCount: document.querySelector("#table-count"),
  targetTableBody: document.querySelector("#target-table-body"),
  targetTablePrev: document.querySelector("#target-table-prev"),
  targetTableNext: document.querySelector("#target-table-next"),
  targetTablePageInfo: document.querySelector("#target-table-page-info"),
  targetTableExport: document.querySelector("#target-table-export"),
  modifierSummary: document.querySelector("#modifier-summary"),
  modifierSummaryPrev: document.querySelector("#modifier-summary-prev"),
  modifierSummaryNext: document.querySelector("#modifier-summary-next"),
  modifierSummaryPageInfo: document.querySelector("#modifier-summary-page-info"),
  modifierSummaryExport: document.querySelector("#modifier-summary-export"),
  seedLineage: document.querySelector("#seed-lineage"),
  seedLineageExport: document.querySelector("#seed-lineage-export"),
  signalSummary: document.querySelector("#signal-summary"),
  signalSummaryExport: document.querySelector("#signal-summary-export"),
  snapshotPanel: document.querySelector("#snapshot-panel"),
  snapshotExport: document.querySelector("#snapshot-export"),
  snapshotTabs: Array.from(document.querySelectorAll(".tab-button")),
  emptyStateTemplate: document.querySelector("#empty-state-template"),
};

function getUrl() {
  return new URL(window.location.href);
}

function getDataPath() {
  return getUrl().searchParams.get("data") || DEFAULT_DATA_PATH;
}

function getManifestPath() {
  return getUrl().searchParams.get("manifest") || DEFAULT_MANIFEST_PATH;
}

function getRequestedDatasetId() {
  return getUrl().searchParams.get("dataset") || "";
}

function shouldUseDirectDataPath() {
  const url = getUrl();
  return url.searchParams.has("data") && !url.searchParams.has("manifest") && !url.searchParams.has("dataset");
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`Failed to load published data: ${response.status}`);
  }
  return response.json();
}

async function loadPayload(path = getDataPath()) {
  return fetchJson(path);
}

async function loadManifest() {
  if (shouldUseDirectDataPath()) {
    return null;
  }

  const manifestUrl = new URL(getManifestPath(), window.location.href).toString();
  try {
    const manifest = await fetchJson(manifestUrl);
    if (!Array.isArray(manifest.datasets) || !manifest.datasets.length) {
      return null;
    }
    state.manifestUrl = manifestUrl;
    return manifest;
  } catch (error) {
    return null;
  }
}

function resetFilterOptions() {
  elements.searchInput.value = "";
  elements.priorityFilter.innerHTML = '<option value="">All</option>';
  elements.signalFilter.innerHTML = '<option value="">All</option>';
  elements.hideNoisyFilter.checked = false;
}

function resetPaging() {
  state.targetTablePage = 1;
  state.modifierSummaryPage = 1;
  state.activeSnapshotTab = "new_keywords";
  for (const button of elements.snapshotTabs) {
    button.classList.toggle("active", button.dataset.tab === state.activeSnapshotTab);
  }
}

function initFilters(payload) {
  resetFilterOptions();
  const priorities = [...new Set((payload.target_table || []).map((row) => row.marketing_priority).filter(Boolean))];
  const signals = [...new Set((payload.target_table || []).flatMap((row) => row.observed_signals || []))];

  for (const value of priorities) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    elements.priorityFilter.append(option);
  }

  for (const value of signals.sort()) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value;
    elements.signalFilter.append(option);
  }
}

function renderMeta(payload, datasetEntry) {
  elements.generatedAt.textContent = payload.generated_at || datasetEntry?.generated_at || "unknown";
  elements.sourceReportDir.textContent = payload.source_report_dir || datasetEntry?.source_report_dir || "unknown";
  elements.datasetSummary.textContent = datasetEntry
    ? `${datasetEntry.label} selected from ${state.manifest?.datasets?.length || 1} published datasets.`
    : "Single published dataset mode.";
}

function renderHelp(payload) {
  const help = payload.help || {};
  const scoreRule = help.score_rule || {};
  const sections = help.sections || [];

  elements.helpScoreTitle.textContent = scoreRule.title || "How scoring works";
  elements.helpScoreSummary.textContent = scoreRule.summary || "";
  renderSimpleList(elements.helpFormulaList, scoreRule.formula_steps || []);
  renderSimpleList(elements.helpPriorityRules, scoreRule.marketing_priority_rules || []);
  renderSimpleList(elements.helpBucketRules, scoreRule.bucket_rules || []);

  elements.helpSignalWeights.innerHTML = "";
  for (const [signal, weight] of Object.entries(scoreRule.signal_weights || {})) {
    const card = document.createElement("article");
    card.className = "list-card";
    card.innerHTML = `
      <h3>${escapeHtml(signal)}</h3>
      <p class="muted-inline">weight ${escapeHtml(weight)}</p>
    `;
    elements.helpSignalWeights.append(card);
  }

  elements.helpSections.innerHTML = "";
  for (const section of sections) {
    const card = document.createElement("article");
    card.className = "list-card";
    card.innerHTML = `
      <h3>${escapeHtml(section.title || "")}</h3>
      <p class="muted-inline"><strong>What it means:</strong> ${escapeHtml(section.business_meaning || "")}</p>
      <p class="muted-inline"><strong>How to use it:</strong> ${escapeHtml(section.how_to_use || "")}</p>
      <p class="muted-inline"><strong>What drives it:</strong> ${escapeHtml(section.scoring_note || "")}</p>
    `;
    elements.helpSections.append(card);
  }
}

function renderKpis(payload) {
  elements.kpiGrid.innerHTML = "";
  const entries = [
    ["High Priority Targets", payload.kpis?.high_priority_targets ?? 0],
    ["Rising Keywords", payload.kpis?.rising_keywords ?? 0],
    ["New Since Snapshot", payload.kpis?.new_keywords ?? 0],
    ["Manual Review Terms", payload.kpis?.manual_review_terms ?? 0],
    ["Tracked Targets", payload.kpis?.tracked_targets ?? 0],
  ];

  for (const [label, value] of entries) {
    const card = document.createElement("article");
    card.className = "kpi-card";
    card.innerHTML = `<span class="stat-label">${label}</span><strong class="kpi-value">${value}</strong>`;
    elements.kpiGrid.append(card);
  }
}

function getFilteredTargets() {
  const rows = state.payload?.target_table || [];
  const searchValue = elements.searchInput.value.trim().toLowerCase();
  const priorityValue = elements.priorityFilter.value;
  const signalValue = elements.signalFilter.value;
  const hideNoisy = elements.hideNoisyFilter.checked;

  return rows.filter((row) => {
    const haystack = [
      row.canonical_keyword,
      row.follow_on_modifier,
      ...(row.origin_seeds || []),
      ...(row.observed_signals || []),
    ]
      .join(" ")
      .toLowerCase();

    if (searchValue && !haystack.includes(searchValue)) {
      return false;
    }
    if (priorityValue && row.marketing_priority !== priorityValue) {
      return false;
    }
    if (signalValue && !(row.observed_signals || []).includes(signalValue)) {
      return false;
    }
    if (hideNoisy && row.is_noisy) {
      return false;
    }
    return true;
  });
}

function getPageSlice(rows, page, pageSize) {
  const totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
  const safePage = Math.min(Math.max(page, 1), totalPages);
  const start = (safePage - 1) * pageSize;
  const end = start + pageSize;
  return {
    pageRows: rows.slice(start, end),
    safePage,
    totalPages,
    start,
    end: Math.min(end, rows.length),
  };
}

function renderTargetTable(rows) {
  elements.targetTableBody.innerHTML = "";
  const { pageRows, safePage, totalPages, start, end } = getPageSlice(rows, state.targetTablePage, state.pageSize);
  state.targetTablePage = safePage;
  elements.tableCount.textContent = rows.length
    ? `${start + 1}-${end} of ${rows.length} visible targets`
    : "0 visible targets";
  elements.targetTablePageInfo.textContent = `Page ${safePage} / ${totalPages}`;
  elements.targetTablePrev.disabled = safePage <= 1;
  elements.targetTableNext.disabled = safePage >= totalPages;

  if (!pageRows.length) {
    const tr = document.createElement("tr");
    const td = document.createElement("td");
    td.colSpan = 7;
    td.append(elements.emptyStateTemplate.content.cloneNode(true));
    tr.append(td);
    elements.targetTableBody.append(tr);
    return;
  }

  for (const row of pageRows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="keyword-cell">
        <strong>${escapeHtml(row.canonical_keyword || "")}</strong>
        <span class="muted-inline">${escapeHtml(row.target_reason || "")}</span>
      </td>
      <td>${escapeHtml(row.follow_on_modifier || "n/a")}</td>
      <td>${renderPriorityBadge(row.marketing_priority || "unknown")}</td>
      <td class="mono">${row.priority_score ?? ""}</td>
      <td>${escapeHtml(row.keyword_bucket || "")}</td>
      <td>${renderBadgeRow(row.observed_signals || [])}</td>
      <td>${renderBadgeRow(row.origin_seeds || [])}</td>
    `;
    elements.targetTableBody.append(tr);
  }
}

function renderCollection(container, rows, buildCard) {
  container.innerHTML = "";
  if (!rows.length) {
    container.append(elements.emptyStateTemplate.content.cloneNode(true));
    return;
  }

  for (const row of rows) {
    container.append(buildCard(row));
  }
}

function renderSimpleList(container, values) {
  container.innerHTML = "";
  for (const value of values) {
    const item = document.createElement("li");
    item.textContent = value;
    container.append(item);
  }
}

function renderModifierSummary(payload) {
  const rows = payload.modifier_summary || [];
  const { pageRows, safePage, totalPages } = getPageSlice(rows, state.modifierSummaryPage, state.pageSize);
  state.modifierSummaryPage = safePage;
  elements.modifierSummaryPageInfo.textContent = `Page ${safePage} / ${totalPages}`;
  elements.modifierSummaryPrev.disabled = safePage <= 1;
  elements.modifierSummaryNext.disabled = safePage >= totalPages;

  renderCollection(elements.modifierSummary, pageRows, (row) => {
    const card = document.createElement("article");
    card.className = "list-card";
    card.innerHTML = `
      <h3>${escapeHtml(row.follow_on_modifier || "unknown")}</h3>
      <div class="stats-row">
        <span class="stat-chip">keywords ${row.keyword_count ?? 0}</span>
        <span class="stat-chip">avg score ${row.avg_priority_score ?? 0}</span>
      </div>
      <p class="muted-inline">${escapeHtml(row.top_keywords || "")}</p>
    `;
    return card;
  });
}

function renderSeedLineage(payload) {
  renderCollection(elements.seedLineage, payload.seed_lineage || [], (row) => {
    const card = document.createElement("article");
    card.className = "list-card";
    card.innerHTML = `
      <h3>${escapeHtml(row.origin_seed || "unknown")}</h3>
      <div class="stats-row">
        <span class="stat-chip">keywords ${row.keyword_count ?? 0}</span>
        <span class="stat-chip">avg score ${row.avg_priority_score ?? 0}</span>
      </div>
      <p class="muted-inline">${escapeHtml(row.modifiers || "")}</p>
    `;
    return card;
  });
}

function renderSignalSummary(payload) {
  renderCollection(elements.signalSummary, payload.signal_summary || [], (row) => {
    const card = document.createElement("article");
    card.className = "list-card";
    card.innerHTML = `
      <h3>${escapeHtml(row.signal || "unknown")}</h3>
      <div class="stats-row">
        <span class="stat-chip">keywords ${row.keyword_count ?? 0}</span>
        <span class="stat-chip">avg score ${row.avg_priority_score ?? 0}</span>
      </div>
    `;
    return card;
  });
}

function renderSnapshotPanel() {
  const rows = state.payload?.snapshot_changes?.[state.activeSnapshotTab] || [];
  renderCollection(elements.snapshotPanel, rows, (row) => {
    const card = document.createElement("article");
    card.className = "list-card";
    card.innerHTML = `
      <h3>${escapeHtml(row.canonical_keyword || row.canonical_keyword_current || row.canonical_keyword_previous || "keyword")}</h3>
      <p class="muted-inline mono">${escapeHtml(JSON.stringify(row))}</p>
    `;
    return card;
  });
}

function renderPriorityBadge(priority) {
  const value = escapeHtml(priority);
  return `<span class="badge priority-${value.toLowerCase()}">${value}</span>`;
}

function renderBadgeRow(values) {
  if (!values.length) {
    return `<span class="muted-inline">n/a</span>`;
  }
  return `<div class="badge-row">${values.map((value) => `<span class="badge">${escapeHtml(value)}</span>`).join("")}</div>`;
}

function buildCsv(rows) {
  if (!rows.length) {
    return "\uFEFFNo data\n";
  }

  const headers = [...rows.reduce((keys, row) => {
    for (const key of Object.keys(row)) {
      keys.add(key);
    }
    return keys;
  }, new Set())];

  const lines = [
    headers.join(","),
    ...rows.map((row) => headers.map((header) => csvEscape(row[header])).join(",")),
  ];
  return `\uFEFF${lines.join("\n")}`;
}

function csvEscape(value) {
  if (Array.isArray(value)) {
    return csvEscape(value.join(" | "));
  }
  if (value && typeof value === "object") {
    return csvEscape(JSON.stringify(value));
  }
  const normalized = value ?? "";
  const stringValue = String(normalized).replaceAll('"', '""');
  return `"${stringValue}"`;
}

function downloadRows(filename, rows) {
  const blob = new Blob([buildCsv(rows)], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.append(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function openHelpDialog() {
  if (typeof elements.helpDialog.showModal === "function") {
    elements.helpDialog.showModal();
    return;
  }
  elements.helpDialog.setAttribute("open", "open");
}

function closeHelpDialog() {
  if (typeof elements.helpDialog.close === "function") {
    elements.helpDialog.close();
    return;
  }
  elements.helpDialog.removeAttribute("open");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function populateDatasetSelector(manifest) {
  elements.datasetSelect.innerHTML = "";
  const sorted = [...manifest.datasets].sort((left, right) => {
    return (right.generated_at || "").localeCompare(left.generated_at || "");
  });

  for (const entry of sorted) {
    const option = document.createElement("option");
    option.value = entry.dataset_id;
    option.textContent = entry.label;
    elements.datasetSelect.append(option);
  }
}

function getActiveDatasetEntry() {
  return state.manifest?.datasets?.find((entry) => entry.dataset_id === state.activeDatasetId) || null;
}

function resolveDatasetPath(entry) {
  if (!state.manifestUrl) {
    return entry.path;
  }
  return new URL(entry.path, state.manifestUrl).toString();
}

async function selectDataset(datasetId) {
  const entry = state.manifest?.datasets?.find((candidate) => candidate.dataset_id === datasetId);
  if (!entry) {
    throw new Error(`Unknown dataset: ${datasetId}`);
  }

  elements.statusText.textContent = `Loading ${entry.label}...`;
  const payload = await loadPayload(resolveDatasetPath(entry));
  state.activeDatasetId = entry.dataset_id;
  elements.datasetSelect.value = entry.dataset_id;
  applyPayload(payload, entry);
  elements.statusText.textContent = `${entry.label} loaded.`;
}

function applyPayload(payload, datasetEntry = null) {
  state.payload = payload;
  resetPaging();
  initFilters(payload);
  renderMeta(payload, datasetEntry);
  renderHelp(payload);
  renderKpis(payload);
  renderTargetTable(getFilteredTargets());
  renderModifierSummary(payload);
  renderSeedLineage(payload);
  renderSignalSummary(payload);
  renderSnapshotPanel();
}

function bindEvents() {
  const rerenderTable = ({ resetPage = false } = {}) => {
    if (resetPage) {
      state.targetTablePage = 1;
    }
    renderTargetTable(getFilteredTargets());
  };

  elements.datasetSelect.addEventListener("change", async () => {
    if (!state.manifest || !elements.datasetSelect.value) {
      return;
    }
    await selectDataset(elements.datasetSelect.value);
  });
  elements.searchInput.addEventListener("input", () => rerenderTable({ resetPage: true }));
  elements.priorityFilter.addEventListener("change", () => rerenderTable({ resetPage: true }));
  elements.signalFilter.addEventListener("change", () => rerenderTable({ resetPage: true }));
  elements.hideNoisyFilter.addEventListener("change", () => rerenderTable({ resetPage: true }));
  elements.targetTablePrev.addEventListener("click", () => {
    state.targetTablePage -= 1;
    rerenderTable();
  });
  elements.targetTableNext.addEventListener("click", () => {
    state.targetTablePage += 1;
    rerenderTable();
  });
  elements.modifierSummaryPrev.addEventListener("click", () => {
    state.modifierSummaryPage -= 1;
    renderModifierSummary(state.payload || {});
  });
  elements.modifierSummaryNext.addEventListener("click", () => {
    state.modifierSummaryPage += 1;
    renderModifierSummary(state.payload || {});
  });
  elements.kpiExport.addEventListener("click", () => {
    downloadRows("published-kpis.csv", [state.payload?.kpis || {}]);
  });
  elements.targetTableExport.addEventListener("click", () => {
    downloadRows("korea-keyword-comparison.csv", getFilteredTargets());
  });
  elements.modifierSummaryExport.addEventListener("click", () => {
    downloadRows("modifier-summary.csv", state.payload?.modifier_summary || []);
  });
  elements.seedLineageExport.addEventListener("click", () => {
    downloadRows("root-seed-lineage.csv", state.payload?.seed_lineage || []);
  });
  elements.signalSummaryExport.addEventListener("click", () => {
    downloadRows("signal-summary.csv", state.payload?.signal_summary || []);
  });
  elements.snapshotExport.addEventListener("click", () => {
    downloadRows(`snapshot-${state.activeSnapshotTab}.csv`, state.payload?.snapshot_changes?.[state.activeSnapshotTab] || []);
  });
  elements.helpButton.addEventListener("click", () => {
    openHelpDialog();
  });
  elements.helpClose.addEventListener("click", () => {
    closeHelpDialog();
  });
  elements.helpDialog.addEventListener("click", (event) => {
    if (event.target === elements.helpDialog) {
      closeHelpDialog();
    }
  });

  for (const button of elements.snapshotTabs) {
    button.addEventListener("click", () => {
      state.activeSnapshotTab = button.dataset.tab;
      for (const candidate of elements.snapshotTabs) {
        candidate.classList.toggle("active", candidate === button);
      }
      renderSnapshotPanel();
    });
  }
}

async function main() {
  bindEvents();

  try {
    const manifest = await loadManifest();
    if (manifest) {
      state.manifest = manifest;
      populateDatasetSelector(manifest);
      const requestedDatasetId = getRequestedDatasetId();
      const defaultDatasetId = requestedDatasetId || manifest.default_dataset_id || manifest.datasets[0].dataset_id;
      await selectDataset(defaultDatasetId);
      return;
    }

    const payload = await loadPayload();
    applyPayload(payload);
    elements.datasetSelect.innerHTML = '<option value="">Single dataset</option>';
    elements.statusText.textContent = "Published dashboard data loaded.";
  } catch (error) {
    elements.statusText.textContent = error.message;
    elements.generatedAt.textContent = "unavailable";
    elements.sourceReportDir.textContent = "unavailable";
    elements.datasetSummary.textContent = "No published dataset available.";
    renderHelp({});
    renderKpis({ kpis: {} });
    renderTargetTable([]);
    renderModifierSummary({ modifier_summary: [] });
    renderSeedLineage({ seed_lineage: [] });
    renderSignalSummary({ signal_summary: [] });
    renderSnapshotPanel();
  }
}

main();
