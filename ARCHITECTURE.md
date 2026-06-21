# Architecture — YouTube Summarization Agent

## Overview

youtube_sum is a Python application with a modular pipeline architecture. The core flow is:

**YouTube URL → Transcript → Summary → Study Notes → Export**

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client Layer                               │
│  ┌─────────────────┐  ┌──────────────────┐                      │
│  │  Streamlit UI    │  │  REST API Client │                      │
│  │  (Port 8501)     │  │  (curl, etc.)    │                      │
│  └────────┬─────────┘  └────────┬─────────┘                      │
└───────────┼──────────────────────┼───────────────────────────────┘
            │                      │
            ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                      API Layer (FastAPI)                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  api/routes.py                                            │   │
│  │  POST /summarize  POST /notes  POST /translate           │   │
│  │  POST /export     GET /history  GET /video-info          │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬──────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────┐
│                      Service Layer                                │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐       │
│  │   YouTube     │  │  Transcript  │  │  Summarization   │       │
│  │   Service     │──▶│  Service     │──▶│  Service         │       │
│  └──────────────┘  └──────────────┘  └────────┬─────────┘       │
│                                                │                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────▼─────────┐       │
│  │   Chapter     │  │  Translation │  │  Notes           │       │
│  │   Service     │  │  Service     │  │  Service         │       │
│  └──────────────┘  └──────────────┘  └────────┬─────────┘       │
│                                                │                  │
│  ┌──────────────┐  ┌──────────────┐           │                  │
│  │   Export      │  │  History     │           │                  │
│  │   Service     │  │  Service     │           │                  │
│  └──────────────┘  └──────────────┘           │                  │
└───────────────────────────────────────────────┼──────────────────┘
                                                │
                            ┌───────────────────┼───────────┐
                            ▼                   ▼           ▼
                     ┌──────────┐      ┌──────────┐  ┌────────┐
                     │  Ollama  │      │  OpenAI  │  │ Gemini │
                     │ (local)  │      │ (cloud)  │  │(cloud) │
                     └──────────┘      └──────────┘  └────────┘
```

## Module Dependency Graph

```
main.py (FastAPI entry)
  └── api/routes.py
        ├── services/youtube_service.py     ← yt-dlp
        ├── services/transcript_service.py  ← youtube-transcript-api, yt-dlp
        ├── services/summarization_service.py ← httpx → Ollama/OpenAI/Gemini
        ├── services/notes_service.py       ← httpx → Ollama/OpenAI/Gemini
        ├── services/chapter_service.py     ← yt-dlp, httpx → LLM
        ├── services/translation_service.py ← httpx → Ollama/OpenAI/Gemini
        ├── services/export_service.py      ← pure Python
        └── services/history_service.py     ← SQLite

streamlit_app.py (Streamlit entry)
  └── requests → FastAPI endpoints

app/config.py        ← pydantic-settings (env vars + .env)
app/database.py      ← sqlite3
```

## Pipeline Stages

### 1. URL Validation
- Regex-based matching for youtube.com/watch, youtu.be, shorts, embed URLs
- Extracts 11-character video ID

### 2. Video Info Retrieval
- Uses yt-dlp to fetch title, channel, duration, thumbnail
- No download required (extract_flat mode)

### 3. Transcript Retrieval
- **Primary**: youtube-transcript-api (free, no download, supports EN/TH/auto-generated)
- **Fallback**: yt-dlp subtitle download → VTT parsing
- Handles: missing captions, disabled subtitles, private videos, rate limiting

### 4. Summarization
- **Chunking**: Splits long transcripts at sentence boundaries with configurable overlap
- **Single-pass**: Direct LLM call for short transcripts
- **Multi-pass**: Per-chunk summary → synthesis for long transcripts
- **Levels**: Short (1 paragraph + bullets), Detailed (sections + quotes), Bullet (nested bullets)
- **Providers**: Ollama (default), OpenAI, Gemini

### 5. Study Note Generation
- Structured output: Overview, Key Concepts, Important Points, Timeline, Actionable Takeaways, Review Questions, Vocabulary, Further Reading
- Supports English and Thai output

### 6. Chapter Detection
- **Native**: yt-dlp chapter metadata
- **Description**: Regex timestamp parsing from video description
- **Inferred**: LLM-based chapter inference from transcript

### 7. Translation
- EN ↔ TH via LLM (Ollama/OpenAI/Gemini)
- Preserves Markdown formatting

### 8. Export
- **Markdown**: Full structured document
- **TXT**: Plain text with formatting stripped
- **JSON**: Machine-readable structured data
- **CSV**: Flashcard Q&A pairs extracted from study notes

### 9. History
- SQLite storage of all generated summaries
- CRUD operations with pagination
- Used as cache to avoid re-processing

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Ollama as default LLM | Free, local, no API key needed |
| youtube-transcript-api primary | Free, no download, fast |
| yt-dlp as fallback | Handles edge cases, subtitle download |
| pydantic-settings for config | Type-safe, env + .env support |
| Typer not used (FastAPI only) | Streamlit provides the UI; CLI via API |
| SQLite for history | Zero config, no external DB needed |
| Streamlit for frontend | Beginner-friendly, single-page, no JS |
| httpx for HTTP calls | Async-compatible, modern replacement for requests |
| Each service independently testable | Mock LLM calls, isolated unit tests |

## Error Handling

- Each service raises domain-specific exceptions (TranscriptError, SummarizationError, etc.)
- API layer catches and returns appropriate HTTP status codes
- Streamlit UI displays user-friendly error messages
- Graceful degradation (e.g., chapters skipped if extraction fails)

## Configuration

All configuration via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `ollama` | LLM backend: ollama, openai, gemini |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `gemma3:latest` | Model to use |
| `OPENAI_API_KEY` | (empty) | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model |
| `GEMINI_API_KEY` | (empty) | Gemini API key |
| `DATABASE_PATH` | `./youtube_sum.db` | SQLite database path |
| `CHUNK_SIZE` | `8000` | Transcript chunk size |
| `CHUNK_OVERLAP` | `500` | Overlap between chunks |

## Future Enhancements

- **Chat with Video**: Q&A interface over video content
- **Keyword Extraction**: Auto-generate topics, tags, keywords
- **Podcast Mode**: Audio-friendly summary generation
- **Batch Processing**: Process multiple URLs at once
- **YouTube Captions Fallback**: Use native captions before Whisper
- **Caching**: Skip re-download for same video ID
- **User Accounts**: Multi-user support with authentication
