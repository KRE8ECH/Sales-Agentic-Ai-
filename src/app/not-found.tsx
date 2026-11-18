import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex flex-col items-start gap-3 py-16">
      <span className="font-mono text-[11px] uppercase tracking-[0.08em] text-ink-faint">
        404
      </span>
      <h1 className="text-[22px] font-semibold tracking-[-0.02em]">
        This page could not be found.
      </h1>
      <p className="max-w-md text-[13px] leading-relaxed text-ink-soft">
        The link may point at a record from a different serverless instance, or it simply
        does not exist. Head back to the pipeline and pick a lead there.
      </p>
      <Link href="/leads" className="btn btn-ghost mt-1">
        <ArrowLeft size={13} /> Back to leads
      </Link>
    </div>
  );
}
