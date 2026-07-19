import { FABLE_VECTOR, MEDIA_TYPES } from './fable5MediaSpell.js';

const DEFAULT_MAX_ITERATIONS = 3;
const MIN_ACCEPTANCE_SCORE = 0.7;
const MAX_ACCEPTANCE_SCORE = 0.95;
const WEAK_METRIC_SCORE = 0.65;

const METRICS_BY_MEDIUM = Object.freeze({
  image: Object.freeze(['sharpness', 'composition', 'subjectConsistency', 'artifactControl']),
  video: Object.freeze([
    'temporalConsistency',
    'motionCoherence',
    'frameArtifactControl',
    'audioSync',
  ]),
  audio: Object.freeze(['clarity', 'dynamicRange', 'noiseControl', 'spatialBalance']),
});

const ADJUSTMENTS_BY_METRIC = Object.freeze({
  sharpness: 'increase_detail',
  composition: 'reframe_composition',
  subjectConsistency: 'stabilize_subject',
  artifactControl: 'reduce_artifacts',
  temporalConsistency: 'stabilize_temporal_flow',
  motionCoherence: 'refine_motion_coherence',
  frameArtifactControl: 'reduce_frame_artifacts',
  audioSync: 'align_audio_timing',
  clarity: 'improve_audio_clarity',
  dynamicRange: 'rebalance_dynamics',
  noiseControl: 'reduce_noise_floor',
  spatialBalance: 'rebalance_spatial_field',
});

function validateMediaManifest(manifest) {
  if (!manifest || manifest.schema !== 'what_spell.fable5_media_spell.v1') {
    throw new TypeError('manifest must be a Fable 5 media spell manifest');
  }
  if (!MEDIA_TYPES.has(manifest.medium)) {
    throw new TypeError('manifest medium is unsupported');
  }
  const { controls } = manifest;
  const controlChecks = [
    Boolean(controls),
    controls?.localOnly === true,
    controls?.externalRequests === 0,
    controls?.remoteWrites === false,
    controls?.modelOutputCommandsAllowed === false,
    controls?.executionMode === 'manifest_only',
  ];
  if (controlChecks.some((check) => !check)) {
    throw new TypeError('manifest controls do not permit local review');
  }
}

function boundedIteration(value, name) {
  if (!Number.isInteger(value) || value < 0 || value > DEFAULT_MAX_ITERATIONS) {
    throw new RangeError(`${name} must be an integer between 0 and ${DEFAULT_MAX_ITERATIONS}`);
  }
  return value;
}

function normalizeMetrics(medium, metrics) {
  if (!metrics || typeof metrics !== 'object' || Array.isArray(metrics)) {
    throw new TypeError('metrics must be an object');
  }
  const allowed = new Set(METRICS_BY_MEDIUM[medium]);
  const names = Object.keys(metrics);
  if (!names.length) {
    throw new TypeError('metrics must contain at least one supported metric');
  }
  names.forEach((name) => {
    if (!allowed.has(name)) {
      throw new TypeError(`${name} is not a supported ${medium} metric`);
    }
    if (!Number.isFinite(metrics[name]) || metrics[name] < 0 || metrics[name] > 1) {
      throw new RangeError(`${name} must be between 0 and 1`);
    }
  });
  return Object.fromEntries(names.sort().map((name) => [name, metrics[name]]));
}

