"""Tests for NotesService."""

from unittest.mock import MagicMock, patch

import pytest

from services.notes_service import NotesError, NotesService


class TestNotesService:
    def test_empty_transcript_raises(self):
        service = NotesService()
        with pytest.raises(NotesError, match="Cannot generate notes from empty transcript"):
            service.generate_notes("")

    def test_generate_notes_calls_llm(self, mock_ollama_client, sample_transcript):
        service = NotesService()
        result = service.generate_notes(sample_transcript)
        assert result is not None
        mock_ollama_client.post.assert_called()

    def test_generate_notes_thai(self, mock_ollama_client, sample_transcript):
        service = NotesService()
        result = service.generate_notes(sample_transcript, language="th")
        assert result is not None


class TestNotesChunking:
    def test_short_text_no_chunking(self):
        text = "Short transcript."
        chunks = NotesService._chunk_text(text)
        assert len(chunks) == 1

    def test_long_text_chunked(self):
        text = "A" * 10000
        chunks = NotesService._chunk_text(text)
        assert len(chunks) > 1
