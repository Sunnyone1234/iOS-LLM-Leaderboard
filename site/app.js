const POWER_DATA_URL = "results/power/text-generation-performance/2.0.0/ranking.json";
const POWER_CURRENT_URL = "products/power/current.json";
const SHIP_DATA_URL = "results/ship-1.0/deployment-profiles.json";
const CONTRIBUTOR_GUIDE_URL = "https://github.com/YizeSun/iOS-LLM-Leaderboard/blob/main/contributor-kit/power.md";
const THEME_STORAGE_KEY = "ios-llm-leaderboard-theme";

const state = {
  power: null,
  ship: null,
  active: false,
  mode: "ux",
  sortKey: "value",
  sortDirection: "asc",
  query: "",
  device: "all",
  runtime: "all",
  size: "all",
};

const elements = {
  head: document.querySelector("#ranking-head"),
  body: document.querySelector("#ranking-body"),
  rowCount: document.querySelector("#row-count"),
  empty: document.querySelector("#empty-state"),
  loadError: document.querySelector("#load-error"),
  search: document.querySelector("#model-search"),
  device: document.querySelector("#device-filter"),
  runtime: document.querySelector("#runtime-filter"),
  size: document.querySelector("#size-filter"),
  theme: document.querySelector("#theme-select"),
  contextLabel: document.querySelector("#context-label"),
  contextDescription: document.querySelector("#context-description"),
  dialog: document.querySelector("#detail-dialog"),
  dialogContent: document.querySelector("#dialog-content"),
  releaseLabel: document.querySelector("#release-label"),
  footerStatus: document.querySelector("#footer-status"),
  footerChecksums: document.querySelector("#footer-checksums"),
  footerTable: document.querySelector("#footer-table"),
};

const powerModes = {
  ux: {
    viewID: "interactive-responsiveness",
    label: "First-renderable time",
    description: "Decoded renderable output at the certified adapter boundary. Lower is better; this is not screen-render latency.",
    direction: "asc",
    unit: "ms",
  },
  pipe: {
    viewID: "sustained-generation",
    label: "Sustained decode throughput",
    description: "Output token generation after the first token. Higher is better.",
    direction: "desc",
    unit: "tok/s",
  },
};

const COLUMN_HELP = Object.freeze({
  rank: "Position after sorting this exact Power comparison view.",
  model: "Exact model artifact and immutable source revision.",
  quantization: "Quantization recorded by the registered model artifact.",
  device: "Physical Apple device identity used by this evidence.",
  runtime: "Exact inference runtime version recorded by the result.",
  value: "Primary metric for the selected workload. The arrow shows ranking direction.",
  contributors: "Distinct GitHub contributors; one account counts once per exact cell.",
  state: "Accepted at one contributor, reproduced at two, contributor-weighted at three.",
  details: "Complete comparison identity and immutable source-result hashes.",
});

function applyTheme(theme, persist = false) {
  const selected = theme === "light" ? "light" : "dark";
  document.documentElement.dataset.theme = selected;
  elements.theme.value = selected;
  document.querySelector('meta[name="theme-color"]').setAttribute(
    "content",
    selected === "dark" ? "#131210" : "#ffffff",
  );
  if (persist) {
    try {
      localStorage.setItem(THEME_STORAGE_KEY, selected);
    } catch (_) {
      // Theme selection remains useful when persistence is unavailable.
    }
  }
}

