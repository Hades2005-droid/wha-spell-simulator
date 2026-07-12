const MAX_TAG_LENGTH = 80;
const MAX_TEXT_LENGTH = 240;
const MAX_MOTION_BEATS = 5;
const MIN_MOTION_BEATS = 3;

function requiredText(value, name) {
  if (typeof value !== 'string' || !value.trim() || value.trim().length > MAX_TEXT_LENGTH) {
    throw new TypeError(`${name} must be non-empty text of at most ${MAX_TEXT_LENGTH} characters`);
  }
  return value.trim();
}

function metadataTag(value, name) {
  if (typeof value !== 'string' || !/^[a-z0-9][a-z0-9_-]{0,79}$/i.test(value)) {
    throw new TypeError(`${name} must be an alphanumeric metadata tag`);
  }
  return value.toLowerCase();
}

function tags(values) {
  if (!Array.isArray(values) || values.length > 12) {
    throw new TypeError('wardrobeTags must contain at most 12 metadata tags');
  }
  return [...new Set(values.map((value) => metadataTag(value, 'wardrobeTags')))].sort();
}

function sceneSetting(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError('setting must be an object');
  }
  return {
    location: requiredText(value.location, 'setting.location'),
    lighting: requiredText(value.lighting, 'setting.lighting'),
    timeOfDay: requiredText(value.timeOfDay, 'setting.timeOfDay'),
  };
}

function cameraPlan(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError('camera must be an object');
  }
  return {
    framing: requiredText(value.framing, 'camera.framing'),
    lens: requiredText(value.lens, 'camera.lens'),
    movement: requiredText(value.movement, 'camera.movement'),
  };
}

function motionPlan(value) {
  if (!Array.isArray(value) || value.length < MIN_MOTION_BEATS || value.length > MAX_MOTION_BEATS) {
    throw new TypeError(`motionBeats must contain ${MIN_MOTION_BEATS} to ${MAX_MOTION_BEATS} beats`);
  }
  return value.map((beat, index) => {
    if (!beat || typeof beat !== 'object' || Array.isArray(beat)) {
      throw new TypeError(`motion beat ${index + 1} must be an object`);
    }
    if (!Number.isFinite(beat.durationSeconds) || beat.durationSeconds < 0.5 || beat.durationSeconds > 12) {
      throw new RangeError(`motion beat ${index + 1} durationSeconds must be between 0.5 and 12`);
    }
    return {
      action: requiredText(beat.action, `motion beat ${index + 1} action`),
      durationSeconds: beat.durationSeconds,
      transition: metadataTag(beat.transition ?? 'fade', `motion beat ${index + 1} transition`),
    };
  });
}

function safetySeal(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError('safetySeal must be an object');
  }
  if (
    value.fictionalAdults !== true
    || value.consentConfirmed !== true
    || value.nonExplicit !== true
  ) {
    throw new TypeError('safetySeal requires fictional adults, consent, and non-explicit content');
  }
  return {
    consentConfirmed: true,
    fictionalAdults: true,
    nonExplicit: true,
  };
}

export function buildTechnicalSceneCatalyst({
  setting,
  camera,
  wardrobeTags = [],
  voiceRoute = 'local_bbv_reference',
  motionBeats,
  safetySeal: seal,
} = {}) {
  return {
    schema: 'what_spell.technical_scene_catalyst.v1',
    catalyst: 3,
    mode: 'technical_scene_metadata',
    setting: sceneSetting(setting),
    camera: cameraPlan(camera),
    wardrobeTags: tags(wardrobeTags),
    voiceRoute: metadataTag(voiceRoute, 'voiceRoute'),
    motionBeats: motionPlan(motionBeats),
    safetySeal: safetySeal(seal),
    controls: {
      approved: false,
      executionMode: 'manifest_only',
      externalRequests: 0,
      localOnly: true,
      remoteWrites: false,
    },
  };
}

export function validateTechnicalSceneCatalyst(plan) {
  if (!plan || plan.schema !== 'what_spell.technical_scene_catalyst.v1' || plan.catalyst !== 3) {
    throw new TypeError('scenePlan must be a C=3 technical scene catalyst');
  }
  const canonical = buildTechnicalSceneCatalyst(plan);
  if (
    plan.controls?.approved !== false
    || plan.controls?.localOnly !== true
    || plan.controls?.externalRequests !== 0
    || plan.controls?.remoteWrites !== false
    || plan.controls?.executionMode !== 'manifest_only'
  ) {
    throw new TypeError('scenePlan controls must remain local-only and approval-gated');
  }
  return canonical;
}
