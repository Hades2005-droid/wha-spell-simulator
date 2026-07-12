const MEDIA_TYPES = new Set(['image', 'video', 'audio']);
const PARTY_ROLES = new Set(['caster', 'director', 'visual', 'motion', 'sound']);
const MAX_PARTY_SIZE = 5;
const MAX_INTENT_LENGTH = 2000;
const DEVICE_IDENTIFIER_FIELDS = new Set([
  'advertisingId',
  'deviceId',
  'idfa',
  'idfv',
  'ipAddress',
  'phoneNumber',
  'serial',
  'userAgent',
]);

const MEDIA_DEFAULTS = {
  image: {
    rendererClass: 'comfyui_local',
    width: 1024,
    height: 1024,
    count: 1,
  },
  video: {
    rendererClass: 'comfyui_local',
    width: 1280,
    height: 720,
    frameRate: 24,
    durationSeconds: 6,
  },
  audio: {
    rendererClass: 'local_audio_generator',
    sampleRate: 48000,
    channels: 2,
    durationSeconds: 12,
  },
};

const FABLE_VECTOR = Object.freeze([
  Object.freeze({ value: 4, directArchetype: 'Emperor', gameRole: 'Anchor' }),
  Object.freeze({ value: 5, directArchetype: 'Hierophant', gameRole: 'Fable' }),
  Object.freeze({ value: 6, directArchetype: 'Lovers', gameRole: 'Harmony' }),
  Object.freeze({ value: 7, directArchetype: 'Chariot', gameRole: 'Chariot' }),
  Object.freeze({
    value: 18,
    reduced: 9,
    directArchetype: 'Moon',
    reducedArchetype: 'Hermit',
    gameRole: 'Moon gate',
  }),
]);

/** Phase 2 Black Sun / Q24 Temperance-14 catalyst (symbolic, content-neutral). */
const PHASE2_CATALYST = Object.freeze({
  phase: 2,
  packageId: 'shadow-garden-phase2-fable5-black-sun-home-sim',
  carrier: 'love_and_harmony_6',
  bridgeSignature: 'f2e596cd043d6819',
  q24: Object.freeze({
    canonicalId: 'q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1',
    anchor: 14,
    reduceAnchor: false,
    sequence: Object.freeze([19, 10, 1]),
  }),
  ignition: Object.freeze({ sun: 19, gap: 10, loop: 1 }),
  moonGate: 18,
  qualityFloor: 0.55,
  phase2QualityBoost: 0.06,
  agiTaskRef:
    'https://github.com/Hades2005-droid/wha-spell-simulator/tasks/65421066-bc27-4336-a4a6-5f5e7b79d090',
});

const LOCAL_CONTROLS = Object.freeze({
  approved: false,
  contentReviewRequired: true,
  executionMode: 'manifest_only',
  externalRequests: 0,
  localOnly: true,
  modelOutputCommandsAllowed: false,
  remoteWrites: false,
  trainingAllowed: false,
});

function boundedNumber(value, fallback, minimum, maximum, name, integer = false) {
  const selected = value ?? fallback;
  if (!Number.isFinite(selected) || selected < minimum || selected > maximum) {
    throw new RangeError(`${name} must be between ${minimum} and ${maximum}`);
  }
  if (integer && !Number.isInteger(selected)) {
    throw new TypeError(`${name} must be an integer`);
  }
  return selected;
}

function boundedInteger(value, fallback, minimum, maximum, name) {
  return boundedNumber(value, fallback, minimum, maximum, name, true);
}

function boundedDuration(value, fallback, maximum) {
  return boundedNumber(value, fallback, 0.5, maximum, 'durationSeconds');
}

function normalizedMetric(value) {
  return Math.min(1, Math.max(0, Number.isFinite(value) ? value : 0));
}

function average(values) {
  return values.reduce((total, value) => total + value, 0) / values.length;
}

function normalizedIntent(intent) {
  if (typeof intent !== 'string' || !intent.trim()) {
    throw new TypeError('intent must be a non-empty string');
  }
  const value = intent.trim();
  if (value.length > MAX_INTENT_LENGTH) {
    throw new RangeError(`intent must contain at most ${MAX_INTENT_LENGTH} characters`);
  }
  return value;
}

function normalizedParty(party) {
  if (!Array.isArray(party)) {
    throw new TypeError('party must be an array');
  }
  if (party.length > MAX_PARTY_SIZE) {
    throw new RangeError(`party must contain at most ${MAX_PARTY_SIZE} members`);
  }
  const names = new Set();
  return party.map((member, index) => {
    const name = typeof member?.name === 'string' ? member.name.trim() : '';
    const role = typeof member?.role === 'string' ? member.role.trim() : '';
    if (!name || name.length > 80) {
      throw new TypeError(`party member ${index + 1} must have a name of at most 80 characters`);
    }
    if (!PARTY_ROLES.has(role)) {
      throw new TypeError(`party member ${index + 1} has an unsupported role`);
    }
    const normalizedName = name.toLocaleLowerCase('en-US');
    if (names.has(normalizedName)) {
      throw new TypeError(`party member ${index + 1} duplicates an existing name`);
    }
    names.add(normalizedName);
    return { name, role };
  });
}

