#!/usr/bin/env node
/**
 * CLI: report spell-simulator glyph telemetry to Asana.
 *
 * Server/CLI-only. Reads credentials from environment variables (see
 * docs/asana-connector.md). Never accepts a token as a command-line argument
 * (argv is visible in process listings).
 *
 * Usage:
 *   ASANA_ACCESS_TOKEN=... ASANA_PROJECT_SPELLSIM=... ASANA_REPORTING_ENABLED=1 \
 *     node tools/asanaReport.js --input samples.json --milestone "Sprint 3"
 *
 * The --input file is a JSON array of { spellIR, glyphAST } sample objects. If
 * omitted, samples are read from stdin. Use --verify to only check credentials.
 */

import { readFileSync } from 'node:fs';
import { loadAsanaConfig, describeAsanaConfig } from '../src/reporting/asanaConfig.js';
import { AsanaReporter } from '../src/reporting/asanaReporter.js';
import { aggregateMetrics, formatMetricsComment } from '../src/reporting/asanaMetrics.js';

function parseArgs(argv) {
  const args = {
    milestone: '', input: null, verify: false, dryRun: false,
  };
  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--verify') {
      args.verify = true;
    } else if (arg === '--dry-run') {
      args.dryRun = true;
    } else if (arg === '--milestone') {
      args.milestone = argv[i + 1] ?? '';
      i += 1;
    } else if (arg === '--input') {
      args.input = argv[i + 1] ?? null;
      i += 1;
    }
  }
  return args;
}

function readSamples(inputPath) {
  const raw = inputPath
    ? readFileSync(inputPath, 'utf8')
    : readFileSync(0, 'utf8');
  if (!raw.trim()) return [];
  const parsed = JSON.parse(raw);
  return Array.isArray(parsed) ? parsed : [parsed];
}

async function main() {
  const args = parseArgs(process.argv);
  const config = loadAsanaConfig({ ...process.env });

  if (args.verify) {
    const reporter = new AsanaReporter({ config });
    const result = await reporter.verify();
    console.log(JSON.stringify({ config: describeAsanaConfig(config), verify: result }, null, 2));
    process.exitCode = result.ok ? 0 : 1;
    return;
  }

  let samples = [];
  try {
    samples = readSamples(args.input);
  } catch (error) {
    console.error(`Failed to read samples: ${error.message}`);
    process.exitCode = 1;
    return;
  }

  if (args.dryRun || !config.enabled) {
    // Print what would be sent without contacting Asana.
    const metrics = aggregateMetrics(samples);
    const comment = formatMetricsComment(metrics, { milestone: args.milestone });
    console.log(config.enabled ? '[dry-run] would post:\n' : '[disabled] preview only:\n');
    console.log(comment);
    return;
  }

  const reporter = new AsanaReporter({ config });
  const result = await reporter.reportMetrics(samples, { milestone: args.milestone });
  console.log(JSON.stringify(result, null, 2));
  process.exitCode = result.ok || result.skipped ? 0 : 1;
}

main().catch((error) => {
  console.error(`asanaReport failed: ${error.message}`);
  process.exitCode = 1;
});
