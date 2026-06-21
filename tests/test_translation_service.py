"""Tests for TranslationService."""

import pytest

from services.translation_service import TranslationError, TranslationService


class TestTranslationService:
    def test_empty_text_returns_empty(self):
        service = TranslationService()
        result = service.translate("", "th")
        assert result == ""

    def test_translate_to_thai(self, mock_ollama_client):
        service = TranslationService()
        result = service.translate("Hello world", "th")
        assert result is not None
        mock_ollama_client.post.assert_called()

    def test_translate_to_english(self, mock_ollama_client):
        service = TranslationService()
        result = service.translate("สวัสดี", "en")
        assert result is not None

    def test_unsupported_language_raises(self):
        service = TranslationService()
        with pytest.raises(TranslationError, match="Unsupported target language"):
            service.translate("Hello", "fr")
