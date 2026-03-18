const DEFAULT_DATA_PATH = "./data/dashboard_data.json";

const state = {
  payload: null,
  activeSnapshotTab: "new_keywords",
  targetTablePage: 1,
  modifierSummaryPage: 1,
  pageSize: 10,
};

const elements = {
  datasetVersion: document.querySelector("#dataset-version"),
  generatedAt: document.querySelector("#generated-at"),
  sourceReportDir: document.querySelector("#source-report-dir"),
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

function getDataPath() {
  const url = new URL(window.location.href);
  return url.searchParams.get("data") || DEFAULT_DATA_PATH;
}

async function loadPayload() {
  const response = await fetch(getDataPath());
  if (!response.ok) {
    throw new Error(`Failed to load published data: ${response.status}`);
  }
  return response.json();
}

function initFilters(payload) {
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

function renderMeta(payload) {
  elements.datasetVersion.textContent = payload.dataset_version || "unknown";
  elements.generatedAt.textContent = payload.generated_at || "unknown";
  elements.sourceReportDir.textContent = payload.source_report_dir || "unknown";
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function bindEvents() {
  const rerenderTable = ({ resetPage = false } = {}) => {
    if (resetPage) {
      state.targetTablePage = 1;
    }
    renderTargetTable(getFilteredTargets());
  };

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
    const payload = await loadPayload();
    state.payload = payload;
    renderMeta(payload);
    initFilters(payload);
    renderKpis(payload);
    renderTargetTable(getFilteredTargets());
    renderModifierSummary(payload);
    renderSeedLineage(payload);
    renderSignalSummary(payload);
    renderSnapshotPanel();
    elements.statusText.textContent = "Published dashboard data loaded.";
  } catch (error) {
    elements.statusText.textContent = error.message;
    elements.generatedAt.textContent = "unavailable";
    elements.datasetVersion.textContent = "unavailable";
    elements.sourceReportDir.textContent = "unavailable";
    renderKpis({ kpis: {} });
    renderTargetTable([]);
    renderModifierSummary({ modifier_summary: [] });
    renderSeedLineage({ seed_lineage: [] });
    renderSignalSummary({ signal_summary: [] });
    renderSnapshotPanel();
  }
}

main();
