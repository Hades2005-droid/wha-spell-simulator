# Contributing to Witch Hat Spell Simulator

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn
- Git

### Setup
```bash
# Clone repository
git clone https://github.com/[user]/wha-spell-simulator.git
cd wha-spell-simulator

# Install dependencies
npm install

# Start development server
npm start

# Open in browser
# http://127.0.0.1:5173/
```

## Development Workflow

### Running Tests
```bash
# Run all tests
npm test

# Run with watch mode
npm test -- --watch
```

### Linting and Formatting
```bash
# Check code style
npm run lint

# Auto-fix style issues
npm run lint:fix

# Format code
npm run format

# Check format without fixing
npm run format:check
```

### Building
```bash
# Build for production
npm run build

# Output goes to dist/
```

## Code Organization

### Directory Structure
```
src/
├── bridge/          # Service mesh integration (sovereign authority)
├── compiler/        # Spell compilation and validation
├── debug/          # Development debugging utilities
├── dictionary/     # Dictionary and asset loading
├── input/          # User input handling
├── parser/         # Drawing parsing and symbol recognition
├── renderer/       # Canvas rendering and effects
│   └── effects/    # Element-specific effect implementations
├── ui/             # User interface components
├── utils/          # Shared utilities
├── main.js         # Application entry point
└── config.js       # Configuration constants
```

### Module Naming Conventions
- **XXXRenderer.js**: Canvas drawing logic
- **XXXEffect.js**: Animated effects
- **XXXDetector.js**: Symbol/pattern detection
- **XXXBuilder.js**: Construction/assembly logic
- **XXXUtils.js**: Utility functions

## Architecture Guidelines

### Adding a New Element (Fire, Water, etc.)
1. Create **elementEffect.js** in `src/renderer/effects/`
2. Export `renderElementEffect(ctx, params)` function
3. Add element definition to `assets/sigils.json`
4. Add compile rules to `src/compiler/semanticRules.js`
5. Add tests in `tests/compiler.test.js`

### Adding a New Sign (Modifier)
1. Add sign template to `assets/signs.json`
2. Create validation rules in `src/compiler/semanticRules.js`
3. Update `src/parser/signRotation.js` for orientation rules
4. Update spell compilation in `src/compiler/spellBuilder.js`
5. Add tests for the sign interaction

### Adding a New UI Component
1. Create component function in `src/ui/`
2. Return DOM elements from function
3. Register in main app initialization
4. Add styling to `src/ui/*.css`
5. Test with diagnostics panel

## Testing Best Practices

### Unit Tests
```javascript
import { test } from 'node:test';
import assert from 'node:assert';
import { functionToTest } from '../src/module/file.js';

test('Function Description', async (t) => {
  await t.test('should do something', () => {
    const result = functionToTest(input);
    assert.strictEqual(result, expected);
  });
});
```

### Test Organization
- One test file per module or feature
- Nested describe/test structure for readability
- Clear test names describing behavior
- Use meaningful assertions

### Performance Testing
```javascript
// Measure performance
const start = performance.now();
// ... code to benchmark
const elapsed = performance.now() - start;
console.log(`Execution time: ${elapsed.toFixed(2)}ms`);
```

## Debugging Tips

### Debug Overlay
- Press `Ctrl+Alt+D` to toggle debug overlay
- Shows:
  - Parser diagnostics
  - Glyph AST
  - SpellIR
  - Recognition confidence scores
  - Contamination analysis

### Browser DevTools
```javascript
// Add to code for debugging
debugger;
console.log('value:', value);

// Performance profiling
performance.measure('myMeasure', 'start-mark', 'end-mark');
```

### Common Issues

**Ring not detected**
- Check `ringDetector.test.js` for expected ring topology
- Verify ring is closed and roughly circular
- Check stroke order and speed

**Symbol not recognized**
- Use `/tools/sigilSignDetectorLab.html` to test recognition
- Check template matching confidence in debug overlay
- Verify symbol is drawn clearly within ring

**Spell won't compile**
- Check semanticRules for sign-sigil compatibility
- Verify only one primary sigil present
- Check for contamination (stray strokes)

## Performance Considerations

### Hot Paths (Optimize These First)
1. Ring detection (`ringDetector.js`) - runs per stroke
2. Symbol recognition (`symbolRecognizer.js`) - runs per shape
3. Effect rendering (`spellEffectRenderer.js`) - runs every frame

### Optimization Techniques
- **Memoize** repeated calculations: `import { memoize } from '../utils/memoize.js'`
- **Throttle** events: `import { throttle } from '../utils/throttle.js'`
- **Cache** dictionary lookups
- **Profile** before optimizing

## Pull Request Process

1. Fork repository
2. Create feature branch: `git checkout -b feature/description`
3. Make changes following code style
4. Run tests: `npm test` (must all pass)
5. Run linter: `npm run lint:fix`
6. Commit with clear message
7. Push to fork
8. Create Pull Request with:
   - Description of changes
   - Any new features/fixes
   - Testing performed
   - Screenshots for visual changes

## Commit Message Format

```
feat: add new element type
^--^ ^-- subject (50 chars)
|
type: (feat|fix|docs|style|refactor|test|chore)

Body (wrap at 72 chars)

Closes #123
```

## Resources

- [Spell Parsing Rules](./play-rules.md)
- [Dictionary Authoring](./dictionary-authoring.md)
- [Glyph AST Contract](./glyph-ast.md)
- [SpellIR Contract](./spell-ir.md)
- [Effect Rendering Notes](./effect-rendering.md)

## Questions or Issues?

- Check existing [Issues](https://github.com/[user]/wha-spell-simulator/issues)
- Join [Community Discord](https://discord.gg/XkdEe4wB)
- Review documentation in `/docs` folder

Happy contributing! 🎨✨
