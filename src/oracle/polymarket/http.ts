/**
 * Defensive HTTP helper: timeouts, retries, Retry-After, circuit breaker.
 */

import { PolymarketError } from './types.ts';
import { SlidingWindowLimiter } from './rateLimit.ts';

export interface HttpOptions {
  fetchImpl?: typeof fetch;
  timeoutMs?: number;
  maxRetries?: number;
  now?: () => number;
  limiter?: SlidingWindowLimiter;
  circuitOpenAfter?: number;
  circuitCoolMs?: number;
}

export interface HttpResponse {
  ok: boolean;
  status: number;
  headers: Headers;
  text: string;
  json: unknown;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isRetryableStatus(status: number): boolean {
  return status === 408 || status === 425 || status === 429 || status >= 500;
}

export class DefensiveHttp {
  private readonly fetchImpl: typeof fetch;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;
  private readonly now: () => number;
  private readonly limiter: SlidingWindowLimiter | null;
  private readonly circuitOpenAfter: number;
  private readonly circuitCoolMs: number;
  private failures = 0;
  private circuitOpenUntil = 0;

  constructor(opts: HttpOptions = {}) {
    this.fetchImpl = opts.fetchImpl ?? fetch;
    this.timeoutMs = opts.timeoutMs ?? 8000;
    this.maxRetries = opts.maxRetries ?? 2;
    this.now = opts.now ?? (() => Date.now());
    this.limiter = opts.limiter ?? null;
    this.circuitOpenAfter = opts.circuitOpenAfter ?? 5;
    this.circuitCoolMs = opts.circuitCoolMs ?? 30_000;
  }

  private assertCircuit(): void {
    if (this.now() < this.circuitOpenUntil) {
      throw new PolymarketError(
        'circuit_open',
        `Polymarket circuit open for ${this.circuitOpenUntil - this.now()}ms`,
        { retryable: true },
      );
    }
  }

  private recordSuccess(): void {
    this.failures = 0;
  }

  private recordFailure(): void {
    this.failures += 1;
    if (this.failures >= this.circuitOpenAfter) {
      this.circuitOpenUntil = this.now() + this.circuitCoolMs;
      this.failures = 0;
    }
  }

  async get(url: string, init: RequestInit = {}): Promise<HttpResponse> {
    this.assertCircuit();

    let attempt = 0;
    let lastError: unknown = null;

    while (attempt <= this.maxRetries) {
      if (this.limiter) {
        let guard = 0;
        while (!this.limiter.tryAcquire()) {
          const wait = this.limiter.waitMs();
          if (wait > 5_000 || guard++ > 20) {
            throw new PolymarketError(
              'rate_limited_local',
              'Local rate budget exhausted',
              { retryable: true },
            );
          }
          await sleep(Math.min(wait, 250));
        }
      }

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.timeoutMs);
      try {
        const res = await this.fetchImpl(url, {
          ...init,
          method: 'GET',
          signal: controller.signal,
          headers: {
            Accept: 'application/json',
            ...(init.headers || {}),
          },
        });
        const text = await res.text();
        let json: unknown = null;
        if (text) {
          try {
            json = JSON.parse(text);
          } catch {
            json = null;
          }
        }

        if (!res.ok) {
          if (isRetryableStatus(res.status) && attempt < this.maxRetries) {
            const retryAfter = Number(res.headers.get('retry-after') || 0);
            const backoff =
              retryAfter > 0
                ? retryAfter * 1000
                : Math.min(2000, 150 * 2 ** attempt);
            attempt += 1;
            await sleep(backoff);
            continue;
          }
          this.recordFailure();
          throw new PolymarketError(
            'http_error',
            `HTTP ${res.status} for ${url}`,
            { status: res.status, retryable: isRetryableStatus(res.status) },
          );
        }

        this.recordSuccess();
        return { ok: true, status: res.status, headers: res.headers, text, json };
      } catch (err) {
        lastError = err;
        if (err instanceof PolymarketError) throw err;
        const aborted =
          err instanceof Error &&
          (err.name === 'AbortError' || /aborted/i.test(err.message));
        if (attempt < this.maxRetries) {
          attempt += 1;
          await sleep(Math.min(2000, 150 * 2 ** attempt));
          continue;
        }
        this.recordFailure();
        throw new PolymarketError(
          aborted ? 'timeout' : 'network_error',
          aborted ? `Timeout after ${this.timeoutMs}ms` : String(err),
          { retryable: true },
        );
      } finally {
        clearTimeout(timer);
      }
    }

    this.recordFailure();
    throw new PolymarketError('exhausted_retries', String(lastError), {
      retryable: true,
    });
  }
}
