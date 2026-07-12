// Fable 5 spell -> ComfyUI local adapter.
//
// Compiles a WHA spell descriptor (or a full SpellIR from ../src/compiler)
// into a deterministic, ComfyUI-shaped manifest for image / video / audio
// generation, and — only when explicitly approved — hands that manifest to a
// *local* ComfyUI instance.
//
// Design contract (see docs/fable5-comfyui-adapter.md):
//   * manifest_only by default — compileManifest() never touches the network.
//   * approve:true AND mode:"queue" are both required before anything queues.
//   * externalRequests = 0 — only loopback endpoints are ever contacted, and
//     only when the caller opts in with allowLocalRequests:true.
//   * trainingAllowed = false, never auto-download weights (pointer-only).
//   * policy no_scrape_pointer_only — model/LoRA references are local pointers,
//     never URLs, never fetched.
//   * video <= 30s, at most five abstract roles.
//   * content guard rejects prohibited categories and real-person likeness.
//
// Pure, dependency-free, deterministic: the same spec always compiles to the
// same manifest (no wall-clock, no RNG in the compiled output).

export const ADAPTER_VERSION = "1.0.0";

// Provenance — canonical task wiring for the unification effort.
export const PROVENANCE = Object.freeze({
  targetTaskId: "37bce2fb-1ba6-471f-854f-3871d9c19947",
  leadTaskId: "2366bfee-b78c-4ddc-9f86-304c30c67c4d",
  branch: "fable5-comfyui-unification",
  policy: "no_scrape_pointer_only",
});

// Local-only endpoints. Fable 5 :5619, ComfyUI :8188, EDEN :8791.
export const ADAPTER_ENDPOINTS = Object.freeze({
  fable5: "http://127.0.0.1:5619",
  comfyui: "http://127.0.0.1:8188",
  comfyuiHealthPath: "/system_stats",
  eden: "http://127.0.0.1:8791",
});

// The two abstract adapter roles this unification supports.
export const ADAPTER_ROLES = Object.freeze([
  "unification_target",
  "fable5_comfyui_open_merge_target",
]);

export const MEDIA_TYPES = Object.freeze(["image", "video", "audio"]);

// Immutable safety/policy defaults. Callers may override only the knobs that
// tighten behaviour; the hard caps below are re-clamped in normalizePolicy().
export const DEFAULT_POLICY = Object.freeze({
  mode: "manifest_only", // "manifest_only" | "queue"
  approve: false,
  externalRequests: 0,
  trainingAllowed: false,
  autoDownloadWeights: false,
  scrape: "no_scrape_pointer_only",
  maxVideoSeconds: 30,
  maxAudioSeconds: 30,
  maxRoles: 5,
  allowLocalRequests: false,
});

// Loopback hosts that count as local (externalRequests stays 0).
const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "0.0.0.0", "::1"]);

// Deterministic content screen. Word/substring patterns per prohibited
// category. Kept conservative and explicit so the block reasons are auditable.
export const PROHIBITED_PATTERNS = Object.freeze({
  minors: [
    "child", "children", "minor", "underage", "under-age", "under age",
    "preteen", "pre-teen", "teen", "teenage", "kid", "infant", "toddler",
    "loli", "lolicon", "shota", "shotacon", "schoolgirl", "schoolboy",
    "cp", "csam", "jailbait",
  ],
  non_consent: [
    "non-consent", "nonconsent", "non consensual", "nonconsensual",
    "without consent", "no consent", "rape", "forced", "coerced", "coercion",
    "unwilling", "drugged", "unconscious", "molest",
  ],
  incest: [
    "incest", "incestuous", "step-sister", "stepsister", "step-brother",
    "stepbrother", "step-daughter", "stepdaughter", "step-son", "stepson",
    "father-daughter", "mother-son", "sibling sex", "family sex",
  ],
  trafficking: [
    "trafficking", "trafficked", "sex slave", "sexual slavery", "smuggled",
    "smuggling", "prostitution ring", "pimp",
  ],
  hidden_cam: [
    "hidden cam", "hidden camera", "spycam", "spy cam", "voyeur", "voyeurism",
    "upskirt", "creepshot", "peeping", "covert recording", "secretly filmed",
  ],
  exploitation: [
    "exploitation", "exploited", "revenge porn", "blackmail sex", "sextortion",
    "grooming",
  ],
  real_person_likeness: [
    "deepfake", "deep fake", "real person", "real celebrity", "actual celebrity",
    "likeness of", "nonconsensual likeness",
  ],
});

