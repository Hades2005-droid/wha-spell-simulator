import { test } from 'node:test';
import assert from 'node:assert';
import { throttle, debounce } from '../src/utils/throttle.js';
import { memoize, memoizeDeep, memoizeWithExpiry } from '../src/utils/memoize.js';

test('Performance Utilities', async (t) => {
  await t.test('throttle function', async (t2) => {
    await t2.test('should limit function execution rate', async () => {
      let callCount = 0;
      const throttled = throttle(() => {
        callCount += 1;
      }, 10);

      throttled();
      throttled();
      throttled();

      assert.strictEqual(callCount, 1, 'should execute immediately on first call');

      await new Promise((resolve) => {
        setTimeout(() => {
          assert.ok(callCount >= 1, 'should have executed at least once');
          resolve();
        }, 20);
      });
    });
  });

  await t.test('debounce function', async (t2) => {
    await t2.test('should delay function execution', async () => {
      let callCount = 0;
      const debounced = debounce(() => {
        callCount += 1;
      }, 10);

      debounced();
      debounced();
      debounced();

      assert.strictEqual(callCount, 0, 'should not execute immediately');

      await new Promise((resolve) => {
        setTimeout(() => {
          assert.strictEqual(callCount, 1, 'should execute once after delay');
          resolve();
        }, 20);
      });
    });
  });

  await t.test('memoize function', async (t2) => {
    await t2.test('should cache single-argument results', () => {
      let callCount = 0;
      const expensive = (n) => {
        callCount += 1;
        return n * 2;
      };

      const memoized = memoize(expensive);

      assert.strictEqual(memoized(5), 10);
      assert.strictEqual(callCount, 1);

      assert.strictEqual(memoized(5), 10);
      assert.strictEqual(callCount, 1, 'should use cache on second call');

      assert.strictEqual(memoized(6), 12);
      assert.strictEqual(callCount, 2, 'should compute for new argument');
    });
  });

  await t.test('memoizeDeep function', async (t2) => {
    await t2.test('should cache multi-argument results', () => {
      let callCount = 0;
      const expensive = (a, b) => {
        callCount += 1;
        return a + b;
      };

      const memoized = memoizeDeep(expensive);

      assert.strictEqual(memoized(1, 2), 3);
      assert.strictEqual(callCount, 1);

      assert.strictEqual(memoized(1, 2), 3);
      assert.strictEqual(callCount, 1, 'should use cache on second call');

      assert.strictEqual(memoized(2, 3), 5);
      assert.strictEqual(callCount, 2);
    });
  });

  await t.test('memoizeWithExpiry function', async (t2) => {
    await t2.test('should expire cache after delay', async () => {
      let callCount = 0;
      const expensive = (n) => {
        callCount += 1;
        return n * 2;
      };

      const memoized = memoizeWithExpiry(expensive, 10);

      assert.strictEqual(memoized(5), 10);
      assert.strictEqual(callCount, 1);

      assert.strictEqual(memoized(5), 10);
      assert.strictEqual(callCount, 1, 'should use cache immediately');

      await new Promise((resolve) => {
        setTimeout(() => {
          assert.strictEqual(memoized(5), 10);
          assert.strictEqual(callCount, 2, 'should recompute after expiry');
          resolve();
        }, 15);
      });
    });
  });
});
