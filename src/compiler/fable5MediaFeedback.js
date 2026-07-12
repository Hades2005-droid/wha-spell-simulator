// fable5MediaFeedback.js
// The bounded, recursive learning loop for Fable 5 media. Each pass scores the
// current render against per-medium metrics, proposes the next local refinement,
// and stops at a configured bound — never issuing an external request or a
// submission. The final step is a ComfyUI review manifest the user approves
// locally; there is no submit endpoint anywhere in this module.

import { FABLE5_VECTOR, LOCAL_CONTROLS } from "./fable5MediaSpell.js";

// A metric is "weak" (needs another pass) below this bar.
const WEAK_THRESHOLD = 0.75;

// Which local adjustment each metric maps to when it comes back weak.
const ADJUSTMENTS = {
  // image
  sharpness: "sharpen_detail",
  composition: "reframe_composition",
  subjectConsistency: "stabilize_subject",
  artifactControl: "suppress_artifacts",
  // video
  temporalConsistency: "stabilize_temporal",
  motionCoherence: "smooth_motion",
  frameArtifactControl: "suppress_frame_artifacts",
  audioSync: "align_audio",
  // audio
  clarity: "clarify_signal",
  dynamicRange: "expand_dynamics",
  noiseControl: "reduce_noise",
  spatialBalance: "balance_spatial",
};

const SAFE_WORKFLOW_ID = /^[A-Za-z0-9._-]+$/;

function assertLocalOnly(controls, where) {
  const c = controls || {};
  if (c.remoteWrites || c.submitAllowed || (Number(c.externalRequests) || 0) > 0) {
    throw new Error(`${where}.controls must stay local-only (no remote writes or submissions)`);
  }
}

/**
 * Score one pass and propose the next local refinement, bounded by maxIterations.
 * @returns {object} feedback (status: accepted | refine_proposed | needs_review)
 */
export function evaluateFable5MediaFeedback({ manifest, metrics = {}, iteration = 0, maxIterations = 3 } = {}) {
  if (!manifest || typeof manifest !== "object") {
    throw new Error("evaluateFable5MediaFeedback requires a media manifest");
  }
  assertLocalOnly(manifest.controls, "manifest");
  if (!Number.isInteger(iteration) || iteration < 0) {
    throw new Error(`iteration must be a non-negative integer, got ${iteration}`);
  }
  if (iteration > maxIterations) {
    throw new Error(`iteration ${iteration} exceeds the maxIterations bound of ${maxIterations}`);
  }

  const weakMetrics = [];
  for (const [name, raw] of Object.entries(metrics)) {
    if ((Number(raw) || 0) < WEAK_THRESHOLD) weakMetrics.push(name);
  }
  const adjustments = weakMetrics.map((name) => ADJUSTMENTS[name] || `refine_${name}`);

  let status;
  let nextIteration;
  if (weakMetrics.length === 0) {
    status = "accepted";
    nextIteration = iteration;
  } else if (iteration < maxIterations) {
    status = "refine_proposed";
    nextIteration = iteration + 1;
  } else {
    status = "needs_review";
    nextIteration = iteration;
  }

  return {
    status,
    medium: manifest.medium,
    iteration,
    nextIteration,
    maxIterations,
    weakMetrics,
    adjustments,
    metrics: { ...metrics },
    manifestFingerprint: manifest.fingerprint,
    fable5: { vector: FABLE5_VECTOR },
    controls: { ...LOCAL_CONTROLS },
  };
}

/**
 * Build a local ComfyUI review manifest for user approval. No endpoint, no
 * request payload — the render is reviewed on the local machine only.
 */
export function buildComfyUIMediaReview({ manifest, feedback, workflowId } = {}) {
  if (!manifest || typeof manifest !== "object") {
    throw new Error("buildComfyUIMediaReview requires a media manifest");
  }
  assertLocalOnly(manifest.controls, "manifest");

  const wf = workflowId || `fable5.${manifest.medium}.review`;
  if (typeof wf !== "string" || !SAFE_WORKFLOW_ID.test(wf) || wf.includes("..")) {
    throw new Error(`invalid workflowId: ${wf} (local workflow names only, no paths)`);
  }

  if (feedback && feedback.manifestFingerprint !== manifest.fingerprint) {
    throw new Error("feedback does not belong to the media manifest");
  }

  return {
    status: "ready_for_user_approval",
    target: "comfyui_local",
    workflowId: wf,
    medium: manifest.medium,
    fingerprint: manifest.fingerprint,
    feedback: feedback || null,
    controls: { ...LOCAL_CONTROLS },
    // Deliberately no `endpoint` and no `request`: review is local-only.
  };
}
