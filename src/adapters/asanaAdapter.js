/**
 * Wha-Spell-Simulator Asana Adapter.
 * Reports glyph recognition and spell compilation metrics to Asana.
 *
 * Bridges parser/compiler output to NWW Asana Connector for soul-resonance tracking.
 * Supports both Node.js (via fetch polyfill) and browser environments.
 */

/**
 * Spell compilation metrics.
 * @typedef {Object} SpellMetrics
 * @property {string} timestamp - ISO format timestamp
 * @property {number} glyphAccuracy - Glyph recognition accuracy 0-100
 * @property {number} compilationSuccess - Spell compilation success 0-100
 * @property {number} spellsCompiled - Count of spells compiled
 * @property {number} copyTechniquePrecision - Copy technique effectiveness 0-100
 * @property {string} lastGlyphName - Name of the last glyph recognized
 * @property {number} drawingConfidence - Confidence score 0-100
 * @property {number?} renderTime - Render time in milliseconds
 * @property {string?} errorMessage - Error description if failed
 */

/**
 * Glyph recognition metrics.
 * @typedef {Object} GlyphMetrics
 * @property {string} timestamp - ISO format timestamp
 * @property {string} glyphName - Name of recognized glyph
 * @property {number} accuracy - Recognition accuracy 0-100
 * @property {number} confidence - Confidence score 0-100
 * @property {number} processingTime - Time in milliseconds
 * @property {number} strokeCount - Number of strokes in glyph
 * @property {boolean} success - Did recognition succeed
 * @property {string?} errorMessage - Error description if failed
 */

/**
 * Asana API client wrapper for browser/Node.js environments.
 * Minimal implementation for spell simulator metrics.
 */
class AsanaClientJS {
  constructor(apiToken, workspaceId) {
    this.apiToken = apiToken;
    this.workspaceId = workspaceId;
    this.baseUrl = 'https://app.asana.com/api/1.0';
    this.isNode = typeof process !== 'undefined' && process.versions && process.versions.node;
  }

  /**
   * Make an API request.
   * @param {string} method - HTTP method
   * @param {string} endpoint - API endpoint
   * @param {Object?} data - Request body
   * @returns {Promise<Object>} Response data
   */
  async _request(method, endpoint, data = null) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Authorization': `Bearer ${this.apiToken}`,
      'Content-Type': 'application/json',
      'User-Agent': 'NWW-Asana-Connector-JS/0.1.0',
    };

    const options = {
      method,
      headers,
    };

    if (data) {
      options.body = JSON.stringify({ data });
    }

    try {
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`Asana API error: ${response.status}`);
      }
      const json = await response.json();
      return json.data || {};
    } catch (error) {
      console.error(`Asana API request failed (${endpoint}):`, error.message);
      throw error;
    }
  }

  async createTask(name, projectId, description, customFields = {}) {
    const data = {
      name,
      projects: [projectId],
    };
    if (description) {
      data.notes = description;
    }
    if (Object.keys(customFields).length > 0) {
      data.custom_fields = customFields;
    }
    return this._request('POST', '/tasks', data);
  }

  async addTaskComment(taskId, text) {
    return this._request('POST', `/tasks/${taskId}/stories`, { text });
  }

  async getProject(projectId) {
    return this._request('GET', `/projects/${projectId}`);
  }

  async testConnection() {
    try {
      const user = await this._request('GET', '/users/me');
      return !!user.gid;
    } catch {
      return false;
    }
  }
}

/**
 * Data mapper for spell simulator metrics (browser-compatible).
 * Maps technical metrics to magical custom field values.
 */
class DataMapperJS {
  constructor(fieldIds = {}) {
    this.fieldIds = fieldIds;
  }

  mapResonanceScore(technicalScore) {
    const fieldId = this.fieldIds.resonance_score;
    if (!fieldId) return {};
    return {
      gid: fieldId,
      number_value: Math.min(100, Math.max(0, technicalScore)),
    };
  }

  mapTechniqueMastery(masteryLevel) {
    const fieldId = this.fieldIds.technique_mastery;
    if (!fieldId) return {};
    const validLevels = ['Novice', 'Adept', 'Expert', 'Master', 'Transcendent'];
    const level = validLevels.includes(masteryLevel) ? masteryLevel : 'Adept';
    return {
      gid: fieldId,
      text_value: level,
    };
  }

  mapSoulAlignment(descriptor) {
    const fieldId = this.fieldIds.soul_alignment;
    if (!fieldId) return {};
    return {
      gid: fieldId,
      text_value: descriptor,
    };
  }

  mapCopyTechnique(percentage) {
    const fieldId = this.fieldIds.copy_technique_success;
    if (!fieldId) return {};
    return {
      gid: fieldId,
      number_value: Math.min(100, Math.max(0, percentage)),
    };
  }