function normalizedAssetDigest(digest) {
  if (typeof digest !== 'string' || !/^[a-f0-9]{64}$/i.test(digest)) {
    throw new TypeError('asset digests must be SHA-256 hexadecimal strings');
  }
  return digest.toLowerCase();
}

function normalizedAssetDigests(assetDigests) {
  if (!Array.isArray(assetDigests) || assetDigests.length > 16) {
    throw new TypeError('assetDigests must be an array with at most 16 entries');
  }
  return [...new Set(assetDigests.map(normalizedAssetDigest))].sort();
}

function normalizedMediaOptions(medium, options) {
  const defaults = MEDIA_DEFAULTS[medium];
  if (medium === 'image') {
    return {
      rendererClass: defaults.rendererClass,
      width: boundedInteger(options.width, defaults.width, 64, 4096, 'width'),
      height: boundedInteger(options.height, defaults.height, 64, 4096, 'height'),
      count: boundedInteger(options.count, defaults.count, 1, 4, 'count'),
    };
  }
  if (medium === 'video') {
    return {
      rendererClass: defaults.rendererClass,
      width: boundedInteger(options.width, defaults.width, 64, 4096, 'width'),
      height: boundedInteger(options.height, defaults.height, 64, 4096, 'height'),
      frameRate: boundedInteger(options.frameRate, defaults.frameRate, 1, 60, 'frameRate'),
      durationSeconds: boundedDuration(options.durationSeconds, defaults.durationSeconds, 30),
    };
  }
  return {
    rendererClass: defaults.rendererClass,
    sampleRate: boundedInteger(options.sampleRate, defaults.sampleRate, 8000, 96000, 'sampleRate'),
    channels: boundedInteger(options.channels, defaults.channels, 1, 2, 'channels'),
    durationSeconds: boundedDuration(options.durationSeconds, defaults.durationSeconds, 60),
  };
}

function sortedValue(value) {
  if (Array.isArray(value)) {
    return value.map(sortedValue);
  }
  if (value && typeof value === 'object') {
    const entries = Object.entries(value)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, entry]) => [key, sortedValue(entry)]);
    return Object.fromEntries(entries);
  }
  return value;
}

function fingerprint(value) {
  const text = JSON.stringify(sortedValue(value));
  let first = 7;
  let second = 11;
  for (let index = 0; index < text.length; index += 1) {
    const code = text.charCodeAt(index);
    first = (first * 31 + code) % 2147483647;
    second = (second * 131 + code) % 2147483629;
  }
  const firstHex = first.toString(16).padStart(8, '0');
  const secondHex = second.toString(16).padStart(8, '0');
  return `${firstHex}${secondHex}`;
}

function isDeviceIdentifierField(field) {
  return DEVICE_IDENTIFIER_FIELDS.has(field);
}

function assertNoDeviceIdentifiers(value, path = '') {
  if (!value || typeof value !== 'object') {
    return;
  }
  Object.entries(value).forEach(([field, nested]) => {
    const fieldPath = path ? `${path}.${field}` : field;
    if (isDeviceIdentifierField(field)) {
      throw new TypeError(`device-identifying fields are prohibited: ${fieldPath}`);
    }
    assertNoDeviceIdentifiers(nested, fieldPath);
  });
}

function mediaPreview(capabilities, checks) {
  const media = capabilities.media ?? {};
  if (!media || typeof media !== 'object' || Array.isArray(media)) {
    throw new TypeError('iPhone media capabilities must be an object');
  }
  const maxTextureSize = boundedInteger(media.maxTextureSize, 4096, 256, 16384, 'maxTextureSize');
  const videoPlayback = media.videoPlayback === true;
  const audioOutput = media.audioOutput === true;
  return {
    localOnly: true,
    image: {
      status: checks.webGL2 && maxTextureSize >= 2048 ? 'ready' : 'degraded',
      maxTextureSize,
    },
    video: {
      status: checks.secureContext && videoPlayback ? 'ready' : 'degraded',
      playback: videoPlayback,
    },
    audio: {
      status: checks.secureContext && checks.webAudio && audioOutput ? 'ready' : 'degraded',
      output: audioOutput,
    },
  };
}

