const POWER_DATA_URL = "results/suite-b-power-community/normalized-results.json";
const OFFICIAL_POWER_DATA_URL = "results/suite-b-power-1.0/normalized-results.json";
const SHIP_DATA_URL = "results/ship-1.0/deployment-profiles.json";
const MODEL_CATALOG_URL = "models/power-test-catalog.json";
const CONTRIBUTOR_GUIDE_URL = "https://github.com/YizeSun/iOS-LLM-Leaderboard/blob/main/contributor-kit/power-1.0-quickstart.md";
const MODEL_TEST_GUIDE_URL = "https://github.com/YizeSun/iOS-LLM-Leaderboard/blob/main/contributor-kit/test-recommended-model.md";

const state = {
  power: null,
  ship: null,
  catalog: null,
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
      column("contributors", "Contributors", row => row.community.contributorCount, (_, row) => communityCount(row), true),
      column("variation", "Variation", row => row.community.primaryMetricVariation.value, (_, row) => communityVariation(row), true),
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
      column("contributors", "Contributors", row => row.community.contributorCount, (_, row) => communityCount(row), true),
      column("variation", "Variation", row => row.community.primaryMetricVariation.value, (_, row) => communityVariation(row), true),
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
  coverage: {
    kind: "coverage",
    label: "Community evidence coverage",
    description: "Each exact workload cell needs two independent metric-eligible GitHub contributors to display as Reproduced.",
    defaultSort: "gaps",
    defaultDirection: "desc",
    columns: [
      column("model", "Model", row => row.configuration.model.displayName, value => value),
      column("quantization", "Quant", row => row.configuration.model.quantization, value => escapeHtml(value)),
      column("device", "Device", row => row.configuration.device.displayName, value => escapeHtml(value), true),
      column("coverage-ux", "Responsiveness", row => row.coverage.ux?.eligibleContributorCount ?? -1, (_, row) => coverageCell(row.coverage.ux), true),
      column("coverage-pipe", "Sustained generation", row => row.coverage.pipe?.eligibleContributorCount ?? -1, (_, row) => coverageCell(row.coverage.pipe), true),
      column("gaps", "Open contributor slots", row => row.openContributorSlots, value => String(value), true, true),
      column("contribute", "Action", () => 0, () => `<a class="details-button" href="${CONTRIBUTOR_GUIDE_URL}" target="_blank" rel="noreferrer">Contribute result</a>`, false),
    ],
  },
  catalog: {
    kind: "catalog",
    label: "Open model catalog",
    description: "App-ready candidates and requested open models awaiting compatible Apple-device artifacts. These are not rankings.",
    defaultSort: "priority",
    defaultDirection: "asc",
    columns: [
      column("priority", "Priority", row => row.catalogEntryType === "app-ready" ? row.recommendedPriority : null, value => value == null ? "—" : `#${value}`, true, true),
      column("model", "Model", row => row.configuration.model.displayName, value => value),
      column("quantization", "Quant", row => row.configuration.model.quantization, value => value == null ? "—" : escapeHtml(value)),
      column("size", "Download", row => row.configuration.model.artifactRepositorySizeBytes, value => value == null ? "—" : formatBytes(value), true),
      column("license", "License", row => row.configuration.model.licenseIdentifier, value => escapeHtml(value), true),
      column("support", "App status", row => row.runtimeRegistryStatus, (_, row) => catalogSupportMarkup(row), true),
      column("status", "Evidence", row => row.physicalDeviceEvidenceStatus, (_, row) => catalogEvidenceMarkup(row), true),
      column("reason", "Why listed", row => row.recommendationReason ?? row.appEligibilityReason, value => escapeHtml(value), false),
      column("catalog-action", "Action", () => 0, (_, row) => catalogActionMarkup(row), false),
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
    const [powerResponse, shipResponse, catalogResponse] = await Promise.all([
      fetch(POWER_DATA_URL, { cache: "no-store" }),
      fetch(SHIP_DATA_URL, { cache: "no-store" }),
      fetch(MODEL_CATALOG_URL, { cache: "no-store" }),
    ]);
    if (!powerResponse.ok) throw new Error(`Power evidence request failed: ${powerResponse.status}`);
    if (!shipResponse.ok) throw new Error(`Ship evidence request failed: ${shipResponse.status}`);
    if (!catalogResponse.ok) throw new Error(`Model catalog request failed: ${catalogResponse.status}`);
    const [power, ship, catalog] = await Promise.all([powerResponse.json(), shipResponse.json(), catalogResponse.json()]);
    if (!Array.isArray(power.results) || power.results.length === 0) throw new Error("Power evidence is empty");
    if (!Array.isArray(ship.profiles) || ship.profiles.length === 0) throw new Error("Ship profiles are empty");
    if (!Array.isArray(catalog.models) || catalog.models.length === 0) throw new Error("Model test catalog is empty");
    if (!Array.isArray(catalog.openModelWatchlist)) throw new Error("Open model watchlist is unavailable");
    state.power = power;
    state.ship = ship;
    state.catalog = catalog;
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
  elements.releaseLabel.textContent = "Power 1.0 + Community";
  elements.releaseLabel.title = `Live community view derived from ${OFFICIAL_POWER_DATA_URL}`;
  elements.footerStatus.textContent = "Power 1.0 reference · Live merged community evidence";
}

function workloadRows(rows, workload) {
  return rows.filter(row => row.workload.id === workload && row.rankingEligibility.candidateEligible);
}

function buildCoverageRows(rows) {
  const profiles = new Map();
  rows.forEach(row => {
    const identity = row.comparisonIdentity;
    const key = JSON.stringify({
      sourceEvidenceRelease: identity.sourceEvidenceRelease,
      runner: identity.runner,
      model: identity.model,
      runtime: identity.runtime,
      device: identity.device,
    });
    if (!profiles.has(key)) {
      profiles.set(key, {
        configuration: row.configuration,
        coverage: { ux: null, pipe: null },
        openContributorSlots: 4,
      });
    }
    const profile = profiles.get(key);
    const slot = row.workload.id === "b-ux-001-short-interaction" ? "ux" : "pipe";
    profile.coverage[slot] = {
      comparisonID: row.comparisonID,
      eligibleContributorCount: row.community.eligibleContributorCount,
      contributorCount: row.community.contributorCount,
      runCount: row.community.runCount,
      status: row.community.status,
    };
  });
  return [...profiles.values()].map(profile => {
    profile.openContributorSlots = [profile.coverage.ux, profile.coverage.pipe]
      .reduce((total, evidence) => total + Math.max(0, 2 - (evidence?.eligibleContributorCount ?? 0)), 0);
    return profile;
  });
}

function buildCatalogRows(catalog) {
  const appReady = catalog.models.map(model => ({
    ...model,
    catalogEntryType: "app-ready",
    configuration: { model, runtime: catalog.runtime },
  }));
  const watchlist = catalog.openModelWatchlist.map(model => ({
    ...model,
    catalogEntryType: "open-model-watchlist",
    runtimeRegistryStatus: "unsupported-in-locked-runtime",
    physicalDeviceEvidenceStatus: "not-app-testable",
    configuration: {
      model: {
        ...model,
        artifactID: model.officialModelID,
        quantization: null,
        artifactRepositorySizeBytes: null,
      },
      runtime: catalog.runtime,
    },
  }));
  return [...appReady, ...watchlist];
}

function catalogSupportMarkup(row) {
  return row.catalogEntryType === "app-ready"
    ? '<span class="catalog-support">Ready in App</span>'
    : '<span class="catalog-watchlist">Not App-ready</span>';
}

function catalogEvidenceMarkup(row) {
  return row.catalogEntryType === "app-ready"
    ? '<span class="catalog-status">Untested</span>'
    : '<span class="catalog-watchlist">Watchlist</span>';
}

function catalogActionMarkup(row) {
  const source = `<a class="catalog-source" href="${escapeAttribute(row.configuration.model.sourceURL)}" target="_blank" rel="noreferrer">Source</a>`;
  if (row.catalogEntryType !== "app-ready") {
    return `<span class="catalog-unavailable">Await compatible artifact</span>${source}`;
  }
  return `<a class="details-button" href="${MODEL_TEST_GUIDE_URL}" target="_blank" rel="noreferrer">Test this model</a>${source}`;
}

function renderBoard() {
  if (!state.power || !state.ship || !state.catalog) return;
  const config = modeConfig[state.mode];
  let rows;
  if (config.kind === "ship") rows = state.ship.profiles;
  else if (config.kind === "coverage") rows = buildCoverageRows(state.power.results);
  else if (config.kind === "catalog") rows = buildCatalogRows(state.catalog);
  else rows = workloadRows(state.power.results, config.workload);
  rows = filterRows(rows, config);
  rows = sortRows(rows, config);
  elements.device.disabled = config.kind === "catalog";
  elements.runtime.disabled = config.kind === "catalog";
  elements.contextLabel.textContent = config.label;
  elements.contextDescription.textContent = config.description;
  const openSlots = rows.reduce((total, row) => total + (row.openContributorSlots ?? 0), 0);
  elements.rowCount.textContent = config.kind === "coverage"
    ? `${rows.length} tested profile${rows.length === 1 ? "" : "s"} · ${openSlots} open contributor slot${openSlots === 1 ? "" : "s"}`
    : config.kind === "catalog"
      ? `${rows.filter(row => row.catalogEntryType === "app-ready").length} App-ready · ${rows.filter(row => row.catalogEntryType === "open-model-watchlist").length} watchlist`
      : `${rows.length} tested configuration${rows.length === 1 ? "" : "s"}`;
  elements.footerStatus.textContent = config.kind === "ship"
    ? "Ship 1.0 · Published evidence profiles · No deployment score"
    : config.kind === "coverage"
      ? "Coverage derived from live Power evidence · No placeholder devices"
      : config.kind === "catalog"
        ? "Open model catalog · App-ready and watchlist entries are explicitly separated · No performance claims"
      : "Power 1.0 reference · Live merged community evidence";
  elements.footerChecksums.href = config.kind === "ship"
    ? "results/ship-1.0/SHA256SUMS"
    : config.kind === "catalog"
      ? MODEL_CATALOG_URL
    : "results/suite-b-power-1.0/SHA256SUMS";
  elements.footerTable.href = config.kind === "ship"
    ? "results/ship-1.0/PROFILES.md"
    : config.kind === "catalog"
      ? MODEL_TEST_GUIDE_URL
    : config.kind === "coverage"
      ? "results/suite-b-power-community/COVERAGE.md"
      : "results/suite-b-power-community/LEADERBOARD.md";
  elements.footerChecksums.textContent = config.kind === "catalog" ? "Catalog JSON" : "Checksums";
  elements.footerTable.textContent = config.kind === "ship"
    ? "Profile table"
    : config.kind === "catalog" ? "Testing guide"
      : config.kind === "coverage" ? "Coverage report" : "Evidence table";
  elements.empty.hidden = rows.length !== 0;
  renderHead(config.columns);
  renderRows(rows, config.columns);
}

function filterRows(rows, config) {
  const query = state.query.trim().toLowerCase();
  return rows.filter(row => {
    const model = row.configuration.model;
    const runtime = row.configuration.runtime;
    const device = row.configuration.device;
    const searchable = `${model.displayName} ${model.artifactID} ${model.quantization} ${runtime.name}`.toLowerCase();
    const runtimeKey = `${runtime.name}@${runtime.version}`;
    return (!query || searchable.includes(query))
      && (config.kind === "catalog" || state.device === "all" || device.machineIdentifier === state.device)
      && (config.kind === "catalog" || state.runtime === "all" || runtimeKey === state.runtime);
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
    const metadata = row.catalogEntryType === "open-model-watchlist"
      ? `${model.licenseIdentifier} · Open model watchlist`
      : `${model.parameterSizeClass} · ${model.modelFormat}`;
    return `<td class="model-cell"><span class="model-name">${escapeHtml(model.displayName)}</span><span class="model-meta">${escapeHtml(metadata)}</span></td>`;
  }
  if (columnConfig.key === "details") {
    const identity = row.comparisonID ?? row.profileID;
    return `<td><button class="details-button" type="button" data-result="${escapeHtml(identity)}">${row.profileID ? "Profile" : "Evidence"}</button></td>`;
  }
  if (columnConfig.key === "reason") {
    return `<td class="catalog-reason">${columnConfig.formatter(columnConfig.accessor(row), row)}</td>`;
  }
  if (columnConfig.key === "catalog-action") {
    return `<td class="catalog-actions">${columnConfig.formatter(0, row)}</td>`;
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
  const row = state.power.results.find(item => item.comparisonID === resultID);
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
      ${detailItem("Community evidence", `${eligibleContributorLabel(row)} · ${row.community.runCount} run${row.community.runCount === 1 ? "" : "s"}`)}
      ${detailItem("Reproduction", row.community.status === "reproduced" ? "Reproduced" : "Single contributor")}
      ${detailItem("Primary variation", variationText(row))}
      ${detailItem("Source release", row.sourceEvidenceRelease.version)}
    </div>
    <div class="dialog-links">
      <a class="button button-primary" href="${escapeAttribute(model.sourceURL)}" target="_blank" rel="noreferrer">Model source</a>
      <a class="button button-secondary" href="${escapeAttribute(model.licenseSourceURL)}" target="_blank" rel="noreferrer">License source</a>
      ${rawLinks(row)}
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

function rawLinks(row) {
  return row.evidence.map(item => `<a class="button button-secondary" href="${escapeAttribute(item.rawPath)}">${escapeHtml(item.contributor)} · ${escapeHtml(shortWorkload(row.workload.id))}</a>`).join("");
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

function communityCount(row) {
  const count = row.community.eligibleContributorCount;
  const label = `${count} contributor${count === 1 ? "" : "s"}`;
  return row.community.status === "reproduced"
    ? `<span class="evidence-status reproduced">${label}</span>`
    : `<span class="evidence-status">${label}</span>`;
}

function eligibleContributorLabel(row) {
  const eligible = row.community.eligibleContributorCount;
  const total = row.community.contributorCount;
  const base = `${eligible} metric-eligible contributor${eligible === 1 ? "" : "s"}`;
  return eligible === total ? base : `${base} · ${total} total`;
}

function communityVariation(row) {
  const variation = row.community.primaryMetricVariation;
  if (variation.value == null) return "—";
  const value = `${variation.value.toFixed(2)}%`;
  return variation.high
    ? `<span class="variation-warning">${value} · High</span>`
    : value;
}

function variationText(row) {
  const variation = row.community.primaryMetricVariation;
  if (variation.value == null) return "Not available with one contributor";
  return `${variation.value.toFixed(2)}%${variation.high ? " · High variation" : ""}`;
}

function coverageCell(evidence) {
  if (!evidence) return '<span class="coverage-status missing">No evidence</span>';
  const eligible = evidence.eligibleContributorCount;
  const remaining = Math.max(0, 2 - eligible);
  const label = remaining === 0 ? "Reproduced" : `${eligible} eligible · needs ${remaining}`;
  const className = remaining === 0 ? "reproduced" : "needed";
  return `<button class="coverage-status ${className}" type="button" data-result="${escapeAttribute(evidence.comparisonID)}">${escapeHtml(label)}</button>`;
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
  const tabStrip = button.parentElement;
  if (tabStrip && tabStrip.scrollWidth > tabStrip.clientWidth) {
    tabStrip.scrollTo({
      left: button.offsetLeft - (tabStrip.clientWidth - button.offsetWidth) / 2,
      behavior: "smooth",
    });
  }
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
