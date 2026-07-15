const STATUS_PATH = 'data/project_status.json';
const HISTORY_PATH = 'data/project_history.json';
const BASE_REFRESH_MS = 10_000;
const MAX_REFRESH_MS = 60_000;
const SMOKE_MODE = typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('smoke');

const REQUIRED_SAFETY_KEYS = new Set([
  'TEST_SPLIT_READ',
  'MODEL_INFERENCE_EXECUTED',
  'CANONICAL_ANNOTATION_MODIFIED',
  'CANONICAL_COCO_MODIFIED',
  'DATASET_MODIFIED',
  'REGISTRY_MODIFIED',
  'FIXED_SPLITS_MODIFIED',
  'TRAINING_STARTED',
  'RETRAINING_STATUS',
  'DEPLOYMENT_ACCEPTANCE',
]);

const STATUS_LABELS = {
  COMPLETED: '已完成',
  IN_PROGRESS: '執行中',
  PENDING_REVIEW: '待審核',
  READY: '可開始',
  PENDING_EXECUTION: '待執行',
  BLOCKED: 'BLOCKED',
  NOT_APPROVED: '尚未核准',
  PLANNED: '已規劃',
  FUTURE: '未來',
  FROZEN: '已封存',
  DEPRECATED: '已停用',
};

const TRUST_LABELS = {
  REPOSITORY_VERIFIED: 'Repository verified',
  ARTIFACT_VERIFIED: 'Artifact verified',
  WORKTREE_VERIFIED: 'Worktree verified',
  OPERATOR_REPORTED: 'Operator reported',
  STALE_OR_CONFLICTING: 'Stale / conflicting',
  UNVERIFIED: 'Unverified',
};

const state = {
  statusDocument: null,
  historyDocument: null,
  selectedPhase: 'ALL',
  statusFilter: 'ALL',
  query: '',
  refreshDelay: BASE_REFRESH_MS,
  refreshTimer: null,
  lastSuccessfulRefresh: null,
  loading: false,
};

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function duplicateValues(values) {
  const seen = new Set();
  const duplicates = new Set();
  for (const value of values) {
    if (seen.has(value)) duplicates.add(value);
    seen.add(value);
  }
  return [...duplicates];
}

function requireString(errors, value, label) {
  if (typeof value !== 'string' || value.length === 0) errors.push(`${label} must be a non-empty string`);
}

