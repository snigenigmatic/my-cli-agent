import argparse
import os
from pathlib import Path
from agent.core import query_ollama
from agent.executor import run_code
from agent.memory import Memory
from agent.utils import load_config, extract_code_blocks, highlight_output, console


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", help="Ollama model to use")
    args = parser.parse_args()

    cfg = load_config()
    model = args.model or cfg.get("model", "deepseek-coder")

    console.print(f"[bold green]CLI Coding Agent (Model: {model})[/bold green]")
    console.print(
        "Type /run <lang> to execute last code, /runfile <path> to execute a file, /clear to reset memory, or /exit to quit.\n"
    )

    memory = Memory()
    last_code = None
    last_lang = None

    while True:
        try:
            prompt = input("You> ").strip()
            if not prompt:
                continue
            if prompt.lower() in ["/exit", "exit", "quit"]:
                break
            if prompt.lower() == "/clear":
                memory = Memory()
                console.print("[cyan]Memory cleared[/cyan]\n")
                continue

            if prompt.startswith("/run"):
                parts = prompt.split()
                if not last_code:
                    console.print("[red]No code to run yet[/red]\n")
                    continue

                # Allow `/run` (use last detected language) or `/run <lang>`
                if len(parts) == 1:
                    if not last_lang:
                        console.print(
                            "[red]No language specified and no last detected language; use /run <lang>[/red]\n"
                        )
                        continue
                    lang = last_lang
                else:
                    lang = parts[1]

                console.print(f"[yellow]Running last code as {lang}...[/yellow]")
                output = run_code(lang, last_code)
                console.print("\n[bold blue]Program output:[/bold blue]")
                highlight_output(output, "text")
                console.print()
                continue

            if prompt.startswith("/runfile "):
                path = prompt.split(" ", 1)[1].strip()
                # Resolve path relative to project root if not absolute
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)

                if not os.path.exists(path):
                    console.print(f"[red]File not found: {path}[/red]\n")
                    continue

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        code = f.read()
                except Exception as e:
                    console.print(f"[red]Error reading file:[/red] {e}\n")
                    continue

                ext = Path(path).suffix.lower()
                ext_map = {
                    ".py": "python",
                    ".js": "js",
                    ".sh": "bash",
                    ".c": "c",
                    ".cpp": "cpp",
                }
                lang = ext_map.get(ext, "text")
                console.print(f"[yellow]Running file {path} as {lang}...[/yellow]")
                output = run_code(lang, code)
                console.print("\n[bold blue]Program output:[/bold blue]")
                highlight_output(output, "text")
                console.print()
                continue

            memory.add("user", prompt)
            full_prompt = memory.context() + "\n\nAssistant:"
            response = query_ollama(full_prompt, model)

            console.print("\n[bold magenta]Assistant>[/bold magenta]")
            console.print(response)
            console.print()

            memory.add("assistant", response)

            lang, code = extract_code_blocks(response)
            if code:
                last_code = code
                last_lang = lang
                console.print(f"[green]Detected code block ({lang})[/green]")
                highlight_output(code, lang)
                console.print()

        except KeyboardInterrupt:
            console.print("\n[Interrupted]")
            break
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    main()
