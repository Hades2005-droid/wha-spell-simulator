import { test } from 'node:test';
import assert from 'node:assert';
import { HistoryStack, createSnapshot, restoreSnapshot } from '../src/utils/history.js';
import { DEFAULT_SHORTCUTS } from '../src/utils/keyboard.js';

test('Feature: Undo/Redo History', async (t) => {
  await t.test('HistoryStack', async (t2) => {
    await t2.test('should push states onto stack', () => {
      const history = new HistoryStack();
      history.push({ strokes: [1, 2, 3], timestamp: Date.now() });

      assert.ok(history.canUndo(), 'should be able to undo after push');
      assert.strictEqual(history.getSize().undo, 1);
    });

    await t2.test('should undo to previous state', () => {
      const history = new HistoryStack();
      history.push({ data: 'state1' });
      history.push({ data: 'state2' });

      const previous = history.undo();
      assert.deepStrictEqual(previous, { data: 'state1' });
      assert.ok(history.canRedo(), 'should be able to redo after undo');
    });

    await t2.test('should redo to next state', () => {
      const history = new HistoryStack();
      history.push({ data: 'state1' });
      history.push({ data: 'state2' });

      history.undo();
      const redone = history.redo();

      assert.deepStrictEqual(redone, { data: 'state2' });
      assert.strictEqual(history.canRedo(), false, 'should not be able to redo');
    });

    await t2.test('should clear redo stack on new push', () => {
      const history = new HistoryStack();
      history.push({ data: 'state1' });
      history.push({ data: 'state2' });

      history.undo();
      assert.ok(history.canRedo(), 'should have redo available');

      history.push({ data: 'state3' });
      assert.strictEqual(history.canRedo(), false, 'redo stack should be cleared');
    });

    await t2.test('should respect max size', () => {
      const history = new HistoryStack(3);

      history.push({ data: '1' });
      history.push({ data: '2' });
      history.push({ data: '3' });
      history.push({ data: '4' });

      assert.strictEqual(history.getSize().undo, 3, 'should limit to max size');
    });

    await t2.test('should clear history', () => {
      const history = new HistoryStack();
      history.push({ data: 'state1' });

      history.clear();
      assert.strictEqual(history.canUndo(), false);
      assert.strictEqual(history.canRedo(), false);
    });
  });

  await t.test('State Snapshots', async (t2) => {
    await t2.test('should create snapshot of strokes', () => {
      const strokes = [{ id: '1', points: [{ x: 0, y: 0 }] }];
      const snapshot = createSnapshot(strokes);

      assert.ok(snapshot.timestamp);
      assert.deepStrictEqual(snapshot.strokes, strokes);
    });

    await t2.test('should restore snapshot', () => {
      const strokes = [{ id: '1', points: [{ x: 0, y: 0 }] }];
      const snapshot = createSnapshot(strokes);

      const restored = restoreSnapshot(snapshot);
      assert.deepStrictEqual(restored, strokes);
    });

    await t2.test('should handle null snapshot', () => {
      const restored = restoreSnapshot(null);
      assert.deepStrictEqual(restored, []);
    });
  });
});

test('Feature: Keyboard Shortcuts', async (t) => {
  await t.test('DEFAULT_SHORTCUTS', async (t2) => {
    await t2.test('should have UNDO shortcut', () => {
      assert.strictEqual(DEFAULT_SHORTCUTS.UNDO, 'ctrl+z');
    });

    await t2.test('should have REDO shortcut', () => {
      assert.strictEqual(DEFAULT_SHORTCUTS.REDO, 'ctrl+shift+z');
    });

    await t2.test('should have CLEAR shortcut', () => {
      assert.strictEqual(DEFAULT_SHORTCUTS.CLEAR, 'ctrl+alt+c');
    });

    await t2.test('should have EXPORT shortcut', () => {
      assert.strictEqual(DEFAULT_SHORTCUTS.EXPORT, 'ctrl+s');
    });

    await t2.test('should have IMPORT shortcut', () => {
      assert.strictEqual(DEFAULT_SHORTCUTS.IMPORT, 'ctrl+o');
    });

    await t2.test('should have DEBUG shortcut', () => {
      assert.strictEqual(DEFAULT_SHORTCUTS.DEBUG, 'ctrl+alt+d');
    });
  });
});
