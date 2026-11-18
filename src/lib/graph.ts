/**
 * Minimal LangGraph-style runner: a typed state object flows through named nodes,
 * each returning the next state. Nodes are where decisions get logged.
 */
export interface GraphNode<C> {
  name: string;
  run: (ctx: C) => Promise<C>;
}

export async function runGraph<C>(nodes: GraphNode<C>[], initial: C): Promise<C> {
  let ctx = initial;
  for (const node of nodes) {
    ctx = await node.run(ctx);
  }
  return ctx;
}

/** Deterministic pseudo-random in [0,1) from a string seed. */
export function seededUnit(seed: string): number {
  let h = 2166136261;
  for (let i = 0; i < seed.length; i++) {
    h ^= seed.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return ((h >>> 0) % 100000) / 100000;
}

export function addDays(iso: string, days: number): string {
  const t = new Date(iso).getTime() + days * 86_400_000;
  return new Date(t).toISOString();
}

export function daysBetween(a: string, b: string): number {
  return (new Date(b).getTime() - new Date(a).getTime()) / 86_400_000;
}
