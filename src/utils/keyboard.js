/**
 * Keyboard shortcut manager
 */
export class KeyboardShortcuts {
  constructor() {
    this.shortcuts = new Map();
    this.isEnabled = true;

    // Only add event listener in browser environment
    if (typeof document !== 'undefined') {
      document.addEventListener('keydown', (e) => this.handleKeyDown(e));
    }
  }

  /**
   * Register a keyboard shortcut
   */
  register(keys, callback, description = '') {
    const keyString = this.normalizeKeys(keys);
    this.shortcuts.set(keyString, { callback, description, keys });
  }

  /**
   * Unregister a shortcut
   */
  unregister(keys) {
    const keyString = this.normalizeKeys(keys);
    this.shortcuts.delete(keyString);
  }

  /**
   * Handle keydown event
   */
  handleKeyDown(event) {
    if (!this.isEnabled) return;

    const keyString = this.getKeyString(event);
    const shortcut = this.shortcuts.get(keyString);

    if (shortcut) {
      event.preventDefault();
      shortcut.callback(event);
    }
  }

  /**
   * Get current key string from event
   */
  getKeyString(event) {
    const parts = [];

    if (event.ctrlKey || event.metaKey) parts.push('ctrl');
    if (event.shiftKey) parts.push('shift');
    if (event.altKey) parts.push('alt');

    // Add the actual key
    parts.push(event.key.toLowerCase());

    return parts.join('+');
  }

  /**
   * Normalize key string
   */
  normalizeKeys(keys) {
    return keys
      .toLowerCase()
      .split('+')
      .map((k) => k.trim())
      .join('+');
  }

  /**
   * Enable/disable shortcuts
   */
  enable() {
    this.isEnabled = true;
  }

  disable() {
    this.isEnabled = false;
  }

  /**
   * Get all registered shortcuts
   */
  getShortcuts() {
    return Array.from(this.shortcuts.values());
  }

  /**
   * Clear all shortcuts
   */
  clear() {
    this.shortcuts.clear();
  }
}

// Default shortcuts
export const DEFAULT_SHORTCUTS = {
  UNDO: 'ctrl+z',
  REDO: 'ctrl+shift+z',
  CLEAR: 'ctrl+alt+c',
  EXPORT: 'ctrl+s',
  IMPORT: 'ctrl+o',
  HELP: 'ctrl+?',
  DEBUG: 'ctrl+alt+d',
  FULLSCREEN: 'f11',
};
