# PuterAgent

PuterAgent is a local multi-agent coding assistant with a local model runner (Ollama) and expert agents. It supports both a terminal CLI mode and a browser-based web UI.

## Features

- Terminal CLI interaction via `--cli`
- Browser UI via `--web`
- Local model execution via Ollama
- Model selection support for multiple Ollama models
- Expert routing across Code, File, Shell, and Debug agents
- Web chat history and clear session support
- Text file uploads in the browser UI
- Active model display with provider avatar switching
- Persistent profile and per-model chat history
- Theme selection and live web UI personalization
- Directory and GitHub repo analysis from the browser settings panel
- Per-turn and session token metrics

## Requirements

- Python 3.11+ recommended
- `requests` library
- **Ollama** running locally (https://ollama.ai)

Install dependencies:

```bash
pip install requests
```

## Setup

### 1. Install Ollama

Download and install Ollama from https://ollama.ai

### 2. Pull the default model

```bash
ollama pull qwen2.5-coder:14b
```

You can also pull other supported models:

```bash
ollama pull qwen2.5-coder:7b
ollama pull deepseek-coder:6.7b
ollama pull neural-chat:7b
ollama pull mistral:7b
ollama pull llama2:13b
```

### 3. Start Ollama

```bash
ollama serve
```

This will start the Ollama API server on `http://localhost:11434`.

## Running

### Terminal CLI

```bash
python src/main.py --cli
```

### Browser UI

```bash
python src/main.py --web
```

The web UI will launch locally and serve `src/ui.html`, including profile settings, theme selection, and repo analysis.

## Model Selection

### CLI mode

Choose a model with `--model`:

```bash
python src/main.py --cli --model mistral:7b
```

### Web mode

Use the model dropdown in the sidebar.

### Supported models

All Ollama-compatible models are supported. Some popular options:

- `qwen2.5-coder:14b` (default)
- `qwen2.5-coder:7b`
- `deepseek-coder:6.7b`
- `neural-chat:7b`
- `mistral:7b`
- `llama2:13b`

## Commands

In CLI mode, use:

- `exit` or `quit` to stop
- `/clear` to reset the conversation

In web mode, use the `Clear conversation` button. Uploaded files are attached as bounded text context for the current turn.

## Project Layout

- `src/main.py` — application entrypoint and CLI/web launcher
- `src/config.py` — configuration, available models, and token loading
- `src/base_agent.py` — core API integration and tool loop
- `src/orchestrator.py` — orchestrator that routes tasks to expert agents
- `src/ui.html` — browser user interface

## Notes

- Make sure Ollama is running before starting PuterAgent
- Models are pulled once and cached locally by Ollama
- First run may be slow as the model is loaded into memory
