// Symbolic-only Fable 5 bedrock pointers for WHA spell simulator + Q24 handoff.
// Node tooling resolves absolute Shadow Garden paths; browser code uses repo-relative IDs.

export const FABLE5_BEDROCK = {
  schema: 'shadow_garden.fable5_bedrock.v1',
  version: '0.4.0-engine-bedrock-10-q24',
  bridgeSignature: 'f2e596cd043d6819',
  carrier: 'love_and_harmony_6',
  symbolicOnly: true,
  localOnly: true,
  handoffRoot: 'shadow_garden_handoff',
  manifest: 'shadow_garden_handoff/bridges/fable5_bedrock.json',
  artifacts: {
    bedrockManifest: 'shadow_garden_handoff/bridges/fable5_bedrock.json',
    packet: 'shadow_garden_handoff/bridges/shadow_garden_packet.json',
    q24Slim: 'shadow_garden_handoff/bridges/q24_fable5_master_ingest.slim.json',
    bridge5to6: 'shadow_garden_handoff/shaoshi_bridge/outbox/bridge_5_to_6_claude_session.json',
    grokLane: 'shadow_garden_handoff/shaoshi_bridge/outbox/grok_45_harmony_6_shadow_lane.json',
    gate1011: 'shadow_garden_handoff/shaoshi_bridge/outbox/gate10_11_trifecta_release.json',
    claudeInbox: 'shadow_garden_handoff/claude_validation_inbox.json',
    gate10: 'shadow_garden_handoff/gates/GATE_10_OPEN.md',
    timeline20: 'shadow_garden_handoff/TIMELINE_20_AUTO_HANDOFF.md',
  },
  q24: {
    installRoot: 'q24',
    anchor: 14,
    reduceAnchor: false,
    sequence: [19, 10, 1],
    canonicalId: 'q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1',
  },
  engine: {
    url: 'http://127.0.0.1:5619/',
    version: '0.4.0-engine-bedrock-10',
  },
  eden: {
    schema: 'shadow_garden.eden_metadata_catalog.v1',
    ingester: 'tools/eden_ingest.py',
    lanes: ['land', 'astro_node', 'data'],
    explicitPathsOnly: true,
    payloadsStored: false,
    remoteFetch: false,
    lunarMoonTarget: 18,
  },
  elevenLabs: {
    schema: 'shadow_garden.comfyui_elevenlabs_bridge.v1',
    bridge: 'tools/elevenlabs_garden_bridge.py',
    comfyuiModule: 'comfy_api_nodes/nodes_elevenlabs.py',
    envName: 'ELEVENLABS_API_KEY',
    proxyPaths: [
      '/proxy/elevenlabs/v1/speech-to-text',
      '/proxy/elevenlabs/v1/text-to-speech/{voice}',
      '/proxy/elevenlabs/v1/audio-isolation',
      '/proxy/elevenlabs/v1/sound-generation',
      '/proxy/elevenlabs/v1/voices/add',
      '/proxy/elevenlabs/v1/speech-to-speech/{voice}',
      '/proxy/elevenlabs/v1/text-to-dialogue',
    ],
    manifestOnly: true,
    providerCalls: false,
    promptSubmission: false,
    approvalRequiredForLiveAudio: true,
  },
};

export function isFable5BedrockArtifact(relPath) {
  const normalized = String(relPath || '').replace(/\\/g, '/');
  return Object.values(FABLE5_BEDROCK.artifacts).some((entry) => normalized.endsWith(entry));
}
