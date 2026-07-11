import { CONFIG } from './config.js';
import { loadDictionary } from './dictionary/dictionaryLoader.js';
import { DrawingCapture } from './input/drawingCapture.js';
import { createStrokeStore } from './input/strokeStore.js';
import { classifyDrawing } from './parser/drawingClassifier.js';
import { compileSpell } from './compiler/spellBuilder.js';
import { CanvasRenderer } from './renderer/canvasRenderer.js';
import { setupCanvasSizing as setupResponsiveCanvasSizing } from './ui/canvasSizing.js';
import { updateDiagnostics, updateDiagnosticsMode } from './ui/diagnosticsView.js';
import { getElements } from './ui/elements.js';
import { renderDictionaryReference } from './ui/dictionaryReferenceView.js';
import { updateStatus, updateSummary } from './ui/spellSummaryView.js';
import { setupTabs } from './ui/tabs.js';
import { SpellSimulatorAsanaReporter } from './adapters/asanaAdapter.js';

const elements = getElements();
const store = createStrokeStore();
let dictionary = null;
let renderer = null;
let capture = null;
let pipeline = null;
let spellIR = null;
let previousRing = null;
let resizeObserver = null;
let asanaReporter = null;

function setupCanvasSizing() {
  resizeObserver = setupResponsiveCanvasSizing({
    elements,
    store,
    onCanvasResized: () => {
      previousRing = null;
      recompute();
    },
  });
}

function recompute() {
  if (!dictionary) {
    return;
  }

  const startTime = performance.now();

  pipeline = classifyDrawing({
    strokes: store.getStrokes(),
    previousRing,
    dictionary,
    config: CONFIG,
  });
  const classifyTime = performance.now() - startTime;

  previousRing = pipeline.ring;

  const compileStart = performance.now();
  spellIR = compileSpell({ glyphAST: pipeline.glyphAST, dictionary, config: CONFIG });
  const compileTime = performance.now() - compileStart;

  // Report glyph recognition metrics to Asana (if reporter is available)
  if (asanaReporter && pipeline.glyphName) {
    asanaReporter.reportGlyphAccuracy({
      timestamp: new Date().toISOString(),
      glyphName: pipeline.glyphName || 'unknown',
      accuracy: pipeline.confidence || 85,
      confidence: pipeline.confidence || 85,
      processingTime: classifyTime,
      strokeCount: store.getStrokes().length,
      success: !!pipeline.glyphAST,
    }).catch(err => console.warn('Asana glyph reporting failed:', err));
  }

  // Report spell compilation metrics to Asana (if reporter is available)
  if (asanaReporter && spellIR) {
    asanaReporter.reportSpellCompilation({
      timestamp: new Date().toISOString(),
      glyphAccuracy: pipeline.confidence || 85,
      compilationSuccess: spellIR.active ? 100 : 75,
      spellsCompiled: 1,
      copyTechniquePrecision: spellIR.quality || 80,
      lastGlyphName: pipeline.glyphName || 'unknown',
      drawingConfidence: pipeline.confidence || 85,
      renderTime: compileTime,
    }).catch(err => console.warn('Asana spell reporting failed:', err));
  }

  updateSummary({
    elements, store, capture, pipeline, spellIR,
  });
  updateDiagnostics({
    elements, store, pipeline, spellIR,
  });
}

function animationFrame(timestamp) {
  renderer.renderGlyph({
    strokes: store.getStrokes(),
    currentStroke: capture.getCurrentStroke(),
    pipeline,
    showGuides: elements.guidesToggle.checked,
    showDebug: elements.diagnosticsToggle.checked,
  });

  if (spellIR.active) {
    renderer.renderActivatedGlyph({
      activatedAt: spellIR.activatedAt,
      duration: spellIR.duration,
      strokes: store.getStrokes(),
      pipeline,
      timestamp,
    });
  }

  renderer.renderEffect({
    spellIR,
    ring: pipeline?.ring,
    timestamp,
    showGuides: elements.guidesToggle.checked,
  });
  requestAnimationFrame(animationFrame);
}

function setupControls() {
  elements.undoButton.addEventListener('click', () => {
    store.undo();
    previousRing = null;
    recompute();
  });

  elements.clearButton.addEventListener('click', () => {
    store.clear();
    previousRing = null;
    recompute();
  });

  elements.guidesToggle.addEventListener('change', () => {
    updateSummary({
      elements, store, capture, pipeline, spellIR,
    });
    updateDiagnostics({
      elements, store, pipeline, spellIR,
    });
  });

  elements.diagnosticsToggle.addEventListener('change', () => {
    updateDiagnosticsMode(elements);
    updateDiagnostics({
      elements, store, pipeline, spellIR,
    });
  });

  updateDiagnosticsMode(elements);
}

async function init() {
  setupTabs(elements);
  setupControls();
  setupCanvasSizing();
  renderer = new CanvasRenderer({
    glyphCanvas: elements.glyphCanvas,
    effectCanvas: elements.effectCanvas,
    config: CONFIG,
  });
  capture = new DrawingCapture(elements.glyphCanvas, store, CONFIG, {
    onPreview: () => {},
    onCommit: recompute,
  });

  // Initialize Asana reporter (optional; requires ASANA_ACCESS_TOKEN in backend)
  try {
    asanaReporter = new SpellSimulatorAsanaReporter();
    console.info('Asana reporting enabled for spell simulator');
  } catch (err) {
    console.info('Asana reporting not configured:', err.message);
    asanaReporter = null;
  }

  try {
    dictionary = await loadDictionary();
    renderDictionaryReference(elements, dictionary);
    capture.enable();
    recompute();
    requestAnimationFrame(animationFrame);
  } catch (error) {
    console.error(error);
    updateStatus(elements, 'Dictionary load failed', 'invalid');
  }
}

init();
