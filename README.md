# 🎬 YouTube Summarization Agent

Summarize YouTube videos into structured summaries and study notes using local LLMs (Ollama) or cloud APIs (OpenAI, Gemini).

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **📝 Multi-level Summaries** — Short, detailed, or bullet-point summaries
- **📚 Study Notes** — Structured notes with key concepts, timeline, takeaways, review questions, and vocabulary
- **⏱️ Chapter Detection** — Extracts native YouTube chapters or infers them from transcripts
- **🌐 Multi-language** — English and Thai support
- **📥 Export** — Download as Markdown, TXT, JSON, or CSV flashcards
- **💬 Translation** — Translate between English and Thai
- **📜 History** — SQLite-backed history of all summaries
- **🖥️ Web UI** — Clean Streamlit interface
- **🔌 REST API** — FastAPI endpoints for programmatic access
- **🐳 Docker** — Run with `docker compose up`
- **🆓 Free & Local** — Runs entirely locally with Ollama

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Streamlit   │────▶│   FastAPI    │────▶│    Services     │
│  Frontend    │     │   Backend    │     │                 │
└─────────────┘     └──────────────┘     │  YouTube        │
                                          │  Transcript     │
                                          │  Summarization  │
                                          │  Notes          │
                                          │  Chapters       │
                                          │  Translation    │
                                          │  Export         │
                                          │  History        │
                                          └────────┬────────┘
                                                   │
                                          ┌────────▼────────┐
                                          │   Ollama /      │
                                          │   OpenAI /      │
                                          │   Gemini        │
                                          └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- [Ollama](https://ollama.com/) (for local LLM inference)
- ffmpeg (for audio processing)

### 1. Clone and Install

```bash
git clone https://github.com/kittanu-t/youtube_sum.git
cd youtube_sum
uv venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev]"
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your settings
```

Minimal `.env` for Ollama:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest
LLM_PROVIDER=ollama
```

### 3. Run

**Start the API:**
```bash
python main.py
# API docs: http://localhost:8000/docs
```

**Start the Web UI:**
```bash
streamlit run streamlit_app.py
# Open: http://localhost:8501
```

### Docker

```bash
docker compose up
# API: http://localhost:8000
# Web UI: http://localhost:8501
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/video-info?url=` | Get video metadata |
| `POST` | `/api/summarize` | Summarize a video |
| `POST` | `/api/notes` | Generate study notes |
| `POST` | `/api/translate` | Translate text |
| `POST` | `/api/export` | Export in various formats |
| `GET` | `/api/history` | List history |
| `DELETE` | `/api/history/{id}` | Delete entry |
| `DELETE` | `/api/history` | Clear all history |

### Example: Summarize a Video

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=...", "level": "detailed", "language": "en"}'
```

### Example: Generate Study Notes

```bash
curl -X POST http://localhost:8000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=...", "language": "th"}'
```

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English |
| `th` | Thai (ภาษาไทย) |

## Recommended Local Models

| Model | Size | Notes |
|-------|------|-------|
| `gemma3:latest` | ~5B | Great balance of quality and speed |
| `qwen3:latest` | ~4B | Strong multilingual support |
| `llama3.2:latest` | ~3B | Fast, good for summarization |

## Development

```bash
# Run tests
pytest -v

# Run with coverage
pytest --cov=app --cov=services --cov=api

# Lint
ruff check .
ruff format .
```

## Project Structure

```
youtube_sum/
├── app/                    # Core app (config, database)
│   ├── __init__.py
│   ├── config.py           # pydantic-settings
│   └── database.py         # SQLite schema
├── api/                    # FastAPI routes
│   ├── __init__.py
│   └── routes.py           # All API endpoints
├── services/               # Business logic
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
├── tests/                  # Test suite (95 tests)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## Resume Bullet Points

- Built a YouTube Summarization Agent that converts YouTube videos into structured summaries and study notes.
- Integrated YouTube transcript extraction, multilingual summarization, and local LLM inference using Ollama.
- Designed modular pipelines for transcript processing, chapter generation, and note export.
- Implemented a FastAPI backend with Streamlit frontend, supporting EN/Thai translation and multiple export formats.
- Achieved 95 passing tests with comprehensive mocking of external API dependencies.

## License

MIT
