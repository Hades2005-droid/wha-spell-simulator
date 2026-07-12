#!/usr/bin/env node
// Eden spell hook — a headless burst of the WHA spell simulation, narrated by
// Claude Fable 5. Invoked by the Shadow Garden launcher with the one input:
//
//     node eden/eden_spell.mjs "<intent>"
//
// It runs a small, deterministic "spell" physics burst so the hook always
// produces telemetry, independent of the browser simulator in ../src, then asks
// Fable 5 to narrate it. No API key => it just prints the telemetry.

import { ask, Fable5Refused, hasCredentials } from "./fable5.mjs";

// Deterministic burst seeded from the intent text, so the same command yields
// the same numbers — handy for a reproducible launch.
function castSpell(seedText) {
  let seed = 0;
  for (const ch of seedText) seed = (seed * 31 + ch.charCodeAt(0)) >>> 0;
  const rng = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 2 ** 32);

  const particles = Array.from({ length: 12 }, () => {
    const a = rng() * Math.PI * 2;
    const sp = 40 + rng() * 220;
    return { vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, mass: 1 + rng() * 4 };
  });

  const ke = particles.reduce(
    (s, p) => s + 0.5 * p.mass * (p.vx ** 2 + p.vy ** 2),
    0,
  );
  const px = particles.reduce((s, p) => s + p.mass * p.vx, 0);
  const py = particles.reduce((s, p) => s + p.mass * p.vy, 0);

  return {
    count: particles.length,
    kineticEnergy: Math.round(ke),
    momentum: Math.round(Math.hypot(px, py)),
  };
}

async function main() {
  const intent = process.argv.slice(2).join(" ").trim() || "cast";
  const telemetry = castSpell(intent);
  console.log(`[eden-spell] burst for ${JSON.stringify(intent)} ->`, telemetry);

  if (!hasCredentials()) {
    console.log("[eden-spell] No ANTHROPIC_API_KEY — skipping Fable 5 narration.");
    return;
  }

  try {
    const line = await ask(
      `Narrate this spell burst in one vivid sentence for the intent ` +
        `${JSON.stringify(intent)}: ${JSON.stringify(telemetry)}`,
      {
        system:
          "You are the spell-caster of Shadow Garden. One sentence, no preamble.",
        maxTokens: 200,
      },
    );
    console.log("[eden-spell] Fable 5:", line.trim());
  } catch (err) {
    if (err instanceof Fable5Refused) console.log("[eden-spell]", err.message);
    else console.log("[eden-spell] Fable 5 narration failed:", err.message);
  }
}

main();
