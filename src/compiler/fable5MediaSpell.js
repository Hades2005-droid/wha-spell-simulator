// fable5MediaSpell.js
// Compiles a Fable 5 media "spell" into a local-only manifest and diagnoses an
// on-device (iPhone) preview bridge. Pure ESM, no Node-only or browser-only APIs
// so it runs in Vite and in `node --test` alike.
//
// Local-only by construction: manifests never carry a submission endpoint, never
// permit remote writes, and never emit external requests. The recursive learning
// loop lives in fable5MediaFeedback.js and is bounded.

/** Digital root: 18 -> 9, 12 -> 3, 0 -> 0. The Black Sun reduction. */
export function digitalRoot(n) {
  if (!Number.isFinite(n) || n <= 0) return 0;
  return 1 + ((Math.trunc(n) - 1) % 9);
}

// The Black Sun / Fable 5 catalyst vector: 3 · 6 · 9 doubling into 12 · 18,
// each reduced to its digital root. Frozen so every reader sees the same vector
// regardless of medium or metrics.
export const FABLE5_VECTOR = Object.freeze(
  [3, 6, 9, 12, 18].map((value) => Object.freeze({ value, reduced: digitalRoot(value) })),
);

// The one and only control surface: local, silent, no remote reach.
export const LOCAL_CONTROLS = Object.freeze({
  submitAllowed: false,
  externalRequests: 0,
  remoteWrites: false,
  localOnly: true,
});

// Identifier fields we refuse to read from a device probe — the preview reports
// readiness without ever touching a hardware identifier.
const IDENTIFIER_KEYS = ["deviceId", "groupId", "label"];

function fnv1a(str) {
  let h = 0x811c9dc5;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return (h >>> 0).toString(16).padStart(8, "0");
}

/**
 * Compile a spell IR + medium into a local-only media manifest.
 * @returns {object} manifest carrying a deterministic fingerprint and LOCAL_CONTROLS.
 */
export function compileFable5MediaSpell({ spellIR, medium = "image", intent = "", assetDigests = [] } = {}) {
  if (!spellIR || typeof spellIR !== "object") {
    throw new Error("compileFable5MediaSpell requires a spellIR object");
  }
  if (!["image", "video", "audio"].includes(medium)) {
    throw new Error(`unsupported medium: ${medium}`);
  }
  const digests = Array.isArray(assetDigests) ? assetDigests.slice() : [];
  const canonical = [
    spellIR.element,
    spellIR.primaryManifestation,
    medium,
    spellIR.signature,
    digests.join(","),
  ].join("|");

  return {
    version: "fable5.media.v1",
    medium,
    intent,
    element: spellIR.element,
    signature: spellIR.signature,
    spell: {
      element: spellIR.element,
      primaryManifestation: spellIR.primaryManifestation,
      quality: spellIR.quality,
      stability: spellIR.stability,
      neatness: spellIR.neatness,
      focus: spellIR.focus,
    },
    assetDigests: digests,
    fingerprint: `fable5-${medium}-${fnv1a(canonical)}`,
    fable5: { vector: FABLE5_VECTOR },
    controls: { ...LOCAL_CONTROLS },
  };
}

/**
 * Diagnose an on-device media preview bridge. Reports readiness only; refuses to
 * read any hardware identifier.
 */
export function diagnoseIPhoneBridge(input = {}) {
  const media = input.media || {};
  for (const key of IDENTIFIER_KEYS) {
    if (Object.hasOwn(media, key)) {
      throw new Error(`media.${key} is not permitted — the local preview reports no identifiers`);
    }
  }

  const secure = !!input.secureContext;
  const maxTexture = Number(media.maxTextureSize) || 0;

  const ready = (ok) => ({ status: ok ? "ready" : "unavailable" });

  return {
    secureContext: secure,
    touchPoints: Number(input.touchPoints) || 0,
    mediaPreview: {
      image: ready(secure && !!input.webGL2 && maxTexture >= 2048),
      video: ready(secure && !!media.videoPlayback),
      audio: ready(!!input.webAudio && !!media.audioOutput),
    },
    controls: { ...LOCAL_CONTROLS },
  };
}
