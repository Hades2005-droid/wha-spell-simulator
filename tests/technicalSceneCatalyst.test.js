import assert from 'node:assert/strict';
import test from 'node:test';

import {
  buildTechnicalSceneCatalyst,
  validateTechnicalSceneCatalyst,
} from '../src/compiler/technicalSceneCatalyst.js';
import { buildComfyUIMediaReview } from '../src/compiler/fable5MediaFeedback.js';
import { compileFable5MediaSpell } from '../src/compiler/fable5MediaSpell.js';

function scenePlan() {
  return buildTechnicalSceneCatalyst({
    setting: {
      location: 'Moonlit workshop',
      lighting: 'soft practical lamps',
      timeOfDay: 'night',
    },
    camera: {
      lens: '35mm',
      movement: 'slow dolly',
      framing: 'medium wide',
    },
    wardrobeTags: ['cloak', 'silhouette'],
    voiceRoute: 'local_bbv_reference',
    motionBeats: [
      { action: 'Establish the workshop', durationSeconds: 2, transition: 'fade' },
      { action: 'Track the spell circle', durationSeconds: 2.5, transition: 'dissolve' },
      { action: 'Hold on the completed sigil', durationSeconds: 2, transition: 'fade' },
    ],
    safetySeal: {
      fictionalAdults: true,
      consentConfirmed: true,
      nonExplicit: true,
    },
  });
}

function mediaManifest() {
  return compileFable5MediaSpell({
    spellIR: {
      valid: true,
      active: true,
      element: 'light',
      quality: 0.9,
      stability: 0.9,
      neatness: 0.9,
      focus: 0.9,
    },
    medium: 'video',
    intent: 'Create a local technical scene study.',
  });
}

test('builds a local-only C=3 technical scene plan', () => {
  const plan = scenePlan();

  assert.equal(plan.catalyst, 3);
  assert.equal(plan.mode, 'technical_scene_metadata');
  assert.equal(plan.motionBeats.length, 3);
  assert.deepEqual(plan.wardrobeTags, ['cloak', 'silhouette']);
  assert.deepEqual(plan.controls, {
    approved: false,
    executionMode: 'manifest_only',
    externalRequests: 0,
    localOnly: true,
    remoteWrites: false,
  });
  assert.deepEqual(validateTechnicalSceneCatalyst(plan), plan);
});

test('rejects scene plans that drop safety or local-only controls', () => {
  const plan = scenePlan();

  assert.throws(
    () => buildTechnicalSceneCatalyst({
      ...plan,
      safetySeal: { fictionalAdults: true, consentConfirmed: true, nonExplicit: false },
    }),
    /safetySeal/,
  );
  assert.throws(
    () => validateTechnicalSceneCatalyst({
      ...plan,
      controls: { ...plan.controls, remoteWrites: true },
    }),
    /controls/,
  );
});

test('attaches a validated scene plan to an approval-gated media review', () => {
  const review = buildComfyUIMediaReview({
    manifest: mediaManifest(),
    scenePlan: scenePlan(),
  });

  assert.equal(review.scenePlan.catalyst, 3);
  assert.equal(review.controls.submitAllowed, false);
  assert.equal(review.controls.externalRequests, 0);
});