export function validateStatusDocument(documentValue) {
  const errors = [];
  if (!isObject(documentValue)) return ['project_status root must be an object'];
  if (documentValue.schema_version !== '1.0') errors.push('unsupported project_status schema_version');
  requireString(errors, documentValue.snapshot_id, 'snapshot_id');
  requireString(errors, documentValue.generated_at_utc, 'generated_at_utc');
  if (!isObject(documentValue.project)) errors.push('project must be an object');
  if (!isObject(documentValue.repository)) errors.push('repository must be an object');
  if (!isObject(documentValue.current_focus)) errors.push('current_focus must be an object');

  const arrayFields = ['safety_gates', 'phases', 'gates', 'evidence', 'warnings'];
  for (const field of arrayFields) {
    if (!Array.isArray(documentValue[field])) errors.push(`${field} must be an array`);
  }
  if (errors.length > 0) return errors;

  const phaseIds = documentValue.phases.map((item) => item?.phase_id);
  const gateIds = documentValue.gates.map((item) => item?.gate_id);
  const evidenceIds = documentValue.evidence.map((item) => item?.evidence_id);
  const phaseSet = new Set(phaseIds);
  const gateSet = new Set(gateIds);
  const evidenceSet = new Set(evidenceIds);

  for (const value of duplicateValues(phaseIds)) errors.push(`duplicate phase_id: ${value}`);
  for (const value of duplicateValues(gateIds)) errors.push(`duplicate gate_id: ${value}`);
  for (const value of duplicateValues(evidenceIds)) errors.push(`duplicate evidence_id: ${value}`);

  for (const phase of documentValue.phases) {
    if (!isObject(phase)) {
      errors.push('phase record must be an object');
      continue;
    }
    requireString(errors, phase.phase_id, 'phase_id');
    if (!Number.isFinite(phase.progress) || phase.progress < 0 || phase.progress > 100) {
      errors.push(`phase ${phase.phase_id ?? '<unknown>'} progress must be between 0 and 100`);
    }
    if (!Array.isArray(phase.gate_ids)) errors.push(`phase ${phase.phase_id ?? '<unknown>'} gate_ids must be an array`);
    for (const gateId of phase.gate_ids ?? []) {
      if (!gateSet.has(gateId)) errors.push(`phase ${phase.phase_id} references unknown gate_id: ${gateId}`);
    }
  }

  for (const gate of documentValue.gates) {
    if (!isObject(gate)) {
      errors.push('gate record must be an object');
      continue;
    }
    requireString(errors, gate.gate_id, 'gate_id');
    if (!phaseSet.has(gate.phase_id)) errors.push(`gate ${gate.gate_id} references unknown phase_id: ${gate.phase_id}`);
    if (!Number.isFinite(gate.progress) || gate.progress < 0 || gate.progress > 100) {
      errors.push(`gate ${gate.gate_id} progress must be between 0 and 100`);
    }
    for (const evidenceId of gate.evidence_ids ?? []) {
      if (!evidenceSet.has(evidenceId)) errors.push(`gate ${gate.gate_id} references unknown evidence_id: ${evidenceId}`);
    }
  }

  const safetyKeys = new Set(documentValue.safety_gates.map((item) => item?.key));
  for (const key of REQUIRED_SAFETY_KEYS) {
    if (!safetyKeys.has(key)) errors.push(`missing safety gate: ${key}`);
  }

  const gatesById = new Map(documentValue.gates.map((item) => [item.gate_id, item]));
  const evidenceById = new Map(documentValue.evidence.map((item) => [item.evidence_id, item]));
  const n1 = gatesById.get('04.5N-1');
  const n2 = gatesById.get('04.5N-2');
  if (n1 && n2) {
    if (n2.status === 'NOT_APPROVED') {
      if (!(n2.blocking_conditions ?? []).some((message) => message.includes('N1 PASS'))) {
        errors.push('04.5N-2 must explicitly state that N1 PASS does not authorize N2');
      }
    } else {
      if (n1.status !== 'COMPLETED' || n1.outcome !== 'PASS') {
        errors.push('04.5N-2 cannot progress before a completed N1 PASS');
      }
      const hasAuthorization = (n2.evidence_ids ?? []).some((evidenceId) => {
        const item = evidenceById.get(evidenceId);
        return item?.type === 'AUTHORIZATION'
          && ['REPOSITORY_VERIFIED', 'ARTIFACT_VERIFIED'].includes(item.verification_status);
      });
      if (!hasAuthorization) errors.push('04.5N-2 progression requires verified authorization evidence');
    }
  }

  return errors;
}

