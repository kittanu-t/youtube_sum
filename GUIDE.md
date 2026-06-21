# 📖 youtube_sum — User Guide

Step-by-step guide to install, configure, and use the YouTube Summarization Agent.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Running the Application](#4-running-the-application)
5. [Using the Web UI](#5-using-the-web-ui)
6. [Using the API](#6-using-the-api)
7. [Using Docker](#7-using-docker)
8. [Supported Models](#8-supported-models)
9. [Troubleshooting](#9-troubleshooting)
10. [Development](#10-development)

---

## 1. Prerequisites

Before you start, make sure you have:

| Requirement | Minimum Version | Notes |
|-------------|----------------|-------|
| **Python** | 3.12+ | [Download](https://www.python.org/downloads/) |
| **uv** (package manager) | latest | [Install guide](https://docs.astral.sh/uv/getting-started/installation/) |
| **Ollama** (local LLM) | latest | [Download](https://ollama.com/) — required for local mode |
| **ffmpeg** | any | Needed for audio processing (yt-dlp fallback) |

### Install uv

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Install Ollama

1. Download from [ollama.com](https://ollama.com/)
2. Install and start the Ollama service
3. Pull a model (see [Supported Models](#8-supported-models)):
   ```bash
   ollama pull gemma3:latest
   ```

### Install ffmpeg

**Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install ffmpeg
```

---

## 2. Installation

### Step 1: Clone the repository

```bash
git clone https://github.com/kittanu-t/youtube_sum.git
cd youtube_sum
```

### Step 2: Create a virtual environment and install

```bash
uv venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
uv pip install -e ".[dev]"
```

> **Note:** The `.[dev]` includes testing and linting tools. For production, use `uv pip install -e .` instead.

### Step 3: Verify installation

```bash
python -c "import app; print(app.__version__)"
# Should output: 0.1.0
```

---

## 3. Configuration

### Step 1: Create your `.env` file

```bash
cp .env.example .env
```

### Step 2: Edit `.env` with your settings

Open `.env` in any text editor. Here are the most common configurations:

#### Option A: Ollama (Local, Free) — Recommended

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest
```

That's it! No API key needed.

#### Option B: OpenAI (Cloud)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

#### Option C: Gemini (Cloud)

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key-here
```

### Full `.env` Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM backend: `ollama`, `openai`, or `gemini` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma3:latest` | Ollama model name |
| `OPENAI_API_KEY` | *(empty)* | OpenAI API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API URL |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `GEMINI_API_KEY` | *(empty)* | Gemini API key |
| `DATABASE_PATH` | `./youtube_sum.db` | SQLite database file path |
| `CHUNK_SIZE` | `8000` | Transcript chunk size for long videos |
| `CHUNK_OVERLAP` | `500` | Overlap between chunks |
| `API_HOST` | `0.0.0.0` | FastAPI bind address |
| `API_PORT` | `8000` | FastAPI port |
| `STREAMLIT_PORT` | `8501` | Streamlit port |

---

## 4. Running the Application

You need **two terminals** — one for the API, one for the Web UI.

### Terminal 1: Start the API

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

The API docs are available at: **http://localhost:8000/docs**

### Terminal 2: Start the Web UI

```bash
streamlit run streamlit_app.py
```

You should see:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

Open **http://localhost:8501** in your browser.

---

## 5. Using the Web UI

### Step 1: Paste a YouTube URL

On the main page, paste any YouTube video URL into the input field. Supported formats:

- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://youtu.be/VIDEO_ID`
- `https://www.youtube.com/shorts/VIDEO_ID`

### Step 2: Choose your settings (sidebar)

| Setting | Options | Description |
|---------|---------|-------------|
| **Output Language** | English / Thai | Language for the summary and notes |
| **Summary Level** | Short / Detailed / Bullet | How detailed the summary should be |

### Step 3: Click a button

| Button | What it does |
|--------|-------------|
| **📝 Summarize** | Fetches transcript → generates summary → displays result |
| **📚 Study Notes** | Fetches transcript → generates structured study notes |

### Step 4: View results

After processing, you'll see:

- **Video Information** — title, channel, duration
- **Summary / Study Notes** — formatted Markdown output
- **⏱️ Chapters** — video sections with timestamps (if available)
- **📌 Key Points** — extracted bullet points

### Step 5: Export

Click any export button:

| Button | Format | Use case |
|--------|--------|----------|
| **📄 Download Markdown** | `.md` | Read in any Markdown editor, Obsidian, Notion |
| **📝 Download TXT** | `.txt` | Plain text, universal compatibility |
| **🔧 Download JSON** | `.json` | Programmatic use, structured data |
| **🃏 Flashcards CSV** | `.csv` | Import into Anki or other flashcard apps |

### History

Click **📜 History** at the bottom of the page to see previously summarized videos. You can delete individual entries or clear all history from the sidebar.

---

## 6. Using the API

The API runs on `http://localhost:8000` by default. Interactive docs: **http://localhost:8000/docs**

### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{"status": "ok", "service": "youtube_sum"}
```

### Get Video Info

```bash
curl "http://localhost:8000/api/video-info?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

### Summarize a Video

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "level": "detailed",
    "language": "en"
  }'
```

**Parameters:**

| Field | Type | Default | Options |
|-------|------|---------|---------|
| `url` | string | *required* | Any YouTube URL |
| `level` | string | `detailed` | `short`, `detailed`, `bullet` |
| `language` | string | `en` | `en`, `th` |

### Generate Study Notes

```bash
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "th"
  }'
```

### Translate Text

```bash
curl -X POST http://localhost:8000/api/translate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, how are you?",
    "target_language": "th"
  }'
```

### Export Content

```bash
curl -X POST http://localhost:8000/api/export \
  -H "Content-Type: application/json" \
  -d '{
    "video_id": "dQw4w9WgXcQ",
    "video_title": "My Video",
    "channel": "My Channel",
    "summary": "## Overview\n\nThis is a summary.",
    "chapters": [{"title": "Intro", "timestamp": "00:00", "seconds": 0}],
    "key_points": ["Point 1", "Point 2"],
    "format": "markdown"
  }'
```

**Format options:** `markdown`, `txt`, `json`, `csv`

### History

```bash
# List history (default: 50 entries)
curl "http://localhost:8000/api/history?limit=20&offset=0"

# Delete one entry
curl -X DELETE http://localhost:8000/api/history/1

# Clear all history
curl -X DELETE http://localhost:8000/api/history
```

---

## 7. Using Docker

Docker lets you run both the API and Web UI without installing Python locally.

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Ollama running on your host machine (for local LLM)

### Step 1: Configure

```bash
cp .env.example .env
```

Make sure `OLLAMA_BASE_URL` in `.env` is set to reach your host machine:

```env
OLLAMA_BASE_URL=http://host.docker.internal:11434
```

### Step 2: Build and run

```bash
docker compose up --build
```

### Step 3: Access

| Service | URL |
|---------|-----|
| API Docs | http://localhost:8000/docs |
| Web UI | http://localhost:8501 |

### Step 4: Stop

```bash
docker compose down
```

### Docker Commands Reference

```bash
# Start in background
docker compose up -d

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up --build

# Stop everything
docker compose down

# Stop and remove volumes
docker compose down -v
```

---

## 8. Supported Models

### Local Models (via Ollama)

| Model | Size | Quality | Speed | Best For |
|-------|------|---------|-------|----------|
| `gemma3:latest` | ~5B | ⭐⭐⭐⭐ | Fast | Best overall balance |
| `qwen3:latest` | ~4B | ⭐⭐⭐⭐ | Fast | Multilingual content |
| `llama3.2:latest` | ~3B | ⭐⭐⭐ | Very Fast | Quick summaries |
| `llama3.1:8b` | ~8B | ⭐⭐⭐⭐⭐ | Slower | Highest quality local |

**Pull a model:**
```bash
ollama pull gemma3:latest
```

**List installed models:**
```bash
ollama ls
```

**Change model in `.env`:**
```env
OLLAMA_MODEL=llama3.2:latest
```

### Cloud Models

| Provider | Model | Cost |
|----------|-------|------|
| OpenAI | `gpt-4o-mini` | Pay per token |
| OpenAI | `gpt-4o` | Pay per token (higher quality) |
| Gemini | `gemini-1.5-flash` | Free tier available |

---

## 9. Troubleshooting

### "No module named 'app'"

Make sure you installed in editable mode:
```bash
uv pip install -e ".[dev]"
```

### "Connection refused" to Ollama

1. Make sure Ollama is running:
   ```bash
   ollama serve
   ```
2. Check the URL in `.env`:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   ```
3. Test the connection:
   ```bash
   curl http://localhost:11434/api/tags
   ```

### "Could not retrieve transcript"

Some videos don't have transcripts available. The app handles this gracefully:

- **Private/unavailable videos** → Error message displayed
- **No captions** → Tries auto-generated captions, then yt-dlp fallback
- **Rate limiting** → Wait a few seconds and try again

### "Model not found" (Ollama)

Pull the model first:
```bash
ollama pull gemma3:latest
```

### Port already in use

Change the port in `.env`:
```env
API_PORT=8001
STREAMLIT_PORT=8502
```

Or find and kill the process using the port:
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
kill -9 <PID>
```

### Streamlit UI shows "Connection error"

Make sure the API is running on port 8000. Check the `API_URL` in the Streamlit sidebar — it defaults to `http://localhost:8000/api`.

### Docker: Cannot connect to Ollama

On Linux, `host.docker.internal` may not work. Use your host machine's IP instead:
```env
OLLAMA_BASE_URL=http://192.168.x.x:11434
```

Or use Docker network mode:
```yaml
# In docker-compose.yml, add to each service:
network_mode: host
```

---

## 10. Development

### Run Tests

```bash
# All tests
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=app --cov=services --cov=api

# Specific test file
pytest tests/test_youtube_service.py -v
```

### Lint and Format

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Project Structure

```
youtube_sum/
├── app/                    # Core application
│   ├── __init__.py         # Package init, version
│   ├── config.py           # Settings (pydantic-settings)
│   └── database.py         # SQLite schema + connection
├── api/                    # FastAPI routes
│   ├── __init__.py
│   └── routes.py           # All API endpoints
├── services/               # Business logic
│   ├── __init__.py         # Service exports
│   ├── youtube_service.py  # URL validation, video info
│   ├── transcript_service.py  # Transcript retrieval
│   ├── summarization_service.py  # LLM summarization
│   ├── notes_service.py    # Study note generation
│   ├── chapter_service.py  # Chapter extraction
│   ├── translation_service.py  # EN↔TH translation
│   ├── export_service.py   # Markdown/TXT/CSV/JSON export
│   └── history_service.py  # SQLite history CRUD
├── streamlit_app.py        # Streamlit frontend
├── main.py                 # FastAPI entry point
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures
│   └── test_*.py           # Test modules
├── Dockerfile              # Docker build
├── docker-compose.yml      # Docker orchestration
├── pyproject.toml          # Project config
└── .env.example            # Config template
```

### Adding a New LLM Provider

1. Add provider settings to `app/config.py`
2. Add a `_call_<provider>()` method to the relevant service class
3. Update the `_call_llm()` dispatcher method
4. Add tests with mocked HTTP responses

---

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                  youtube_sum Quick Reference                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  INSTALL:                                                   │
│    uv venv && uv pip install -e ".[dev]"                    │
│                                                             │
│  CONFIGURE:                                                 │
│    cp .env.example .env  # edit settings                    │
│                                                             │
│  RUN API:                                                   │
│    python main.py           → http://localhost:8000/docs    │
│                                                             │
│  RUN UI:                                                    │
│    streamlit run streamlit_app.py  → http://localhost:8501  │
│                                                             │
│  DOCKER:                                                    │
│    docker compose up --build                                │
│                                                             │
│  TEST:                                                      │
│    pytest -v                                                │
│                                                             │
│  LINT:                                                      │
│    ruff check . && ruff format .                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
