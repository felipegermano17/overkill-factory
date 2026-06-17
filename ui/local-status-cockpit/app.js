const DATA_URL = "data/status-cockpit.json";
const root = document.querySelector("[data-cockpit-root]");
const globalSearch = document.querySelector("#globalSearch");
const themeToggle = document.querySelector("#themeToggle");

const state = {
  data: null,
  selectedId: null,
  stateFilter: "all",
  query: "",
  receipts: [],
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

function setBusy(value) {
  root.setAttribute("aria-busy", value ? "true" : "false");
}

function clearRoot() {
  root.replaceChildren();
}

function setTheme(theme, persist = true) {
  const next = theme === "dark" ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  if (persist) localStorage.setItem("of-cockpit-theme", next);
  if (themeToggle) themeToggle.textContent = next === "dark" ? "Claro" : "Escuro";
}

function titleBlock(eyebrow, title, copy) {
  const children = [];
  if (eyebrow) children.push(node("p", { className: "eyebrow", text: eyebrow }));
  children.push(node("h2", { text: title }));
  if (copy) children.push(node("p", { className: "section-meta", text: copy }));
  return children;
}

function pill(label, value, extraClass = "pill") {
  const text = label ? `${label}: ${value || "-"}` : value || "-";
  return node("span", { className: extraClass }, [text]);
}

function selectedSnapshot() {
  return state.data.snapshots.find((snapshot) => snapshot.id === state.selectedId) || state.data.snapshots[0];
}

function stateLabel(value) {
  const labels = {
    success: "aprovado",
    empty: "vazio",
    loading: "carregando",
    error: "erro",
    blocked: "bloqueado",
    stale: "desatualizado",
    missing: "faltando",
    contradictory: "contraditório",
    private_unavailable: "privado",
    superseded: "superado",
    security_negative: "segurança",
    "missing-gate": "gate faltando",
    manual_estimate: "estimado",
  };
  return labels[value] || value || "-";
}

function stateUiLabel(value) {
  const labels = {
    loading_snapshot: "Carregando",
    empty_no_snapshots: "Sem snapshots",
    success_current_snapshot: "Atual",
    input_error_or_parse_failure: "Erro de entrada",
    blocked_gate: "Bloqueado",
    stale_snapshot: "Desatualizado",
    contradictory_state: "Contraditório",
    private_evidence_unavailable: "Evidência privada",
    review_pending_failed_passed: "Revisão",
    long_dense_data: "Dados densos",
  };
  return labels[value] || value || "-";
}

function actionLabel(value) {
  const labels = {
    block: "bloquear",
    blocked: "bloquear",
    review: "revisar",
    refresh: "atualizar",
    inspect: "inspecionar",
    continue: "acompanhar",
    fix: "corrigir",
  };
  return labels[value] || value || "acompanhar";
}

function snapshotTitle(snapshot) {
  const byState = {
    success_current_snapshot: "Projeção atual",
    empty_no_snapshots: "Sem snapshot disponível",
    loading_snapshot: "Atualização em curso",
    input_error_or_parse_failure: "Erro de leitura",
    blocked_gate: "Gate bloqueado",
    stale_snapshot: "Snapshot desatualizado",
    contradictory_state: "Estado contraditório",
    private_evidence_unavailable: "Evidência privada indisponível",
    review_pending_failed_passed: "Revisão pendente",
    long_dense_data: "Lista densa",
  };
  return byState[snapshot.state_ui] || snapshot.title || snapshot.id;
}

function shortRef(snapshotOrRef) {
  if (typeof snapshotOrRef === "object" && snapshotOrRef && snapshotOrRef.id) return snapshotOrRef.id;
  const value = String(snapshotOrRef || "");
  const match = value.match(/(FX\d+)/);
  return match ? match[1] : value;
}

function formatCount(value) {
  return String(Number(value || 0));
}

function renderLoading() {
  setBusy(true);
  clearRoot();
  root.appendChild(
    node("section", { className: "loading-panel", "aria-label": "Carregando dados locais" }, [
      node("p", { className: "eyebrow", text: "Carregando" }),
      node("h2", { text: "Lendo snapshots locais" }),
      node("p", { text: "Nenhum estado de gate, revisão ou publicação é inferido antes do JSON público carregar." }),
    ]),
  );
}

function renderEmpty(reason = "Nenhum snapshot público foi encontrado.") {
  setBusy(false);
  clearRoot();
  root.appendChild(
    node("section", { className: "empty-panel", "data-state-ui": "empty_no_snapshots", "data-current-state": "empty", "aria-label": "Sem snapshots" }, [
      node("p", { className: "eyebrow", text: "Vazio" }),
      node("h2", { text: "Sem snapshot local" }),
      node("p", { text: reason }),
      node("p", { className: "subtle", text: "Próximo passo: gerar o pacote público e revisar antes de operar." }),
    ]),
  );
}

function renderError(error) {
  setBusy(false);
  clearRoot();
  root.appendChild(
    node("section", { className: "error-panel", "data-state-ui": "input_error_or_parse_failure", "data-current-state": "error", role: "alert", "aria-label": "Erro ao ler dados" }, [
      node("p", { className: "eyebrow", text: "Erro" }),
      node("h2", { text: "O cockpit não conseguiu ler os dados locais" }),
      node("p", { text: error && error.message ? error.message : String(error) }),
      node("p", { className: "subtle", text: "Nada é aprovado, fechado ou publicado a partir de input inválido." }),
    ]),
  );
}

function metric(label, value) {
  return node("article", { className: "metric" }, [
    node("span", { text: label }),
    node("strong", { text: value }),
  ]);
}

function renderSummary() {
  const metrics = state.data.metrics;
  const running = state.data.snapshots.filter((snapshot) => !["success", "empty"].includes(snapshot.current_state)).length;
  return node("section", { className: "summary-grid", "aria-label": "Resumo da fábrica" }, [
    metric("Frentes", formatCount(metrics.total_snapshots)),
    metric("Bloqueios", formatCount(metrics.blocked_or_review_count)),
    metric("Rodando", formatCount(running)),
    metric("Privado bruto", formatCount(metrics.raw_private_payload_count)),
  ]);
}

function renderFactoryLine() {
  const counts = state.data.metrics.state_ui_counts || {};
  const stages = [
    ["Entrada", counts.loading_snapshot || 0, "snapshots"],
    ["Triagem", counts.blocked_gate || 0, "bloqueios"],
    ["Construção", counts.long_dense_data || 0, "densos"],
    ["Validação", counts.review_pending_failed_passed || 0, "revisões"],
    ["Prova", counts.success_current_snapshot || 0, "atuais"],
    ["Risco", counts.contradictory_state || 0, "conflitos"],
  ];
  return node("section", { className: "panel", "aria-label": "Linha de produção" }, [
    ...titleBlock("Linha de produção", "Fábrica agora"),
    node("div", { className: "factory-line" }, stages.map(([label, value, unit]) => node("article", { className: "stage" }, [
      node("b", { text: label }),
      node("strong", { text: value }),
      node("span", { text: unit }),
    ]))),
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

function renderStateFilters() {
  const buttons = [
    node("button", {
      className: "state-filter",
      type: "button",
      "aria-pressed": state.stateFilter === "all" ? "true" : "false",
      onClick: () => {
        state.stateFilter = "all";
        renderApp();
      },
    }, [node("strong", { text: "Todos" }), node("span", { className: "subtle", text: `${state.data.snapshots.length} frentes` })]),
  ];
  state.data.state_registry.forEach((entry) => {
    buttons.push(node("button", {
      className: "state-filter",
      type: "button",
      "data-state-ui": entry.id,
      "aria-pressed": state.stateFilter === entry.id ? "true" : "false",
      onClick: () => {
        state.stateFilter = entry.id;
        const first = filteredSnapshots()[0];
        if (first) state.selectedId = first.id;
        renderApp();
      },
    }, [node("strong", { text: stateUiLabel(entry.id) }), node("span", { className: "subtle", text: `${stateCountFor(entry.id)} itens` })]));
  });
  return node("aside", { className: "state-rail", "aria-label": "Filtros de estado" }, [
    ...titleBlock("Navegação", "Estados"),
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
    const haystack = [
      snapshot.id,
      snapshot.title,
      snapshot.current_state,
      snapshot.state_ui,
      snapshot.phase,
      snapshot.next_safe_action.label,
      snapshot.input_ref,
    ].join(" ").toLowerCase();
    return haystack.includes(query);
  });
}

function updateQuery(value) {
  state.query = value;
  if (globalSearch && globalSearch.value !== value) globalSearch.value = value;
  renderApp();
}

function renderToolbar() {
  return node("section", { className: "toolbar", "aria-label": "Controles da fila" }, [
    node("input", {
      type: "search",
      value: state.query,
      placeholder: "Título, estado ou evidência",
      "aria-label": "Buscar na fila",
      onInput: (event) => updateQuery(event.target.value),
    }),
    node("button", { type: "button", dataset: { action: "new-front" }, onClick: () => localAction("Nova frente local") }, ["Nova frente"]),
    node("button", { type: "button", dataset: { action: "refresh" }, onClick: () => localAction("Snapshot atualizado") }, ["Atualizar"]),
    node("button", { type: "button", dataset: { action: "download-receipt" }, onClick: () => downloadReceipt() }, ["Baixar recibo"]),
  ]);
}

function renderSnapshotList() {
  const snapshots = filteredSnapshots();
  if (!snapshots.find((snapshot) => snapshot.id === state.selectedId) && snapshots[0]) {
    state.selectedId = snapshots[0].id;
  }
  const rows = snapshots.map((snapshot) => node("button", {
    className: "snapshot-row",
    type: "button",
    dataset: { snapshotId: snapshot.id },
    "data-state-ui": snapshot.state_ui,
    "data-current-state": snapshot.current_state,
    "aria-current": snapshot.id === state.selectedId ? "true" : "false",
    onClick: () => {
      state.selectedId = snapshot.id;
      renderApp();
    },
  }, [
    node("span", { className: "snapshot-status" }, [pill("", stateLabel(snapshot.current_state), "state-pill current-pill")]),
    node("span", { className: "snapshot-title-cell" }, [
      node("strong", { text: snapshotTitle(snapshot) }),
      node("span", { className: "subtle", text: shortRef(snapshot) }),
    ]),
    node("span", { className: "snapshot-phase", text: snapshot.phase }),
    node("span", { className: "snapshot-action", text: actionLabel(snapshot.next_safe_action.action_type) }),
  ]));
  return node("section", { className: "panel", id: "queue", "aria-label": "Fila da fábrica" }, [
    ...titleBlock("Fila", "Frentes", `${snapshots.length} itens visíveis`),
    node("div", { className: "queue-table" }, [
      node("div", { className: "snapshot-head", "aria-hidden": "true" }, [
        node("span", { text: "Estado" }),
        node("span", { text: "Frente" }),
        node("span", { text: "Etapa" }),
        node("span", { text: "Ação" }),
      ]),
      ...(rows.length ? rows : [node("p", { className: "subtle", text: "Nada encontrado." })]),
    ]),
  ]);
}

function kv(label, value) {
  return node("div", { className: "kv" }, [node("span", { text: label }), node("strong", { text: value || "-" })]);
}

function refList(refs) {
  if (!refs || !refs.length) return node("p", { className: "subtle", text: "Sem refs públicas." });
  return node("p", { className: "pill-row" }, refs.map((ref) => node("code", { className: "ref-code", text: ref })));
}

function renderObjectList(title, items, formatter, emptyCopy) {
  const content = items && items.length
    ? node("ul", { className: "object-list" }, items.map((item) => node("li", { className: "object-row" }, formatter(item))))
    : node("p", { className: "subtle", text: emptyCopy });
  return node("section", { className: "stack", "aria-label": title }, [node("h3", { text: title }), content]);
}

function localAction(label) {
  const selected = selectedSnapshot();
  const receipt = {
    at: new Date().toISOString(),
    item: selected ? selected.id : "local",
    action: label,
    scope: "local",
  };
  state.receipts.unshift(receipt);
  state.receipts = state.receipts.slice(0, 6);
  renderApp();
}

function downloadReceipt() {
  const selected = selectedSnapshot();
  const payload = {
    record_type: "local_cockpit_receipt",
    item: selected ? selected.id : null,
    action: "export_local_receipt",
    scope: "local-only",
    created_at: new Date().toISOString(),
    selected_state: selected ? selected.current_state : null,
    receipts: state.receipts,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = node("a", { href: url, download: `cockpit-receipt-${payload.item || "local"}.json` });
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
  localAction("Recibo baixado");
}

function renderActions(selected) {
  const blocked = selected.current_state !== "success";
  const title = blocked ? "Gate humano" : "Sem gate humano";
  const primary = blocked ? "Pedir evidência" : "Baixar recibo";
  return node("section", { className: "detail-card action-card", id: "commands", "data-state-ui": selected.state_ui, "data-current-state": selected.current_state, "aria-label": "Ações locais" }, [
    node("p", { className: "eyebrow", text: "Operar" }),
    node("h2", { text: title }),
    node("p", { className: "section-meta", text: blocked ? "Ação local registra intenção; não aprova gate nem altera runtime." : "Frente sem bloqueio humano no snapshot atual." }),
    node("div", { className: "action-grid" }, [
      node("button", { className: "primary", type: "button", dataset: { action: "primary" }, onClick: () => blocked ? localAction("Evidência solicitada") : downloadReceipt() }, [primary]),
      node("button", { type: "button", dataset: { action: "follow" }, onClick: () => localAction("Acompanhamento registrado") }, ["Acompanhar"]),
      node("button", { type: "button", dataset: { action: "request-change" }, onClick: () => localAction("Ajuste solicitado") }, ["Pedir ajuste"]),
      node("button", { type: "button", dataset: { action: "context" }, onClick: () => localAction("Contexto aberto") }, ["Contexto"]),
    ]),
  ]);
}

function renderDetail() {
  const selected = selectedSnapshot();
  if (!selected) return node("section", { className: "detail-card", id: "inspector" }, [node("p", { text: "Sem frente selecionada." })]);
  return node("section", {
    className: "detail-card",
    id: "inspector",
    "data-state-ui": selected.state_ui,
    "data-current-state": selected.current_state,
    "aria-label": "Detalhe da frente",
  }, [
    node("div", { className: "inspector-kicker" }, [
      node("p", { className: "eyebrow", text: "Frente aberta" }),
      node("span", { className: "subtle", text: selected.id }),
    ]),
    node("h2", { text: snapshotTitle(selected) }),
    node("p", { className: "next-action", text: selected.next_safe_action.label }),
    node("div", { className: "pill-row" }, [
      pill("estado", stateLabel(selected.current_state), "state-pill current-pill"),
      pill("ui", selected.state_ui, "state-pill"),
      pill("risco", selected.risk_effective),
    ]),
    node("div", { className: "detail-grid" }, [
      kv("Observado", selected.observed_at),
      kv("Fonte", selected.input_ref),
      kv("Revisão", selected.review.status),
      kv("Recibo", selected.receipt.status),
      kv("Ação", actionLabel(selected.next_safe_action.action_type)),
      kv("Freshness", selected.freshness_state),
    ]),
    renderObjectList("Gates", selected.gate_states, (item) => [
      node("strong", { text: `${item.label} · ${item.state}` }),
      node("p", { text: `Responsável: ${item.owner}. Desbloqueio: ${item.unblock_condition}` }),
      refList(item.source_refs),
    ], "Sem gate listado."),
    renderObjectList("Bloqueios", selected.blockers, (item) => [
      node("strong", { text: `${item.id} · ${item.state}` }),
      node("p", { text: item.summary }),
      node("p", { className: "subtle", text: `Desbloqueio: ${item.unblock_condition}` }),
      refList(item.source_refs),
    ], "Sem bloqueio listado."),
    renderObjectList("Evidências", selected.evidence_refs, (item) => [
      node("strong", { text: `${item.id} · ${item.public_safety_state}` }),
      node("p", { text: `${item.kind} · ${item.freshness_state} · ${item.verification_status}` }),
      item.unavailable_reason ? node("p", { className: "subtle", text: item.unavailable_reason }) : null,
      refList([item.ref, ...item.source_refs]),
    ], "Sem evidência listada."),
  ]);
}

function renderProductFacePanel() {
  const packet = state.data.product_face;
  const review = state.data.product_face_review;
  return node("section", { className: "panel", id: "reports", "aria-label": "Prova de produto" }, [
    ...titleBlock("Qualidade", "Face do Produto", "Critérios públicos do cockpit."),
    node("div", { className: "pill-row" }, [
      pill("review", review.verdict),
      pill("consumo", review.may_consume_product_face_packet ? "liberado" : "bloqueado"),
      pill("resultado", review.is_product_face_result ? "sim" : "não"),
    ]),
    kv("Tom visual", packet.visual_tone),
    kv("Densidade", packet.density),
    kv("Interação", packet.interaction_style),
  ]);
}

function renderReceipts() {
  const rows = state.receipts.length
    ? state.receipts.map((receipt) => node("div", { className: "receipt-row" }, [
      node("strong", { text: receipt.action }),
      node("span", { className: "subtle", text: receipt.item }),
    ]))
    : [node("p", { className: "subtle", text: "Sem ação local registrada." })];
  return node("section", { className: "panel", "aria-label": "Recibos locais" }, [
    ...titleBlock("Recibos", "Ações locais"),
    node("div", { className: "receipt-list" }, rows),
  ]);
}

function renderTimeline() {
  const rows = state.data.timeline.slice(-10).reverse().map((item) => node("article", {
    className: "timeline-row",
    "data-state-ui": item.state_ui,
    "data-current-state": item.current_state,
  }, [
    node("time", { text: item.at }),
    node("strong", { text: snapshotTitle({ state_ui: item.state_ui, title: item.label }) }),
    node("p", { className: "subtle", text: `${stateLabel(item.current_state)} · ${actionLabel(item.next_action)} · ${shortRef(item.source_ref)}` }),
  ]));
  return node("section", { className: "panel", "aria-label": "Linha do tempo" }, [
    ...titleBlock("Linha do tempo", "Eventos recentes"),
    node("div", { className: "timeline" }, rows),
  ]);
}

function renderGuardrails() {
  return node("section", { className: "panel", "aria-label": "Limites" }, [
    ...titleBlock("Limites", "Bloqueado neste cockpit"),
    node("ul", { className: "guardrail-list" }, state.data.policy.forbidden_actions.slice(0, 12).map((item) => node("li", { text: item }))),
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
  const selected = selectedSnapshot();
  root.appendChild(node("div", { className: "app-shell" }, [
    renderStateFilters(),
    node("div", { className: "main-stack stack" }, [
      renderSummary(),
      renderFactoryLine(),
      renderToolbar(),
      renderSnapshotList(),
    ]),
    node("div", { className: "inspector-stack stack" }, [
      renderDetail(),
      renderActions(selected),
      renderReceipts(),
      renderProductFacePanel(),
      renderTimeline(),
      renderGuardrails(),
    ]),
  ]));
}

async function loadData() {
  const params = new URLSearchParams(window.location.search);
  const theme = params.get("theme") || localStorage.getItem("of-cockpit-theme") || "light";
  setTheme(theme, false);
  const demo = params.get("demo");
  if (demo === "loading") {
    renderLoading();
    return;
  }
  if (demo === "empty") {
    renderEmpty("Modo demo: nenhum snapshot local disponível.");
    return;
  }
  if (demo === "error") {
    renderError(new Error("Modo demo: falha simulada ao ler evidência."));
    return;
  }
  renderLoading();
  try {
    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`Falha ao ler ${DATA_URL}: ${response.status}`);
    state.data = await response.json();
    state.stateFilter = params.get("state") || "all";
    state.query = params.get("q") || "";
    if (globalSearch) globalSearch.value = state.query;
    state.selectedId = params.get("snapshot") || (state.data.snapshots && state.data.snapshots[0] ? state.data.snapshots[0].id : null);
    renderApp();
  } catch (error) {
    renderError(error);
  }
}

if (globalSearch) {
  globalSearch.addEventListener("input", (event) => updateQuery(event.target.value));
  window.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement !== globalSearch) {
      event.preventDefault();
      globalSearch.focus();
    }
  });
}

if (themeToggle) {
  themeToggle.addEventListener("click", () => {
    const current = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
    setTheme(current === "dark" ? "light" : "dark");
  });
}

document.querySelectorAll("[data-dock-target]").forEach((button) => {
  button.addEventListener("click", () => {
    const target = document.querySelector(`#${button.dataset.dockTarget}`);
    if (target) target.scrollIntoView({ block: "start" });
  });
});

loadData();
