import test from 'node:test';
import assert from 'node:assert/strict';

import { readFile } from 'node:fs/promises';

const modulePath = new URL('../../docs/00_project_management/project_dashboard/assets/dashboard.js', import.meta.url);
const moduleSource = await readFile(modulePath, 'utf8');
const moduleUrl = `data:text/javascript;base64,${Buffer.from(moduleSource).toString('base64')}`;
const {
  computeHardGateSummary,
  filterGateRecords,
  validateHistoryDocument,
  validateStatusDocument,
} = await import(moduleUrl);

function sourceRef() {
  return [{ type: 'repository_file', path: 'PROJECT_STATUS.md', ref: 'abc', section: 'current' }];
}

function minimalStatus() {
  return {
    schema_version: '1.0',
    snapshot_id: `sha256:${'a'.repeat(64)}`,
    generated_at_utc: '2026-07-15T00:00:00Z',
    display_timezone: 'Asia/Taipei',
    project: { name: 'FleetVision', display_name: 'FleetVision', dashboard_kind: 'governance', progress_label: '治理里程碑完成度' },
    repository: { repository_name: 'FleetVision', repository_root: 'G:/Project/FleetVision', branch: 'main', local_head: 'a', origin_main: 'a', remote_head: 'a', checkpoint_subject: 'x', production_worktree_status: ['?? outputs/metadata/external_assets/'], allowed_untracked_paths: ['outputs/metadata/external_assets/'], candidate_worktrees: [], verification_level: 'REPOSITORY_VERIFIED', verified_at_utc: '2026-07-15T00:00:00Z' },
    state_alignment: { value: 'SYNCED', summary: 'ok', trust_level: 'REPOSITORY_VERIFIED' },
    current_focus: { technical_phase: 'P', technical_gate: 'G', formal_status: 'COMPLETED', candidate_status: 'READY', current_work_summary: 'x', next_authorized_action: 'y', prohibited_actions: [], blocking_conditions: [] },
    safety_gates: [
      'TEST_SPLIT_READ', 'MODEL_INFERENCE_EXECUTED', 'CANONICAL_ANNOTATION_MODIFIED',
      'CANONICAL_COCO_MODIFIED', 'DATASET_MODIFIED', 'REGISTRY_MODIFIED',
      'FIXED_SPLITS_MODIFIED', 'TRAINING_STARTED', 'RETRAINING_STATUS',
      'DEPLOYMENT_ACCEPTANCE',
    ].map((key) => ({ key, value: 'NO', expected_safe_value: 'NO', status: 'CLEAR', trust_level: 'REPOSITORY_VERIFIED' })),
    phases: [{ phase_id: 'P', title: 'Phase', status: 'COMPLETED', progress: 100, weight: 1, gate_ids: ['G'], summary: 'x', source_refs: sourceRef() }],
    gates: [{ gate_id: 'G', phase_id: 'P', title: 'Gate', status: 'COMPLETED', outcome: 'PASS', classification: 'DONE', progress: 100, weight: 1, trust_level: 'REPOSITORY_VERIFIED', test_summary: { focused: null, regression: null, full: null, skipped: 0, failed: 0 }, evidence_ids: [], git_checkpoint: null, authorized_actions: [], prohibited_actions: [], blocking_conditions: [], source_refs: sourceRef() }],
    evidence: [],
    warnings: [],
  };
}

test('status structural validation accepts a complete minimal document', () => {
  assert.deepEqual(validateStatusDocument(minimalStatus()), []);
});

test('status structural validation rejects duplicate gates', () => {
  const status = minimalStatus();
  status.gates.push({ ...status.gates[0] });
  assert.ok(validateStatusDocument(status).some((message) => message.includes('duplicate gate_id')));
});

test('hard gate is clear only for verified safe values', () => {
  const clear = computeHardGateSummary([
    { key: 'A', value: 'NO', expected_safe_value: 'NO', status: 'CLEAR', trust_level: 'ARTIFACT_VERIFIED' },
  ]);
  assert.equal(clear.level, 'clear');

  const reported = computeHardGateSummary([
    { key: 'A', value: 'NO', expected_safe_value: 'NO', status: 'SAFE_REPORTED', trust_level: 'OPERATOR_REPORTED' },
  ]);
  assert.equal(reported.level, 'caution');

  const blocked = computeHardGateSummary([
    { key: 'A', value: 'YES', expected_safe_value: 'NO', status: 'BLOCKED', trust_level: 'ARTIFACT_VERIFIED' },
  ]);
  assert.equal(blocked.level, 'blocked');
});

test('gate filtering matches classification and status', () => {
  const status = minimalStatus();
  const phases = new Map(status.phases.map((phase) => [phase.phase_id, phase]));
  assert.equal(filterGateRecords(status.gates, phases, 'done', 'ALL').length, 1);
  assert.equal(filterGateRecords(status.gates, phases, '', 'COMPLETED').length, 1);
  assert.equal(filterGateRecords(status.gates, phases, '', 'BLOCKED').length, 0);
});

test('history validation rejects unknown gates', () => {
  const status = minimalStatus();
  const history = {
    schema_version: '1.0',
    snapshot_id: `sha256:${'b'.repeat(64)}`,
    generated_at_utc: '2026-07-15T00:00:00Z',
    events: [{
      event_id: 'E1', occurred_at_utc: '2026-07-15T00:00:00Z', recorded_at_utc: '2026-07-15T00:00:00Z', phase_id: 'P', gate_id: 'UNKNOWN', event_type: 'GATE_COMPLETED', status: 'COMPLETED', outcome: 'PASS', classification: 'X', summary: 'x', git_checkpoint: null, test_summary: { focused: null, regression: null, full: null, skipped: 0, failed: 0 }, evidence_ids: [], safety_snapshot: {}, trust_level: 'REPOSITORY_VERIFIED', source_refs: sourceRef(), corrects_event_id: null,
    }],
  };
  assert.ok(validateHistoryDocument(history, status).some((message) => message.includes('unknown gate_id')));
});

test('runtime validation rejects N2 progression without N1 PASS and authorization evidence', async () => {
  const statusPath = new URL('../../docs/00_project_management/project_dashboard/data/project_status.json', import.meta.url);
  const status = JSON.parse(await readFile(statusPath, 'utf8'));
  const n2 = status.gates.find((gate) => gate.gate_id === '04.5N-2');
  n2.status = 'READY';
  n2.blocking_conditions = ['Fresh pre-promotion verification remains required.'];
  assert.ok(validateStatusDocument(status).some((message) => message.includes('authorization evidence')));
});
