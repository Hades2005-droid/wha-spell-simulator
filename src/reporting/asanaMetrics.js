/**
 * Aggregation of spell-simulator telemetry into report-ready metrics.
 *
 * A "sample" is derived from a compiled spell (SpellIR) plus its source glyph
 * AST. All values are numeric or boolean; no raw stroke coordinates, canvas
 * pixels, user identifiers, or free-form text are retained. This keeps the
 * reported payload sanitized by construction.
 */

function clamp01(value) {
  if (typeof value !== 'number' || Number.isNaN(value)) {
    return 0;
  }
  return Math.min(1, Math.max(0, value));
}

function average(values) {
  const nums = values.filter((v) => typeof v === 'number' && !Number.isNaN(v));
  if (nums.length === 0) {
    return 0;
  }
  return nums.reduce((sum, v) => sum + v, 0) / nums.length;
}

function round(value, digits = 3) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}

/**
 * Reduce a compiled spell result into a single sanitized sample.
 *
 * @param {object} result
 * @param {object} [result.spellIR]  Output of compileSpell.
 * @param {object} [result.glyphAST] Source glyph AST (for recognition stats).
 * @returns {{
 *   valid: boolean,
 *   recognitionAccuracy: number,
 *   compiled: boolean,
 *   copyEffectiveness: number,
 *   soulResonance: number,
 * }}
 */
export function toSample(result = {}) {
  const spell = result.spellIR ?? {};
  const glyph = result.glyphAST ?? {};

  const valid = Boolean(spell.valid);

  // Glyph recognition accuracy: how confidently symbols were recognized.
  const primaryConfidence = glyph.primarySigil?.confidence
    ?? spell.elementConfidence
    ?? 0;
  const signConfidences = (glyph.signs ?? []).map((s) => s?.confidence ?? 0);
  const recognitionAccuracy = clamp01(
    average([primaryConfidence, ...signConfidences].filter((v) => v > 0)) || primaryConfidence,
  );

  // Copy technique effectiveness: neatness/stability of the drawn glyph.
  const copyEffectiveness = clamp01(
    average([
      spell.neatness ?? glyph.globalMetrics?.neatness ?? 0,
      spell.stability ?? 0,
    ]),
  );

  // Soul alignment / resonance: coherence of intent (quality + directional
  // coherence + stability blended).
  const soulResonance = clamp01(
    (spell.quality ?? 0) * 0.5
      + (spell.directionCoherence ?? 0) * 0.25
      + (spell.stability ?? 0) * 0.25,
  );

  return {
    valid,
    recognitionAccuracy: round(recognitionAccuracy),
    compiled: valid,
    copyEffectiveness: round(copyEffectiveness),
    soulResonance: round(soulResonance),
  };
}

/**
 * Aggregate many results into report-ready metrics.
 *
 * @param {Array<object>} results Array of { spellIR, glyphAST } objects.
 * @returns {object} sanitized aggregate metrics.
 */
export function aggregateMetrics(results = []) {
  const samples = results.map(toSample);
  const total = samples.length;
  const compiledCount = samples.filter((s) => s.compiled).length;

  return {
    sampleCount: total,
    glyphRecognitionAccuracy: round(average(samples.map((s) => s.recognitionAccuracy))),
    compilationSuccessRate: total === 0 ? 0 : round(compiledCount / total),
    copyTechniqueEffectiveness: round(average(samples.map((s) => s.copyEffectiveness))),
    soulAlignmentResonance: round(average(samples.map((s) => s.soulResonance))),
    generatedAt: new Date().toISOString(),
  };
}

/**
 * Render aggregate metrics as a human-readable, sanitized comment body.
 *
 * @param {object} metrics Output of aggregateMetrics.
 * @param {object} [context]
 * @param {string} [context.milestone] Short milestone label (sanitized).
 * @param {string} [context.appVersion]
 * @returns {string}
 */
export function formatMetricsComment(metrics, context = {}) {
  const pct = (v) => `${round((v ?? 0) * 100, 1)}%`;
  const lines = [
    'Spell Simulator — Glyph Telemetry Report',
  ];
  if (context.milestone) {
    lines.push(`Milestone: ${sanitizeLabel(context.milestone)}`);
  }
  if (context.appVersion) {
    lines.push(`Build: ${sanitizeLabel(context.appVersion)}`);
  }
  lines.push('');
  lines.push(`Samples analyzed: ${metrics.sampleCount}`);
  lines.push(`Glyph recognition accuracy: ${pct(metrics.glyphRecognitionAccuracy)}`);
  lines.push(`Compilation success rate: ${pct(metrics.compilationSuccessRate)}`);
  lines.push(`Copy technique effectiveness: ${pct(metrics.copyTechniqueEffectiveness)}`);
  lines.push(`Soul alignment / resonance: ${pct(metrics.soulAlignmentResonance)}`);
  lines.push('');
  lines.push(`Generated: ${metrics.generatedAt}`);
  return lines.join('\n');
}

/**
 * Strip anything that is not a safe label character. Prevents accidental
 * leakage of secrets or injection of markup into Asana stories.
 */
export function sanitizeLabel(value) {
  return String(value ?? '')
    .replace(/[\r\n]+/g, ' ')
    .replace(/[^\w .:+/-]/g, '')
    .trim()
    .slice(0, 120);
}
