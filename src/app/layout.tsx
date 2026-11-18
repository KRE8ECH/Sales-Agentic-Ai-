import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "./globals.css";
import type { Metadata } from "next";
import Shell from "@/components/shell";
import { getSimNow, listLeads } from "@/lib/repo";
import { ensureSeed } from "@/lib/seed";
import { DB_MODE } from "@/lib/db";
import { llmStatus } from "@/lib/llm";

export const metadata: Metadata = {
  title: "Cadence — Outreach Console",
  description:
    "Autonomous multi-touch sales outreach: research, plan, draft, send, listen, and decide — with a visible decision log.",
};

export const dynamic = "force-dynamic";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  ensureSeed();
  const now = getSimNow();
  const leads = listLeads().map((l) => ({ id: l.id, name: l.name, company: l.company }));
  const llm = llmStatus();
  return (
    <html lang="en">
      <body>
        <Shell now={now} leads={leads} dbMode={DB_MODE} llm={llm}>{children}</Shell>
      </body>
    </html>
  );
}
