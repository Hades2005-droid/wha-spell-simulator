// Fable 5 client — the native communication layer for the WHA spell simulator.
//
// Mirrors eden/fable5.py in the sibling Eden repos so every corner of the
// constellation talks to Claude Fable 5 the same way:
//   * thinking is always on (we never send a `thinking` param)
//   * no sampling params (temperature/top_p/top_k are rejected on Fable 5)
//   * opt-in server-side refusal fallback to claude-opus-4-8
//
// Auth: `new Anthropic()` reads ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN.
// Requires:  npm install @anthropic-ai/sdk

import Anthropic from "@anthropic-ai/sdk";

export const FABLE_MODEL = "claude-fable-5";
export const FALLBACK_MODEL = "claude-opus-4-8";
const FALLBACK_BETA = "server-side-fallback-2026-06-01";

export class Fable5Refused extends Error {}

export function hasCredentials() {
  return Boolean(
    process.env.ANTHROPIC_API_KEY || process.env.ANTHROPIC_AUTH_TOKEN,
  );
}

/**
 * Send one prompt to Fable 5 and return the reply text.
 * @param {string} prompt
 * @param {{system?: string, maxTokens?: number, effort?: string, client?: Anthropic}} [opts]
 * @returns {Promise<string>}
 */
export async function ask(prompt, opts = {}) {
  const { system, maxTokens = 8000, effort = "high", client } = opts;
  const c = client ?? new Anthropic();

  const resp = await c.beta.messages.create({
    model: FABLE_MODEL,
    max_tokens: maxTokens,
    betas: [FALLBACK_BETA],
    fallbacks: [{ model: FALLBACK_MODEL }],
    output_config: { effort },
    ...(system ? { system } : {}),
    messages: [{ role: "user", content: prompt }],
  });

  if (resp.stop_reason === "refusal") {
    const category = resp.stop_details?.category ?? null;
    throw new Fable5Refused(
      `Fable 5 declined this request (category=${category}).`,
    );
  }

  return resp.content
    .filter((b) => b.type === "text")
    .map((b) => b.text)
    .join("");
}
