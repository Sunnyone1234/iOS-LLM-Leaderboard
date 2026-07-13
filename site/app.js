const DATA_URL = "results/suite-b-pilot-v0.1/normalized-results.json";

const state = {
  data: null,
  mode: "ux",
  sortKey: "response",
  sortDirection: "asc",
  query: "",
  device: "all",
  runtime: "all",
};

const modeConfig = {
  ux: {
    workload: "b-ux-001-short-interaction",
    label: "First-renderable proxy TTFT",
    description: "Adapter boundary, not screen-render latency. Lower is better.",
    defaultSort: "response",
    defaultDirection: "asc",
    columns: [
      column("rank", "Rank", () => 0, value => value, false),
      column("model", "Model", row => row.configuration.model.displayName, value => value),
      column("quantization", "Quant", row => row.configuration.model.quantization, value => value),
      column("response", "Proxy TTFT", row => row.summary.medianUserVisibleTTFTMilliseconds, value => formatMs(value), true, true),
      column("pipeline", "Pipeline TTFT", row => row.summary.medianPipelineTTFTMilliseconds, value => formatMs(value), true),
      column("prefill", "Prefill", row => row.summary.medianPrefillTokensPerSecond, value => formatRate(value), true),
      column("decode", "Decode", row => row.summary.medianDecodeTokensPerSecond, value => formatRate(value), true),
      column("memory", "Peak memory", row => row.summary.medianPeakMemoryMegabytes, value => formatMemory(value), true),
      column("thermal", "Thermal", row => thermalOrder(row.summary.finalThermalState), (_, row) => thermalMarkup(row.summary.finalThermalState), true),
      column("details", "Evidence", () => 0, () => "", false),
    ],
  },
  pipe: {
    workload: "b-pipe-001-sustained-generation",
    label: "Sustained decode throughput",
    description: "Five measured generations without a rest interval. Higher is better.",
    defaultSort: "decode",
    defaultDirection: "desc",
    columns: [
      column("rank", "Rank", () => 0, value => value, false),
      column("model", "Model", row => row.configuration.model.displayName, value => value),
      column("quantization", "Quant", row => row.configuration.model.quantization, value => value),
      column("decode", "Decode", row => row.summary.medianDecodeTokensPerSecond, value => formatRate(value), true, true),
      column("pipeline", "Pipeline TTFT", row => row.summary.medianPipelineTTFTMilliseconds, value => formatMs(value), true),
      column("prefill", "Prefill", row => row.summary.medianPrefillTokensPerSecond, value => formatRate(value), true),
      column("memory", "Peak memory", row => row.summary.medianPeakMemoryMegabytes, value => formatMemory(value), true),
      column("degradation", "Decode change", row => row.degradation?.decodePercentChange, value => formatPercent(value), true),
      column("thermal", "Thermal", row => thermalOrder(row.summary.finalThermalState), (_, row) => thermalMarkup(row.summary.finalThermalState), true),
      column("details", "Evidence", () => 0, () => "", false),
    ],
  },
  ship: {
    workload: null,
    label: "Deployment facts",
    description: "Source-backed facts from the same tested configurations. No Ship score.",
    defaultSort: "size",
    defaultDirection: "asc",
    columns: [
      column("rank", "Rank", () => 0, value => value, false),
      column("model", "Model", row => row.configuration.model.displayName, value => value),
      column("quantization", "Quant", row => row.configuration.model.quantization, value => value),
      column("size", "Artifact size", row => row.configuration.model.artifactRepositorySizeBytes, value => formatBytes(value), true),
      column("memory", "Max peak", row => row.shipMaximumMemory, value => formatMemory(value), true),
      column("runtime", "Runtime", row => row.configuration.runtime.name, (value, row) => `${escapeHtml(value)} ${escapeHtml(row.configuration.runtime.version)}`),
      column("device", "Tested device", row => row.configuration.device.machineIdentifier, value => escapeHtml(value)),
      column("license", "License", row => row.configuration.model.licenseIdentifier, value => escapeHtml(value)),
      column("details", "Evidence", () => 0, () => "", false),
    ],
  },
};

