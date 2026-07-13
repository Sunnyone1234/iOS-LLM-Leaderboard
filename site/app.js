const POWER_DATA_URL = "results/suite-b-power-1.0/normalized-results.json";
const SHIP_DATA_URL = "results/ship-1.0/deployment-profiles.json";

const state = {
  power: null,
  ship: null,
  mode: "ux",
  sortKey: "response",
  sortDirection: "asc",
  query: "",
  device: "all",
  runtime: "all",
};

const modeConfig = {
  ux: {
    kind: "power",
    workload: "b-ux-001-short-interaction",
    label: "First-renderable proxy TTFT",
    description: "Adapter boundary, not screen-render latency. Lower is better.",
    defaultSort: "response",
    defaultDirection: "asc",
    columns: [
      column("rank", "Rank", () => 0, value => value, false),
      column("model", "Model", row => row.configuration.model.displayName, value => value),
      column("quantization", "Quant", row => row.configuration.model.quantization, value => value),
      column("response", "Proxy TTFT", row => row.summary.medianFirstRenderableProxyTTFTMilliseconds, value => formatMs(value), true, true),
      column("pipeline", "Pipeline TTFT", row => row.summary.medianPipelineTTFTMilliseconds, value => formatMs(value), true),
      column("prefill", "Prefill", row => row.summary.medianPrefillTokensPerSecond, value => formatRate(value), true),
      column("decode", "Decode", row => row.summary.medianDecodeTokensPerSecond, value => formatRate(value), true),
      column("memory", "Peak memory", row => row.summary.medianPeakMemoryMiB, value => formatMemory(value), true),
      column("thermal", "Thermal", row => thermalOrder(row.summary.finalThermalState), (_, row) => thermalMarkup(row.summary.finalThermalState), true),
      column("details", "Evidence", () => 0, () => "", false),
    ],
  },
  pipe: {
    kind: "power",
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
      column("memory", "Peak memory", row => row.summary.medianPeakMemoryMiB, value => formatMemory(value), true),
      column("degradation", "Decode change", row => row.summary.decodeFirstToLastPercentChange, value => formatPercent(value), true),
      column("thermal", "Thermal", row => thermalOrder(row.summary.finalThermalState), (_, row) => thermalMarkup(row.summary.finalThermalState), true),
      column("details", "Evidence", () => 0, () => "", false),
    ],
  },
  ship: {
    kind: "ship",
    label: "Deployment profiles",
    description: "Evidence-backed guidance for the exact tested configurations. No Ship score.",
    defaultSort: "artifact",
    defaultDirection: "asc",
    columns: [
      column("model", "Model", row => row.configuration.model.displayName, value => escapeHtml(value)),
      column("quantization", "Quant", row => row.configuration.model.quantization, value => escapeHtml(value)),
      column("artifact", "Artifact size", row => row.observedConstraints.artifactRepositorySizeBytes, value => formatBytes(value), true, true),
      column("memory", "Observed median peak", row => row.observedConstraints.maximumReportedMedianPeakMemoryMiB, value => formatMemory(value), true),
      column("device", "Tested device", row => row.configuration.device.displayName, value => escapeHtml(value), true),
      column("runtime", "Runtime", row => `${row.configuration.runtime.name} ${row.configuration.runtime.version}`, value => escapeHtml(value), true),
      column("verified", "Verified", row => claimCount(row, "verified"), value => `${value} claims`, true),
      column("unknown", "Unknown", row => claimCount(row, "unknown"), value => `${value} claims`, true),
      column("details", "Profile", () => 0, () => "", false),
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
  releaseLabel: document.querySelector("#release-label"),
  footerStatus: document.querySelector("#footer-status"),
  footerChecksums: document.querySelector("#footer-checksums"),
  footerTable: document.querySelector("#footer-table"),
};

async function loadEvidence() {
  try {
    const [powerResponse, shipResponse] = await Promise.all([
      fetch(POWER_DATA_URL, { cache: "no-store" }),
      fetch(SHIP_DATA_URL, { cache: "no-store" }),
    ]);
    if (!powerResponse.ok) throw new Error(`Power evidence request failed: ${powerResponse.status}`);
    if (!shipResponse.ok) throw new Error(`Ship evidence request failed: ${shipResponse.status}`);
    const [power, ship] = await Promise.all([powerResponse.json(), shipResponse.json()]);
    if (!Array.isArray(power.results) || power.results.length === 0) throw new Error("Power evidence is empty");
    if (!Array.isArray(ship.profiles) || ship.profiles.length === 0) throw new Error("Ship profiles are empty");
    state.power = power;
    state.ship = ship;
    populateFilters([...power.results, ...ship.profiles]);
    renderReleaseSummary(power);
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
  const eligibleRows = data.results.filter(row => row.rankingEligibility.candidateEligible);
  const configurations = new Set(eligibleRows.map(row => row.configuration.model.artifactID));
  const devices = uniqueBy(data.results.map(row => row.configuration.device), item => item.machineIdentifier);
  document.querySelector("#summary-configurations").textContent = String(configurations.size);
  document.querySelector("#summary-results").textContent = String(data.resultCount);
  document.querySelector("#summary-device").textContent = devices.map(device => device.displayName).join(", ");
  const active = data.publication.officialResultEligible
    && data.publication.publicationAuthorized
    && data.publication.rankingAuthorized
    && data.activeRankedResultCount > 0;
  elements.releaseLabel.textContent = active ? "Power 1.0" : "Power 1.0 final candidate";
  elements.footerStatus.textContent = active
    ? "Power 1.0 · Official rankings within each workload"
    : "Power 1.0 final review candidate · Official ranking not yet active";
}

function workloadRows(rows, workload) {
  return rows.filter(row => row.workload.id === workload && row.rankingEligibility.candidateEligible);
}

function renderBoard() {
  if (!state.power || !state.ship) return;
  const config = modeConfig[state.mode];
  let rows = config.kind === "ship"
    ? state.ship.profiles
    : workloadRows(state.power.results, config.workload);
  rows = filterRows(rows);
  rows = sortRows(rows, config);
  elements.contextLabel.textContent = config.label;
  elements.contextDescription.textContent = config.description;
  elements.rowCount.textContent = `${rows.length} tested configuration${rows.length === 1 ? "" : "s"}`;
  elements.footerStatus.textContent = config.kind === "ship"
    ? "Ship 1.0 RC1 · Evidence profiles · No deployment score"
    : "Power 1.0 · Official rankings within each workload";
  elements.footerChecksums.href = config.kind === "ship"
    ? "results/ship-1.0/SHA256SUMS"
    : "results/suite-b-power-1.0/SHA256SUMS";
  elements.footerTable.href = config.kind === "ship"
    ? "results/ship-1.0/PROFILES.md"
    : "results/suite-b-power-1.0/LEADERBOARD.md";
  elements.footerTable.textContent = config.kind === "ship" ? "Profile table" : "Evidence table";
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
  if (columnConfig.key === "details") {
    const identity = row.resultID ?? row.profileID;
    return `<td><button class="details-button" type="button" data-result="${escapeHtml(identity)}">${row.profileID ? "Profile" : "Evidence"}</button></td>`;
  }
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
  const row = state.power.results.find(item => item.resultID === resultID);
  if (!row) return openShipDetails(resultID);
  const model = row.configuration.model;
  const runtime = row.configuration.runtime;
  const device = row.configuration.device;
  const workload = row.workload.id;
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
      ${detailItem("Evidence level", row.evidence.level)}
      ${detailItem("Source release", row.sourceEvidenceRelease.version)}
    </div>
    <div class="dialog-links">
      <a class="button button-primary" href="${escapeAttribute(model.sourceURL)}" target="_blank" rel="noreferrer">Model source</a>
      <a class="button button-secondary" href="${escapeAttribute(model.licenseSourceURL)}" target="_blank" rel="noreferrer">License source</a>
      ${rawLink(row)}
    </div>`;
  elements.dialog.showModal();
}

function openShipDetails(profileID) {
  const profile = state.ship.profiles.find(item => item.profileID === profileID);
  if (!profile) return;
  const model = profile.configuration.model;
  const runtime = profile.configuration.runtime;
  const device = profile.configuration.device;
  const claims = profile.deploymentClaims.map(item => `
    <div class="claim-item">
      <span class="claim-status ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span>
      <div><strong>${escapeHtml(item.label)}</strong><p>${escapeHtml(item.statement)}</p></div>
    </div>`).join("");
  elements.dialogContent.innerHTML = `
    <p class="dialog-kicker">Exact tested deployment profile · No Ship score</p>
    <h2 class="dialog-title">${escapeHtml(model.displayName)} · ${escapeHtml(model.quantization)}</h2>
    <div class="detail-grid">
      ${detailItem("Artifact", `${model.artifactID}@${model.artifactRevision}`)}
      ${detailItem("Runtime", `${runtime.name} ${runtime.version} · ${runtime.backend}`)}
      ${detailItem("Tested device", `${device.displayName} · iOS ${device.systemVersion} (${device.systemBuild})`)}
      ${detailItem("Observed median peak", formatMemory(profile.observedConstraints.maximumReportedMedianPeakMemoryMiB))}
      ${detailItem("Artifact size", formatBytes(model.artifactRepositorySizeBytes))}
      ${detailItem("Minimum supported device", "Unknown")}
      ${detailItem("Evidence", `${profile.evidence.level} · ${profile.evidence.sourceResultCount} Power results`)}
      ${detailItem("License metadata", `${model.licenseIdentifier} · developer review required`)}
    </div>
    <h3 class="claim-heading">Deployment evidence</h3>
    <div class="claim-list">${claims}</div>
    <div class="dialog-links">
      <a class="button button-primary" href="${escapeAttribute(profile.integrationRecipe.path)}">Swift recipe</a>
      <a class="button button-secondary" href="results/ship-1.0/deployment-profiles.json">Profile data</a>
      <a class="button button-secondary" href="docs/ship-deployment-profiles.md">Evidence method</a>
      <a class="button button-secondary" href="${escapeAttribute(model.licenseSourceURL)}" target="_blank" rel="noreferrer">License source</a>
    </div>`;
  elements.dialog.showModal();
}

function claimCount(row, status) {
  return row.deploymentClaims.filter(item => item.status === status).length;
}

function rawLink(row) {
  return `<a class="button button-secondary" href="${escapeAttribute(row.source.rawPath)}">Raw ${escapeHtml(shortWorkload(row.workload.id))}</a>`;
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
