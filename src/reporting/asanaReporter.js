/**
 * Asana reporter core.
 *
 * Orchestrates sanitized telemetry reporting to Asana. Every public method is
 * optional and non-blocking: when reporting is disabled or misconfigured the
 * methods resolve to a skipped result instead of throwing, so simulator
 * behavior is never affected by Asana availability.
 */

import { loadAsanaConfig } from './asanaConfig.js';
import { AsanaAdapter } from './asanaAdapter.js';
import { aggregateMetrics, formatMetricsComment, sanitizeLabel } from './asanaMetrics.js';

const skipped = (reason) => ({ ok: false, skipped: true, reason });

export class AsanaReporter {
  /**
   * @param {object} [options]
   * @param {ReturnType<typeof loadAsanaConfig>} [options.config]
   * @param {AsanaAdapter} [options.adapter]
   * @param {typeof fetch} [options.fetch]
   */
  constructor(options = {}) {
    this.config = options.config ?? loadAsanaConfig();
    this.adapter = options.adapter
      ?? new AsanaAdapter({ config: this.config, fetch: options.fetch });
  }

  get enabled() {
    return this.config.enabled && this.adapter.isReady();
  }

  /**
   * Report aggregate glyph telemetry as a comment (and optional task notes).
   *
   * @param {Array<object>} results Array of { spellIR, glyphAST }.
   * @param {object} [context] { milestone, appVersion, taskId, projectId }.
   * @returns {Promise<object>} result descriptor (never throws for network/config).
   */
  async reportMetrics(results, context = {}) {
    if (!this.enabled) {
      return skipped('asana reporting disabled or not configured');
    }

    const metrics = aggregateMetrics(results);
    const comment = formatMetricsComment(metrics, context);
    const taskId = context.taskId ?? this.config.taskId;
    const projectId = context.projectId ?? this.config.projectId;

    try {
      if (taskId) {
        await this.adapter.addComment(taskId, comment);
        return {
          ok: true, skipped: false, target: 'task', taskId, metrics,
        };
      }
      if (projectId) {
        const milestone = sanitizeLabel(context.milestone || 'Glyph Telemetry Report');
        const task = await this.adapter.createTask(projectId, {
          name: milestone,
          notes: comment,
        });
        return {
          ok: true, skipped: false, target: 'project', projectId, taskId: task?.gid, metrics,
        };
      }
      return skipped('no target task or project configured');
    } catch (error) {
      // Non-blocking: swallow the error into the result descriptor.
      return {
        ok: false, skipped: false, error: error.message, metrics,
      };
    }
  }

  /**
   * Post a sanitized milestone/task status update.
   *
   * @param {string} milestone Short label.
   * @param {string} [status] Short status note.
   * @returns {Promise<object>}
   */
  async reportMilestone(milestone, status = '') {
    if (!this.enabled) {
      return skipped('asana reporting disabled or not configured');
    }
    const { taskId } = this.config;
    const body = [
      `Milestone: ${sanitizeLabel(milestone)}`,
      status ? `Status: ${sanitizeLabel(status)}` : null,
      `Updated: ${new Date().toISOString()}`,
    ].filter(Boolean).join('\n');

    try {
      if (taskId) {
        await this.adapter.addComment(taskId, body);
        return { ok: true, skipped: false, taskId };
      }
      if (this.config.projectId) {
        const task = await this.adapter.createTask(this.config.projectId, {
          name: sanitizeLabel(milestone),
          notes: body,
        });
        return { ok: true, skipped: false, taskId: task?.gid };
      }
      return skipped('no target task or project configured');
    } catch (error) {
      return { ok: false, skipped: false, error: error.message };
    }
  }

  /** Validate credentials without mutating anything. */
  async verify() {
    if (!this.adapter.isReady()) {
      return { ok: false, reason: 'adapter not ready (missing token or fetch)' };
    }
    try {
      const me = await this.adapter.getMe();
      return { ok: true, user: me?.gid ?? null };
    } catch (error) {
      return { ok: false, error: error.message };
    }
  }
}

/**
 * Convenience factory that returns a reporter or `null` when disabled, so
 * callers can do `reporter?.reportMetrics(...)` safely.
 */
export function createAsanaReporter(options = {}) {
  const reporter = new AsanaReporter(options);
  return reporter;
}
