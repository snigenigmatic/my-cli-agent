import subprocess
import os


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
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
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

        if err:
            return f"[Error from Ollama]\n{err.strip()}"
        return out.strip()
    except FileNotFoundError:
        return (
            "Error: Ollama not found. Make sure it’s installed and in PATH.\n"
            "For development you can set the environment variable OLLAMA_MOCK=1 to use a mocked response."
        )
