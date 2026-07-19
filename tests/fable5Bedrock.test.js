import assert from 'node:assert/strict';
import test from 'node:test';

import { FABLE5_BEDROCK, isFable5BedrockArtifact } from '../src/bedrock/fable5Bedrock.js';

test('exports symbolic Q24 bedrock metadata', () => {
  assert.equal(FABLE5_BEDROCK.schema, 'shadow_garden.fable5_bedrock.v1');
  assert.equal(FABLE5_BEDROCK.q24.anchor, 14);
  assert.deepEqual(FABLE5_BEDROCK.q24.sequence, [19, 10, 1]);
  assert.equal(FABLE5_BEDROCK.symbolicOnly, true);
});

test('exports bounded Eden metadata ingestion lanes', () => {
  assert.deepEqual(FABLE5_BEDROCK.eden.lanes, ['land', 'astro_node', 'data']);
  assert.equal(FABLE5_BEDROCK.eden.explicitPathsOnly, true);
  assert.equal(FABLE5_BEDROCK.eden.payloadsStored, false);
  assert.equal(FABLE5_BEDROCK.eden.remoteFetch, false);
  assert.equal(FABLE5_BEDROCK.eden.lunarMoonTarget, 18);
});

test('recognizes registered handoff artifacts', () => {
  assert.equal(
    isFable5BedrockArtifact('shadow_garden_handoff/bridges/fable5_bedrock.json'),
    true,
  );
  assert.equal(isFable5BedrockArtifact('src/main.js'), false);
});
