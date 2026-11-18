import { listPlaybooks } from "@/lib/repo";
import PlaybookEditor from "@/components/playbook-editor";

export default function PlaybooksPage() {
  const playbooks = listPlaybooks();
  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-[22px] font-semibold tracking-[-0.02em]">Playbooks</h1>
        <p className="mt-1 text-[13px] text-ink-soft">
          The cadence engine reads these templates when the planner builds a sequence.
        </p>
      </header>
      <PlaybookEditor playbooks={playbooks} />
    </div>
  );
}