async function loadEvidence() {
  try {
    const [powerResponse, shipResponse, currentResponse] = await Promise.all([
      fetch(POWER_DATA_URL, { cache: "no-store" }),
      fetch(SHIP_DATA_URL, { cache: "no-store" }),
      fetch(POWER_CURRENT_URL, { cache: "no-store" }),
    ]);
    if (!powerResponse.ok) {
      throw new Error(`Power evidence request failed: ${powerResponse.status}`);
    }
    if (!shipResponse.ok) {
      throw new Error(`Ship evidence request failed: ${shipResponse.status}`);
    }
    state.power = await powerResponse.json();
    state.ship = await shipResponse.json();
    state.active = currentResponse.ok;
    if (!Array.isArray(state.power.views)) {
      throw new Error("Power ranking views are unavailable");
    }
    if (!Array.isArray(state.ship.profiles)) {
      throw new Error("Ship profiles are unavailable");
    }
    populateFilters();
    renderSummary();
    renderBoard();
  } catch (error) {
    console.error(error);
    elements.loadError.hidden = false;
    elements.rowCount.textContent = "Evidence unavailable";
  }
}

function powerRows() {
  const mode = powerModes[state.mode] ?? powerModes.ux;
  return state.power.views.filter(row => row.viewID === mode.viewID);
}

function allFilterRows() {
  return [
    ...state.power.views.map(row => ({
      device: row.comparisonIdentity.machineIdentifier,
      runtime: runtimeLabel(row.comparisonIdentity.runtimeIdentity),
    })),
    ...state.ship.profiles.map(row => ({
      device: row.configuration.device.machineIdentifier,
      runtime: runtimeLabel(row.configuration.runtime),
    })),
  ];
}

function populateFilters() {
  const rows = allFilterRows();
  const devices = [...new Set(rows.map(row => row.device))].sort();
  const runtimes = [...new Set(rows.map(row => row.runtime))].sort();
  devices.forEach(value => elements.device.add(new Option(value, value)));
  runtimes.forEach(value => elements.runtime.add(new Option(value, value)));
}

function renderSummary() {
  const identities = state.power.views.map(row => row.comparisonIdentity);
  const configurations = new Set(
    identities.map(identity => identity.modelArtifactID),
  );
  const devices = [...new Set(
    identities.map(identity => identity.machineIdentifier),
  )];
  document.querySelector("#summary-configurations").textContent = String(
    configurations.size,
  );
  document.querySelector("#summary-results").textContent = String(
    state.power.acceptedContributionCount,
  );
  document.querySelector("#summary-device").textContent = devices.length
    ? devices.join(", ")
    : "Physical iPhone";
  elements.releaseLabel.textContent = state.active
    ? "Power 2"
    : "Power 2 · activation checkpoint";
  elements.footerStatus.textContent = state.active
    ? "Power 2 · Public intake open"
    : "Power 2 · Public intake remains fail-closed";
}

function renderBoard() {
  const tabs = document.querySelectorAll(".mode-tab");
  tabs.forEach(tab => {
    const selected = tab.dataset.mode === state.mode;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });

  if (state.mode === "ship") {
    renderShip();
    return;
  }
  renderPower();
}

