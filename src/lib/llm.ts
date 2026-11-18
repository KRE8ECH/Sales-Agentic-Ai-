/**
 * LLM provider. Uses the NVIDIA NIM OpenAI-compatible endpoint when
 * NVIDIA_API_KEY is set; otherwise callers fall back to the deterministic brain.
 */

export function llmStatus(): { available: boolean; model: string; source: string } {
  const key = process.env.NVIDIA_API_KEY;
  const model = process.env.NVIDIA_MODEL || "meta/llama-3.1-8b-instruct";
  return {
    available: Boolean(key),
    model,
    source: key ? "nvidia" : "fallback",
  };
}

interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

/** Last failure from chat(), for diagnostics (health probe / server logs). */
let lastLlmError: string | null = null;
export function lastLlmError(): string | null {
  return lastLlmError;
}

export async function chat(
  messages: ChatMessage[],
  opts: { temperature?: number; maxTokens?: number } = {}
): Promise<string | null> {
  const key = process.env.NVIDIA_API_KEY;
  if (!key) return null;
  const model = process.env.NVIDIA_MODEL || "meta/llama-3.1-8b-instruct";
  const base = process.env.NVIDIA_BASE_URL || "https://integrate.api.nvidia.com/v1";

  try {
    const res = await fetch(`${base}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${key}`,
      },
      body: JSON.stringify({
        model,
        messages,
        temperature: opts.temperature ?? 0.4,
        max_tokens: opts.maxTokens ?? 900,
      }),
      signal: AbortSignal.timeout(45_000),
    });
    if (!res.ok) {
      const detail = (await res.text()).slice(0, 300);
      lastLlmError = `http ${res.status}: ${detail}`;
      console.error("[llm] request failed:", lastLlmError);
      return null;
    }
    const data = (await res.json()) as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const text = data.choices?.[0]?.message?.content ?? null;
    lastLlmError = text ? null : "empty completion";
    return text;
  } catch (e) {
    lastLlmError = e instanceof Error ? e.message : String(e);
    console.error("[llm] error:", lastLlmError);
    return null;
  }
}

/** Extract the first JSON object/array from an LLM response. */
export function extractJson<T = unknown>(text: string): T | null {
  const cleaned = text.replace(/```(?:json)?/g, "").trim();
  const candidates = [cleaned];
  const firstObj = cleaned.indexOf("{");
  const firstArr = cleaned.indexOf("[");
  if (firstObj >= 0) candidates.push(cleaned.slice(firstObj));
  if (firstArr >= 0 && firstArr !== firstObj) candidates.push(cleaned.slice(firstArr));
  for (const c of candidates) {
    const tryParse = (s: string): T | null => {
      try {
        return JSON.parse(s) as T;
      } catch {
        return null;
      }
    };
    const direct = tryParse(c);
    if (direct !== null) return direct;
    const start = c.search(/[[{]/);
    if (start < 0) continue;
    // trim trailing prose after the last bracket
    const last = Math.max(c.lastIndexOf("}"), c.lastIndexOf("]"));
    if (last > start) {
      const trimmed = tryParse(c.slice(start, last + 1));
      if (trimmed !== null) return trimmed;
    }
  }
  return null;
}
