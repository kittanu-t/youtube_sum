# Task Tracker — YouTube Summarization Agent

## Milestone 1: Project Skeleton
- [ ] Create directories: `app/`, `api/`, `services/`, `tests/`
- [ ] `.gitignore`
- [ ] `.env.example`
- [ ] `pyproject.toml`
- [ ] `Dockerfile`
- [ ] `docker-compose.yml`
- [ ] `app/__init__.py`, `app/config.py`, `app/database.py`
- [ ] `services/__init__.py`

## Milestone 2: Core Services
- [ ] `services/youtube_service.py`
- [ ] `services/transcript_service.py`
- [ ] `services/summarization_service.py`

## Milestone 3: Enrichment Services
- [ ] `services/notes_service.py`
- [ ] `services/chapter_service.py`
- [ ] `services/translation_service.py`
- [ ] `services/export_service.py`
- [ ] `services/history_service.py`

## Milestone 4: API Layer
- [ ] `api/__init__.py`, `api/routes.py`
- [ ] POST `/summarize`
- [ ] POST `/notes`
- [ ] POST `/translate`
- [ ] GET `/history`
- [ ] GET `/video-info`
- [ ] GET `/health`
- [ ] `main.py`

## Milestone 5: Streamlit Frontend
- [ ] `streamlit_app.py` — full UI

## Milestone 6: Tests
- [ ] `tests/conftest.py`
- [ ] `tests/test_youtube_service.py`
- [ ] `tests/test_transcript_service.py`
- [ ] `tests/test_summarization_service.py`
- [ ] `tests/test_notes_service.py`
- [ ] `tests/test_chapter_service.py`
- [ ] `tests/test_translation_service.py`
- [ ] `tests/test_export_service.py`
- [ ] `tests/test_history_service.py`
- [ ] `tests/test_api.py`

## Milestone 7: Documentation & Polish
- [ ] `README.md`
- [ ] `ARCHITECTURE.md`
- [ ] `CLAUDE.md` update
- [ ] Lint + format pass
- [ ] Docker end-to-end test
