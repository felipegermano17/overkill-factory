const DATA_URL = "data/status-cockpit.json";
const root = document.querySelector("[data-cockpit-root]");
const state = {
  data: null,
  selectedId: null,
  stateFilter: "all",
  query: "",
};

function node(tag, attributes = {}, children = []) {
  const element = document.createElement(tag);
  Object.entries(attributes).forEach(([key, value]) => {
    if (value === undefined || value === null || value === false) return;
    if (key === "className") element.className = value;
    else if (key === "text") element.textContent = String(value);
    else if (key === "dataset") {
      Object.entries(value).forEach(([dataKey, dataValue]) => {
        element.dataset[dataKey] = String(dataValue);
      });
    } else if (key.startsWith("on") && typeof value === "function") {
      element.addEventListener(key.slice(2).toLowerCase(), value);
    } else if (value === true) {
      element.setAttribute(key, "");
    } else {
      element.setAttribute(key, String(value));
    }
  });
  const items = Array.isArray(children) ? children : [children];
  items.forEach((child) => {
    if (child === null || child === undefined) return;
    if (typeof child === "string" || typeof child === "number") {
      element.appendChild(document.createTextNode(String(child)));
    } else {
      element.appendChild(child);
    }
  });
  return element;
}

function clearRoot() {
  root.replaceChildren();
}

function setBusy(value) {
  root.setAttribute("aria-busy", value ? "true" : "false");
}

function pill(label, value, extraClass = "pill") {
  return node("span", { className: extraClass }, [label ? `${label}: ${value}` : value]);
}

function sectionTitle(eyebrow, title, copy) {
  const children = [];
  if (eyebrow) children.push(node("p", { className: "eyebrow", text: eyebrow }));
  children.push(node("h2", { text: title }));
  if (copy) children.push(node("p", { className: "subtle", text: copy }));
  return children;
}

function renderLoading() {
  setBusy(true);
  clearRoot();
  root.appendChild(
    node("section", { className: "loading-panel", "aria-label": "Loading local cockpit data" }, [
      node("p", { className: "eyebrow", text: "Loading snapshot" }),
      node("h2", { text: "Reading local StatusSnapshot projections" }),
      node("p", { text: "The cockpit is waiting for the local JSON bundle. No success, review, release or completion state is inferred yet." }),
    ]),
  );
}

function renderEmpty(reason = "No local snapshots were found in the cockpit data bundle.") {
  setBusy(false);
  clearRoot();
  root.appendChild(
    node("section", { className: "empty-panel", "data-state-ui": "empty_no_snapshots", "data-current-state": "empty", "aria-label": "No snapshots" }, [
      node("p", { className: "eyebrow", text: "Empty / no snapshots" }),
      node("h2", { text: "No canonical snapshot available" }),
      node("p", { text: reason }),
      node("p", { className: "subtle", text: "Next safe action: regenerate the public-safe local data bundle, then request independent Product Face proof. This surface has no mutation controls." }),
    ]),
  );
}

function renderError(error) {
  setBusy(false);
  clearRoot();
  root.appendChild(
    node("section", { className: "error-panel", "data-state-ui": "input_error_or_parse_failure", "data-current-state": "error", role: "alert", "aria-label": "Input parse error" }, [
      node("p", { className: "eyebrow", text: "Input error / parse failure" }),
      node("h2", { text: "The local cockpit data could not be parsed" }),
      node("p", { text: error && error.message ? error.message : String(error) }),
      node("p", { className: "subtle", text: "No gate, review, done, release or issue-completion claim is inferred from invalid input." }),
    ]),
  );
}

function metric(label, value) {
  return node("article", { className: "metric" }, [
    node("span", { text: label }),
    node("strong", { text: value }),
  ]);
}

