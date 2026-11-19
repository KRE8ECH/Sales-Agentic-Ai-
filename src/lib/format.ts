/** Pure date formatting — safe to import from client components. */

export function formatSim(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function fullSim(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

export function relDay(iso: string | null | undefined, nowIso: string): string {
  if (!iso) return "—";
  const diff = Math.round(
    (new Date(iso).getTime() - new Date(nowIso).getTime()) / 86_400_000
  );
  if (diff === 0) return "today";
  if (diff === 1) return "tomorrow";
  if (diff === -1) return "yesterday";
  if (diff > 1) return `in ${diff}d`;
  return `${-diff}d ago`;
}
