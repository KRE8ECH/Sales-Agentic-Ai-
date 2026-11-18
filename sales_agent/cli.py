import sys
import os
import json
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt

from sales_agent.config import config
from sales_agent.db import Database
from sales_agent.llm.ollama_client import OllamaClient
from sales_agent.agents.orchestrator import OutreachOrchestrator

console = Console()

def print_banner():
    banner = """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║        PERSONALIZED MULTI-TOUCH SALES OUTREACH AGENT (Track D)         ║
    ║       Local Ollama LLM + DuckDuckGo RAG + Multi-Agent Orchestrator     ║
    ╚════════════════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    console.print(f"[yellow]Ollama Host:[/yellow] {config.ollama_base_url} | [yellow]Model:[/yellow] {config.ollama_model}")
    console.print("[dim]Commands: 'demo', 'research <name> at <company>', 'leads', 'show <id>', 'approve <touch_id>', 'reply <id>', 'settings', 'logs <id>', 'exit'[/dim]\n")

def check_ollama(client: OllamaClient):
    if client.is_connected():
        models = client.list_available_models()
        console.print(f"[bold green]✔ Connected to local Ollama server.[/bold green]")
        if models:
            console.print(f"[cyan]Available models:[/cyan] {', '.join(models)}")
        else:
            console.print("[yellow]Warning: No models found. Run `ollama pull llama3` or similar.[/yellow]")
    else:
        console.print(f"[bold yellow]⚠ Ollama server is not reachable at {client.base_url}.[/bold yellow]")
        console.print("[dim]Tip: Start Ollama by running `ollama serve` in another terminal tab.[/dim]")
        console.print("[dim]The agent will use fallback heuristic intelligence when Ollama is offline.[/dim]\n")

def display_leads(db: Database):
    leads = db.list_leads()
    if not leads:
        console.print("[yellow]No leads found in database. Use 'add' or 'demo' command to prospect a lead.[/yellow]")
        return

    table = Table(title="Lead Pipeline & Stateful Sequence Tracking", show_lines=True)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Name", style="bold white")
    table.add_column("Company", style="green")
    table.add_column("Role", style="magenta")
    table.add_column("Status", style="bold")
    table.add_column("Touch", justify="center")
    table.add_column("Next Action", style="dim")

    for l in leads:
        status = l["status"]
        if status == "AWAITING_APPROVAL":
            status_text = "[bold yellow]Draft - Awaiting Approval[/bold yellow]"
        elif status == "IN_SEQUENCE":
            status_text = "[blue]IN_SEQUENCE[/blue]"
        elif status == "ESCALATED":
            status_text = "[bold green]ESCALATED[/bold green]"
        elif status == "PAUSED":
            status_text = "[yellow]PAUSED[/yellow]"
        elif status == "STOPPED":
            status_text = "[red]STOPPED[/red]"
        else:
            status_text = f"[white]{status}[/white]"

        table.add_row(
            str(l["id"]),
            l["name"],
            l["company"],
            l.get("role") or "N/A",
            status_text,
            f"#{l['current_touch']}/4",
            l.get("next_touch_date") or ("Ready for Approval" if status == "AWAITING_APPROVAL" else "Active")
        )

    console.print(table)

def show_lead_details(db: Database, lead_id: int):
    lead = db.get_lead(lead_id)
    if not lead:
        console.print(f"[red]Lead #{lead_id} not found.[/red]")
        return

    status_str = "Draft - Awaiting Approval" if lead["status"] == "AWAITING_APPROVAL" else lead["status"]
    console.print(Panel(
        f"[bold white]Lead #{lead['id']}: {lead['name']}[/bold white] ({lead.get('role', 'N/A')} at [bold cyan]{lead['company']}[/bold cyan])\n"
        f"Status: [bold yellow]{status_str}[/bold yellow] | Current Touch: #{lead['current_touch']}/4 | Email: {lead.get('email', 'N/A')}",
        title="Lead Overview"
    ))

    # Research Dossier
    dossier = lead.get("research_dossier")
    if dossier:
        # Check warning
        if dossier.get("search_warning"):
            console.print(Panel(
                f"[bold yellow]⚠️ {dossier['search_warning']}[/bold yellow]",
                border_style="yellow",
                title="Search Notice"
            ))

        md_text = f"### Company Overview\n{dossier.get('company_overview', 'NOT FOUND')}\n\n"
        md_text += "### Verified Facts (DuckDuckGo RAG)\n"
        facts = dossier.get("facts", [])
        if not facts or (len(facts) == 1 and (isinstance(facts[0], dict) and facts[0].get("fact") == "NOT FOUND" or facts[0] == "NOT FOUND")):
            md_text += "**[NOT FOUND]** No verified public web facts were discovered.\n"
        else:
            for f in facts:
                if isinstance(f, dict):
                    md_text += f"- **{f.get('fact', '')}**\n  [Source Link]({f.get('source_url', '')})\n"
                else:
                    md_text += f"- {f}\n"

        md_text += "\n### Role Priorities & Strategic Focus\n"
        for rp in dossier.get("role_priorities", []):
            md_text += f"- {rp}\n"

        if dossier.get("tailored_hooks") and dossier["tailored_hooks"][0] != "NOT FOUND":
            md_text += "\n### Tailored Outreach Angles\n"
            for hook in dossier.get("tailored_hooks", []):
                md_text += f"- {hook}\n"

        console.print(Panel(Markdown(md_text), title="🔍 Research Dossier & RAG Context", border_style="cyan"))

    # Touches
    touches = db.get_touches_for_lead(lead_id)
    if touches:
        console.print("\n[bold]Outreach Sequence Touches:[/bold]")
        for t in touches:
            is_awaiting = (t["status"] == "AWAITING_APPROVAL")
            status_label = "[bold yellow]Draft - Awaiting Approval[/bold yellow]" if is_awaiting else "[bold green]SENT (Simulated)[/bold green]"
            approval_prompt = f"\n\n[bold green]👉 To approve and dispatch: type 'approve {t['id']}'[/bold green]" if is_awaiting else ""

            console.print(Panel(
                f"[bold cyan]Subject:[/bold cyan] {t.get('subject') or '(No Subject / LinkedIn)'}\n\n"
                f"{t['content']}\n\n"
                f"[dim]Evidence Grounded:[/dim] [yellow]{t.get('researched_evidence_used', 'N/A')}[/yellow]"
                f"{approval_prompt}",
                title=f"Touch #{t['touch_number']} [{t['channel'].upper()}] - {status_label} (Touch ID: #{t['id']})",
                border_style="yellow" if is_awaiting else "green"
            ))

    # Replies
    replies = db.get_replies_for_lead(lead_id)
    if replies:
        console.print("\n[bold]Inbound Replies & Classification:[/bold]")
        for r in replies:
            console.print(Panel(
                f"[bold]Reply Text:[/bold] \"{r['reply_text']}\"\n\n"
                f"Classification: [bold magenta]{r['classification']}[/bold magenta] (Confidence: {r['confidence']*100:.0f}%)\n"
                f"Sentiment: {r.get('sentiment')} | Extracted Intent: {r.get('extracted_intent')}",
                title=f"Reply to Touch #{r['in_response_to_touch']}",
                border_style="magenta"
            ))

def show_decision_logs(db: Database, lead_id: int):
    logs = db.get_decision_logs(lead_id)
    if not logs:
        console.print(f"[yellow]No decision logs found for Lead #{lead_id}.[/yellow]")
        return

    table = Table(title=f"Audit & Reasoning Decision Logs (Lead #{lead_id})", show_lines=True)
    table.add_column("Timestamp", style="dim", width=18)
    table.add_column("Stage", style="cyan", width=16)
    table.add_column("Decision", style="bold yellow", width=26)
    table.add_column("Reasoning & Thought Process", style="white")

    for log in logs:
        table.add_row(
            log["timestamp"][:19],
            log["stage"],
            log["decision"],
            log["reasoning"]
        )

    console.print(table)

def handle_settings(db: Database):
    current = db.get_product_settings()
    console.print(Panel(
        f"[bold]1. Product Name:[/bold] {current.get('product_name')}\n"
        f"[bold]2. What It Does:[/bold] {current.get('what_it_does')}\n"
        f"[bold]3. Sender Name:[/bold] {current.get('sender_name')}\n"
        f"[bold]4. Company Name:[/bold] {current.get('company_name')}\n"
        f"[bold]5. Meeting Link:[/bold] {current.get('calendly_link') or '(none)'}",
        title="Current 'My Product' Settings",
        border_style="cyan"
    ))

    choice = Prompt.ask("Do you want to edit these settings? (y/n)", choices=["y", "n"], default="n")
    if choice == "y":
        p_name = Prompt.ask("Product Name", default=current.get("product_name"))
        w_does = Prompt.ask("What Product Does", default=current.get("what_it_does"))
        s_name = Prompt.ask("Your Name (Sender)", default=current.get("sender_name"))
        c_name = Prompt.ask("Your Company Name", default=current.get("company_name"))
        cal = Prompt.ask("Meeting Link", default=current.get("calendly_link", ""))

        db.save_product_settings({
            "product_name": p_name,
            "what_it_does": w_does,
            "sender_name": s_name,
            "company_name": c_name,
            "calendly_link": cal
        })
        console.print("[bold green]✔ Settings saved successfully! Every future email will use ONLY these details.[/bold green]")

def handle_demo_lead(orchestrator: OutreachOrchestrator, db: Database):
    console.print("[bold cyan]Choose a pre-configured offline demo lead:[/bold cyan]")
    console.print("  [1] [bold green]Startup Founder[/bold green]: Alex Rivera (Founder & CEO @ KiteFlow AI - DevTools & AI)")
    console.print("  [2] [bold green]HR Head[/bold green]: Maya Patel (Chief People Officer @ Lumina Health - HealthTech)")
    console.print("  [3] [bold green]Chief Technology Officer[/bold green]: Marcus Sterling (CTO @ Apex Payments - Fintech)")

    choice = Prompt.ask("Select (1/2/3)", choices=["1", "2", "3"], default="1")
    type_map = {"1": "founder", "2": "hr", "3": "cto"}
    demo_type = type_map[choice]

    with console.status(f"[bold green]Loading realistic demo lead with verified facts & drafting Touch #1..."):
        res = orchestrator.load_demo_lead(demo_type)

    console.print(f"[bold green]✔ Demo lead loaded successfully! (Lead ID: #{res['lead_id']})[/bold green]")
    show_lead_details(db, res["lead_id"])

def main():
    print_banner()
    db = Database()
    ollama = OllamaClient()
    check_ollama(ollama)
    orchestrator = OutreachOrchestrator(db=db, ollama=ollama)

    while True:
        try:
            cmd = Prompt.ask("\n[bold green]agent-cli>[/bold green]").strip()
            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            action = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if action in ["exit", "quit", "q"]:
                console.print("[dim]Goodbye![/dim]")
                sys.exit(0)

            elif action in ["help", "h", "?", "--help"]:
                console.print(Panel(
                    "[bold cyan]Available Terminal Commands:[/bold cyan]\n\n"
                    "  [bold green]demo[/bold green]\n"
                    "      Load 1 of 3 realistic offline demo leads (Founder, HR Head, CTO)\n\n"
                    "  [bold green]approve <touch_id>[/bold green]\n"
                    "      Approve & Send a drafted touchpoint (Human-in-the-loop)\n\n"
                    "  [bold green]settings[/bold green]\n"
                    "      View and update 'My Product' settings (product name, description, sender)\n\n"
                    "  [bold green]research <Name> at <Company>, <Role>[/bold green]\n"
                    "      Quick research & launch (e.g. 'research Jensen Huang at NVIDIA, CEO')\n\n"
                    "  [bold green]add[/bold green]\n"
                    "      Interactive wizard to prospect and research a new lead\n\n"
                    "  [bold green]leads[/bold green] (or [bold green]list[/bold green])\n"
                    "      Show all leads and their pipeline state machine status\n\n"
                    "  [bold green]show <id>[/bold green]\n"
                    "      Inspect a lead's DuckDuckGo RAG dossier, touches, and replies\n\n"
                    "  [bold green]reply <id>[/bold green]\n"
                    "      Simulate an inbound prospect reply (test Interested, Objection, OOO)\n\n"
                    "  [bold green]advance <id>[/bold green]\n"
                    "      Advance sequence cadence (simulates no-reply timeout)\n\n"
                    "  [bold green]logs <id>[/bold green]\n"
                    "      Display transparent reasoning and autonomous decision logs\n\n"
                    "  [bold green]models[/bold green]\n"
                    "      Check local Ollama server connection and installed models",
                    title="Agent Command Quick Reference",
                    border_style="cyan"
                ))

            elif action in ["demo", "demolead", "demo-lead"]:
                handle_demo_lead(orchestrator, db)

            elif action in ["settings", "config"]:
                handle_settings(db)

            elif action in ["approve", "send"]:
                if not arg.isdigit():
                    console.print("[red]Usage: approve <touch_id>[/red]")
                    continue
                touch_id = int(arg)
                try:
                    res = orchestrator.approve_and_send(touch_id)
                    console.print(f"[bold green]✔ Touch #{touch_id} approved and dispatched (simulated)![/bold green]")
                    console.print(f"Lead #{res['lead_id']} status updated to: [blue]IN_SEQUENCE[/blue] (Touch #{res['touch_number']}/4)")
                except Exception as e:
                    console.print(f"[red]Approval failed: {e}[/red]")

            elif action in ["leads", "list"]:
                display_leads(db)

            elif action in ["show", "inspect", "lead"]:
                if not arg.isdigit():
                    console.print("[red]Usage: show <lead_id>[/red]")
                    continue
                show_lead_details(db, int(arg))

            elif action in ["logs", "audit"]:
                if not arg.isdigit():
                    console.print("[red]Usage: logs <lead_id>[/red]")
                    continue
                show_decision_logs(db, int(arg))

            elif action in ["research", "prospect"] or (action == "add" and " at " in arg):
                import re
                m = re.search(r"(?:research|prospect|add)?\s*([A-Za-z\s]+?)\s+at\s+([A-Za-z0-9\s]+?)(?:,\s*([A-Za-z0-9\s]+))?$", cmd, re.IGNORECASE)
                if m:
                    p_name = m.group(1).strip()
                    p_comp = m.group(2).strip()
                    p_role = m.group(3).strip() if m.group(3) else "Executive"
                    email = f"{p_name.lower().replace(' ', '.')}@{p_comp.lower().replace(' ', '')}.com"

                    console.print(f"[bold cyan]Initiating Autonomous Pipeline for {p_name} at {p_comp} ({p_role})...[/bold cyan]")
                    with console.status(f"[bold green]DuckDuckGo search + RAG scoring + Sequence Drafting..."):
                        result = orchestrator.onboard_and_launch_lead(
                            name=p_name,
                            company=p_comp,
                            role=p_role,
                            email=email,
                            industry="Technology"
                        )
                    console.print(f"[bold green]✔ Lead onboarded and Touch #1 drafted (Awaiting Approval)![/bold green] (Lead ID: {result['lead_id']})")
                    show_lead_details(db, result["lead_id"])
                else:
                    console.print("[yellow]Could not parse name and company. Format: 'research <Name> at <Company>, <Role>' or use 'add'[/yellow]")

            elif action == "add":
                console.print("[bold cyan]Enter Lead Details for Research & Outreach:[/bold cyan]")
                name = Prompt.ask("Prospect Full Name").strip()
                company = Prompt.ask("Company Name").strip()
                role = Prompt.ask("Job Title / Role (e.g. VP Sales, CTO)").strip()
                email = Prompt.ask("Email (optional, simulated)", default=f"{name.lower().replace(' ', '.')}@{company.lower().replace(' ', '')}.com")
                industry = Prompt.ask("Industry (e.g. SaaS, Fintech, AI)", default="Technology")

                with console.status(f"[bold green]Running Multi-Agent Pipeline for {name} at {company}..."):
                    result = orchestrator.onboard_and_launch_lead(
                        name=name,
                        company=company,
                        role=role,
                        email=email,
                        industry=industry
                    )

                console.print(f"[bold green]✔ Lead onboarded and Touch #1 drafted (Awaiting Approval)![/bold green] (Lead ID: {result['lead_id']})")
                show_lead_details(db, result["lead_id"])

            elif action == "reply":
                if not arg:
                    console.print("[red]Usage: reply <lead_id>[/red]")
                    continue
                lead_id = int(arg)
                lead = db.get_lead(lead_id)
                if not lead:
                    console.print(f"[red]Lead #{lead_id} not found.[/red]")
                    continue

                console.print(f"[cyan]Simulate prospect reply for {lead['name']} ({lead['company']})[/cyan]")
                console.print("[dim]Example responses you can test:[/dim]")
                console.print("  1. 'Hey, this is interesting. Can you send over a demo link or calendar?' [INTERESTED]")
                console.print("  2. 'Please remove me from your list. Not interested.' [NOT_INTERESTED]")
                console.print("  3. 'We already use a competitor, so we are good for now.' [OBJECTION]")
                console.print("  4. 'I am out of the office until October 28th with limited email access.' [OUT_OF_OFFICE]")
                
                reply_text = Prompt.ask("Inbound Reply Text")
                with console.status("[bold magenta]Classifying reply and computing adaptive next action..."):
                    res = orchestrator.handle_inbound_reply(lead_id, reply_text)

                console.print("\n[bold]Agent Evaluation Result:[/bold]")
                cls = res["classification"]
                dec = res["decision"]
                console.print(f"Classification: [bold yellow]{cls['classification']}[/bold yellow] (Confidence: {cls.get('confidence', 0)*100:.0f}%)")
                console.print(f"Next Action Decision: [bold green]{dec['decision']}[/bold green] (New Status: {dec['status']})")
                console.print(f"[dim]Reasoning:[/dim] {dec['reasoning']}")
                console.print(f"[dim]Recommendation:[/dim] [cyan]{dec['recommended_action']}[/cyan]")

                if res.get("next_touch_draft"):
                    nxt = res["next_touch_draft"]
                    console.print(Panel(
                        f"[bold]Subject:[/bold] {nxt.get('subject')}\n\n{nxt['content']}\n\n"
                        f"[bold green]👉 Status: Draft - Awaiting Approval. Run 'approve {nxt['touch_id']}' to send.[/bold green]",
                        title=f"Autonomous Follow-up Touch Drafted",
                        border_style="yellow"
                    ))

            elif action == "advance":
                if not arg.isdigit():
                    console.print("[red]Usage: advance <lead_id> (simulates cadence timeout / no-reply)[/red]")
                    continue
                lead_id = int(arg)
                with console.status("[bold cyan]Advancing sequence cadence..."):
                    res = orchestrator.advance_cadence_no_reply(lead_id)
                dec = res["decision"]
                console.print(f"Decision: [bold green]{dec['decision']}[/bold green] -> Lead Status: {dec['status']}")
                console.print(f"Reasoning: {dec['reasoning']}")
                if res.get("next_touch_draft"):
                    nxt = res["next_touch_draft"]
                    console.print(Panel(
                        f"[bold]Subject:[/bold] {nxt.get('subject')}\n\n{nxt['content']}\n\n"
                        f"[bold green]👉 Status: Draft - Awaiting Approval. Run 'approve {nxt['touch_id']}' to send.[/bold green]",
                        title="Next Cadence Touch Generated",
                        border_style="yellow"
                    ))

            elif action == "models":
                models = ollama.list_available_models()
                console.print(f"Current Model: [bold cyan]{ollama.model}[/bold cyan]")
                console.print(f"Installed Models on Ollama: {models or 'None found'}")

            else:
                # Conversational AI assistant query
                console.print("[yellow]Processing as agent conversational query...[/yellow]")
                try:
                    response = ollama.generate(
                        prompt=cmd,
                        system_prompt=(
                            "You are the conversational AI orchestrator for the Personalized Multi-Touch Sales Outreach Agent. "
                            "Assist the user with prospecting strategy, email copy reviews, sequence cadences, or answering questions."
                        )
                    )
                    console.print(Panel(response, title="Agent Response", border_style="cyan"))
                except Exception as e:
                    console.print(f"[red]Could not query Ollama: {e}[/red]")
                    console.print("[dim]Use commands like 'demo', 'add', 'leads', 'show 1', 'approve 1', 'reply 1'[/dim]")

        except KeyboardInterrupt:
            console.print("\n[dim]Exiting...[/dim]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

if __name__ == "__main__":
    main()