export class ContentRejectedError extends Error {
  constructor(violations) {
    const cats = violations.map((v) => v.category).join(", ");
    super(`Content rejected by adapter safety policy (${cats}).`);
    this.name = "ContentRejectedError";
    this.violations = violations;
  }
}

export class PolicyViolationError extends Error {
  constructor(message, code) {
    super(message);
    this.name = "PolicyViolationError";
    this.code = code;
  }
}

// FNV-1a 32-bit — small, stable, dependency-free deterministic hash.
function fnv1a(str) {
  let hash = 0x811c9dc5;
  for (let i = 0; i < str.length; i += 1) {
    hash ^= str.charCodeAt(i);
    hash = Math.imul(hash, 0x01000193);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

// Merge caller overrides onto DEFAULT_POLICY, then re-clamp the hard caps so a
// caller can only make the policy *stricter*, never looser than the defaults.
export function normalizePolicy(overrides = {}) {
  const merged = { ...DEFAULT_POLICY, ...overrides };
  merged.externalRequests = 0;
  merged.trainingAllowed = false;
  merged.autoDownloadWeights = false;
  merged.scrape = "no_scrape_pointer_only";
  merged.maxVideoSeconds = Math.min(merged.maxVideoSeconds, DEFAULT_POLICY.maxVideoSeconds);
  merged.maxAudioSeconds = Math.min(merged.maxAudioSeconds, DEFAULT_POLICY.maxAudioSeconds);
  merged.maxRoles = Math.min(merged.maxRoles, DEFAULT_POLICY.maxRoles);
  return merged;
}

function collectText(spec) {
  const parts = [];
  if (typeof spec.intent === "string") parts.push(spec.intent);
  if (typeof spec.negativeIntent === "string") parts.push(spec.negativeIntent);
  if (Array.isArray(spec.tags)) parts.push(spec.tags.join(" "));
  if (Array.isArray(spec.roles)) {
    for (const role of spec.roles) {
      if (role && typeof role === "object") {
        parts.push([role.id, role.descriptor, role.label].filter(Boolean).join(" "));
      } else if (typeof role === "string") {
        parts.push(role);
      }
    }
  }
  return parts.join(" \n ").toLowerCase();
}

// Screen a spec for prohibited content. Returns { allowed, violations }.
// Deterministic: pure substring/keyword matching, no external calls.
export function screenContent(spec = {}) {
  const haystack = collectText(spec);
  const violations = [];

  for (const [category, patterns] of Object.entries(PROHIBITED_PATTERNS)) {
    const matched = patterns.filter((p) => haystack.includes(p));
    if (matched.length > 0) {
      violations.push({ category, matched });
    }
  }

  // Structured real-person likeness signal — reject any explicit request to
  // reproduce a real, identifiable person. There is no real-person likeness
  // engine here by design. (Role-level real-person requests are handled as a
  // PolicyViolation in normalizeRoles.)
  if (spec.realPersonLikeness === true || spec.likenessOf) {
    if (!violations.some((v) => v.category === "real_person_likeness")) {
      violations.push({ category: "real_person_likeness", matched: ["structured_flag"] });
    }
  }

  return { allowed: violations.length === 0, violations };
}

export function assertContentAllowed(spec) {
  const { allowed, violations } = screenContent(spec);
  if (!allowed) {
    throw new ContentRejectedError(violations);
  }
}

// Validate + normalize the abstract roles. At most maxRoles, all abstract.
function normalizeRoles(rawRoles, policy) {
  if (rawRoles == null) return [];
  if (!Array.isArray(rawRoles)) {
    throw new PolicyViolationError("roles must be an array", "roles_type");
  }
  if (rawRoles.length > policy.maxRoles) {
    throw new PolicyViolationError(
      `too many roles: ${rawRoles.length} > max ${policy.maxRoles}`,
      "roles_max",
    );
  }
  return rawRoles.map((role, index) => {
    const obj = typeof role === "string" ? { id: role } : { ...role };
    if (obj.realPerson === true || obj.kind === "real_person" || obj.likenessOf) {
      throw new PolicyViolationError(
        `role[${index}] requests a real-person likeness, which is not supported`,
        "real_person_role",
      );
    }
    return {
      id: obj.id || `role_${index}`,
      kind: "abstract",
      descriptor: obj.descriptor || obj.label || "",
    };
  });
}

// Map a SpellIR (or plain numbers) onto stable generation parameters.
function deriveParameters(spec) {
  const spell = spec.spell || {};
  const clamp01 = (n) => Math.max(0, Math.min(1, Number.isFinite(n) ? n : 0));
  const quality = clamp01(spell.quality ?? spec.quality ?? 0.5);
  const stability = clamp01(spell.stability ?? spec.stability ?? 0.5);
  const element = spell.element ?? spec.element ?? "abstract";
  // Deterministic seed derived from the intent + element (no RNG).
  const seed = parseInt(fnv1a(`${element}:${spec.intent ?? ""}`), 16) % 1_000_000_000;
  // steps/cfg scale with spell quality but stay inside sane, fixed bounds.
  const steps = 12 + Math.round(quality * 18); // 12..30
  const cfg = Math.round((5 + stability * 3) * 10) / 10; // 5.0..8.0
  return { element, quality, stability, seed, steps, cfg };
}

function assertMediaDuration(media, requested, policy) {
  if (media !== "video" && media !== "audio") return 0;
  const cap = media === "video" ? policy.maxVideoSeconds : policy.maxAudioSeconds;
  const seconds = Number.isFinite(requested) ? requested : Math.min(6, cap);
  if (seconds <= 0) {
    throw new PolicyViolationError(`${media} duration must be > 0`, "duration_zero");
  }
  if (seconds > cap) {
    throw new PolicyViolationError(
      `${media} duration ${seconds}s exceeds cap of ${cap}s`,
      "duration_cap",
    );
  }
  return seconds;
}

// Pointer-only weight reference. Never a URL, never downloaded.
function weightPointer(name) {
  return {
    source: "local_pointer",
    name,
    autoDownload: false,
    trainingAllowed: false,
  };
}

// Build a deterministic ComfyUI-shaped node graph for each media type.
// Node ids are fixed strings so the compiled graph is byte-stable.
function buildGraph(media, spec, params, durationSeconds) {
  const positive = spec.intent ?? "";
  const negative = spec.negativeIntent ?? "";
  const checkpoint = spec.checkpoint ?? "PLACEHOLDER_local_checkpoint.safetensors";

  const base = {
    checkpoint_loader: {
      class_type: "CheckpointLoaderSimple",
      inputs: { ckpt_name: weightPointer(checkpoint) },
    },
    positive_prompt: {
      class_type: "CLIPTextEncode",
      inputs: { text: positive, clip: ["checkpoint_loader", 1] },
    },
    negative_prompt: {
      class_type: "CLIPTextEncode",
      inputs: { text: negative, clip: ["checkpoint_loader", 1] },
    },
  };

  if (media === "image") {
    return {
      ...base,
      latent: {
        class_type: "EmptyLatentImage",
        inputs: { width: 768, height: 768, batch_size: 1 },
      },
      sampler: {
        class_type: "KSampler",
        inputs: {
          seed: params.seed,
          steps: params.steps,
          cfg: params.cfg,
          sampler_name: "euler",
          scheduler: "normal",
          denoise: 1,
          model: ["checkpoint_loader", 0],
          positive: ["positive_prompt", 0],
          negative: ["negative_prompt", 0],
          latent_image: ["latent", 0],
        },
      },
      vae_decode: {
        class_type: "VAEDecode",
        inputs: { samples: ["sampler", 0], vae: ["checkpoint_loader", 2] },
      },
      save: {
        class_type: "SaveImage",
        inputs: { filename_prefix: "wha_fable5", images: ["vae_decode", 0] },
      },
    };
  }

  if (media === "video") {
    const fps = 12;
    const frames = Math.max(1, Math.round(durationSeconds * fps));
    return {
      ...base,
      latent: {
        class_type: "EmptyLatentImage",
        inputs: { width: 512, height: 512, batch_size: frames },
      },
      sampler: {
        class_type: "KSampler",
        inputs: {
          seed: params.seed,
          steps: params.steps,
          cfg: params.cfg,
          sampler_name: "euler",
          scheduler: "normal",
          denoise: 1,
          model: ["checkpoint_loader", 0],
          positive: ["positive_prompt", 0],
          negative: ["negative_prompt", 0],
          latent_image: ["latent", 0],
        },
      },
      vae_decode: {
        class_type: "VAEDecode",
        inputs: { samples: ["sampler", 0], vae: ["checkpoint_loader", 2] },
      },
      video_combine: {
        class_type: "VHS_VideoCombine",
        inputs: {
          frame_rate: fps,
          loop_count: 0,
          filename_prefix: "wha_fable5_video",
          format: "video/h264-mp4",
          images: ["vae_decode", 0],
        },
      },
    };
  }

  // audio
  const audioCheckpoint = spec.checkpoint ?? "PLACEHOLDER_local_audio_model.safetensors";
  return {
    audio_loader: {
      class_type: "CheckpointLoaderSimple",
      inputs: { ckpt_name: weightPointer(audioCheckpoint) },
    },
    positive_prompt: {
      class_type: "CLIPTextEncode",
      inputs: { text: positive, clip: ["audio_loader", 1] },
    },
    negative_prompt: {
      class_type: "CLIPTextEncode",
      inputs: { text: negative, clip: ["audio_loader", 1] },
    },
    sampler: {
      class_type: "KSamplerAudio",
      inputs: {
        seed: params.seed,
        steps: params.steps,
        cfg: params.cfg,
        seconds: durationSeconds,
        model: ["audio_loader", 0],
        positive: ["positive_prompt", 0],
        negative: ["negative_prompt", 0],
      },
    },
    save: {
      class_type: "SaveAudio",
      inputs: { filename_prefix: "wha_fable5_audio", audio: ["sampler", 0] },
    },
  };
}

/**
 * Compile a spell descriptor into a deterministic ComfyUI manifest.
 * Never performs I/O.
 *
 * @param {object} spec  { media, intent, negativeIntent?, roles?, tags?,
 *                         spell?, element?, quality?, stability?,
 *                         durationSeconds?, checkpoint? }
 * @param {object} [options] { role, policy }
 *   role: one of ADAPTER_ROLES (default "unification_target")
 *   policy: overrides merged onto DEFAULT_POLICY (only tightening allowed)
 * @returns {object} manifest
 */
export function compileManifest(spec = {}, options = {}) {
  const role = options.role ?? "unification_target";
  if (!ADAPTER_ROLES.includes(role)) {
    throw new PolicyViolationError(`unknown adapter role: ${role}`, "unknown_role");
  }

  const media = spec.media ?? "image";
  if (!MEDIA_TYPES.includes(media)) {
    throw new PolicyViolationError(`unknown media type: ${media}`, "unknown_media");
  }

  const policy = normalizePolicy(options.policy);

  // Safety first: reject prohibited content and real-person likeness.
  assertContentAllowed(spec);

  const roles = normalizeRoles(spec.roles, policy);
  const durationSeconds = assertMediaDuration(media, spec.durationSeconds, policy);
  const params = deriveParameters(spec);
  const graph = buildGraph(media, spec, params, durationSeconds);

  const core = {
    schema: "fable5.comfyui.manifest.v1",
    adapterVersion: ADAPTER_VERSION,
    role,
    media,
    provenance: PROVENANCE,
    endpoints: {
      fable5: ADAPTER_ENDPOINTS.fable5,
      comfyui: ADAPTER_ENDPOINTS.comfyui,
      eden: ADAPTER_ENDPOINTS.eden,
    },
    policy,
    intent: spec.intent ?? "",
    negativeIntent: spec.negativeIntent ?? "",
    roles,
    tags: Array.isArray(spec.tags) ? [...spec.tags] : [],
    parameters: params,
    durationSeconds,
    weights: { source: "local_pointer", autoDownload: false },
    prompt: graph, // ComfyUI /prompt "prompt" payload
  };

  // Deterministic manifest id over the stable core (excludes the id itself).
  const manifestId = fnv1a(JSON.stringify(core));
  return { manifestId, ...core };
}

// True only for loopback endpoints. Anything else is an external request.
export function isLocalEndpoint(url) {
  try {
    const { hostname } = new URL(url);
    return LOOPBACK_HOSTS.has(hostname);
  } catch {
    return false;
  }
}

// Assert a manifest carries no auto-download / training / URL-fetch requests.
function assertPointerOnly(manifest) {
  const json = JSON.stringify(manifest);
  if (manifest.policy.trainingAllowed || manifest.policy.autoDownloadWeights) {
    throw new PolicyViolationError("training/auto-download must stay disabled", "pointer_only");
  }
  if (/https?:\/\//i.test(JSON.stringify(manifest.prompt))) {
    throw new PolicyViolationError("weight pointers must not contain URLs", "pointer_only");
  }
  if (/"autoDownload"\s*:\s*true/.test(json)) {
    throw new PolicyViolationError("auto-download of weights is forbidden", "pointer_only");
  }
}

/**
 * Read-only local health probe of ComfyUI's /system_stats.
 * Refuses non-loopback endpoints and does nothing unless the caller opts in
 * with policy.allowLocalRequests:true. Uses an injectable fetch for testing.
 */
export async function checkComfyUiHealth(options = {}) {
  const policy = normalizePolicy(options.policy);
  const endpoint = options.endpoint ?? ADAPTER_ENDPOINTS.comfyui;
  if (!isLocalEndpoint(endpoint)) {
    throw new PolicyViolationError(
      `refusing non-local endpoint (externalRequests=0): ${endpoint}`,
      "non_local_endpoint",
    );
  }
  if (!policy.allowLocalRequests) {
    return { ok: false, reason: "local_requests_disabled", endpoint };
  }
  const doFetch = options.fetchImpl ?? globalThis.fetch;
  if (typeof doFetch !== "function") {
    return { ok: false, reason: "no_fetch_available", endpoint };
  }
  const url = `${endpoint.replace(/\/+$/, "")}${ADAPTER_ENDPOINTS.comfyuiHealthPath}`;
  try {
    const res = await doFetch(url, { method: "GET" });
    if (!res.ok) return { ok: false, reason: `http_${res.status}`, endpoint };
    const stats = await res.json();
    return { ok: true, endpoint, stats };
  } catch (err) {
    return { ok: false, reason: err.message, endpoint };
  }
}

/**
 * Queue a compiled manifest to a *local* ComfyUI. Gated: requires
 * options.approve === true AND policy.mode === "queue" AND
 * policy.allowLocalRequests === true. Otherwise returns a manifest_only result
 * and performs no I/O.
 *
 * @returns {Promise<{queued:boolean, ...}>}
 */
export async function queueManifest(manifest, options = {}) {
  if (!manifest || manifest.schema !== "fable5.comfyui.manifest.v1") {
    throw new PolicyViolationError("invalid or missing manifest", "bad_manifest");
  }
  assertPointerOnly(manifest);

  const policy = normalizePolicy({ ...manifest.policy, ...options.policy });
  const approve = options.approve === true;

  if (policy.mode !== "queue") {
    return { queued: false, reason: "manifest_only", manifestId: manifest.manifestId };
  }
  if (!approve) {
    return { queued: false, reason: "approval_required", manifestId: manifest.manifestId };
  }

  const endpoint = options.endpoint ?? ADAPTER_ENDPOINTS.comfyui;
  if (!isLocalEndpoint(endpoint)) {
    throw new PolicyViolationError(
      `refusing non-local endpoint (externalRequests=0): ${endpoint}`,
      "non_local_endpoint",
    );
  }
  if (!policy.allowLocalRequests) {
    return { queued: false, reason: "local_requests_disabled", manifestId: manifest.manifestId };
  }

  const doFetch = options.fetchImpl ?? globalThis.fetch;
  if (typeof doFetch !== "function") {
    return { queued: false, reason: "no_fetch_available", manifestId: manifest.manifestId };
  }

  const url = `${endpoint.replace(/\/+$/, "")}/prompt`;
  const res = await doFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt: manifest.prompt, client_id: manifest.manifestId }),
  });
  if (!res.ok) {
    return { queued: false, reason: `http_${res.status}`, manifestId: manifest.manifestId };
  }
  const body = await res.json();
  return { queued: true, manifestId: manifest.manifestId, promptId: body.prompt_id ?? null };
}

export default {
  ADAPTER_VERSION,
  ADAPTER_ENDPOINTS,
  ADAPTER_ROLES,
  MEDIA_TYPES,
  DEFAULT_POLICY,
  PROVENANCE,
  PROHIBITED_PATTERNS,
  normalizePolicy,
  screenContent,
  assertContentAllowed,
  compileManifest,
  isLocalEndpoint,
  checkComfyUiHealth,
  queueManifest,
  ContentRejectedError,
  PolicyViolationError,
};
