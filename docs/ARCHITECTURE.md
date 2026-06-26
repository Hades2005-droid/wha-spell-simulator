# Witch Hat Atelier Spell Simulator - Architecture Overview

## Project Purpose
A browser-based spell drawing simulator that parses freehand drawings of magical spell diagrams and compiles them into animated visual effects. Inspired by the manga "Witch Hat Atelier".

## High-Level Architecture

```
User Input (Pointer/Touch/Pen)
    ↓
Input Capture Layer (drawingCapture.js)
    ↓
Stroke Normalization (pointerNormalizer.js)
    ↓
Drawing Classification (drawingClassifier.js) → Ring Detection (ringDetector.js)
    ↓
Glyph AST Generation (symbolRecognizer.js, templateMatcher.js)
    ↓
Parser Warnings (glyphWarnings.js)
    ↓
Spell Compilation (spellBuilder.js, semanticRules.js)
    ↓
Spell Quality Assessment (spellQuality.js)
    ↓
SpellIR Output
    ↓
Effect Rendering (spellEffectRenderer.js)
    ↓
Canvas Visualization + Diagnostics UI
```

## Core Modules

### Input Layer (src/input/)
- **drawingCapture.js**: Captures pointer events (mouse, touch, pen) and converts to strokes
- **pointerNormalizer.js**: Normalizes pointer coordinates to canvas space
- **strokeStore.js**: Manages current drawing state and stroke history

### Parser Layer (src/parser/)
- **ringDetector.js**: Detects and validates the primary enclosing ring
- **drawingClassifier.js**: Classifies symbols into primary sigils and modifier signs
- **symbolRecognizer.js**: Recognizes individual symbols using template matching
- **templateMatcher.js**: Implements template-based pattern recognition
- **topologicalFloodFill.js**: Fills regions and analyzes topology
- **layerMapper.js**: Assigns symbols to prepared (outside ring) vs active (inside ring) layers
- **signRotation.js**: Validates sign orientation based on ring position
- **glyphWarnings.js**: Detects parsing errors and issues diagnostics
- **coordinateNormalizer.js**: Maps coordinates between spaces

### Compiler Layer (src/compiler/)
- **spellBuilder.js**: Orchestrates spell compilation from glyph AST to SpellIR
- **semanticRules.js**: Validates sign-sigil combinations and spell semantics
- **spellQuality.js**: Assesses drawing quality and stability

### Renderer Layer (src/renderer/)
- **spellEffectRenderer.js**: Main animation loop, orchestrates effects
- **canvasRenderer.js**: Low-level canvas drawing utilities
- **paperRenderer.js**: Paper-like background and texture
- **glyphOverlayRenderer.js**: Draws glyph classifications as debug overlay

#### Effects (src/renderer/effects/)
- **fireEffect.js**: Radiating orange/red particles
- **waterEffect.js**: Blue waves and ripples
- **windEffect.js**: Light trails and vortex
- **earthEffect.js**: Brown/tan settling particles
- **lightEffect.js**: Bright ascending particles
- **effectUtils.js**: Shared animation utilities

### UI Layer (src/ui/)
- **elements.js**: UI component creation
- **tabs.js**: Tab panel management
- **diagnosticsView.js**: Displays parser output
- **spellSummaryView.js**: Shows compiled spell info
- **dictionaryReferenceView.js**: Sample spells and symbol reference
- **canvasSizing.js**: Responsive canvas sizing

### Bridge Layer (src/bridge/)
- **meshBridge.js**: Shadow Garden Mesh service integration
- **sovereignExecutor.js**: Sovereign spell execution (Authority management)
- **bridgeDiagnostics.js**: Mesh status UI

### Utilities (src/utils/)
- **geometry.js**: Math utilities (distance, normalization, bounds)
- **throttle.js**: Event throttling and debouncing
- **memoize.js**: Function result caching
- **templateNormalizer.js**: Template preprocessing

### Debug Layer (src/debug/)
- **debugOverlay.js**: Development debug panel
- **diagnosticState.js**: Diagnostic data management
- **jsonTreeRenderer.js**: Hierarchical data visualization

## Data Flow

### Spell Representation

**GlyphAST** (Glyph Abstract Syntax Tree)
```javascript
{
  ring: {
    points: [...],
    complete: boolean,
    center: {x, y},
    radius: number
  },
  prepared: [...],     // Symbols outside ring
  active: [...]        // Symbols inside ring (if ring complete)
}
```

**SpellIR** (Spell Intermediate Representation)
```javascript
{
  state: 'prepared' | 'active',
  quality: {...},
  manifestations: [{
    element: 'fire' | 'water' | 'wind' | 'earth' | 'light',
    direction: {x, y, z},
    range: number,
    duration: number,
    effects: [...]
  }]
}
```

## Key Algorithms

### Ring Detection
- **Approach**: Topological analysis using flood fill
- **Purpose**: Identify enclosing ring boundary
- **Constraints**: Single ring per drawing

### Symbol Recognition
- **Approach**: Template matching with rotation/scale invariance
- **Purpose**: Classify sigils and signs
- **Optimization**: Memoization, early exit on low confidence

### Spell Compilation
- **Approach**: Semantic validation and IR generation
- **Purpose**: Convert symbols to executable spell effects
- **Rules**: Sign-sigil compatibility, direction mapping, duration/range interaction

### Effect Rendering
- **Approach**: Canvas-based particle animation
- **Purpose**: Visualize spell execution
- **Optimization**: RequestAnimationFrame sync, dirty rectangle tracking

## Extension Points

### Adding New Elements
1. Create effect file in `src/renderer/effects/elementEffect.js`
2. Add element to dictionary in `assets/sigils.json`
3. Add parser rules in `src/compiler/semanticRules.js`

### Adding New Signs (Modifiers)
1. Add sign template to dictionary in `assets/signs.json`
2. Add validation rules in `src/compiler/semanticRules.js`
3. Update sign rotation logic in `src/parser/signRotation.js`

### Customizing Rendering
1. Modify effect implementations in `src/renderer/effects/`
2. Update colors and animation parameters
3. Adjust canvas renderer in `src/renderer/canvasRenderer.js`

## Performance Considerations

1. **Ring Detection** (high frequency): Consider caching for identical strokes
2. **Symbol Recognition** (medium frequency): Use memoization for common patterns
3. **Effect Rendering** (continuous): Use dirty rectangles and transform matrices
4. **Dictionary Loading**: Lazy-load on first use

## Testing Strategy

- **Unit Tests**: Parser, compiler, geometry utilities
- **Integration Tests**: Ring detection + classification pipeline
- **Snapshot Tests**: Spell IR generation for known drawings
- **Visual Tests**: Effect rendering frame comparison

