import assert from 'node:assert/strict';
import test from 'node:test';

import { FABLE5_BEDROCK, isFable5BedrockArtifact } from '../src/bedrock/fable5Bedrock.js';

test('exports symbolic Q24 bedrock metadata', () => {
  assert.equal(FABLE5_BEDROCK.schema, 'shadow_garden.fable5_bedrock.v1');
  assert.equal(FABLE5_BEDROCK.q24.anchor, 14);
  assert.deepEqual(FABLE5_BEDROCK.q24.sequence, [19, 10, 1]);
  assert.equal(FABLE5_BEDROCK.symbolicOnly, true);
});

test('recognizes registered handoff artifacts', () => {
  assert.equal(
    isFable5BedrockArtifact('shadow_garden_handoff/bridges/fable5_bedrock.json'),
    true,
  );
  assert.equal(isFable5BedrockArtifact('src/main.js'), false);
});
