import subprocess
import os
import re


def query_ollama(prompt, model):
    """Query Ollama. If OLLAMA_MOCK is set (1/true), return a canned mock response useful for development.

    Returns the assistant response (string).
    """
    mock_env = os.environ.get("OLLAMA_MOCK", "").lower()
    if mock_env in ("1", "true", "yes"):
        # Return a helpful mock response that includes a python code block so the CLI can detect and run it.
        return (
            "Mock assistant response (OLLAMA_MOCK=1 enabled).\n\n"
            "Here is a sample Python snippet:\n\n"
            "```python\nprint('Hello from mock Ollama')\n```"
        )

    try:
        cmd = ["ollama", "run", model]
        # Use explicit UTF-8 decoding and replace invalid bytes to avoid crashes on Windows
        # and ensure we receive Python strings rather than raw bytes.
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        # Allow configuring timeout via OLLAMA_TIMEOUT (seconds); default to 20s
        try:
            timeout = int(os.environ.get("OLLAMA_TIMEOUT", "20"))
        except Exception:
            timeout = 20

        try:
            out, err = process.communicate(prompt, timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except Exception:
                pass
            return (
                f"[Error] Ollama did not respond within {timeout} seconds."
                " Try setting OLLAMA_MOCK=1 for development or check that the Ollama daemon is running."
            )

        # Strip common ANSI escape sequences (cursor movements, color codes, etc.)
        def strip_ansi(s: str) -> str:
            if not s:
                return s
            # remove CSI and other ESC sequences
            s = re.sub(r"\x1B\[[0-9;?]*[ -/]*[@-~]", "", s)
            # remove leftover OSC / operating system commands
            s = re.sub(r"\x1B\].*?\x07", "", s)
            return s

        out = strip_ansi(out)
        err = strip_ansi(err)

        if err and not out:
            return f"[Error from Ollama]\n{err.strip()}"
        return out.strip()
    except FileNotFoundError:
        return (
            "Error: Ollama not found. Make sure it’s installed and in PATH.\n"
            "For development you can set the environment variable OLLAMA_MOCK=1 to use a mocked response."
        )