function stateCountFor(stateId) {
  const counts = state.data.metrics.state_ui_counts || {};
  if (stateId === "review_pending_failed_passed") {
    return Object.values(state.data.metrics.review_state_counts || {}).reduce((sum, value) => sum + Number(value || 0), 0);
  }
  if (stateId === "long_dense_data") {
    return state.data.snapshots.filter((snapshot) => snapshot.density && snapshot.density.is_dense).length;
  }
  return counts[stateId] || 0;
}

function renderCommandStrip() {
  const metrics = state.data.metrics;
  return node("section", { className: "command-strip", "aria-label": "Cockpit summary metrics" }, [
    metric("Fixture projections", metrics.status_fixture_projections),
    metric("Adapter report projections", metrics.adapter_report_projections),
    metric("Blocked or review states", metrics.blocked_or_review_count),
    metric("Raw private payloads shown", metrics.raw_private_payload_count),
  ]);
}

function renderStateFilters() {
  const buttons = [node("button", {
    className: "state-filter",
    type: "button",
    "aria-pressed": state.stateFilter === "all" ? "true" : "false",
    onClick: () => {
      state.stateFilter = "all";
      renderApp();
    },
  }, [node("strong", { text: "All states" }), node("br"), node("span", { className: "subtle", text: `${state.data.snapshots.length} projections` })])];

  state.data.state_registry.forEach((entry) => {
    buttons.push(node("button", {
      className: "state-filter",
      type: "button",
      "data-state-ui": entry.id,
      "aria-pressed": state.stateFilter === entry.id ? "true" : "false",
      onClick: () => {
        state.stateFilter = entry.id;
        const selected = filteredSnapshots()[0];
        if (selected) state.selectedId = selected.id;
        renderApp();
      },
    }, [node("strong", { text: entry.label }), node("br"), node("span", { className: "subtle", text: `${stateCountFor(entry.id)} matches · ${entry.demo_query}` })]));
  });

  return node("section", { className: "panel", "aria-label": "State filters" }, [
    ...sectionTitle("State semantics", "Required states", "Filter by the Product Face packet state matrix. Color is paired with text labels."),
    node("div", { className: "state-filter-grid" }, buttons),
  ]);
}

function filteredSnapshots() {
  const query = state.query.trim().toLowerCase();
  return state.data.snapshots.filter((snapshot) => {
    const filterMatch = state.stateFilter === "all"
      || snapshot.state_ui === state.stateFilter
      || (state.stateFilter === "review_pending_failed_passed" && snapshot.review)
      || (state.stateFilter === "long_dense_data" && snapshot.density && snapshot.density.is_dense);
    if (!filterMatch) return false;
    if (!query) return true;
    const haystack = [snapshot.id, snapshot.title, snapshot.current_state, snapshot.state_ui, snapshot.phase, snapshot.next_safe_action.label].join(" ").toLowerCase();
    return haystack.includes(query);
  });
}

function renderSnapshotList() {
  const snapshots = filteredSnapshots();
  if (!snapshots.find((snapshot) => snapshot.id === state.selectedId) && snapshots[0]) {
    state.selectedId = snapshots[0].id;
  }
  const input = node("input", {
    type: "search",
    value: state.query,
    placeholder: "Search source, state, blocker or next action",
    "aria-label": "Search snapshots",
    onInput: (event) => {
      state.query = event.target.value;
      renderApp();
    },
  });

  const rows = snapshots.map((snapshot) => node("button", {
    className: "snapshot-row",
    type: "button",
    "data-state-ui": snapshot.state_ui,
    "data-current-state": snapshot.current_state,
    "aria-current": snapshot.id === state.selectedId ? "true" : "false",
    onClick: () => {
      state.selectedId = snapshot.id;
      renderApp();
    },
  }, [
    node("strong", { text: snapshot.title }),
    node("span", { className: "subtle", text: snapshot.input_ref }),
    node("span", { className: "snapshot-meta" }, [
      pill("state", snapshot.current_state, "state-pill current-pill"),
      pill("ui", snapshot.state_ui, "state-pill"),
      pill("review", snapshot.review.status),
    ]),
  ]));

  return node("aside", { className: "panel", "aria-label": "Snapshot list" }, [
    ...sectionTitle("Local sources", "Snapshots", "Fixture and adapter report projections only."),
    node("div", { className: "search-row" }, [input]),
    rows.length ? node("div", { className: "snapshot-list" }, rows) : node("p", { className: "subtle", text: "No snapshot matches the current filter." }),
  ]);
}

