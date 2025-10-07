# MyAssistant

A personal, multilingual memory assistant. Tell it anything to remember; ask later to recall. Works with any language for both input and output.

## Features
- Store memories with optional tags and source
- Full-text search (SQLite FTS5)
- Automatic language detection for each memory
- REST API via FastAPI
- Simple CLI
- **NEW: Desktop GUI with voice input and text-to-speech**

## Requirements
- Python 3.10+

## Setup

```bash
# Option 1: using uv (fast)
pip install uv
uv pip install -e .

# Option 2: standard pip
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run the API server

```bash
uvicorn myassistant.api:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/docs` for interactive docs.

## GUI App (Recommended)

Launch the desktop application with voice and text input:

```bash
assistant-gui
```

**Features:**
- 🎤 **Voice Input**: Click the microphone button to speak your memories or questions
- ⌨️ **Text Input**: Type directly in the text box
- 🔊 **Voice Output**: Hear responses with text-to-speech
- 🔄 **Two Modes**: 
  - **Remember**: Store new memories
  - **Ask**: Search existing memories
- 🌍 **Multilingual**: Works with any language for both input and output

## CLI usage

```bash
# Remember something
assistant remember "Call mom on Friday"
assistant remember "买牛奶和鸡蛋" --tags shopping personal
assistant remember "Reunión el jueves a las 10" --source calendar

# Recall
assistant ask "What should I buy?"
assistant ask "viernes"
assistant ask "jueves 10"

# List recent
assistant list --limit 10
```

## Data location

By default, the database is stored at `~/.myassistant/memories.db`. Override with env var `ASSISTANT_DB_PATH`.

## License
MIT

