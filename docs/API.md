# Witch Hat Spell Simulator - API Reference

## Core APIs

### Spell Compilation Pipeline

#### parseDrawing(strokes) → GlyphAST
Parses stroke input into glyph abstract syntax tree.

```javascript
import { parseDrawing } from './parser/main.js';

const strokes = [
  { points: [{x: 0, y: 0}, {x: 10, y: 10}, ...] },
  // ... more strokes
];

const glyph = parseDrawing(strokes);
// Returns:
// {
//   ring: { points, complete, center, radius },
//   prepared: [...],
//   active: [...]
// }
```

#### compileSpell(glyph) → SpellIR
Compiles glyph AST to spell intermediate representation.

```javascript
import { compileSpell } from './compiler/spellBuilder.js';

const spell = compileSpell(glyph);
// Returns:
// {
//   state: 'prepared' | 'active',
//   quality: { ... },
//   manifestations: [...]
// }
```

#### renderSpell(canvas, spell) → AnimationController
Renders spell effects on canvas.

```javascript
import { renderSpell } from './renderer/spellEffectRenderer.js';

const controller = renderSpell(canvas, spell);

// Control animation
controller.play();
controller.pause();
controller.stop();
controller.setSpeed(1.5);
```

### Input Handling

#### captureDrawing(canvasElement) → DrawingController
Sets up drawing capture on canvas element.

```javascript
import { captureDrawing } from './input/drawingCapture.js';

const controller = captureDrawing(canvasElement);

controller.onStrokeAdded = (stroke) => {
  console.log('Stroke added:', stroke);
};

controller.onDrawingCleared = () => {
  console.log('Drawing cleared');
};

controller.clear();
controller.getStrokes();
```

### Symbol Recognition

#### recognizeSymbol(points) → Recognition
Recognizes a symbol from its stroke points.

```javascript
import { recognizeSymbol } from './parser/symbolRecognizer.js';

const recognition = recognizeSymbol(points);
// Returns:
// {
//   type: 'sigil' | 'sign',
//   element: 'fire' | 'water' | ...,
//   confidence: 0.85,
//   diagnostics: [...]
// }
```

#### detectRing(strokes) → Ring
Detects enclosing ring in drawing.

```javascript
import { detectRing } from './parser/ringDetector.js';

const ring = detectRing(strokes);
// Returns:
// {
//   points: [...],
//   complete: true/false,
//   center: {x, y},
//   radius: number,
//   quality: { ... }
// }
```

### Geometry Utilities

#### distance(point1, point2) → number
```javascript
import { distance } from './utils/geometry.js';

const d = distance({x: 0, y: 0}, {x: 3, y: 4});
// Returns: 5
```

#### boundsForPoints(points) → Bounds
```javascript
import { boundsForPoints } from './utils/geometry.js';

const bounds = boundsForPoints(points);
// Returns: { minX, minY, width, height }
```

#### centerOfBounds(bounds) → Point
```javascript
import { centerOfBounds } from './utils/geometry.js';

const center = centerOfBounds(bounds);
// Returns: { x, y }
```

#### normalizeVector(vector) → Vector
```javascript
import { normalizeVector } from './utils/geometry.js';

const unit = normalizeVector({x: 3, y: 4});
// Returns unit vector with length 1
```

### Performance Utilities

#### throttle(func, delay) → Function
Throttles function execution.

```javascript
import { throttle } from './utils/throttle.js';

const throttled = throttle(onPointerMove, 16); // ~60fps
canvas.addEventListener('pointermove', throttled);
```

#### debounce(func, delay) → Function
Debounces function execution.

```javascript
import { debounce } from './utils/throttle.js';

const debounced = debounce(onSpellCompile, 500);
// Recompile only after user stops drawing for 500ms
```

#### memoize(func, options) → Function
Caches function results.

```javascript
import { memoize } from './utils/memoize.js';

const memoized = memoize(expensiveCalculation, {
  maxSize: 100  // Keep 100 results
});
```