function kv(label, value) {
  return node("div", { className: "kv" }, [node("span", { text: label }), node("strong", { text: value || "—" })]);
}

function renderObjectList(title, items, formatter, emptyCopy) {
  const content = items && items.length
    ? node("ul", { className: "object-list" }, items.map((item) => node("li", { className: "object-card" }, formatter(item))))
    : node("p", { className: "subtle", text: emptyCopy });
  return node("section", { className: "stack", "aria-label": title }, [node("h3", { text: title }), content]);
}

function refList(refs) {
  if (!refs || !refs.length) return node("p", { className: "subtle", text: "No public refs listed." });
  return node("p", { className: "pill-row" }, refs.map((ref) => node("code", { className: "ref-code", text: ref })));
}

function renderDetail() {
  const selected = state.data.snapshots.find((snapshot) => snapshot.id === state.selectedId) || state.data.snapshots[0];
  if (!selected) return node("section", { className: "detail-card" }, [node("p", { text: "No selected snapshot." })]);
  return node("section", {
    className: "detail-card",
    "data-state-ui": selected.state_ui,
    "data-current-state": selected.current_state,
    "aria-label": "Selected snapshot detail",
  }, [
    node("p", { className: "eyebrow", text: selected.phase }),
    node("h2", { text: selected.title }),
    node("p", { className: "subtle", text: selected.next_safe_action.label }),
    node("div", { className: "pill-row" }, [
      pill("current", selected.current_state, "state-pill current-pill"),
      pill("ui", selected.state_ui, "state-pill"),
      pill("freshness", selected.freshness_state),
      pill("risk", selected.risk_effective),
    ]),
    node("div", { className: "detail-grid" }, [
      kv("Observed", selected.observed_at),
      kv("Source updated", selected.source_updated_at || "not supplied"),
      kv("Review lane", selected.review.status),
      kv("Receipt status", selected.receipt.status),
      kv("Next action", selected.next_safe_action.action_type),
      kv("Source ref", selected.input_ref),
    ]),
    renderObjectList("Gate states", selected.gate_states, (item) => [
      node("strong", { text: `${item.label} · ${item.state}` }),
      node("p", { text: `Owner: ${item.owner}. Unblock: ${item.unblock_condition}` }),
      refList(item.source_refs),
    ], "No gate state listed."),
    renderObjectList("Blockers", selected.blockers, (item) => [
      node("strong", { text: `${item.id} · ${item.state}` }),
      node("p", { text: item.summary }),
      node("p", { className: "subtle", text: `Unblock condition: ${item.unblock_condition}` }),
      refList(item.source_refs),
    ], "No blockers listed."),
    renderObjectList("Evidence refs", selected.evidence_refs, (item) => [
      node("strong", { text: `${item.id} · ${item.public_safety_state}` }),
      node("p", { text: `${item.kind} · freshness ${item.freshness_state} · verification ${item.verification_status}` }),
      item.unavailable_reason ? node("p", { className: "subtle", text: `Redaction/unavailable reason: ${item.unavailable_reason}` }) : null,
      refList([item.ref, ...item.source_refs]),
    ], "No evidence refs listed."),
  ]);
}

