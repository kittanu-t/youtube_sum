# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`youtube_sum` — YouTube Summarization Agent. Accepts a YouTube URL, fetches the transcript, generates summaries and study notes using local LLMs (Ollama) or cloud APIs (OpenAI, Gemini). Provides both a Streamlit web UI and a FastAPI REST API.

## Tech Stack

- **Language**: Python 3.12
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **LLM**: Ollama (default), OpenAI, Gemini
- **Transcript**: youtube-transcript-api + yt-dlp fallback
- **Database**: SQLite
- **Logging**: loguru
- **Package Manager**: uv
- **Container**: Docker + docker-compose

## Build / Run / Test / Lint

```bash
# --- Setup ---
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
cp .env.example .env  # edit with your settings

# --- Run API ---
python main.py
# API docs: http://localhost:8000/docs

# --- Run Web UI ---
streamlit run streamlit_app.py
# Open: http://localhost:8501

# --- Docker ---
docker compose up

# --- Tests ---
pytest -v                          # all tests (95 tests)
pytest --cov=app --cov=services --cov=api  # with coverage

# --- Lint / Format ---
ruff check .                       # lint
ruff check --fix .                 # auto-fix
ruff format .                      # format
```

## Architecture

### Directory Layout
```
youtube_sum/
├── app/                    # Core app (config, database)
│   ├── config.py           # pydantic-settings
│   └── database.py         # SQLite schema + connection
├── api/                    # FastAPI routes
│   └── routes.py           # All endpoints
├── services/               # Business logic modules
│   ├── youtube_service.py  # URL validation, video info (yt-dlp)
│   ├── transcript_service.py  # Transcript retrieval (youtube-transcript-api + yt-dlp)
│   ├── summarization_service.py  # LLM summarization (Ollama/OpenAI/Gemini)
│   ├── notes_service.py    # Study note generation
│   ├── chapter_service.py  # Chapter extraction/inference
│   ├── translation_service.py  # EN↔TH translation
│   ├── export_service.py   # Markdown/TXT/CSV/JSON export
│   └── history_service.py  # SQLite history CRUD
├── streamlit_app.py        # Streamlit frontend
├── main.py                 # FastAPI entry point
├── tests/                  # Test suite
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

### Pipeline
```
YouTube URL → validate → fetch video info → fetch transcript → chunk → summarize → generate notes → export
```

### Key Patterns
- Each service is a standalone class with type hints, logging, error handling, docstrings
- Services raise domain-specific exceptions (TranscriptError, SummarizationError, etc.)
- LLM calls go through a provider abstraction (Ollama/OpenAI/Gemini)
- History is stored in SQLite and used as a cache
- Config via pydantic-settings from env vars + .env

### API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/video-info?url=` | Video metadata |
| POST | `/api/summarize` | Summarize video |
| POST | `/api/notes` | Generate study notes |
| POST | `/api/translate` | Translate text |
| POST | `/api/export` | Export content |
| GET | `/api/history` | List history |
| DELETE | `/api/history/{id}` | Delete entry |
