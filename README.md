# CLI Coding Agent

An autonomous coding agent that can analyze, debug, and fix code files using local Ollama models. The agent reads files, identifies issues, applies fixes directly, and executes code to verify results.

## What This Does

**Core Function**: Interactive CLI that connects to Ollama models for autonomous code debugging and execution.

**Key Capabilities**:
- `/debug <file>` - Automatically analyzes and fixes code issues in place
- `/runfile <file>` - Executes code files and shows output  
- `/run [language]` - Runs the last processed code
- Natural language interaction with coding context memory
- Supports Python, JavaScript, C, C++, Bash

**Autonomous Operation**: The agent reads your files, sends them to the LLM for analysis, extracts fixed code from responses, and applies changes directly without manual intervention.

## Requirements

- **Python 3.12+**
- **Ollama CLI** installed and accessible in PATH
- **At least one Ollama model** pulled locally (e.g., `llama3:8b`, `deepseek-coder`)
- **Language-specific tools** for code execution:
  - Python: `python` (usually included)
  - JavaScript: `node` 
  - C/C++: `gcc`/`g++`
  - Bash: `bash` (Linux/macOS) or `powershell` (Windows)

## Installation

1. **Install dependencies**:
   ```bash
   pip install pyyaml rich
   ```
   Or with uv:
   ```bash
   uv sync
   ```

2. **Install and setup Ollama**:
   - Download from [ollama.com](https://ollama.com)
   - Pull a model: `ollama pull llama3:8b`
   - Verify: `ollama list`

3. **Configure model** (optional):

   Edit `config.yaml` to set your preferred model:

   ```yaml
   model: llama3:8b
   temperature: 0.3
   ```

## Usage

### Start the agent

```bash
python cli.py
```

**Options**:
- `--model <name>` - Override config model
- `--mock` - Use mock responses (no Ollama required)
- `--timeout <seconds>` - Set response timeout (default: 20s)

### Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `/debug <path>` | Analyze and fix file automatically | `/debug src/app.py` |
| `/runfile <path>` | Execute a code file | `/runfile scripts/test.js` |
| `/run [lang]` | Run last processed code | `/run` or `/run python` |
| `/open <path>` | Display file with syntax highlighting | `/open config.json` |
| `/sendfile <path>` | Send file to model for analysis only | `/sendfile README.md` |
| `/clear` | Reset conversation memory | `/clear` |
| `/exit` | Quit | `/exit` |

### Typical Workflow

1. **Debug a problematic file**:

   ```
   You> /debug buggy_script.py
   ```

   - Agent reads the file
   - Sends to LLM for analysis  
   - Extracts fixed code
   - Overwrites original file
   - Shows what was changed

2. **Test the fix**:

   ```
   You> /run
   ```

   - Executes the fixed code
   - Shows output/errors

3. **Ask follow-up questions**:

   ```
   You> why did the original code fail?
   You> add error handling to this function
   ```

## How It Works

1. **File Analysis**: Reads code files and sends them to the configured Ollama model
2. **LLM Processing**: Model analyzes code for syntax errors, logic bugs, missing imports, style issues
3. **Code Extraction**: Parses LLM response for code blocks using regex pattern matching
4. **Direct Application**: Overwrites original files with fixed code (no backups by design)
5. **Execution**: Uses appropriate interpreters/compilers based on file extension
6. **Memory**: Maintains conversation context (last 8 messages) for follow-up questions

## Configuration

- **Model Selection**: Set in `config.yaml` or use `--model` flag
- **Timeout**: Default 20s, configurable via `--timeout` or `OLLAMA_TIMEOUT` env var
- **Mock Mode**: Use `--mock` or `OLLAMA_MOCK=1` for offline development/testing

## Language Support

| Extension | Language | Execution Method |
|-----------|----------|------------------|
| `.py` | Python | `python <file>` |
| `.js` | JavaScript | `node <file>` |
| `.c` | C | `gcc <file> -o exe && ./exe` |
| `.cpp`, `.cc`, `.cxx` | C++ | `g++ <file> -o exe && ./exe` |
| `.sh` | Bash | `bash <file>` (Linux/Mac), `powershell <file>` (Windows) |

## Error Handling

- **File not found**: Clear error message with path
- **Missing tools**: Detects unavailable compilers/interpreters and reports specific missing tool
- **Ollama timeout**: Configurable timeout prevents hanging on unresponsive model calls
- **Invalid code blocks**: Warns when LLM doesn't return parseable code
- **Execution errors**: Captures and displays stdout/stderr from code execution

## Development Mode

For development without Ollama:

```bash
python cli.py --mock
```

Returns synthetic responses with sample code blocks for testing CLI functionality.

## Limitations

- **No sandboxing**: Executes code directly on your system
- **No backup**: Files are modified in place (use version control)
- **Language dependencies**: Requires appropriate compilers/interpreters installed
- **LLM dependent**: Code quality depends on the Ollama model's capabilities

## Project Structure

```
cli.py              # Main CLI interface
config.yaml         # Default model configuration  
agent/
  ├── core.py       # Ollama integration and mock mode
  ├── executor.py   # Code execution with tool detection
  ├── memory.py     # Conversation context management
  └── utils.py      # Config loading, code extraction, syntax highlighting
```
