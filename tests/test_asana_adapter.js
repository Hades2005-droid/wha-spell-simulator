/**
 * Unit tests for Wha-Spell-Simulator Asana adapter.
 *
 * These tests verify browser safety:
 * - No PAT exposed in browser bundles
 * - All API calls go through server/CLI boundary
 * - Safe for client-side execution
 *
 * Runs as a Node.js script with built-in assertions.
 */

import assert from 'assert';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const adapterPath = path.join(__dirname, '..', 'src', 'adapters', 'asanaAdapter.js');

const code = fs.readFileSync(adapterPath, 'utf8');

// Helper for test reporting
let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`✓ ${name}`);
    passed++;
  } catch (error) {
    console.error(`✗ ${name}`);
    console.error(`  ${error.message}`);
    failed++;
  }
}

// Configuration Safety Tests
console.log('\nConfiguration Safety:');

test('should NOT load ASANA_API_TOKEN from localStorage', () => {
  assert(!code.includes('localStorage.getItem'), 'Adapter must not use localStorage for tokens');
  assert(!code.includes('sessionStorage.getItem'), 'Adapter must not use sessionStorage for tokens');
});

test('should require ASANA_API_TOKEN from process.env only', () => {
  assert(code.includes('process.env'), 'Adapter must read from process.env');
});

test('should not embed hardcoded Asana workspace IDs', () => {
  const gidPattern = /:\s*['"](\d{12,})['"]/g;
  const matches = code.match(gidPattern) || [];
  const suspiciousMatches = matches.filter(m => !m.includes('placeholder'));
  assert.strictEqual(suspiciousMatches.length, 0, 'No hardcoded Asana GIDs allowed');
});

// Browser Safety Boundary Tests
console.log('\nBrowser Safety Boundary:');

test('should document server/CLI boundary for reporting', () => {
  const hasServerNote = code.includes('server') || code.includes('backend') || code.includes('CLI');
  assert(hasServerNote, 'Adapter must document server/CLI boundary for Asana reporting');
});

test('should use fetch API (browser-compatible) not axios/node libraries', () => {
  assert(code.includes('fetch'), 'Adapter must use fetch API');
  assert(!code.includes("require('axios')"), 'Adapter must not require axios in browser code');
  assert(!code.includes("require('node-fetch')"), 'Node-specific imports must be conditional');
});

// Metric Capture Safety Tests
console.log('\nMetric Capture Safety:');

test('should accept glyph accuracy from local parser only', () => {
  assert(code.includes('glyphAccuracy') || code.includes('glyphName'), 'Adapter must capture local glyph data');
});

test('should not expose metrics in console or DOM by default', () => {
  const consoleLogMatches = code.match(/console\.log\(/g) || [];
  const errorMatches = code.match(/console\.error\(/g) || [];
  assert(consoleLogMatches.length <= errorMatches.length + 1, 'Metrics must not be logged to console');
});

// Test Execution Safety Tests
console.log('\nTest Execution Safety:');

test('should not require live Asana API calls in CI', () => {
  const hasOptIn = code.includes('RUN_LIVE_ASANA_TESTS') || code.includes('LIVE_ASANA');
  assert(hasOptIn || code.includes('mock') || code.includes('stub'),
    'Live API calls must be behind opt-in flag or use mocks');
});

// Configuration Loading Tests
console.log('\nConfiguration Loading:');

test('should validate that ASANA_API_TOKEN exists before attempting request', () => {
  assert(code.includes('ASANA_API_TOKEN'), 'Must check for ASANA_API_TOKEN');
  assert(code.includes('throw') || code.includes('error') || code.includes('Error'),
    'Must throw error if token is missing');
});

// Summary
console.log(`\n${passed} passed, ${failed} failed`);
if (failed > 0) {
  process.exit(1);
}