export function validateHistoryDocument(documentValue, statusDocument) {
  const errors = [];
  if (!isObject(documentValue)) return ['project_history root must be an object'];
  if (documentValue.schema_version !== '1.0') errors.push('unsupported project_history schema_version');
  requireString(errors, documentValue.snapshot_id, 'history snapshot_id');
  if (!Array.isArray(documentValue.events)) errors.push('events must be an array');
  if (errors.length > 0) return errors;

  const phaseIds = new Set((statusDocument?.phases ?? []).map((item) => item.phase_id));
  const gateIds = new Set((statusDocument?.gates ?? []).map((item) => item.gate_id));
  const evidenceIds = new Set((statusDocument?.evidence ?? []).map((item) => item.evidence_id));
  const eventIds = documentValue.events.map((item) => item?.event_id);
  for (const value of duplicateValues(eventIds)) errors.push(`duplicate event_id: ${value}`);

  let previousRecordedAt = '';
  const seenEvents = new Set();
  for (const event of documentValue.events) {
    if (!isObject(event)) {
      errors.push('history event must be an object');
      continue;
    }
    if (!phaseIds.has(event.phase_id)) errors.push(`history event ${event.event_id} references unknown phase_id: ${event.phase_id}`);
    if (!gateIds.has(event.gate_id)) errors.push(`history event ${event.event_id} references unknown gate_id: ${event.gate_id}`);
    for (const evidenceId of event.evidence_ids ?? []) {
      if (!evidenceIds.has(evidenceId)) errors.push(`history event ${event.event_id} references unknown evidence_id: ${evidenceId}`);
    }
    if (previousRecordedAt && event.recorded_at_utc < previousRecordedAt) errors.push('history events are not ordered by recorded_at_utc');
    previousRecordedAt = event.recorded_at_utc;
    if (event.corrects_event_id && !seenEvents.has(event.corrects_event_id)) {
      errors.push(`history correction ${event.event_id} references missing or future event: ${event.corrects_event_id}`);
    }
    seenEvents.add(event.event_id);
  }
  return errors;
}

export function computeHardGateSummary(safetyGates) {
  if (!Array.isArray(safetyGates) || safetyGates.length === 0) {
    return { level: 'blocked', label: 'HARD GATE NOT CLEAR', detail: '缺少安全硬閘資料' };
  }
  const unsafe = safetyGates.find((item) => item.status === 'BLOCKED' || item.status === 'CONFLICT' || item.value !== item.expected_safe_value);
  if (unsafe) {
    return { level: 'blocked', label: 'HARD GATE BLOCKED', detail: `${unsafe.key}=${unsafe.value}` };
  }
  const uncertain = safetyGates.find((item) => item.status !== 'CLEAR' || !['REPOSITORY_VERIFIED', 'ARTIFACT_VERIFIED', 'WORKTREE_VERIFIED'].includes(item.trust_level));
  if (uncertain) {
    return { level: 'caution', label: 'HARD GATE NOT CLEAR', detail: `${uncertain.key} 尚未達 verified clear` };
  }
  return { level: 'clear', label: 'HARD GATE CLEAR', detail: '全部安全值均有已驗證證據' };
}

export function filterGateRecords(gates, phasesById, query, statusFilter) {
  const normalized = String(query ?? '').trim().toLocaleLowerCase('zh-Hant');
  return gates.filter((gate) => {
    if (statusFilter && statusFilter !== 'ALL' && gate.status !== statusFilter) return false;
    if (!normalized) return true;
    const phase = phasesById.get(gate.phase_id);
    const haystack = [
      gate.gate_id,
      gate.title,
      gate.classification,
      gate.git_checkpoint,
      gate.status,
      gate.outcome,
      ...(gate.evidence_ids ?? []),
      phase?.phase_id,
      phase?.title,
      phase?.summary,
    ].filter(Boolean).join(' ').toLocaleLowerCase('zh-Hant');
    return haystack.includes(normalized);
  });
}

export function formatTaipeiTimestamp(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat('zh-TW', {
    timeZone: 'Asia/Taipei',
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
    hour12: false,
  }).format(date);
}

