/**
 * History stack for undo/redo support
 */
export class HistoryStack {
  constructor(maxSize = 50) {
    this.undoStack = [];
    this.redoStack = [];
    this.maxSize = maxSize;
  }

  /**
   * Push a state onto the undo stack
   */
  push(state) {
    // Add state to undo stack
    this.undoStack.push(state);

    // Limit stack size
    if (this.undoStack.length > this.maxSize) {
      this.undoStack.shift();
    }

    // Clear redo stack when new action is performed
    this.redoStack = [];
  }

  /**
   * Undo to previous state
   */
  undo() {
    if (this.undoStack.length === 0) {
      return null;
    }

    const previousState = this.undoStack[this.undoStack.length - 1];
    this.redoStack.push(previousState);
    this.undoStack.pop();

    return this.undoStack.length > 0 ? this.undoStack[this.undoStack.length - 1] : null;
  }

  /**
   * Redo to next state
   */
  redo() {
    if (this.redoStack.length === 0) {
      return null;
    }

    const nextState = this.redoStack[this.redoStack.length - 1];
    this.redoStack.pop();
    this.undoStack.push(nextState);

    return nextState;
  }

  /**
   * Check if undo is available
   */
  canUndo() {
    return this.undoStack.length > 0;
  }

  /**
   * Check if redo is available
   */
  canRedo() {
    return this.redoStack.length > 0;
  }

  /**
   * Clear all history
   */
  clear() {
    this.undoStack = [];
    this.redoStack = [];
  }

  /**
   * Get current history size
   */
  getSize() {
    return {
      undo: this.undoStack.length,
      redo: this.redoStack.length,
    };
  }
}

/**
 * State snapshot helper
 */
export function createSnapshot(strokes) {
  return {
    strokes: JSON.parse(JSON.stringify(strokes)),
    timestamp: Date.now(),
  };
}

/**
 * Restore state from snapshot
 */
export function restoreSnapshot(snapshot) {
  return snapshot ? snapshot.strokes : [];
}
