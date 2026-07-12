import assert from 'node:assert/strict';
import test from 'node:test';

import {
  mergeLocalAssetSources,
  digestsForMedium,
  mediaKind,
  isLocalPath,
} from '../src/compiler/fable5MediaAssets.js';
import { compileFable5MediaSpell } from '../src/compiler/fable5MediaSpell.js';

const sha = (c) => c.repeat(64);

test('merges Downloads + local Drive folder into deduped local digests', () => {
  const merged = mergeLocalAssetSources({
    sources: [
      {
        label: 'downloads',
        root: '/home/user/Downloads',
        files: [
          { path: '/home/user/Downloads/aura.png', size: 10, sha256: sha('a') },
          { path: '/home/user/Downloads/riff.wav', size: 20, sha256: sha('b') },
        ],
      },
      {
        label: 'drive',
        root: '/home/user/GoogleDrive/fable5',
        files: [
          { path: '/home/user/GoogleDrive/fable5/aura.png', size: 10, sha256: sha('a') }, // dup bytes
          { path: '/home/user/GoogleDrive/fable5/clip.mp4', size: 30, sha256: sha('c') },
        ],
      },
    ],
  });

  assert.equal(merged.count, 3); // 'a' deduped across both folders
  assert.deepEqual(merged.assetDigests, [sha('a'), sha('b'), sha('c')].sort());
  assert.equal(merged.byMedium.image, 1);
  assert.equal(merged.byMedium.audio, 1);
  assert.equal(merged.byMedium.video, 1);
  assert.equal(merged.bySource.downloads, 2);
  assert.equal(merged.bySource.drive, 1); // only the non-dup mp4 counted
  assert.equal(merged.controls.externalRequests, 0);
  assert.equal(merged.controls.remoteWrites, false);

  // digests flow straight into the catalyst
  const manifest = compileFable5MediaSpell({
    spellIR: {
      valid: true,
      active: true,
      element: 'light',
      primaryManifestation: 'aura',
      signature: 'light:image:true',
      quality: 0.8,
      stability: 0.8,
      neatness: 0.8,
      focus: 0.8,
    },
    medium: 'image',
    intent: 'Local asset digest review.',
    assetDigests: digestsForMedium(merged, 'image'),
  });
  assert.equal(manifest.assetDigests.length, 1);
  assert.equal(manifest.controls.approved, false);
  assert.equal(manifest.controls.executionMode, 'manifest_only');
});

test('rejects remote sources and bad digests (local-only boundary)', () => {
  assert.throws(
    () => mergeLocalAssetSources({ sources: [{ label: 'remote', root: 'https://drive.google.com/x', files: [] }] }),
    /local/,
  );
  assert.throws(
    () => mergeLocalAssetSources({
      sources: [{ label: 'downloads', root: '/home/user/Downloads', files: [{ path: '/x.png', sha256: 'nope' }] }],
    }),
    /sha256/,
  );
  assert.throws(
    () => mergeLocalAssetSources({
      sources: [{ label: 'd', root: '/home/user/Downloads', files: [{ path: 'https://x/y.png', sha256: sha('a') }] }],
    }),
    /local/,
  );
});

test('classifies media and local paths', () => {
  assert.equal(mediaKind('/a/b.PNG'), 'image');
  assert.equal(mediaKind('clip.mov'), 'video');
  assert.equal(mediaKind('song.flac'), 'audio');
  assert.equal(mediaKind('notes.txt'), 'other');
  assert.equal(isLocalPath('/home/user/Downloads/x.png'), true);
  assert.equal(isLocalPath('file:///home/user/x.png'), true);
  assert.equal(isLocalPath('https://example.com/x.png'), false);
});