function element(tagName, className, text) {
  const node = document.createElement(tagName);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function clearNode(node) {
  node.replaceChildren();
}

function toneForStatus(status) {
  if (['COMPLETED', 'PASS'].includes(status)) return 'success';
  if (['BLOCKED', 'FAIL', 'NOT_APPROVED'].includes(status)) return 'danger';
  if (['IN_PROGRESS', 'READY', 'PENDING_EXECUTION'].includes(status)) return 'accent';
  if (['PENDING_REVIEW', 'UNKNOWN'].includes(status)) return 'warning';
  return 'neutral';
}

function badge(text, tone = 'neutral') {
  const node = element('span', 'badge', text);
  node.dataset.tone = tone;
  return node;
}

function progressNode(value, label) {
  const wrapper = element('div');
  const track = element('div', 'progress-track');
  track.setAttribute('role', 'progressbar');
  track.setAttribute('aria-label', label);
  track.setAttribute('aria-valuemin', '0');
  track.setAttribute('aria-valuemax', '100');
  track.setAttribute('aria-valuenow', String(Math.round(value)));
  const fill = element('div', 'progress-fill');
  fill.style.width = `${Math.max(0, Math.min(100, value))}%`;
  track.append(fill);
  wrapper.append(track);
  return wrapper;
}

function appendKeyValue(parent, label, value, className = '') {
  const block = element('div', `context-block ${className}`.trim());
  block.append(element('h3', '', label), element('p', '', value ?? '—'));
  parent.append(block);
}

function renderOverview(statusDocument) {
  const container = document.getElementById('overview-grid');
  clearNode(container);
  const hardGate = computeHardGateSummary(statusDocument.safety_gates);
  const cards = [
    ['治理里程碑完成度', `${statusDocument.project.overall_progress.toFixed(1)}%`, statusDocument.project.progress_label, 'accent'],
    ['目前技術 Phase', statusDocument.current_focus.technical_phase, statusDocument.current_focus.formal_status, toneForStatus(statusDocument.current_focus.formal_status)],
    ['目前 Gate', statusDocument.current_focus.technical_gate, `Candidate: ${STATUS_LABELS[statusDocument.current_focus.candidate_status] ?? statusDocument.current_focus.candidate_status}`, 'accent'],
    ['Formal checkpoint', statusDocument.repository.remote_head?.slice(0, 12) ?? 'unknown', statusDocument.repository.checkpoint_subject, 'neutral'],
    ['安全硬閘', hardGate.label, hardGate.detail, hardGate.level === 'clear' ? 'success' : hardGate.level === 'blocked' ? 'danger' : 'warning'],
  ];
  for (const [label, value, detail, tone] of cards) {
    const card = element('article', 'overview-card');
    card.append(element('span', 'overview-label', label), element('strong', 'overview-value', value), badge(detail, tone));
    if (label === '治理里程碑完成度') card.append(progressNode(statusDocument.project.overall_progress, label));
    container.append(card);
  }
}

function renderPhaseNavigation(statusDocument) {
  const container = document.getElementById('phase-navigation');
  clearNode(container);
  for (const phase of statusDocument.phases) {
    const button = element('button', 'phase-button');
    button.type = 'button';
    if (state.selectedPhase === phase.phase_id) button.classList.add('is-active');
    button.setAttribute('aria-pressed', String(state.selectedPhase === phase.phase_id));
    button.append(element('span', 'phase-name', phase.title), badge(STATUS_LABELS[phase.status] ?? phase.status, toneForStatus(phase.status)), element('span', 'phase-progress', `${phase.progress.toFixed(1)}%`));
    button.append(progressNode(phase.progress, `${phase.title} 進度`));
    button.addEventListener('click', () => {
      state.selectedPhase = state.selectedPhase === phase.phase_id ? 'ALL' : phase.phase_id;
      renderAll();
    });
    container.append(button);
  }
}

function testCountLabel(testCount) {
  if (!testCount) return '—';
  return `${testCount.passed}/${testCount.total} · ${TRUST_LABELS[testCount.trust_level] ?? testCount.trust_level}`;
}

function renderGateCard(gate, phase) {
  const card = element('article', 'gate-card');
  card.id = `gate-${gate.gate_id.replaceAll('.', '-')}`;
  const header = element('div', 'gate-header');
  const titleBlock = element('div');
  titleBlock.append(element('div', 'gate-id', `${gate.gate_id} · ${phase.title}`), element('h3', '', gate.title));
  header.append(titleBlock, badge(STATUS_LABELS[gate.status] ?? gate.status, toneForStatus(gate.status)));
  card.append(header);
  if (gate.classification) card.append(element('div', 'gate-classification mono', gate.classification));
  card.append(progressNode(gate.progress, `${gate.gate_id} Gate 進度`));

  const metrics = element('dl', 'gate-grid');
  const values = [
    ['Outcome', gate.outcome],
    ['Trust', TRUST_LABELS[gate.trust_level] ?? gate.trust_level],
    ['Git checkpoint', gate.git_checkpoint ? gate.git_checkpoint.slice(0, 12) : '—'],
    ['Focused tests', testCountLabel(gate.test_summary.focused)],
    ['Regression tests', testCountLabel(gate.test_summary.regression)],
    ['Evidence', gate.evidence_ids.length ? gate.evidence_ids.join(', ') : '—'],
  ];
  for (const [label, value] of values) {
    const metric = element('div', 'metric');
    metric.append(element('dt', '', label), element('dd', '', value));
    metrics.append(metric);
  }
  card.append(metrics);

  const notes = element('div', 'gate-notes');
  if (gate.authorized_actions.length) notes.append(element('div', '', `允許：${gate.authorized_actions.join('；')}`));
  if (gate.prohibited_actions.length) notes.append(element('div', '', `禁止：${gate.prohibited_actions.join('；')}`));
  if (gate.blocking_conditions.length) notes.append(element('div', '', `阻塞：${gate.blocking_conditions.join('；')}`));
  if (notes.childElementCount) card.append(notes);
  return card;
}

function renderGates(statusDocument) {
  const container = document.getElementById('gate-list');
  clearNode(container);
  const phasesById = new Map(statusDocument.phases.map((phase) => [phase.phase_id, phase]));
  let gates = filterGateRecords(statusDocument.gates, phasesById, state.query, state.statusFilter);
  if (state.selectedPhase !== 'ALL') gates = gates.filter((gate) => gate.phase_id === state.selectedPhase);
  document.getElementById('gate-count').textContent = `${gates.length} 筆`;
  if (!gates.length) {
    container.append(element('div', 'empty-state', '沒有符合目前搜尋與篩選條件的 Gate。'));
    return;
  }
  for (const gate of gates) container.append(renderGateCard(gate, phasesById.get(gate.phase_id)));
}

function renderCurrentFocus(statusDocument) {
  const panel = document.getElementById('current-focus');
  const heading = panel.querySelector('.panel-heading');
  panel.replaceChildren(heading);
  const body = element('div', 'context-body');
  body.append(badge(STATUS_LABELS[statusDocument.current_focus.candidate_status] ?? statusDocument.current_focus.candidate_status, toneForStatus(statusDocument.current_focus.candidate_status)));
  appendKeyValue(body, '目前工作', statusDocument.current_focus.current_work_summary);
  appendKeyValue(body, '下一個允許動作', statusDocument.current_focus.next_authorized_action);
  const prohibited = element('div', 'context-block');
  prohibited.append(element('h3', '', '禁止動作'));
  const list = element('ul', 'compact-list');
  for (const item of statusDocument.current_focus.prohibited_actions) list.append(element('li', '', item));
  prohibited.append(list);
  body.append(prohibited);
  const blocks = element('div', 'context-block');
  blocks.append(element('h3', '', 'Blocking conditions'));
  const blockList = element('ul', 'compact-list');
  for (const item of statusDocument.current_focus.blocking_conditions) blockList.append(element('li', '', item));
  blocks.append(blockList);
  body.append(blocks);
  panel.append(body);
}

function renderSafety(statusDocument) {
  const panel = document.getElementById('safety-panel');
  const heading = panel.querySelector('.panel-heading');
  panel.replaceChildren(heading);
  const summary = computeHardGateSummary(statusDocument.safety_gates);
  const body = element('div', 'context-body');
  body.append(badge(summary.label, summary.level === 'clear' ? 'success' : summary.level === 'blocked' ? 'danger' : 'warning'));
  body.append(element('p', 'overview-detail', summary.detail));
  const grid = element('div', 'safety-grid');
  for (const item of statusDocument.safety_gates) {
    const row = element('div', 'safety-item');
    row.append(element('span', 'safety-key mono', item.key), badge(item.status, item.status === 'CLEAR' ? 'success' : item.status === 'BLOCKED' ? 'danger' : 'warning'), element('strong', 'safety-value', item.value), element('span', 'safety-trust', TRUST_LABELS[item.trust_level] ?? item.trust_level));
    grid.append(row);
  }
  body.append(grid);
  panel.append(body);
}

function renderGit(statusDocument) {
  const panel = document.getElementById('git-panel');
  const heading = panel.querySelector('.panel-heading');
  panel.replaceChildren(heading);
  const body = element('div', 'context-body');
  appendKeyValue(body, 'Repository', statusDocument.repository.repository_name);
  appendKeyValue(body, 'Branch', statusDocument.repository.branch);
  appendKeyValue(body, 'Local / origin / remote', [statusDocument.repository.local_head, statusDocument.repository.origin_main, statusDocument.repository.remote_head].map((value) => value?.slice(0, 12) ?? 'unknown').join(' / '));
  appendKeyValue(body, 'Production status', statusDocument.repository.production_worktree_status.join('\n') || 'clean');
  appendKeyValue(body, 'Alignment', `${statusDocument.state_alignment.value} — ${statusDocument.state_alignment.summary}`);
  for (const worktree of statusDocument.repository.candidate_worktrees) {
    const block = element('div', 'context-block');
    block.append(element('h3', '', worktree.worktree_id), element('p', 'mono', worktree.path ?? '尚未建立'), element('p', '', `${worktree.branch ?? '—'} · ${worktree.head?.slice(0, 12) ?? '—'}`), badge(TRUST_LABELS[worktree.trust_level] ?? worktree.trust_level, toneForStatus(worktree.implementation_committed ? 'COMPLETED' : 'IN_PROGRESS')));
    body.append(block);
  }
  panel.append(body);
}

function renderEvidence(statusDocument) {
  const body = document.getElementById('evidence-table-body');
  clearNode(body);
  for (const item of statusDocument.evidence) {
    const row = document.createElement('tr');
    const cells = [
      `${item.evidence_id}\n${item.type}`,
      item.classification ?? '—',
      TRUST_LABELS[item.verification_status] ?? item.verification_status,
      item.path ?? item.filename ?? '—',
      item.sha256 ?? '—',
      item.commit_policy,
    ];
    cells.forEach((value, index) => {
      const cell = element('td', index === 4 ? 'hash' : '', value);
      row.append(cell);
    });
    body.append(row);
  }
}

function renderHistory(historyDocument) {
  const container = document.getElementById('history-timeline');
  clearNode(container);
  const reversed = [...historyDocument.events].reverse();
  for (const event of reversed) {
    const item = element('article', 'timeline-item');
    const meta = element('div', 'timeline-meta');
    meta.append(element('span', '', formatTaipeiTimestamp(event.occurred_at_utc)), badge(event.gate_id, 'accent'), badge(TRUST_LABELS[event.trust_level] ?? event.trust_level, toneForStatus(event.status)));
    item.append(meta, element('h3', '', event.classification ?? event.event_type), element('p', '', event.summary));
    container.append(item);
  }
}

function renderWarnings(statusDocument) {
  const container = document.getElementById('warning-list');
  clearNode(container);
  if (!statusDocument.warnings.length) {
    container.append(element('div', 'empty-state', '目前沒有來源警告。'));
    return;
  }
  for (const warning of statusDocument.warnings) {
    const card = element('article', 'warning-card');
    card.append(badge(warning.severity, warning.severity === 'CRITICAL' ? 'danger' : warning.severity === 'WARNING' ? 'warning' : 'accent'), element('h3', '', warning.title), element('p', '', warning.message));
    container.append(card);
  }
}

function renderAll() {
  if (!state.statusDocument || !state.historyDocument || typeof document === 'undefined') return;
  const scrollPosition = window.scrollY;
  document.getElementById('project-subtitle').textContent = `${state.statusDocument.project.display_name} · ${state.statusDocument.state_alignment.value}`;
  document.getElementById('snapshot-meta').textContent = `Snapshot ${state.statusDocument.snapshot_id.slice(0, 18)}… · ${formatTaipeiTimestamp(state.statusDocument.generated_at_utc)}`;
  renderOverview(state.statusDocument);
  renderPhaseNavigation(state.statusDocument);
  renderGates(state.statusDocument);
  renderCurrentFocus(state.statusDocument);
  renderSafety(state.statusDocument);
  renderGit(state.statusDocument);
  renderEvidence(state.statusDocument);
  renderHistory(state.historyDocument);
  renderWarnings(state.statusDocument);
  document.documentElement.dataset.dashboardReady = 'true';
  window.requestAnimationFrame(() => window.scrollTo({ top: scrollPosition, behavior: 'instant' }));
}

async function fetchJson(path) {
  const response = await fetch(`${path}?cacheBust=${Date.now()}`, { cache: 'no-store', headers: { Accept: 'application/json' } });
  if (!response.ok) throw new Error(`${path} HTTP ${response.status}`);
  return response.json();
}

function updateStatusMessage(message, level = 'info') {
  const node = document.getElementById('status-message');
  node.textContent = message;
  node.dataset.level = level;
}

function scheduleRefresh() {
  if (SMOKE_MODE) return;
  if (state.refreshTimer) window.clearTimeout(state.refreshTimer);
  state.refreshTimer = window.setTimeout(() => refreshData(false), state.refreshDelay);
}

async function refreshData(manual = false) {
  if (state.loading) return;
  state.loading = true;
  if (manual) updateStatusMessage('正在重新整理…');
  try {
    const [statusDocument, historyDocument] = await Promise.all([fetchJson(STATUS_PATH), fetchJson(HISTORY_PATH)]);
    const statusErrors = validateStatusDocument(statusDocument);
    const historyErrors = validateHistoryDocument(historyDocument, statusDocument);
    const errors = [...statusErrors, ...historyErrors];
    if (errors.length) throw new Error(errors.slice(0, 8).join('；'));

    const changed = statusDocument.snapshot_id !== state.statusDocument?.snapshot_id || historyDocument.snapshot_id !== state.historyDocument?.snapshot_id;
    state.statusDocument = statusDocument;
    state.historyDocument = historyDocument;
    state.lastSuccessfulRefresh = new Date();
    state.refreshDelay = BASE_REFRESH_MS;
    if (changed || manual) renderAll();
    updateStatusMessage(`資料有效 · 上次成功更新 ${formatTaipeiTimestamp(state.lastSuccessfulRefresh.toISOString())} · 每 10 秒自動檢查`, 'ok');
  } catch (error) {
    state.refreshDelay = Math.min(MAX_REFRESH_MS, Math.max(BASE_REFRESH_MS, state.refreshDelay * 2));
    const retained = state.statusDocument && state.historyDocument ? '；保留最後一份有效 snapshot' : '';
    updateStatusMessage(`更新失敗：${error instanceof Error ? error.message : String(error)}${retained}；${Math.round(state.refreshDelay / 1000)} 秒後重試`, 'error');
  } finally {
    state.loading = false;
    scheduleRefresh();
  }
}

function initializeControls() {
  const search = document.getElementById('search-input');
  search.addEventListener('input', () => {
    state.query = search.value;
    renderGates(state.statusDocument);
  });
  document.getElementById('manual-refresh').addEventListener('click', () => refreshData(true));
  document.getElementById('filter-controls').addEventListener('click', (event) => {
    const button = event.target.closest('button[data-status]');
    if (!button) return;
    state.statusFilter = button.dataset.status;
    for (const item of document.querySelectorAll('#filter-controls button')) item.setAttribute('aria-pressed', String(item === button));
    renderGates(state.statusDocument);
  });
}

function bootstrap() {
  initializeControls();
  refreshData(true);
}

if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bootstrap, { once: true });
  else bootstrap();
}
