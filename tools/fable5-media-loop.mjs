#!/usr/bin/env node
// fable5-media-loop.mjs
// Local terminal loop for the Black Sun / Fable 5 media catalyst.
//
// Scans your Downloads folder and a local Google-Drive-synced folder, hashes the
// media on-device, merges them into the catalyst, compiles a manifest per medium,
// and writes a local ComfyUI review manifest for each. Nothing is uploaded — only
// file fingerprints (sha256) enter the manifests. No network, ever.
//
//   node tools/fable5-media-loop.mjs               # one pass
//   node tools/fable5-media-loop.mjs --watch 30    # re-scan every 30s (terminal loop)
//
// Folders (override with env vars):
//   FABLE5_DOWNLOADS_DIR   default: ~/Downloads
//   FABLE5_DRIVE_DIR       default: first existing of ~/Google Drive, ~/GoogleDrive,
//                                    ~/Library/CloudStorage/GoogleDrive-*
//   FABLE5_OUT_DIR         default: ./eden-out

import { createHash } from "node:crypto";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { mergeLocalAssetSources, mediaKind } from "../src/compiler/fable5MediaAssets.js";
import { compileFable5MediaSpell } from "../src/compiler/fable5MediaSpell.js";
import { buildComfyUIMediaReview } from "../src/compiler/fable5MediaFeedback.js";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const MAX_FILES = 5000;

function log(msg) { process.stderr.write(msg + "\n"); }

function firstExisting(paths) {
  for (const p of paths) { try { if (fs.statSync(p).isDirectory()) return p; } catch { /* skip */ } }
  return null;
}

function driveDefault() {
  const home = os.homedir();
  const candidates = [
    path.join(home, "Google Drive"),
    path.join(home, "GoogleDrive"),
    path.join(home, "My Drive"),
  ];
  try {
    const cs = path.join(home, "Library", "CloudStorage");
    for (const name of fs.readdirSync(cs)) {
      if (name.startsWith("GoogleDrive-")) candidates.push(path.join(cs, name));
    }
  } catch { /* not macOS / no CloudStorage */ }
  return firstExisting(candidates);
}

function scanMedia(root) {
  if (!root) return [];
  let entries;
  try { entries = fs.readdirSync(root, { recursive: true, withFileTypes: true }); }
  catch (err) { log(`  .. cannot read ${root}: ${err.message}`); return []; }

  const files = [];
  for (const ent of entries) {
    if (files.length >= MAX_FILES) break;
    if (!ent.isFile()) continue;
    const dir = ent.parentPath || ent.path || root;
    const full = path.join(dir, ent.name);
    if (mediaKind(ent.name) === "other") continue;
    try {
      const buf = fs.readFileSync(full);
      files.push({ path: full, size: buf.length, sha256: createHash("sha256").update(buf).digest("hex") });
    } catch { /* unreadable — skip */ }
  }
  return files;
}

function onePass(outDir) {
  const downloads = process.env.FABLE5_DOWNLOADS_DIR || path.join(os.homedir(), "Downloads");
  const drive = process.env.FABLE5_DRIVE_DIR || driveDefault();

  log("\n[black-sun] scanning local folders (nothing is uploaded)");
  log(`  downloads: ${downloads}`);
  log(`  drive    : ${drive || "(none found — set FABLE5_DRIVE_DIR)"}`);

  const sources = [
    { label: "downloads", root: downloads, files: scanMedia(downloads) },
  ];
  if (drive) sources.push({ label: "drive", root: drive, files: scanMedia(drive) });

  const merged = mergeLocalAssetSources({ sources });
  log(`  merged   : ${merged.count} unique assets  (image ${merged.byMedium.image} · video ${merged.byMedium.video} · audio ${merged.byMedium.audio})`);

  fs.mkdirSync(outDir, { recursive: true });
  const written = [];
  for (const medium of ["image", "video", "audio"]) {
    const digests = merged.assets.filter((a) => a.medium === medium).map((a) => a.sha256);
    if (digests.length === 0) continue;
    const manifest = compileFable5MediaSpell({
      spellIR: { element: "light", primaryManifestation: "aura", signature: `light:${medium}:true` },
      medium,
      intent: `Local Fable 5 ${medium} study from Downloads + Drive.`,
      assetDigests: digests,
    });
    const review = buildComfyUIMediaReview({ manifest, workflowId: `fable5.${medium}.review` });
    const file = path.join(outDir, `${medium}.review.json`);
    fs.writeFileSync(file, JSON.stringify({ manifest, review }, null, 2));
    written.push(file);
    log(`  ${medium.padEnd(6)} -> ${path.relative(process.cwd(), file)}  (${digests.length} assets · local review, no endpoint)`);
  }
  if (written.length === 0) log("  .. no media assets found in those folders yet");
  log("[black-sun] pass complete · 0 external requests\n");
  return merged.count;
}

function main() {
  const args = process.argv.slice(2);
  const watchIdx = args.indexOf("--watch");
  const outDir = process.env.FABLE5_OUT_DIR || path.join(process.cwd(), "eden-out");

  if (watchIdx === -1) { onePass(outDir); return; }

  const seconds = Math.max(5, Number(args[watchIdx + 1]) || 30);
  log(`[black-sun] terminal loop every ${seconds}s — Ctrl+C to stop`);
  const tick = () => { try { onePass(outDir); } catch (err) { log(`  XX ${err.message}`); } };
  tick();
  const timer = setInterval(tick, seconds * 1000);
  process.on("SIGINT", () => { clearInterval(timer); log("\n[black-sun] loop halted."); process.exit(0); });
}

main();