function column(key, label, accessor, formatter, sortable = true, primary = false) {
  return { key, label, accessor, formatter, sortable, primary };
}

const elements = {
  head: document.querySelector("#ranking-head"),
  body: document.querySelector("#ranking-body"),
  rowCount: document.querySelector("#row-count"),
  empty: document.querySelector("#empty-state"),
  loadError: document.querySelector("#load-error"),
  search: document.querySelector("#model-search"),
  device: document.querySelector("#device-filter"),
  runtime: document.querySelector("#runtime-filter"),
  contextLabel: document.querySelector("#context-label"),
  contextDescription: document.querySelector("#context-description"),
  dialog: document.querySelector("#detail-dialog"),
  dialogContent: document.querySelector("#dialog-content"),
};

async function loadEvidence() {
  try {
    const evidenceResponse = await fetch(DATA_URL, { cache: "no-store" });
    if (!evidenceResponse.ok) throw new Error(`Evidence request failed: ${evidenceResponse.status}`);
    const data = await evidenceResponse.json();
    if (!Array.isArray(data.results) || data.results.length === 0) throw new Error("Evidence is empty");
    state.data = data;
    populateFilters(data.results);
    renderReleaseSummary(data);
    renderBoard();
  } catch (error) {
    console.error(error);
    elements.loadError.hidden = false;
    elements.rowCount.textContent = "Evidence unavailable";
  }
}

function populateFilters(rows) {
  const devices = uniqueBy(rows.map(row => row.configuration.device), item => item.machineIdentifier);
  const runtimes = uniqueBy(rows.map(row => row.configuration.runtime), item => `${item.name}@${item.version}`);
  devices.forEach(device => elements.device.add(new Option(device.displayName, device.machineIdentifier)));
  runtimes.forEach(runtime => elements.runtime.add(new Option(`${runtime.name} ${runtime.version}`, `${runtime.name}@${runtime.version}`)));
}

function uniqueBy(items, key) {
  return [...new Map(items.map(item => [key(item), item])).values()];
}

function renderReleaseSummary(data) {
  const eligibleRows = data.results.filter(row => row.pilotEligibility.eligible);
  const configurations = new Set(eligibleRows.map(row => row.configuration.model.artifactID));
  const devices = uniqueBy(eligibleRows.map(row => row.configuration.device), item => item.machineIdentifier);
  document.querySelector("#summary-configurations").textContent = String(configurations.size);
  document.querySelector("#summary-results").textContent = String(data.eligibleResultCount ?? eligibleRows.length);
  document.querySelector("#summary-device").textContent = devices.map(device => device.displayName).join(", ");
}

function workloadRows(rows, workload) {
  return rows.filter(row => row.workload.id === workload && row.pilotEligibility.eligible);
}

function shipRows(rows) {
  const grouped = new Map();
  rows.filter(row => row.pilotEligibility.eligible).forEach(row => {
    const key = row.configuration.model.artifactID;
    const current = grouped.get(key) ?? { ...row, shipRows: [], shipMaximumMemory: 0 };
    current.shipRows.push(row);
    current.shipMaximumMemory = Math.max(current.shipMaximumMemory, row.summary.medianPeakMemoryMegabytes ?? 0);
    grouped.set(key, current);
  });
  return [...grouped.values()];
}

function renderBoard() {
  if (!state.data) return;
  const config = modeConfig[state.mode];
  let rows = state.mode === "ship" ? shipRows(state.data.results) : workloadRows(state.data.results, config.workload);
  rows = filterRows(rows);
  rows = sortRows(rows, config);
  elements.contextLabel.textContent = config.label;
  elements.contextDescription.textContent = config.description;
  elements.rowCount.textContent = `${rows.length} tested configuration${rows.length === 1 ? "" : "s"}`;
  elements.empty.hidden = rows.length !== 0;
  renderHead(config.columns);
  renderRows(rows, config.columns);
}

