// fable5MediaAssets.js
// Merge explicit local asset sources into the Fable 5 catalyst as deduped
// digests. Pure and
// isomorphic: it takes already-hashed file records and never touches the network
// or the filesystem itself — the Node CLI (tools/fable5-media-loop.mjs) does the
// reading + hashing and hands records here. Local-only by construction: any
// remote-looking source is rejected.

import { LOCAL_CONTROLS } from './fable5MediaSpell.js';

const SHA256_RE = /^[a-f0-9]{64}$/i;
const REMOTE_RE = /^[a-z][a-z0-9+.-]*:\/\//i; // http:// https:// ftp:// s3:// ...

const MEDIA_EXT = {
  image: ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp', 'tiff', 'avif'],
  video: ['mp4', 'mov', 'webm', 'mkv', 'avi', 'm4v'],
  audio: ['wav', 'mp3', 'flac', 'm4a', 'aac', 'ogg', 'opus'],
};

/** Classify a filename into image | video | audio | other by extension. */
export function mediaKind(pathOrName = '') {
  const ext = String(pathOrName).split('.').pop().toLowerCase();
  for (const kind of Object.keys(MEDIA_EXT)) {
    if (MEDIA_EXT[kind].includes(ext)) return kind;
  }
  return 'other';
}

/** True only for a local path — rejects http(s)/ftp/etc. `file://` is allowed. */
export function isLocalPath(p = '') {
  const s = String(p);
  if (s.startsWith('file://')) return true;
  return !REMOTE_RE.test(s);
}

/**
 * Merge local asset sources into deduped digests for the catalyst.
 * @param {{sources: Array<{label:string, root:string, files:Array<{path:string,size?:number,sha256:string}>}>}} opts
 * @returns {object} { count, assetDigests, assets, byMedium, bySource, controls }
 */
export function mergeLocalAssetSources({ sources = [] } = {}) {
  if (!Array.isArray(sources)) {
    throw new Error('mergeLocalAssetSources requires a sources array');
  }

  const seen = new Set();
  const assets = [];
  const bySource = {};
  const byMedium = {
    image: 0, video: 0, audio: 0, other: 0,
  };

  for (const source of sources) {
    const label = source && source.label ? String(source.label) : 'unnamed';
    const root = source && source.root ? String(source.root) : '';
    if (!isLocalPath(root)) {
      throw new Error(`source '${label}' root is not a local path: ${root} (local-only)`);
    }
    bySource[label] = 0;
    const files = Array.isArray(source && source.files) ? source.files : [];
    for (const file of files) {
      const sha = file && file.sha256 ? String(file.sha256).toLowerCase() : '';
      if (!SHA256_RE.test(sha)) {
        throw new Error(`asset in '${label}' has an invalid sha256: ${file && file.sha256}`);
      }
      const filePath = file && file.path ? String(file.path) : '';
      if (!isLocalPath(filePath)) {
        throw new Error(`asset '${filePath}' in '${label}' is not local (local-only)`);
      }
      if (seen.has(sha)) continue; // dedupe identical bytes across folders
      seen.add(sha);
      const medium = mediaKind(filePath);
      byMedium[medium] += 1;
      bySource[label] += 1;
      assets.push({
        sha256: sha, medium, size: Number(file.size) || 0, source: label,
      });
    }
  }

  assets.sort((a, b) => a.sha256.localeCompare(b.sha256));
  return {
    count: assets.length,
    assetDigests: assets.map((a) => a.sha256),
    assets,
    byMedium,
    bySource,
    controls: { ...LOCAL_CONTROLS },
  };
}

/** Digests for a single medium — feed straight into compileFable5MediaSpell. */
export function digestsForMedium(merged, medium) {
  return merged.assets.filter((a) => a.medium === medium).map((a) => a.sha256);
}