function renderPower() {
  const mode = powerModes[state.mode];
  elements.contextLabel.textContent = mode.label;
  elements.contextDescription.textContent = mode.description;
  state.sortDirection = state.sortKey === "value"
    ? mode.direction
    : state.sortDirection;
  const rows = sortRows(filterPowerRows(powerRows()));
  elements.rowCount.textContent = `${rows.length} exact comparison cell${rows.length === 1 ? "" : "s"}`;
  elements.empty.hidden = rows.length !== 0;
  elements.empty.querySelector("strong").textContent = state.active
    ? "No accepted evidence in this view yet"
    : "Power 2 activation is not complete";
  elements.empty.querySelector("span").textContent = state.active
    ? "Run the Official App and contribute the first exact result."
    : "The exact Official build 3 physical-device checkpoint must pass before public intake opens.";
  elements.footerChecksums.href = POWER_DATA_URL;
  elements.footerChecksums.textContent = "Ranking JSON";
  elements.footerTable.href = CONTRIBUTOR_GUIDE_URL;
  elements.footerTable.textContent = "Contribution guide";

  const columns = [
    ["rank", "#"],
    ["model", "Model artifact"],
    ["quantization", "Quant"],
    ["device", "Device"],
    ["runtime", "Runtime"],
    ["value", mode.unit],
    ["contributors", "Contributors"],
    ["state", "Evidence state"],
    ["details", "Evidence"],
  ];
  renderHead(columns);
  elements.body.innerHTML = rows.map((row, index) => {
    const identity = row.comparisonIdentity;
    return `<tr>
      <td class="rank-cell">${index + 1}</td>
      <td class="model-cell"><span class="model-name">${escapeHtml(identity.modelArtifactID)}</span><span class="model-meta">${escapeHtml(identity.modelArtifactRevision.slice(0, 12))} · iOS ${escapeHtml(identity.osVersion)} (${escapeHtml(identity.osBuild)})</span></td>
      <td>${escapeHtml(identity.quantization)}</td>
      <td>${escapeHtml(identity.machineIdentifier)}</td>
      <td>${escapeHtml(runtimeLabel(identity.runtimeIdentity))}</td>
      <td class="metric-value primary-value">${formatMetric(row.value, mode.unit)}</td>
      <td class="metric-value">${row.contributorCount}</td>
      <td>${evidenceState(row.evidenceState)}</td>
      <td><button class="details-button" type="button" data-comparison="${escapeAttribute(row.comparisonID)}">Evidence</button></td>
    </tr>`;
  }).join("");
  elements.body.querySelectorAll("[data-comparison]").forEach(button => {
    button.addEventListener("click", () => openPowerDetails(button.dataset.comparison));
  });
}

function filterPowerRows(rows) {
  const query = state.query.trim().toLowerCase();
  return rows.filter(row => {
    const identity = row.comparisonIdentity;
    const runtime = runtimeLabel(identity.runtimeIdentity);
    const text = `${identity.modelArtifactID} ${identity.quantization} ${runtime}`.toLowerCase();
    return (!query || text.includes(query))
      && (state.device === "all" || identity.machineIdentifier === state.device)
      && (state.runtime === "all" || runtime === state.runtime)
      && (state.size === "all" || modelSizeBucket(identity.modelArtifactID) === state.size);
  });
}

function sortRows(rows) {
  const direction = state.sortDirection === "asc" ? 1 : -1;
  return [...rows].sort((left, right) => {
    let leftValue;
    let rightValue;
    if (state.sortKey === "model") {
      leftValue = left.comparisonIdentity.modelArtifactID;
      rightValue = right.comparisonIdentity.modelArtifactID;
    } else if (state.sortKey === "contributors") {
      leftValue = left.contributorCount;
      rightValue = right.contributorCount;
    } else {
      leftValue = left.value;
      rightValue = right.value;
    }
    return compare(leftValue, rightValue) * direction;
  });
}

function renderShip() {
  elements.contextLabel.textContent = "Ship deployment profiles";
  elements.contextDescription.textContent = "Published separately from Power. Ship may cite accepted Power evidence but is not produced by a benchmark run.";
  const query = state.query.trim().toLowerCase();
  const rows = state.ship.profiles.filter(row => {
    const model = row.configuration.model;
    const runtime = runtimeLabel(row.configuration.runtime);
    const text = `${model.displayName} ${model.artifactID} ${runtime}`.toLowerCase();
    return (!query || text.includes(query))
      && (state.device === "all" || row.configuration.device.machineIdentifier === state.device)
      && (state.runtime === "all" || runtime === state.runtime)
      && (state.size === "all" || modelSizeBucket(model.displayName) === state.size);
  });
  elements.rowCount.textContent = `${rows.length} deployment profile${rows.length === 1 ? "" : "s"}`;
  elements.empty.hidden = rows.length !== 0;
  elements.footerStatus.textContent = "Ship 1.0 · Separate deployment guidance · No Ship score";
  elements.footerChecksums.href = "results/ship-1.0/SHA256SUMS";
  elements.footerChecksums.textContent = "Checksums";
  elements.footerTable.href = "results/ship-1.0/PROFILES.md";
  elements.footerTable.textContent = "Profiles";
  renderHead([
    ["model", "Model"],
    ["quantization", "Quant"],
    ["device", "Device"],
    ["runtime", "Runtime"],
    ["details", "Profile"],
  ]);
  elements.body.innerHTML = rows.map(row => {
    const model = row.configuration.model;
    const device = row.configuration.device;
    return `<tr>
      <td class="model-cell"><span class="model-name">${escapeHtml(model.displayName)}</span><span class="model-meta">${escapeHtml(model.artifactID)}</span></td>
      <td>${escapeHtml(model.quantization)}</td>
      <td>${escapeHtml(device.displayName)}</td>
      <td>${escapeHtml(runtimeLabel(row.configuration.runtime))}</td>
      <td><a class="details-button" href="results/ship-1.0/PROFILES.md">Profile</a></td>
    </tr>`;
  }).join("");
}