function renderProductFacePanel() {
  const packet = state.data.product_face;
  const review = state.data.product_face_review;
  return node("aside", { className: "panel", "aria-label": "Product Face contract" }, [
    ...sectionTitle("Product Face packet", packet.surface, packet.job_to_be_done),
    node("div", { className: "pill-row" }, [
      pill("review", review.verdict),
      pill("consume", review.may_consume_product_face_packet ? "bounded yes" : "blocked"),
      pill("result", review.is_product_face_result ? "result" : "not result"),
    ]),
    kv("Visual tone", packet.visual_tone),
    kv("Density", packet.density),
    kv("Interaction", packet.interaction_style),
    renderObjectList("Must have", packet.must_have || [], (item) => [node("p", { text: item })], "No must-have entries."),
    renderObjectList("Must not have", packet.must_not_have || [], (item) => [node("p", { text: item })], "No must-not-have entries."),
    renderObjectList("Required proof", packet.proof_required || [], (item) => [node("p", { text: item })], "No proof requirements listed."),
  ]);
}

function renderStateCoverage() {
  const cards = state.data.state_registry.map((entry) => node("article", { className: "state-coverage-card", "data-state-ui": entry.id }, [
    node("h3", { text: entry.label }),
    node("p", { text: entry.operator_meaning }),
    pill("matches", stateCountFor(entry.id), "state-pill"),
  ]));
  return node("section", { className: "panel", "aria-label": "State coverage matrix" }, [
    ...sectionTitle("State coverage", "Packet-required state matrix", "Each state is text-labeled and available through fixtures, adapter projections or explicit demo mode."),
    node("div", { className: "state-coverage-grid" }, cards),
  ]);
}

function renderTimeline() {
  const rows = state.data.timeline.slice(-12).reverse().map((item) => node("article", { className: "timeline-row", "data-state-ui": item.state_ui, "data-current-state": item.current_state }, [
    node("time", { text: item.at }),
    node("strong", { text: item.label }),
    node("p", { className: "subtle", text: `${item.current_state} · ${item.next_action} · ${item.source_ref}` }),
  ]));
  return node("section", { className: "panel", "aria-label": "Transition timeline" }, [
    ...sectionTitle("Timeline", "Recent projections", "Replay is based on source refs, not chat memory."),
    node("div", { className: "timeline" }, rows),
  ]);
}

function renderGuardrails() {
  return node("section", { className: "panel", "aria-label": "Forbidden actions" }, [
    ...sectionTitle("Safety boundary", "Forbidden by this surface", "The cockpit makes boundaries visible instead of hiding them behind successful-looking cards."),
    node("ul", { className: "guardrail-list" }, state.data.policy.forbidden_actions.map((item) => node("li", { text: item }))),
  ]);
}

function renderApp() {
  setBusy(false);
  clearRoot();
  if (!state.data || !state.data.snapshots || !state.data.snapshots.length) {
    renderEmpty();
    return;
  }
  if (!state.selectedId) state.selectedId = state.data.snapshots[0].id;
  root.appendChild(renderCommandStrip());
  root.appendChild(node("div", { className: "layout" }, [
    node("div", { className: "stack" }, [renderStateFilters(), renderSnapshotList()]),
    node("div", { className: "stack" }, [renderDetail(), renderStateCoverage(), renderTimeline(), renderGuardrails()]),
    renderProductFacePanel(),
  ]));
}

async function loadData() {
  const params = new URLSearchParams(window.location.search);
  const demo = params.get("demo");
  if (demo === "loading") {
    renderLoading();
    return;
  }
  if (demo === "empty") {
    renderEmpty("Demo mode: no canonical local snapshot is available.");
    return;
  }
  if (demo === "error") {
    renderError(new Error("Demo mode: simulated parse failure for state evidence."));
    return;
  }
  renderLoading();
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`Failed to fetch ${DATA_URL}: ${response.status}`);
    const data = await response.json();
    state.data = data;
    state.stateFilter = params.get("state") || "all";
    state.query = params.get("q") || "";
    const selected = params.get("snapshot");
    state.selectedId = selected || (data.snapshots && data.snapshots[0] ? data.snapshots[0].id : null);
    renderApp();
  } catch (error) {
    renderError(error);
  }
}

loadData();
