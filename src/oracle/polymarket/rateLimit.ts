/**
 * Sliding-window token bucket for Polymarket Cloudflare limits.
 * Defaults stay well under documented caps (Gamma /markets 300/10s, CLOB /price 1500/10s).
 */

export interface RateLimiterOptions {
  capacity: number;
  windowMs: number;
  now?: () => number;
}

export class SlidingWindowLimiter {
  private readonly capacity: number;
  private readonly windowMs: number;
  private readonly now: () => number;
  private hits: number[] = [];

  constructor(opts: RateLimiterOptions) {
    this.capacity = Math.max(1, opts.capacity);
    this.windowMs = Math.max(1, opts.windowMs);
    this.now = opts.now ?? (() => Date.now());
  }

  private prune(t: number): void {
    const cutoff = t - this.windowMs;
    while (this.hits.length && this.hits[0]! < cutoff) {
      this.hits.shift();
    }
  }

  tryAcquire(): boolean {
    const t = this.now();
    this.prune(t);
    if (this.hits.length >= this.capacity) return false;
    this.hits.push(t);
    return true;
  }

  /** Milliseconds until a slot frees, or 0 if available. */
  waitMs(): number {
    const t = this.now();
    this.prune(t);
    if (this.hits.length < this.capacity) return 0;
    const oldest = this.hits[0]!;
    return Math.max(1, oldest + this.windowMs - t);
  }
}