function renderHead(columns) {
  elements.head.innerHTML = `<tr>${columns.map(([key, label]) => column(key, label)).join("")}</tr>`;
  elements.head.querySelectorAll("[data-sort]").forEach(button => {
    button.addEventListener("click", () => {
      if (state.sortKey === button.dataset.sort) {
        state.sortDirection = state.sortDirection === "asc" ? "desc" : "asc";
      } else {
        state.sortKey = button.dataset.sort;
        state.sortDirection = button.dataset.sort === "contributors" ? "desc" : "asc";
      }
      renderBoard();
    });
  });
  elements.head.querySelectorAll(".column-help").forEach(button => {
    button.addEventListener("mouseenter", () => showColumnHelp(button));
    button.addEventListener("focus", () => showColumnHelp(button));
    button.addEventListener("mouseleave", hideColumnHelp);
    button.addEventListener("blur", hideColumnHelp);
  });
}

function column(key, label) {
  const sortable = ["model", "value", "contributors"].includes(key);
  const active = state.sortKey === key;
  const heading = sortable
    ? `<button class="sort-control${active ? " is-active" : ""}" data-sort="${key}" data-arrow="${state.sortDirection === "asc" ? "↑" : "↓"}">${escapeHtml(label)}</button>`
    : `<span class="column-label">${escapeHtml(label)}</span>`;
  return `<th scope="col"><span class="column-heading">${heading}<button class="column-help" type="button" data-column-help="${key}" aria-label="Explain ${escapeAttribute(label)}" aria-describedby="column-tooltip" aria-expanded="false">?</button></span></th>`;
}

