#!/usr/bin/env node
// fable5-media-loop.mjs
// Local terminal loop for the Black Sun / Fable 5 media catalyst.
//
// Scans explicit local media roots, hashes media on-device, merges them into the
// catalyst, compiles a manifest per medium, and writes a local ComfyUI review
// manifest for each. Nothing is uploaded - only file fingerprints (sha256) enter
// the manifests. No network, ever.
//
//   node tools/fable5-media-loop.mjs               # one pass
//   node tools/fable5-media-loop.mjs --watch 30    # re-scan every 30s (terminal loop)
//
// Folders (override with FABLE5_MEDIA_DIRS, separated by the platform path
// delimiter). Defaults match the Jing Power allowlist; Downloads and Drive are
// only scanned when explicitly named with FABLE5_DOWNLOADS_DIR or
// FABLE5_DRIVE_DIR.
//   FABLE5_OUT_DIR         default: ./eden-out

import { createHash } from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { mergeLocalAssetSources, mediaKind } from '../src/compiler/fable5MediaAssets.js';
import { compileFable5MediaSpell } from '../src/compiler/fable5MediaSpell.js';
import { buildComfyUIMediaReview } from '../src/compiler/fable5MediaFeedback.js';

const MAX_FILES = Math.max(
  1,
  Math.min(5000, Number(process.env.FABLE5_MEDIA_MAX_ENTRIES_PER_DIR) || 5000),
);
const MAX_DEPTH = 2;
const DEFAULT_MEDIA_DIRS = [
  path.join(os.homedir(), 'Movies', 'Grok-Videos'),
  path.join(os.homedir(), 'ShadowGarden', 'exports'),
  path.join(os.homedir(), 'ComfyUI', 'output'),
  path.join(os.homedir(), 'Documents', 'ComfyUI', 'output'),
];

function log(msg) { process.stderr.write(`${msg}\n`); }

function scanMedia(root) {
  if (!root) return [];
  const files = [];
  const pending = [{ directory: root, depth: 0 }];
  while (pending.length > 0 && files.length < MAX_FILES) {
    const current = pending.shift();
    let entries;
    try {
      entries = fs.readdirSync(current.directory, { withFileTypes: true });
    } catch (err) {
      log(`  .. cannot read ${current.directory}: ${err.message}`);
      continue;
    }

    for (const ent of entries) {
      if (files.length >= MAX_FILES) break;
      const full = path.join(current.directory, ent.name);
      if (ent.isDirectory() && current.depth < MAX_DEPTH) {
        pending.push({ directory: full, depth: current.depth + 1 });
        continue;
      }
      if (!ent.isFile() || mediaKind(ent.name) === 'other') continue;
      try {
        const buf = fs.readFileSync(full);
        files.push({
          path: full,
          size: buf.length,
          sha256: createHash('sha256').update(buf).digest('hex'),
        });
      } catch { /* unreadable - skip */ }
    }
  }
  return files;
}

function mediaRoots() {
  const configured = process.env.FABLE5_MEDIA_DIRS
    ? process.env.FABLE5_MEDIA_DIRS.split(path.delimiter)
    : [
      process.env.FABLE5_DOWNLOADS_DIR,
      process.env.FABLE5_DRIVE_DIR,
      ...DEFAULT_MEDIA_DIRS,
    ].filter(Boolean);
  return [...new Set(configured.map((root) => path.resolve(root)))];
}

function onePass(outDir) {
  const roots = mediaRoots();

  log('\n[black-sun] scanning allowlisted local folders (nothing is uploaded)');
  log(`  roots    : ${roots.length} (depth <= ${MAX_DEPTH}, files <= ${MAX_FILES}/root)`);

  const sources = roots.map((root, index) => ({
    label: path.basename(root) || `media_${index}`,
    root,
    files: scanMedia(root),
  }));

  const merged = mergeLocalAssetSources({ sources });
  log(`  merged   : ${merged.count} unique assets (image ${merged.byMedium.image}, video ${merged.byMedium.video}, audio ${merged.byMedium.audio})`);

  fs.mkdirSync(outDir, { recursive: true });
  const written = [];
  for (const medium of ['image', 'video', 'audio']) {
    const digests = merged.assets.filter((a) => a.medium === medium).map((a) => a.sha256);
    if (digests.length === 0) continue;
    const manifest = compileFable5MediaSpell({
      spellIR: {
        valid: true,
        active: true,
        element: 'light',
        primaryManifestation: 'aura',
        signature: `light:${medium}:true`,
        quality: 0.8,
        stability: 0.8,
        neatness: 0.8,
        focus: 0.8,
      },
      medium,
      intent: `Local Fable 5 ${medium} study from allowlisted roots.`,
      assetDigests: digests,
    });
    const review = buildComfyUIMediaReview({ manifest, workflowId: `fable5.${medium}.review` });
    const file = path.join(outDir, `${medium}.review.json`);
    fs.writeFileSync(file, JSON.stringify({ manifest, review }, null, 2));
    written.push(file);
    log(`  ${medium.padEnd(6)} -> ${path.relative(process.cwd(), file)} (${digests.length} assets, local review, no endpoint)`);
  }
  if (written.length === 0) log('  .. no media assets found in those folders yet');
  log('[black-sun] pass complete · 0 external requests\n');
  return merged.count;
}

function main() {
  const args = process.argv.slice(2);
  const watchIdx = args.indexOf('--watch');
  const outDir = process.env.FABLE5_OUT_DIR || path.join(process.cwd(), 'eden-out');

  if (watchIdx === -1) { onePass(outDir); return; }

  const seconds = Math.max(5, Number(args[watchIdx + 1]) || 30);
  log(`[black-sun] terminal loop every ${seconds}s - Ctrl+C to stop`);
  const tick = () => { try { onePass(outDir); } catch (err) { log(`  XX ${err.message}`); } };
  tick();
  const timer = setInterval(tick, seconds * 1000);
  process.on('SIGINT', () => { clearInterval(timer); log('\n[black-sun] loop halted.'); process.exit(0); });
}

main();
