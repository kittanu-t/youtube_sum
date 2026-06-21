"""Tests for SummarizationService."""

from unittest.mock import MagicMock, patch

import pytest

from services.summarization_service import SummarizationError, SummarizationService


class TestChunkText:
    def test_short_text_no_chunking(self):
        text = "Short text."
        chunks = SummarizationService._chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_gets_chunked(self):
        # Create text longer than default chunk_size (8000)
        text = "A" * 10000
        chunks = SummarizationService._chunk_text(text)
        assert len(chunks) > 1

    def test_empty_text(self):
        chunks = SummarizationService._chunk_text("")
        assert len(chunks) == 1
        assert chunks[0] == ""


class TestSummarizationService:
    def test_empty_text_raises(self):
        service = SummarizationService()
        with pytest.raises(SummarizationError, match="Cannot summarize empty text"):
            service.summarize("")

    def test_whitespace_only_raises(self):
        service = SummarizationService()
        with pytest.raises(SummarizationError, match="Cannot summarize empty text"):
            service.summarize("   ")

    def test_summarize_calls_ollama(self, mock_ollama_client, sample_transcript):
        service = SummarizationService()
        result = service.summarize(sample_transcript, level="short")
        assert result == "This is a mocked summary."
        mock_ollama_client.post.assert_called()

    def test_summarize_short_level(self, mock_ollama_client, sample_transcript):
        service = SummarizationService()
        result = service.summarize(sample_transcript, level="short")
        assert result is not None

    def test_summarize_detailed_level(self, mock_ollama_client, sample_transcript):
        service = SummarizationService()
        result = service.summarize(sample_transcript, level="detailed")
        assert result is not None

    def test_summarize_bullet_level(self, mock_ollama_client, sample_transcript):
        service = SummarizationService()
        result = service.summarize(sample_transcript, level="bullet")
        assert result is not None

    def test_summarize_thai_language(self, mock_ollama_client, sample_transcript):
        service = SummarizationService()
        result = service.summarize(sample_transcript, language="th")
        assert result is not None
