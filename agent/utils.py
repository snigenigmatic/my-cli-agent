import yaml
import re
from rich.console import Console
from rich.syntax import Syntax

console = Console()


def load_config():
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except Exception:
        return {"model": "deepseek-coder", "temperature": 0.3}


def extract_code_blocks(text):
    pattern = r"```(\w+)?\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    if not matches:
        return None, None
    lang, code = matches[-1]  # take last block
    lang = lang.strip() if lang else "python"
    return lang, code.strip()


def highlight_output(text, lang="python"):
    try:
        syntax = Syntax(text, lang, theme="monokai", line_numbers=False)
        console.print(syntax)
    except Exception:
        console.print(text)
