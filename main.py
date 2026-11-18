import sys
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Personalized Multi-Touch Sales Outreach Agent (Track D) - Local Ollama + DuckDuckGo RAG"
    )
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Launch the interactive web UI and dashboard on http://localhost:8000"
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8000,
        help="Port for the web UI server (default: 8000)"
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=None,
        help="Ollama model name (e.g. llama3, mistral, qwen2.5)"
    )

    args = parser.parse_args()

    if args.model:
        from sales_agent.config import config
        config.ollama_model = args.model

    if args.web:
        from sales_agent.web_ui import start_server
        start_server(port=args.port)
    else:
        from sales_agent.cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()
