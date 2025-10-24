import subprocess
import tempfile
import os
import platform
import sys
import shutil


def get_ext(lang):
    return {
        "python": ".py",
        "cpp": ".cpp",
        "c": ".c",
        "js": ".js",
        "bash": ".sh",
    }.get(lang, ".txt")


def get_command(lang, path):
    """
    Return a command list for subprocess given a language and file path.
    Raises FileNotFoundError with a clear message when a required tool is missing.
    """
    system = platform.system().lower()
    if lang == "python":
        return [sys.executable, path]

    if lang == "js":
        node = shutil.which("node")
        if not node:
            raise FileNotFoundError("Node.js (node) not found on PATH")
        return [node, path]

    if lang == "bash":
        if "win" in system:
            pwsh = shutil.which("powershell") or shutil.which("pwsh")
            if not pwsh:
                raise FileNotFoundError("PowerShell not found on PATH")
            return [pwsh, "-File", path]
        else:
            bash = shutil.which("bash")
            if not bash:
                raise FileNotFoundError("bash not found on PATH")
            return [bash, path]

    if lang == "cpp":
        gpp = shutil.which("g++")
        if not gpp:
            raise FileNotFoundError("g++ not found on PATH")
        exe = path[:-4]
        if "win" in system:
            return ["cmd", "/c", f"{gpp} {path} -o {exe}.exe && {exe}.exe"]
        else:
            return ["bash", "-c", f"{gpp} {path} -o {exe} && {exe}"]

    if lang == "c":
        gcc = shutil.which("gcc")
        if not gcc:
            raise FileNotFoundError("gcc not found on PATH")
        exe = path[:-2]
        if "win" in system:
            return ["cmd", "/c", f"{gcc} {path} -o {exe}.exe && {exe}.exe"]
        else:
            return ["bash", "-c", f"{gcc} {path} -o {exe} && {exe}"]

    # default: print file contents using Python to remain cross-platform
    return [sys.executable, "-c", f"print(open(r'{path}').read())"]


def run_code(lang, code):
    path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=get_ext(lang)) as f:
            f.write(code.encode())
            path = f.name

        cmd = get_command(lang, path)
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = (result.stdout or "") + (result.stderr or "")
        return output.strip() if output else "[No output]"
    except FileNotFoundError as e:
        return f"[Runtime Error] {e}"
    except Exception as e:
        return f"[Runtime Error] {e}"
    finally:
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except Exception:
            pass