## Data Structures

### GlyphAST
```javascript
{
  ring: {
    points: Point[],           // Ring boundary points
    complete: boolean,         // Whether ring is closed
    center: Point,            // Ring center
    radius: number,           // Ring radius
    quality: {
      regularity: 0..1,       // How circular the ring is
      cleanliness: 0..1       // How few stray strokes
    }
  },
  prepared: Symbol[],         // Symbols outside ring
  active: Symbol[]           // Symbols inside ring
}
```

### Symbol
```javascript
{
  type: 'sigil' | 'sign',     // Primary element or modifier
  element: string,            // 'fire', 'water', 'wind', 'earth', 'light'
  position: Point,            // Symbol center
  bounds: Bounds,             // Bounding box
  confidence: 0..1,           // Recognition confidence
  drawn: Point[],             // Actual drawn points
  orientation: number,        // Angle in radians
  diagnostics: any           // Debug information
}
```

### SpellIR
```javascript
{
  state: 'prepared' | 'active',
  quality: {
    score: 0..1,              // Overall spell quality
    cleanliness: 0..1,
    regularity: 0..1,
    stability: 0..1
  },
  manifestations: Manifestation[]
}
```

### Manifestation
```javascript
{
  element: string,            // 'fire', 'water', 'wind', 'earth', 'light'
  direction: Vector3,         // {x, y, z} normalized direction
  range: number,              // Spell range multiplier (0..2)
  duration: number,           // Effect duration in ms
  converged: boolean,         // Convergence sign active
  forced: boolean,            // Force/concentration sign active
  spread: boolean,            // Spread sign active
  focused: boolean,           // Focus sign active
  stable: boolean             // Stability sign active
}
```

## Constants

### Element Types
```javascript
export const ELEMENTS = {
  FIRE: 'fire',
  WATER: 'water',
  WIND: 'wind',
  EARTH: 'earth',
  LIGHT: 'light'
};
```

### Sign Types
```javascript
export const SIGNS = {
  DIRECTION: 'direction',
  LEVITATION: 'levitation',
  CONVERGENCE: 'convergence',
  FORCE: 'force',
  SPREAD: 'spread',
  FOCUS: 'focus',
  RANGE: 'range',
  DURATION: 'duration',
  STABILITY: 'stability'
};
```

## Events

### DrawingController Events
```javascript
controller.onStrokeAdded = (stroke: Stroke) => void
controller.onStrokeRemoved = (strokeId: string) => void
controller.onDrawingCleared = () => void
controller.onDrawingChanged = (strokes: Stroke[]) => void
```

### AnimationController Events
```javascript
controller.onFrameUpdate = (frame: number) => void
controller.onAnimationComplete = () => void
controller.onAnimationStart = () => void
```

## Error Handling

### Parsing Errors
```javascript
const glyph = parseDrawing(strokes);

if (!glyph.ring.complete) {
  console.warn('Ring not closed');
}

if (glyph.active.length === 0 && glyph.prepared.length === 0) {
  console.error('No symbols detected');
}
```

### Compilation Errors
```javascript
const spell = compileSpell(glyph);

if (spell.state === 'invalid') {
  console.error('Spell compilation failed:', spell.errors);
}
```

## Examples

### Complete Workflow
```javascript
import { captureDrawing } from './input/drawingCapture.js';
import { parseDrawing } from './parser/main.js';
import { compileSpell } from './compiler/spellBuilder.js';
import { renderSpell } from './renderer/spellEffectRenderer.js';

// Setup drawing input
const canvas = document.getElementById('spell-canvas');
const drawController = captureDrawing(canvas);

// Setup effect canvas
const effectCanvas = document.getElementById('effect-canvas');

// Process drawing
drawController.onDrawingChanged = (strokes) => {
  const glyph = parseDrawing(strokes);
  const spell = compileSpell(glyph);
  
  if (spell.state !== 'invalid') {
    const animController = renderSpell(effectCanvas, spell);
    animController.play();
  }
};
```