function filterRows(rows) {
  const query = state.query.trim().toLowerCase();
  return rows.filter(row => {
    const model = row.configuration.model;
    const runtime = row.configuration.runtime;
    const device = row.configuration.device;
    const searchable = `${model.displayName} ${model.artifactID} ${model.quantization} ${runtime.name}`.toLowerCase();
    const runtimeKey = `${runtime.name}@${runtime.version}`;
    return (!query || searchable.includes(query))
      && (state.device === "all" || device.machineIdentifier === state.device)
      && (state.runtime === "all" || runtimeKey === state.runtime);
  });
}

function sortRows(rows, config) {
  const selected = config.columns.find(item => item.key === state.sortKey) ?? config.columns[1];
  const direction = state.sortDirection === "asc" ? 1 : -1;
  return [...rows].sort((left, right) => compare(selected.accessor(left), selected.accessor(right)) * direction);
}

function compare(left, right) {
  if (left == null && right == null) return 0;
  if (left == null) return 1;
  if (right == null) return -1;
  if (typeof left === "number" && typeof right === "number") return left - right;
  return String(left).localeCompare(String(right), undefined, { numeric: true, sensitivity: "base" });
}

function renderHead(columns) {
  elements.head.innerHTML = `<tr>${columns.map(item => {
    if (!item.sortable) return `<th scope="col">${escapeHtml(item.label)}</th>`;
    const active = state.sortKey === item.key;
    const ariaSort = active ? (state.sortDirection === "asc" ? "ascending" : "descending") : "none";
    const arrow = state.sortDirection === "asc" ? "↑" : "↓";
    return `<th scope="col" aria-sort="${ariaSort}"><button class="sort-control${active ? " is-active" : ""}" data-sort="${item.key}" data-arrow="${arrow}">${escapeHtml(item.label)}</button></th>`;
  }).join("")}</tr>`;
  elements.head.querySelectorAll("[data-sort]").forEach(button => button.addEventListener("click", () => changeSort(button.dataset.sort)));
}

function renderRows(rows, columns) {
  elements.body.innerHTML = rows.map((row, index) => `<tr>${columns.map(item => renderCell(item, row, index)).join("")}</tr>`).join("");
  elements.body.querySelectorAll("[data-result]").forEach(button => button.addEventListener("click", () => openDetails(button.dataset.result)));
}

function renderCell(columnConfig, row, index) {
  if (columnConfig.key === "rank") return `<td class="rank-cell">${index + 1}</td>`;
  if (columnConfig.key === "model") {
    const model = row.configuration.model;
    return `<td class="model-cell"><span class="model-name">${escapeHtml(model.displayName)}</span><span class="model-meta">${escapeHtml(model.parameterSizeClass)} · ${escapeHtml(model.modelFormat)}</span></td>`;
  }
  if (columnConfig.key === "details") return `<td><button class="details-button" type="button" data-result="${escapeHtml(row.resultID)}">Evidence</button></td>`;
  const value = columnConfig.accessor(row);
  const formatted = columnConfig.formatter(value, row);
  return `<td class="metric-value${columnConfig.primary ? " primary-value" : ""}">${formatted}</td>`;
}

function changeSort(key) {
  if (state.sortKey === key) state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
  else {
    state.sortKey = key;
    state.sortDirection = defaultDirection(key);
  }
  renderBoard();
}

function defaultDirection(key) {
  return ["decode", "prefill"].includes(key) ? "desc" : "asc";
}