function average(values) {
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function sourceScore(manifest) {
  return Number.isFinite(manifest.quality?.score) ? manifest.quality.score : MIN_ACCEPTANCE_SCORE;
}

function feedbackStatus(accepted, exhausted) {
  if (accepted) {
    return 'accepted';
  }
  return exhausted ? 'needs_review' : 'refine_proposed';
}

function acceptanceThreshold(manifest) {
  return Math.min(MAX_ACCEPTANCE_SCORE, Math.max(MIN_ACCEPTANCE_SCORE, sourceScore(manifest)));
}

function feedbackControls() {
  return {
    approved: false,
    executionMode: 'manifest_only',
    externalRequests: 0,
    localOnly: true,
    modelOutputCommandsAllowed: false,
    remoteWrites: false,
    submitAllowed: false,
  };
}

function adjustmentList(options) {
  const weakMetrics = Object.entries(options.metrics)
    .filter(([, value]) => value < WEAK_METRIC_SCORE)
    .map(([name]) => name);
  const adjustments = weakMetrics.map((name) => ADJUSTMENTS_BY_METRIC[name]);
  if (options.score < options.threshold && !adjustments.length) {
    adjustments.push(`raise_${options.medium}_fidelity`);
  }
  return { weakMetrics, adjustments };
}

export function evaluateFable5MediaFeedback({
  manifest,
  metrics,
  iteration = 0,
  maxIterations = DEFAULT_MAX_ITERATIONS,
} = {}) {
  validateMediaManifest(manifest);
  const currentIteration = boundedIteration(iteration, 'iteration');
  const allowedMaxIterations = boundedIteration(maxIterations, 'maxIterations');
  if (currentIteration > allowedMaxIterations) {
    throw new RangeError('iteration cannot exceed maxIterations');
  }
  const observedMetrics = normalizeMetrics(manifest.medium, metrics);
  const observedScore = Number(average(Object.values(observedMetrics)).toFixed(4));
  const threshold = acceptanceThreshold(manifest);
  const feedback = adjustmentList({
    medium: manifest.medium,
    metrics: observedMetrics,
    score: observedScore,
    threshold,
  });
  const accepted = observedScore >= threshold && feedback.weakMetrics.length === 0;
  const exhausted = !accepted && currentIteration >= allowedMaxIterations;
  return {
    schema: 'what_spell.fable5_media_feedback.v1',
    manifestFingerprint: String(manifest.fingerprint ?? ''),
    medium: manifest.medium,
    fable5: {
      catalyst: 5,
      vector: FABLE_VECTOR,
      moonGate: manifest.fable5?.moonGate ?? null,
    },
    iteration: currentIteration,
    maxIterations: allowedMaxIterations,
    observedMetrics,
    observedScore,
    acceptanceThreshold: threshold,
    weakMetrics: feedback.weakMetrics,
    adjustments: feedback.adjustments,
    status: feedbackStatus(accepted, exhausted),
    nextIteration: accepted || exhausted ? currentIteration : currentIteration + 1,
    controls: feedbackControls(),
  };
}

function validateWorkflowId(workflowId) {
  if (typeof workflowId !== 'string' || !/^[A-Za-z0-9_.:-]{1,96}$/.test(workflowId)) {
    throw new TypeError('workflowId must be a bounded local identifier');
  }
  return workflowId;
}

function feedbackReference(feedback, manifest) {
  if (feedback === undefined) {
    return null;
  }
  if (!feedback || feedback.schema !== 'what_spell.fable5_media_feedback.v1') {
    throw new TypeError('feedback must be a Fable 5 media feedback result');
  }
  if (feedback.manifestFingerprint !== String(manifest.fingerprint ?? '')) {
    throw new TypeError('feedback does not belong to the media manifest');
  }
  return {
    status: feedback.status,
    iteration: feedback.iteration,
    observedScore: feedback.observedScore,
    adjustments: feedback.adjustments,
  };
}

export function buildComfyUIMediaReview({
  manifest,
  feedback,
  workflowId = 'fable5-media-review',
} = {}) {
  validateMediaManifest(manifest);
  const review = feedbackReference(feedback, manifest);
  return {
    schema: 'what_spell.comfyui_media_review.v1',
    status: 'ready_for_user_approval',
    target: 'comfyui_local',
    workflowId: validateWorkflowId(workflowId),
    medium: manifest.medium,
    prompt: manifest.intent,
    assetDigests: manifest.assetDigests,
    parameters: manifest.media,
    fable5: {
      catalyst: manifest.fable5.catalyst,
      vector: manifest.fable5.vector,
      moonGate: manifest.fable5.moonGate,
      sourceFingerprint: manifest.fingerprint,
    },
    feedback: review,
    controls: feedbackControls(),
  };
}

export { DEFAULT_MAX_ITERATIONS, METRICS_BY_MEDIUM };
