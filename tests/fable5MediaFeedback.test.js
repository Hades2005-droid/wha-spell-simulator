import assert from 'node:assert/strict';
import test from 'node:test';

import * as mediaFeedback from '../src/compiler/fable5MediaFeedback.js';
import * as mediaSpell from '../src/compiler/fable5MediaSpell.js';

const { buildComfyUIMediaReview, evaluateFable5MediaFeedback } = mediaFeedback;
const { compileFable5MediaSpell, diagnoseIPhoneBridge } = mediaSpell;

function buildManifest(medium = 'image') {
  return compileFable5MediaSpell({
    spellIR: {
      valid: true,
      active: true,
      element: 'light',
      primaryManifestation: 'aura',
      signature: `light:${medium}:true`,
      quality: 0.84,
      stability: 0.8,
      neatness: 0.86,
      focus: 0.82,
    },
    medium,
    intent: `Create a high-quality Fable 5 ${medium} spell study.`,
    assetDigests: ['b'.repeat(64)],
  });
}

test('evaluates bounded image feedback and proposes the next local pass', () => {
  const manifest = buildManifest();
  const feedback = evaluateFable5MediaFeedback({
    manifest,
    metrics: {
      sharpness: 0.82,
      composition: 0.6,
      subjectConsistency: 0.84,
      artifactControl: 0.8,
    },
  });

  assert.equal(feedback.status, 'refine_proposed');
  assert.equal(feedback.iteration, 0);
  assert.equal(feedback.nextIteration, 1);
  assert.deepEqual(feedback.weakMetrics, ['composition']);
  assert.deepEqual(feedback.adjustments, ['reframe_composition']);
  assert.equal(feedback.controls.submitAllowed, false);
  assert.equal(feedback.controls.externalRequests, 0);
});

test('accepts strong video and audio feedback with the Fable vector intact', () => {
  const video = evaluateFable5MediaFeedback({
    manifest: buildManifest('video'),
    metrics: {
      temporalConsistency: 0.96,
      motionCoherence: 0.94,
      frameArtifactControl: 0.95,
      audioSync: 0.93,
    },
  });
  const audio = evaluateFable5MediaFeedback({
    manifest: buildManifest('audio'),
    metrics: {
      clarity: 0.95,
      dynamicRange: 0.94,
      noiseControl: 0.96,
      spatialBalance: 0.93,
    },
  });

  assert.equal(video.status, 'accepted');
  assert.equal(audio.status, 'accepted');
  assert.deepEqual(video.fable5.vector, audio.fable5.vector);
  assert.equal(video.fable5.vector[4].value, 18);
  assert.equal(video.fable5.vector[4].reduced, 9);
});

test('stops recursive refinement at the configured bound', () => {
  const feedback = evaluateFable5MediaFeedback({
    manifest: buildManifest(),
    metrics: { sharpness: 0.2 },
    iteration: 3,
    maxIterations: 3,
  });

  assert.equal(feedback.status, 'needs_review');
  assert.equal(feedback.nextIteration, 3);
  assert.equal(feedback.controls.remoteWrites, false);
  function evaluateOverBound() {
    evaluateFable5MediaFeedback({
      manifest: buildManifest(),
      metrics: { sharpness: 0.2 },
      iteration: 4,
    });
  }
  assert.throws(evaluateOverBound, /iteration/);
});

test('builds a ComfyUI review manifest without a submission endpoint', () => {
  const manifest = buildManifest();
  const feedback = evaluateFable5MediaFeedback({
    manifest,
    metrics: { sharpness: 0.9, composition: 0.9 },
  });
  const review = buildComfyUIMediaReview({
    manifest,
    feedback,
    workflowId: 'fable5.image.review',
  });

  assert.equal(review.status, 'ready_for_user_approval');
  assert.equal(review.target, 'comfyui_local');
  assert.equal(review.workflowId, 'fable5.image.review');
  assert.equal(review.feedback.status, 'accepted');
  assert.equal(review.controls.submitAllowed, false);
  assert.equal(Object.hasOwn(review, 'endpoint'), false);
  assert.equal(Object.hasOwn(review, 'request'), false);
  assert.throws(() => buildComfyUIMediaReview({ manifest, workflowId: '../submit' }), /workflowId/);
});

test('rejects feedback or manifests that cross the local-only boundary', () => {
  const manifest = buildManifest();
  const feedback = evaluateFable5MediaFeedback({
    manifest,
    metrics: { sharpness: 0.9 },
  });
  const remoteManifest = {
    ...manifest,
    controls: { ...manifest.controls, remoteWrites: true },
  };

  assert.throws(() => buildComfyUIMediaReview({ manifest: remoteManifest }), /controls/);
  function buildMismatchedFeedbackReview() {
    buildComfyUIMediaReview({
      manifest,
      feedback: { ...feedback, manifestFingerprint: 'wrong' },
    });
  }
  assert.throws(buildMismatchedFeedbackReview, /belong to the media manifest/);
});

test('reports local iPhone media preview readiness without identifiers', () => {
  const diagnostics = diagnoseIPhoneBridge({
    secureContext: true,
    touchPoints: 5,
    webAudio: true,
    webGL2: true,
    media: {
      maxTextureSize: 4096,
      videoPlayback: true,
      audioOutput: true,
    },
  });

  assert.equal(diagnostics.mediaPreview.image.status, 'ready');
  assert.equal(diagnostics.mediaPreview.video.status, 'ready');
  assert.equal(diagnostics.mediaPreview.audio.status, 'ready');
  assert.throws(() => diagnoseIPhoneBridge({ media: { deviceId: 'blocked' } }), /media.deviceId/);
});