  mapMetricsJson(metrics) {
    const fieldId = this.fieldIds.metrics_json;
    if (!fieldId) return {};
    return {
      gid: fieldId,
      text_value: JSON.stringify(metrics),
    };
  }

  mapLastReported(timestamp = null) {
    const fieldId = this.fieldIds.last_reported;
    if (!fieldId) return {};
    const ts = timestamp || new Date();
    return {
      gid: fieldId,
      date_value: ts.toISOString().split('T')[0],
    };
  }

  scoreToMastery(score) {
    if (score >= 90) return 'Master';
    if (score >= 75) return 'Expert';
    if (score >= 60) return 'Adept';
    if (score >= 40) return 'Novice';
    return 'Novice';
  }

  scoreToSoulAlignment(score) {
    if (score >= 90) return 'Transcendent Resonance';
    if (score >= 75) return 'Ascending Harmony';
    if (score >= 60) return 'Harmonious Synthesis';
    if (score >= 45) return 'Emerging Potential';
    return 'Seeking Alignment';
  }
}

/**
 * SpellSimulatorAsanaReporter - Report spell compilation and glyph metrics.
 */
class SpellSimulatorAsanaReporter {
  constructor(config = null) {
    this.apiToken = config?.apiToken || process.env?.ASANA_API_TOKEN;
    this.workspaceId = config?.workspaceId || process.env?.ASANA_WORKSPACE_ID;
    this.projectId = config?.projectIds?.spell_simulator || process.env?.ASANA_PROJECT_SPELLSIM;

    if (!this.apiToken || !this.workspaceId || !this.projectId) {
      throw new Error(
        'Missing Asana configuration: ASANA_API_TOKEN, ASANA_WORKSPACE_ID, ASANA_PROJECT_SPELLSIM'
      );
    }

    this.client = new AsanaClientJS(this.apiToken, this.workspaceId);
    this.fieldIds = this._loadFieldIds();
    this.mapper = new DataMapperJS(this.fieldIds);
  }

  _loadFieldIds() {
    return {
      resonance_score: process.env?.ASANA_FIELD_RESONANCE_SCORE,
      technique_mastery: process.env?.ASANA_FIELD_TECHNIQUE_MASTERY,
      soul_alignment: process.env?.ASANA_FIELD_SOUL_ALIGNMENT,
      copy_technique_success: process.env?.ASANA_FIELD_COPY_TECHNIQUE,
      last_reported: process.env?.ASANA_FIELD_LAST_REPORTED,
      metrics_json: process.env?.ASANA_FIELD_METRICS_JSON,
    };
  }

  /**
   * Report a spell compilation event.
   * @param {SpellMetrics} metrics
   * @returns {Promise<Object>} Created task
   */
  async reportSpellCompilation(metrics) {
    const avgScore = (metrics.glyphAccuracy + metrics.compilationSuccess) / 2;
    const mastery = this.mapper.scoreToMastery(avgScore);
    const resonance = this.mapper.scoreToSoulAlignment(avgScore);

    const taskName = `Spell Compilation: ${metrics.lastGlyphName || 'Unnamed'} - ${metrics.timestamp.split('T')[0]}`;
    const taskDescription = this._buildSpellDescription(metrics);

    const customFields = {
      ...this.mapper.mapResonanceScore(avgScore),
      ...this.mapper.mapTechniqueMastery(mastery),
      ...this.mapper.mapSoulAlignment(resonance),
      ...this.mapper.mapCopyTechnique(metrics.copyTechniquePrecision),
      ...this.mapper.mapMetricsJson({
        glyph_accuracy: metrics.glyphAccuracy,
        compilation_success: metrics.compilationSuccess,
        spells_compiled: metrics.spellsCompiled,
        copy_technique: metrics.copyTechniquePrecision,
        confidence: metrics.drawingConfidence,
        render_time_ms: metrics.renderTime,
      }),
      ...this.mapper.mapLastReported(),
    };

    const task = await this.client.createTask(
      taskName,
      this.projectId,
      taskDescription,
      customFields
    );

    // Add metric comment
    const comment = this._formatMetricComment(metrics, 'Spell Compilation');
    await this.client.addTaskComment(task.gid, comment);

    return task;
  }