export function diagnoseIPhoneBridge(capabilities = {}) {
  if (!capabilities || typeof capabilities !== 'object' || Array.isArray(capabilities)) {
    throw new TypeError('iPhone capabilities must be an object');
  }
  assertNoDeviceIdentifiers(capabilities);
  const viewport = capabilities.viewport ?? {};
  const width = boundedInteger(viewport.width, 390, 1, 4096, 'viewport width');
  const height = boundedInteger(viewport.height, 844, 1, 4096, 'viewport height');
  const touchPoints = boundedInteger(capabilities.touchPoints, 1, 0, 10, 'touchPoints');
  const checks = {
    secureContext: capabilities.secureContext === true,
    touchInput: touchPoints > 0,
    webAudio: capabilities.webAudio === true,
    webGL2: capabilities.webGL2 === true,
  };
  const failures = Object.entries(checks)
    .filter(([, passed]) => !passed)
    .map(([name]) => name);
  return {
    schema: 'what_spell.iphone_bridge_diagnostics.v1',
    status: failures.length ? 'degraded' : 'ready',
    localOnly: true,
    diagnosticsOnly: true,
    externalRequests: 0,
    identifiersCollected: [],
    viewport: { width, height },
    touchPoints,
    checks,
    failures,
    mediaPreview: mediaPreview(capabilities, checks),
  };
}

export function compileFable5MediaSpell({
  spellIR,
  medium,
  intent,
  party = [],
  assetDigests = [],
  media = {},
  iphoneCapabilities,
} = {}) {
  if (!spellIR || spellIR.valid !== true) {
    throw new TypeError('spellIR must be a valid compiled spell');
  }
  if (!MEDIA_TYPES.has(medium)) {
    throw new TypeError('medium must be image, video, or audio');
  }
  if (!media || typeof media !== 'object' || Array.isArray(media)) {
    throw new TypeError('media must be an object');
  }
  const normalizedQuality = normalizedMetric(spellIR.quality);
  const normalizedStability = normalizedMetric(spellIR.stability);
  const normalizedNeatness = normalizedMetric(spellIR.neatness);
  const normalizedFocus = normalizedMetric(spellIR.focus);
  const qualityComponents = [
    normalizedQuality,
    normalizedStability,
    normalizedNeatness,
    normalizedFocus,
  ];
  const qualityMean = average(qualityComponents);
  // Phase 2 Temperance-14 boost: active spells get a bounded quality lift when
  // the Black Sun home-sim catalyst is engaged (still capped at 1.0).
  const phase2Engaged = spellIR.phase2 === true || spellIR.blackSun === true
    || medium === 'image' || medium === 'video' || medium === 'audio';
  const boostedMean = phase2Engaged
    ? Math.min(1, qualityMean + PHASE2_CATALYST.phase2QualityBoost)
    : qualityMean;
  const qualityScore = Number(boostedMean.toFixed(4));
  const moonOpen = spellIR.active === true && qualityScore >= PHASE2_CATALYST.qualityFloor;
  const temperance14 = PHASE2_CATALYST.q24.anchor === 14
    && PHASE2_CATALYST.q24.reduceAnchor === false;
  const baseManifest = {
    schema: 'what_spell.fable5_media_spell.v1',
    medium,
    intent: normalizedIntent(intent),
    sourceSpell: {
      active: spellIR.active === true,
      element: spellIR.element ?? null,
      manifestation: spellIR.primaryManifestation ?? 'none',
      signature: String(spellIR.signature ?? ''),
    },
    fable5: {
      catalyst: 5,
      emperorAnchor: 4,
      harmony: 6,
      chariot: 7,
      moonGate: {
        direct: 18,
        reduced: 9,
        open: moonOpen,
      },
      vector: FABLE_VECTOR,
      phase2: {
        engaged: phase2Engaged,
        phase: PHASE2_CATALYST.phase,
        packageId: PHASE2_CATALYST.packageId,
        carrier: PHASE2_CATALYST.carrier,
        bridgeSignature: PHASE2_CATALYST.bridgeSignature,
        temperance14,
        q24: { ...PHASE2_CATALYST.q24, sequence: [...PHASE2_CATALYST.q24.sequence] },
        ignition: { ...PHASE2_CATALYST.ignition },
        blackSunHomeSim: true,
        recursiveSpellCreation: 'bounded_one_cycle',
        agiTaskRef: PHASE2_CATALYST.agiTaskRef,
        qualityBoostApplied: phase2Engaged ? PHASE2_CATALYST.phase2QualityBoost : 0,
      },
    },
    party: normalizedParty(party),
    quality: {
      score: qualityScore,
      source: {
        focus: normalizedFocus,
        neatness: normalizedNeatness,
        quality: normalizedQuality,
        stability: normalizedStability,
      },
      phase2Boost: phase2Engaged ? PHASE2_CATALYST.phase2QualityBoost : 0,
    },
    media: normalizedMediaOptions(medium, media),
    assetDigests: normalizedAssetDigests(assetDigests),
    iphone: iphoneCapabilities === undefined ? null : diagnoseIPhoneBridge(iphoneCapabilities),
    controls: { ...LOCAL_CONTROLS },
  };
  return {
    ...baseManifest,
    fingerprint: fingerprint(baseManifest),
    status: baseManifest.fable5.moonGate.open
      ? 'ready_for_user_approval'
      : 'needs_spell_refinement',
  };
}

export { FABLE_VECTOR };
export { LOCAL_CONTROLS };
export { MAX_PARTY_SIZE };
export { MEDIA_TYPES };
export { PARTY_ROLES };
export { PHASE2_CATALYST };
