#!/usr/bin/env node
// Inventory the campaign against its dated baseline. No provider calls or credentials.
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { readFile, mkdir, rename, writeFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync, gunzipSync } from 'node:zlib';
import { BEND_PARSER_PROFILE } from './perch-bend.mjs';
import { assessStyle, changedStyleSources, inventoryScope, loadPatternSheet, prepareStyleInventory } from './perch-style.mjs';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BASELINE = 'docs/perch-calibration/style-project-2026-09-26.json.gz';
const sha256 = value => createHash('sha256').update(value).digest('hex');
const group = path => path.startsWith('packages/') ? path.split('/').slice(0, 2).join('/') : path.split('/')[0];

export function compareStyleBaseline(candidates, inventory, baseline, config, identity) {
  if (baseline.schema !== 2 || baseline.command !== 'style-rank' || baseline.failure
      || !Array.isArray(baseline.rows) || baseline.rows.length === 0) {
    throw new Error('Campaign requires a completed nonempty style baseline, with any unranked files retained');
  }
  const compatible = baseline.rubric_sha256 === identity.rubric_sha256 && baseline.parser === identity.parser;
  const prior = new Map(baseline.rows.map(row => [row.target, row]));
  // Preserve historical classifications if the rubric changed; never reinterpret old answers.
  const axes = new Map();
  for (const a of baseline.assessments ?? []) {
    if (!axes.has(a.target)) axes.set(a.target, {});
    axes.get(a.target)[a.dimension] = { status: a.status, probability_at_target: a.probability_at_target };
  }
  const units = candidates.map(unit => {
    const old = prior.get(unit.target);
    const matches = old && compatible && old.source_sha256 === unit.source_sha256
      && old.state_sha256 === unit.state_sha256 && JSON.stringify(old.context) === JSON.stringify(unit.context);
    const matchedAxes = matches ? assessStyle([old], config) : [];
    const meetsDeclaration = matchedAxes.length >= config.dimensions.length && matchedAxes.every(a => a.status === 'meets_target');
    // A per-declaration inventory cannot establish the separate v4 task and
    // composition requirement. Keep this historical view conservative.
    const meetsRequired = meetsDeclaration && !config.potential_profundity;
    return {
      target: unit.target, kind: unit.kind, line: unit.line,
      scope: inventoryScope(unit.target.split('::')[0], config).id,
      source_sha256: unit.source_sha256, state_sha256: unit.state_sha256,
      baseline_status: !old ? 'unrated' : matches ? 'matches' : 'stale',
      baseline_axes: axes.get(unit.target) ?? null,
      baseline_context_truncated: old?.context?.truncated ?? null,
      current_context_truncated: unit.context?.truncated ?? false,
      matches_declaration_baseline_targets: meetsDeclaration,
      run_requirements_status: config.potential_profundity ? 'requires_task_and_composition_review' : 'declaration_targets_only',
      matches_all_required_baseline_targets: meetsRequired,
      // Keep the legacy field conservative for older inventory consumers.
      matches_all_three_baseline_targets: meetsRequired,
    };
  });
  const active = new Set(candidates.map(unit => unit.target));
  const notCurrentlyParsed = baseline.rows.filter(row => !active.has(row.target)).map(row => row.target);
  const components = [...new Set(units.map(unit => group(unit.target.split('::')[0])))].sort().map(component => {
    const selected = units.filter(unit => group(unit.target.split('::')[0]) === component);
    return { component, declarations: selected.length,
      ...Object.fromEntries(['matches', 'stale', 'unrated'].map(status => [status, selected.filter(u => u.baseline_status === status).length])),
      truncated_context: selected.filter(u => u.current_context_truncated).length,
      matches_all_required_baseline_targets: selected.filter(u => u.matches_all_required_baseline_targets).length,
      matches_all_three_baseline_targets: selected.filter(u => u.matches_all_three_baseline_targets).length };
  });
  const scopes = (config.inventory_scopes ?? []).map(scope => ({ id: scope.id, gate: scope.gate,
    declarations: units.filter(u => u.scope === scope.id).length,
    matches_all_required_baseline_targets: units.filter(u => u.scope === scope.id && u.matches_all_required_baseline_targets).length }));
  return { compatible_rubric_and_parser: compatible,
    scopes,
    baseline_requested_model: baseline.requested_model,
    baseline_resolved_models: [...new Set(baseline.rows.map(row => row.model))],
    summary: { discovered_files: inventory.discovered_files.length, parsed_units: units.length,
      ...Object.fromEntries(['matches', 'stale', 'unrated'].map(status => [status, units.filter(u => u.baseline_status === status).length])),
      unranked_files: inventory.unranked.length, empty_files: inventory.empty_files.length,
      no_longer_parsed_targets: notCurrentlyParsed.length,
      matches_all_required_baseline_targets: units.filter(u => u.matches_all_required_baseline_targets).length,
      matches_all_three_baseline_targets: units.filter(u => u.matches_all_three_baseline_targets).length },
    components, inventory, no_longer_parsed_targets: notCurrentlyParsed, units };
}

export async function buildCampaignInventory(root = ROOT) {
  const baselineBytes = await readFile(resolve(root, BASELINE));
  const baseline = JSON.parse(gunzipSync(baselineBytes));
  const rubricText = await readFile(resolve(root, 'perch-style.json'), 'utf8');
  const config = JSON.parse(rubricText);
  const headBefore = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
  const sheet = await loadPatternSheet(config, root);
  const { candidates, inventory } = await prepareStyleInventory(baseline.cohort, config, root, null, { sheet });
  const changed = await changedStyleSources(candidates, root);
  return { schema: 1, at: new Date().toISOString(), baseline: BASELINE,
    baseline_sha256: sha256(baselineBytes), baseline_at: baseline.at,
    git_head_before_inventory: headBefore,
    git_head_after_inventory: execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim(),
    source_basis: 'working-tree', source_freshness: { status: changed.length ? 'changed-during-inventory' : 'matched-at-inventory', changed_sources: changed },
    rubric_sha256: sha256(rubricText), parser: BEND_PARSER_PROFILE,
    pattern_sheet: sheet ? { path: sheet.path, sha256: sheet.sha256, bytes: sheet.bytes } : null,
    provider_requests: 0, typechecked: false, behavioral_equivalence_checked: false,
    note: 'Dated baseline comparison only. Matching means source, request state, context, parser and rubric match; it is not fresh provider evidence, human acceptance or completion. Batch receipts remain separate. Historical axes stay historical when stale. Unranked and missing declarations remain visible.',
    ...compareStyleBaseline(candidates, inventory, baseline, config, { rubric_sha256: sha256(rubricText), parser: BEND_PARSER_PROFILE }) };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try {
    const args = process.argv.slice(2);
    if (args.length > 1 || args.some(arg => !arg.startsWith('--output=') || !arg.slice(9))) {
      throw new Error('Usage: node scripts/perch-style-campaign.mjs [--output=path.json]');
    }
    const report = await buildCampaignInventory();
    if (args.length) {
      const output = resolve(ROOT, args[0].slice(9));
      await mkdir(dirname(output), { recursive: true });
      const temporary = `${output}.tmp-${process.pid}`;
      const encoded = JSON.stringify(report, null, 2) + '\n';
      await writeFile(temporary, output.endsWith('.gz') ? gzipSync(encoded) : encoded);
      await rename(temporary, output);
      console.log(JSON.stringify({ output, ...report.summary, source_freshness: report.source_freshness }));
    } else console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    console.error(`Campaign inventory failed: ${error.message}`);
    process.exitCode = 1;
  }
}
