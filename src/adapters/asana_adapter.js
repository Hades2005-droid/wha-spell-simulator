/**
 * Wha-Spell-Simulator Asana Adapter (NWW Connector)
 * Tracks glyph mastery, technique, soul resonance.
 * Call after parse/compile.
 */

const ASANA_TOKEN = process.env.ASANA_API_TOKEN;
const ASANA_PROJECT = process.env.ASANA_PROJECT_SPELLSIM || 'YOUR_SPELLSIM_GID';

async function reportGlyphMetrics(glyphName, accuracy, mastery, soulResonance, notes = '') {
  if (!ASANA_TOKEN) {
    console.log('(Asana: no token, skipping spell report)');
    return;
  }
  // Simple fetch example (node 18+)
  const taskData = {
    data: {
      name: `Spell Glyph: ${glyphName} - ${new Date().toISOString().slice(0,10)}`,
      notes: notes || `Glyph accuracy: ${accuracy}%. Mastery: ${mastery}. Resonance: ${soulResonance}`,
      projects: [ASANA_PROJECT]
    }
  };
  try {
    const res = await fetch('https://app.asana.com/api/1.0/tasks', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${ASANA_TOKEN}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(taskData)
    });
    const json = await res.json();
    if (json.data && json.data.gid) {
      console.log(`Asana: Spell report task ${json.data.gid}`);
      // Add custom fields if GIDs known
    }
  } catch (e) {
    console.error('Asana spell report error:', e.message);
  }
}

// Example hook in parser or renderer
// after recognition: reportGlyphMetrics('fireball', 0.92, 'Adept', 78, 'Copy technique successful');

export { reportGlyphMetrics };