function openDetails(resultID) {
  const baseRows = state.mode === "ship" ? shipRows(state.data.results) : state.data.results;
  const row = baseRows.find(item => item.resultID === resultID);
  if (!row) return;
  const model = row.configuration.model;
  const runtime = row.configuration.runtime;
  const device = row.configuration.device;
  const workload = state.mode === "ship" ? "Power + Ship profile" : row.workload.id;
  const rawLinks = state.mode === "ship" ? row.shipRows.map(item => rawLink(item)).join("") : rawLink(row);
  elements.dialogContent.innerHTML = `
    <p class="dialog-kicker">Exact tested configuration</p>
    <h2 class="dialog-title">${escapeHtml(model.displayName)} · ${escapeHtml(model.quantization)}</h2>
    <div class="detail-grid">
      ${detailItem("Artifact", `${model.artifactID}@${model.artifactRevision}`)}
      ${detailItem("Workload", workload)}
      ${detailItem("Runtime", `${runtime.name} ${runtime.version} · ${runtime.backend}`)}
      ${detailItem("Device", `${device.displayName} · iOS ${device.systemVersion} (${device.systemBuild})`)}
      ${detailItem("Model format", model.modelFormat)}
      ${detailItem("Repository size", formatBytes(model.artifactRepositorySizeBytes))}
      ${detailItem("License metadata", model.licenseIdentifier)}
      ${detailItem("App identity", `${device.appVersion} build ${device.appBuild}`)}
    </div>
    <div class="dialog-links">
      <a class="button button-primary" href="${escapeAttribute(model.sourceURL)}" target="_blank" rel="noreferrer">Model source</a>
      <a class="button button-secondary" href="${escapeAttribute(model.licenseSourceURL)}" target="_blank" rel="noreferrer">License source</a>
      ${rawLinks}
    </div>`;
  elements.dialog.showModal();
}

function rawLink(row) {
  return `<a class="button button-secondary" href="results/suite-b-pilot-v0.1/raw/${escapeAttribute(row.source.path)}">Raw ${escapeHtml(shortWorkload(row.workload.id))}</a>`;
}

function detailItem(label, value) {
  return `<div class="detail-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function formatMs(value) {
  return value == null ? "—" : `${value.toFixed(2)} ms`;
}

function formatRate(value) {
  return value == null ? "—" : `${value.toFixed(2)} tok/s`;
}

function formatMemory(value) {
  return value == null ? "—" : `${Math.round(value)} MiB`;
}

function formatBytes(value) {
  return value == null ? "—" : `${(value / 1_000_000_000).toFixed(2)} GB`;
}

function formatPercent(value) {
  if (value == null) return "—";
  return `${value > 0 ? "+" : ""}${value.toFixed(1)}%`;
}

function thermalMarkup(value) {
  const safe = escapeHtml(value ?? "unknown");
  return `<span class="thermal ${safe.toLowerCase()}">${safe}</span>`;
}

function thermalOrder(value) {
  return ({ nominal: 0, fair: 1, serious: 2, critical: 3 })[value] ?? 4;
}

function profileLabel(row) {
  return `${row.configuration.model.displayName} ${row.configuration.model.quantization}`;
}

function shortWorkload(value) {
  if (value.includes("b-ux")) return "B-UX-001";
  if (value.includes("b-pipe")) return "B-PIPE-001";
  return value;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

document.querySelectorAll(".mode-tab").forEach(button => button.addEventListener("click", () => {
  document.querySelectorAll(".mode-tab").forEach(tab => {
    const active = tab === button;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
  });
  state.mode = button.dataset.mode;
  state.sortKey = modeConfig[state.mode].defaultSort;
  state.sortDirection = modeConfig[state.mode].defaultDirection;
  renderBoard();
}));

elements.search.addEventListener("input", event => { state.query = event.target.value; renderBoard(); });
elements.device.addEventListener("change", event => { state.device = event.target.value; renderBoard(); });
elements.runtime.addEventListener("change", event => { state.runtime = event.target.value; renderBoard(); });
document.querySelector(".dialog-close").addEventListener("click", () => elements.dialog.close());
elements.dialog.addEventListener("click", event => {
  if (event.target === elements.dialog) elements.dialog.close();
});

loadEvidence();