function showColumnHelp(button) {
  const description = COLUMN_HELP[button.dataset.columnHelp];
  if (!description) return;
  elements.head.querySelectorAll(".column-help").forEach(item => {
    item.setAttribute("aria-expanded", String(item === button));
  });
  const bounds = button.getBoundingClientRect();
  const tooltip = document.querySelector("#column-tooltip");
  tooltip.textContent = description;
  tooltip.hidden = false;
  const tooltipBounds = tooltip.getBoundingClientRect();
  const left = Math.min(
    window.innerWidth - tooltipBounds.width - 12,
    Math.max(12, bounds.left + bounds.width / 2 - tooltipBounds.width / 2),
  );
  const top = Math.max(12, bounds.top - tooltipBounds.height - 8);
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function hideColumnHelp() {
  document.querySelector("#column-tooltip").hidden = true;
  elements.head.querySelectorAll(".column-help").forEach(item => {
    item.setAttribute("aria-expanded", "false");
  });
}

function openPowerDetails(comparisonID) {
  const row = state.power.views.find(item => item.comparisonID === comparisonID);
  if (!row) return;
  const identity = row.comparisonIdentity;
  elements.dialogContent.innerHTML = `
    <p class="dialog-kicker">Exact Power 2 comparison identity</p>
    <h2 class="dialog-title">${escapeHtml(identity.modelArtifactID)}</h2>
    <div class="detail-grid">
      ${detailItem("Artifact revision", identity.modelArtifactRevision)}
      ${detailItem("Program", `${identity.programID}@${identity.programVersion}`)}
      ${detailItem("Target", `${identity.targetID}@${identity.targetVersion}`)}
      ${detailItem("Workload", `${identity.workloadID}@${identity.workloadVersion}`)}
      ${detailItem("Measurement mode", identity.measurementMode)}
      ${detailItem("Runner certificate", identity.runnerCertificateID)}
      ${detailItem("Runtime", runtimeLabel(identity.runtimeIdentity))}
      ${detailItem("Device", `${identity.machineIdentifier} · ${identity.osVersion} (${identity.osBuild})`)}
      ${detailItem("Primary metric", `${row.metricID}: ${row.value}`)}
      ${detailItem("Evidence state", row.evidenceState)}
    </div>
    <h3 class="claim-heading">Source result SHA-256</h3>
    <div class="history-list">${row.sourceResultSHA256s.map(digest => `<code>${escapeHtml(digest)}</code>`).join("")}</div>
    <p><a href="${escapeAttribute(modelRevisionURL(identity))}" target="_blank" rel="noreferrer">Open exact model revision ↗</a></p>`;
  if (!elements.dialog.open) elements.dialog.showModal();
}

function detailItem(label, value) {
  return `<div class="detail-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;
}

function runtimeLabel(runtime) {
  return `${runtime.name ?? "Unknown runtime"} ${runtime.version ?? ""}`.trim();
}

function evidenceState(value) {
  const labels = {
    accepted: "Accepted",
    reproduced: "Reproduced",
    "contributor-weighted": "Contributor weighted",
  };
  return `<span class="status-pill">${escapeHtml(labels[value] ?? value)}</span>`;
}

function formatMetric(value, unit) {
  if (!Number.isFinite(value)) return "—";
  return `${value.toFixed(unit === "ms" ? 1 : 2)} ${unit}`;
}

function modelParameterBillions(value) {
  const match = String(value).match(/(?:^|[-_/\s])(\d+(?:\.\d+)?)\s*[bB](?=$|[-_/\s])/);
  return match ? Number(match[1]) : null;
}

function modelSizeBucket(value) {
  const billions = modelParameterBillions(value);
  if (!Number.isFinite(billions)) return "unknown";
  if (billions <= 1) return "up-to-1b";
  if (billions <= 2) return "1b-to-2b";
  if (billions <= 4) return "2b-to-4b";
  return "over-4b";
}

function modelRevisionURL(identity) {
  return `https://huggingface.co/${encodeURI(identity.modelArtifactID)}/tree/${encodeURIComponent(identity.modelArtifactRevision)}`;
}

function compare(left, right) {
  if (typeof left === "number" && typeof right === "number") return left - right;
  return String(left).localeCompare(String(right), undefined, {
    numeric: true,
    sensitivity: "base",
  });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value);
}

document.querySelectorAll(".mode-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    state.mode = tab.dataset.mode;
    state.sortKey = state.mode === "ship" ? "model" : "value";
    state.sortDirection = powerModes[state.mode]?.direction ?? "asc";
    renderBoard();
  });
});
elements.search.addEventListener("input", event => {
  state.query = event.target.value;
  renderBoard();
});
elements.device.addEventListener("change", event => {
  state.device = event.target.value;
  renderBoard();
});
elements.runtime.addEventListener("change", event => {
  state.runtime = event.target.value;
  renderBoard();
});
elements.size.addEventListener("change", event => {
  state.size = event.target.value;
  renderBoard();
});
elements.theme.addEventListener("change", event => applyTheme(event.target.value, true));
document.querySelector(".dialog-close").addEventListener("click", () => elements.dialog.close());
elements.dialog.addEventListener("click", event => {
  if (event.target === elements.dialog) elements.dialog.close();
});

let initialTheme = document.documentElement.dataset.theme;
try {
  initialTheme = localStorage.getItem(THEME_STORAGE_KEY) || initialTheme;
} catch (_) {
  // Use the document default.
}
applyTheme(initialTheme);
loadEvidence();
