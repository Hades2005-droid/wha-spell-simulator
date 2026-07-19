import assert from 'node:assert/strict';
import test from 'node:test';

import * as fable5MediaSpell from '../src/compiler/fable5MediaSpell.js';

const { compileFable5MediaSpell, diagnoseIPhoneBridge } = fable5MediaSpell;

function activeSpell(overrides = {}) {
  return {
    valid: true,
    active: true,
    element: 'light',
    primaryManifestation: 'aura',
    signature: 'light:aura:true',
    quality: 0.84,
    stability: 0.8,
    neatness: 0.86,
    focus: 0.82,
    ...overrides,
  };
}

test('compiles a deterministic approval-gated image spell manifest', () => {
  const input = {
    spellIR: activeSpell(),
    medium: 'image',
    intent: 'A luminous atelier spell suspended above a moonlit garden.',
    party: [
      { name: 'Fred', role: 'caster' },
      { name: 'Fable', role: 'director' },
    ],
    assetDigests: ['a'.repeat(64)],
  };
  const first = compileFable5MediaSpell(input);
  const second = compileFable5MediaSpell(input);

  assert.deepEqual(first, second);
  assert.equal(first.status, 'ready_for_user_approval');
  assert.equal(first.media.rendererClass, 'comfyui_local');
  assert.equal(first.media.width, 1024);
  assert.equal(first.controls.approved, false);
  assert.equal(first.controls.executionMode, 'manifest_only');
  assert.equal(first.controls.externalRequests, 0);
  assert.equal(first.controls.trainingAllowed, false);
  assert.equal(first.fable5.catalyst, 5);
  assert.equal(first.fable5.moonGate.direct, 18);
  assert.equal(first.fable5.moonGate.reduced, 9);
  assert.equal(first.fable5.phase2.phase, 2);
  assert.equal(first.fable5.phase2.temperance14, true);
  assert.equal(first.fable5.phase2.q24.anchor, 14);
  assert.equal(first.fable5.phase2.q24.reduceAnchor, false);
  assert.deepEqual(first.fable5.phase2.q24.sequence, [19, 10, 1]);
  assert.equal(first.quality.phase2Boost, 0.06);
  assert.ok(first.quality.score >= 0.88);
});

test('compiles bounded video and audio renderer parameters', () => {
  const video = compileFable5MediaSpell({
    spellIR: activeSpell(),
    medium: 'video',
    intent: 'Animate the completed spell circle with coherent directional motion.',
    media: {
      width: 1920,
      height: 1080,
      frameRate: 60,
      durationSeconds: 8,
    },
  });
  const audio = compileFable5MediaSpell({
    spellIR: activeSpell(),
    medium: 'audio',
    intent: 'Render a layered harmonic spell activation without spoken identity data.',
    media: { sampleRate: 44100, channels: 2, durationSeconds: 20 },
  });

  assert.deepEqual(video.media, {
    rendererClass: 'comfyui_local',
    width: 1920,
    height: 1080,
    frameRate: 60,
    durationSeconds: 8,
  });
  assert.deepEqual(audio.media, {
    rendererClass: 'local_audio_generator',
    sampleRate: 44100,
    channels: 2,
    durationSeconds: 20,
  });
  function compileUnboundedVideo() {
    compileFable5MediaSpell({
      spellIR: activeSpell(),
      medium: 'video',
      intent: 'Unbounded video request',
      media: { durationSeconds: 31 },
    });
  }
  assert.throws(compileUnboundedVideo, /durationSeconds/);
});

test('requires a valid spell, supported medium, and bounded party', () => {
  function compileInvalidSpell() {
    compileFable5MediaSpell({
      spellIR: { valid: false },
      medium: 'image',
      intent: 'Invalid source',
    });
  }
  function compileUnsupportedMedium() {
    compileFable5MediaSpell({
      spellIR: activeSpell(),
      medium: 'text',
      intent: 'Unsupported output',
    });
  }
  function compileOversizedParty() {
    const party = Array.from({ length: 6 }, (_, index) => ({
      name: `Member ${index}`,
      role: 'visual',
    }));
    compileFable5MediaSpell({
      spellIR: activeSpell(),
      medium: 'image',
      intent: 'Oversized party',
      party,
    });
  }
  assert.throws(compileInvalidSpell, /valid compiled spell/);
  assert.throws(compileUnsupportedMedium, /medium/);
  assert.throws(compileOversizedParty, /at most 5/);
});

test('keeps a low-quality or prepared spell behind the refinement gate', () => {
  const manifest = compileFable5MediaSpell({
    spellIR: activeSpell({
      active: false,
      quality: 0.4,
      stability: 0.4,
      neatness: 0.4,
      focus: 0.4,
    }),
    medium: 'image',
    intent: 'Preview an unfinished spell without rendering it.',
  });

  assert.equal(manifest.status, 'needs_spell_refinement');
  assert.equal(manifest.fable5.moonGate.open, false);
  assert.equal(manifest.controls.approved, false);
});

test('reports local iPhone compatibility without collecting identifiers', () => {
  const diagnostics = diagnoseIPhoneBridge({
    secureContext: true,
    touchPoints: 5,
    webAudio: true,
    webGL2: true,
    viewport: { width: 393, height: 852 },
  });

  assert.equal(diagnostics.status, 'ready');
  assert.equal(diagnostics.localOnly, true);
  assert.equal(diagnostics.externalRequests, 0);
  assert.deepEqual(diagnostics.identifiersCollected, []);
  function diagnoseIdentifyingPayload() {
    diagnoseIPhoneBridge({
      deviceId: 'must-not-be-collected',
    });
  }
  assert.throws(diagnoseIdentifyingPayload, /device-identifying fields are prohibited/);
});

test('reports missing iPhone capabilities without probing the device', () => {
  const diagnostics = diagnoseIPhoneBridge({
    secureContext: false,
    touchPoints: 1,
    webAudio: true,
    webGL2: false,
  });

  assert.equal(diagnostics.status, 'degraded');
  assert.deepEqual(diagnostics.failures, ['secureContext', 'webGL2']);
  assert.equal(diagnostics.diagnosticsOnly, true);
});
