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
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock Ollama responses (sets OLLAMA_MOCK=1)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        help="Timeout for Ollama in seconds (sets OLLAMA_TIMEOUT)",
    )
    args = parser.parse_args()

    cfg = load_config()
    model = args.model or cfg.get("model", "deepseek-coder")

    # Wire CLI flags to environment so agent.core will honor them
    if getattr(args, "mock", False):
        os.environ["OLLAMA_MOCK"] = "1"
        console.print(
            "[yellow]Running in MOCK mode: Ollama responses will be synthetic.[/yellow]"
        )
    if getattr(args, "timeout", None) is not None:
        os.environ["OLLAMA_TIMEOUT"] = str(args.timeout)
        console.print(f"[yellow]Ollama timeout set to {args.timeout} seconds[/yellow]")

    console.print(f"[bold green]CLI Coding Agent (Model: {model})[/bold green]")
    console.print(
        "Commands: /run <lang>, /runfile <path>, /debug <path>, /open <path>, /sendfile <path>, /clear, /exit\n"
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
                    ".cc": "cpp",
                    ".cxx": "cpp",
                }
                lang = ext_map.get(
                    ext, "python"
                )  # Default to python for unknown extensions
                console.print(f"[yellow]Running file {path} as {lang}...[/yellow]")
                output = run_code(lang, code)
                console.print("\n[bold blue]Program output:[/bold blue]")
                highlight_output(output, "text")
                console.print()
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
                elif len(parts) == 2:
                    # Check if parts[1] looks like a file path - if so, redirect to /runfile
                    if "/" in parts[1] or "\\" in parts[1] or "." in parts[1]:
                        console.print(
                            f"[yellow]Detected file path. Use /runfile {parts[1]} instead[/yellow]"
                        )
                        continue
                    lang = parts[1]
                else:
                    console.print("[red]Usage: /run [<lang>][/red]\n")
                    continue

                console.print(f"[yellow]Running last code as {lang}...[/yellow]")
                output = run_code(lang, last_code)
                console.print("\n[bold blue]Program output:[/bold blue]")
                highlight_output(output, "text")
                console.print()
                continue

            if prompt.startswith("/open "):
                path = prompt.split(" ", 1)[1].strip()
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

                # Try to detect language and show file
                ext = Path(path).suffix.lower()
                ext_map = {
                    ".py": "python",
                    ".js": "js",
                    ".sh": "bash",
                    ".c": "c",
                    ".cpp": "cpp",
                    ".cc": "cpp",
                    ".cxx": "cpp",
                }
                lang = ext_map.get(ext, "text")
                console.print(f"[green]Opening {path} ({lang}):[/green]")
                highlight_output(code, lang)
                console.print()
                # set last_code so you can /run immediately
                last_code = code
                last_lang = lang
                continue

            if prompt.startswith("/sendfile "):
                path = prompt.split(" ", 1)[1].strip()
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

                # Add file contents to memory and query model
                memory.add("user", f"Please review this file: {path}\n\n" + code)
                full_prompt = memory.context() + "\n\nAssistant:"
                response = query_ollama(full_prompt, model)
                console.print("\n[bold magenta]Assistant>[/bold magenta]")
                console.print(response)
                console.print()
                memory.add("assistant", response)
                # detect code blocks in response
                lang2, code2 = extract_code_blocks(response)
                if code2:
                    last_code = code2
                    last_lang = lang2
                    console.print(
                        f"[green]Detected code block ({lang2}) in assistant response[/green]"
                    )
                    highlight_output(code2, lang2)
                    console.print()
                continue

            if prompt.startswith("/debug "):
                path = prompt.split(" ", 1)[1].strip()
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
                if not os.path.exists(path):
                    console.print(f"[red]File not found: {path}[/red]\n")
                    continue

                try:
                    with open(path, "r", encoding="utf-8") as f:
                        original_code = f.read()
                except Exception as e:
                    console.print(f"[red]Error reading file:[/red] {e}\n")
                    continue

                console.print(f"[yellow]Debugging {path}...[/yellow]")

                # Create a focused debugging prompt
                debug_prompt = f"""Analyze this code file and fix any issues. Return ONLY the corrected code in a single code block, no explanations:

File: {path}
```
{original_code}
```

Instructions:
- Fix syntax errors, logic bugs, missing imports
- Improve code quality and best practices
- Ensure the code actually works and produces expected output
- Return the complete corrected file content in a code block"""

                # Don't add to memory, this is an autonomous operation
                response = query_ollama(debug_prompt, model)

                console.print("\n[bold magenta]Analysis complete.[/bold magenta]")

                # Extract the corrected code
                lang, fixed_code = extract_code_blocks(response)
                if not fixed_code:
                    console.print(
                        "[red]No code block found in response. Manual review needed.[/red]\n"
                    )
                    console.print(response)
                    continue

                # Show the diff concept (simplified)
                if fixed_code.strip() == original_code.strip():
                    console.print(
                        "[green]No issues found. File is already correct.[/green]\n"
                    )
                    continue

                # Apply the fix automatically (no backup)
                try:
                    # Write fixed code directly
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(fixed_code)

                    console.print(f"[green]✓ Fixed and updated {path}[/green]")

                    # Show what was fixed
                    console.print("\n[bold blue]Updated code:[/bold blue]")
                    ext = Path(path).suffix.lower()
                    ext_map = {
                        ".py": "python",
                        ".js": "js",
                        ".sh": "bash",
                        ".c": "c",
                        ".cpp": "cpp",
                        ".cc": "cpp",
                        ".cxx": "cpp",
                    }
                    detected_lang = ext_map.get(ext, "text")
                    highlight_output(fixed_code, detected_lang)
                    console.print()

                    # Set as last code for immediate testing
                    last_code = fixed_code
                    last_lang = detected_lang
                    console.print("[cyan]Type /run to test the fixed code[/cyan]\n")

                except Exception as e:
                    console.print(f"[red]Error writing fixed code:[/red] {e}\n")

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