  /**
   * Report a glyph recognition event.
   * @param {GlyphMetrics} metrics
   * @returns {Promise<Object>} Created task
   */
  async reportGlyphRecognition(metrics) {
    const taskName = `Glyph Recognition: ${metrics.glyphName} - ${metrics.timestamp.split('T')[0]}`;
    const taskDescription = this._buildGlyphDescription(metrics);

    const mastery = this.mapper.scoreToMastery(metrics.accuracy);
    const resonance = metrics.success
      ? this.mapper.scoreToSoulAlignment(metrics.confidence)
      : 'Seeking Alignment';

    const customFields = {
      ...this.mapper.mapResonanceScore(metrics.accuracy),
      ...this.mapper.mapTechniqueMastery(mastery),
      ...this.mapper.mapSoulAlignment(resonance),
      ...this.mapper.mapMetricsJson({
        glyph_name: metrics.glyphName,
        accuracy: metrics.accuracy,
        confidence: metrics.confidence,
        processing_time_ms: metrics.processingTime,
        stroke_count: metrics.strokeCount,
        success: metrics.success,
      }),
      ...this.mapper.mapLastReported(),
    };

    const task = await this.client.createTask(
      taskName,
      this.projectId,
      taskDescription,
      customFields
    );

    const comment = this._formatMetricComment(metrics, 'Glyph Recognition');
    await this.client.addTaskComment(task.gid, comment);

    return task;
  }

  /**
   * Create a daily summary task.
   * @param {string?} date
   * @returns {Promise<Object>} Created task
   */
  async createDailySummary(date = null) {
    if (!date) {
      date = new Date().toISOString().split('T')[0];
    }

    const taskName = `Daily Glyph Mastery Summary - ${date}`;
    const taskDescription = `**Wha-Spell Simulator Daily Report**\n\nDate: ${date}\n\n_This is an automated aggregated summary of all glyph recognition and spell compilation activities for this day._`;

    return this.client.createTask(
      taskName,
      this.projectId,
      taskDescription,
      this.mapper.mapLastReported()
    );
  }

  _buildSpellDescription(metrics) {
    const status = metrics.compilationSuccess >= 85 ? '✅ Success' : '⚠️ Partial';
    return `${status}

**Glyph**: ${metrics.lastGlyphName || 'Unnamed'}
**Timestamp**: ${metrics.timestamp}
**Glyph Accuracy**: ${metrics.glyphAccuracy.toFixed(1)}%
**Compilation Success**: ${metrics.compilationSuccess.toFixed(1)}%
**Spells Compiled**: ${metrics.spellsCompiled}
**Copy Technique Precision**: ${metrics.copyTechniquePrecision.toFixed(1)}%
**Drawing Confidence**: ${metrics.drawingConfidence.toFixed(1)}%
${metrics.renderTime ? `**Render Time**: ${metrics.renderTime.toFixed(1)}ms` : ''}
${metrics.errorMessage ? `**Error**: ${metrics.errorMessage}` : ''}
`;
  }

  _buildGlyphDescription(metrics) {
    const status = metrics.success ? '✅ Recognized' : '❌ Failed';
    return `${status}

**Glyph**: ${metrics.glyphName}
**Timestamp**: ${metrics.timestamp}
**Accuracy**: ${metrics.accuracy.toFixed(1)}%
**Confidence**: ${metrics.confidence.toFixed(1)}%
**Processing Time**: ${metrics.processingTime.toFixed(1)}ms
**Strokes**: ${metrics.strokeCount}
${metrics.errorMessage ? `**Error**: ${metrics.errorMessage}` : ''}
`;
  }

  _formatMetricComment(metrics, metricType) {
    return `**${metricType} Metric Report**

Raw Data (JSON):
\`\`\`json
${JSON.stringify(metrics, null, 2)}
\`\`\`
`;
  }

  async healthCheck() {
    try {
      const project = await this.client.getProject(this.projectId);
      return !!project.gid;
    } catch (error) {
      console.error('⚠️ Health check failed:', error.message);
      return false;
    }
  }
}

// ============ Convenience Functions ============

/**
 * Report spell compilation metrics.
 * @param {Partial<SpellMetrics>} metrics
 * @returns {Promise<Object>}
 */
export async function reportSpellCompilation(metrics) {
  const reporter = new SpellSimulatorAsanaReporter();
  const fullMetrics = {
    timestamp: new Date().toISOString(),
    glyphAccuracy: 85,
    compilationSuccess: 90,
    spellsCompiled: 1,
    copyTechniquePrecision: 88,
    lastGlyphName: 'Unknown',
    drawingConfidence: 92,
    ...metrics,
  };
  return reporter.reportSpellCompilation(fullMetrics);
}

/**
 * Report glyph recognition metrics.
 * @param {Partial<GlyphMetrics>} metrics
 * @returns {Promise<Object>}
 */
export async function reportGlyphAccuracy(metrics) {
  const reporter = new SpellSimulatorAsanaReporter();
  const fullMetrics = {
    timestamp: new Date().toISOString(),
    glyphName: 'Unknown',
    accuracy: 85,
    confidence: 90,
    processingTime: 150,
    strokeCount: 5,
    success: true,
    ...metrics,
  };
  return reporter.reportGlyphRecognition(fullMetrics);
}

export { SpellSimulatorAsanaReporter, AsanaClientJS, DataMapperJS };
