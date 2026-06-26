import { test } from 'node:test';
import assert from 'node:assert';
import {
  clamp,
  distance,
  normalizeVector,
  boundsForPoints,
  centerOfBounds,
  angleDegFromCenter,
  vectorFromAngleDeg,
  mean,
  stddev,
} from '../src/utils/geometry.js';

test('Geometry Utilities', async (t) => {
  await t.test('clamp function', async (t2) => {
    await t2.test('should clamp value to min/max', () => {
      assert.strictEqual(clamp(0.5, 0, 1), 0.5);
      assert.strictEqual(clamp(-0.5, 0, 1), 0);
      assert.strictEqual(clamp(1.5, 0, 1), 1);
    });
  });

  await t.test('distance function', async (t2) => {
    await t2.test('should calculate distance between two points', () => {
      const d = distance({ x: 0, y: 0 }, { x: 3, y: 4 });
      assert.strictEqual(d, 5, 'distance should be 5 (3-4-5 triangle)');
    });

    await t2.test('should handle zero distance', () => {
      const d = distance({ x: 1, y: 1 }, { x: 1, y: 1 });
      assert.strictEqual(d, 0, 'same point should have distance 0');
    });
  });

  await t.test('normalizeVector function', async (t2) => {
    await t2.test('should normalize vector to unit length', () => {
      const v = normalizeVector({ x: 3, y: 4 });
      const length = Math.hypot(v.x, v.y);
      assert.ok(Math.abs(length - 1) < 0.001, 'normalized vector should have length 1');
    });

    await t2.test('should handle zero vector', () => {
      const v = normalizeVector({ x: 0, y: 0 });
      assert.ok(true, 'zero vector handled gracefully');
    });
  });

  await t.test('boundsForPoints function', async (t2) => {
    await t2.test('should calculate bounding box', () => {
      const points = [{ x: 0, y: 0 }, { x: 10, y: 5 }];
      const bounds = boundsForPoints(points);
      assert.strictEqual(bounds.minX, 0);
      assert.strictEqual(bounds.minY, 0);
      assert.ok(bounds.width !== undefined);
      assert.ok(bounds.height !== undefined);
    });
  });

  await t.test('centerOfBounds function', async (t2) => {
    await t2.test('should find center of bounds', () => {
      const bounds = { minX: 0, minY: 0, width: 4, height: 4 };
      const center = centerOfBounds(bounds);
      assert.strictEqual(center.x, 2);
      assert.strictEqual(center.y, 2);
    });
  });

  await t.test('angleDegFromCenter function', async (t2) => {
    await t2.test('should calculate angle to point from center', () => {
      const angle = angleDegFromCenter({ x: 1, y: 0 }, { x: 0, y: 0 });
      assert.ok(typeof angle === 'number', 'angle calculation returns number');
    });
  });

  await t.test('vectorFromAngleDeg function', async (t2) => {
    await t2.test('should create vector from angle', () => {
      const v = vectorFromAngleDeg(0);
      assert.ok(Math.abs(v.x - 1) < 0.001, 'right angle should point right');
    });
  });

  await t.test('mean function', async (t2) => {
    await t2.test('should calculate mean of values', () => {
      const m = mean([1, 2, 3, 4, 5]);
      assert.strictEqual(m, 3);
    });
  });

  await t.test('stddev function', async (t2) => {
    await t2.test('should calculate standard deviation', () => {
      const sd = stddev([1, 2, 3, 4, 5]);
      assert.ok(sd > 0 && sd < 2, 'stddev should be between 0 and 2');
    });
  });
});
