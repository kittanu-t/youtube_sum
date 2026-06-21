"""Tests for TranscriptService."""

from unittest.mock import patch

import pytest

from services.transcript_service import TranscriptError, TranscriptService


class TestTranscriptServiceCleaning:
    def test_clean_transcript_removes_timestamps(self):
        raw = "00:00:01.000 --> 00:00:04.000\nHello world\n\n00:00:05.000 --> 00:00:08.000\nHow are you"
        result = TranscriptService._clean_transcript(raw)
        assert "Hello world" in result
        assert "How are you" in result
        assert "-->" not in result

    def test_clean_transcript_collapses_whitespace(self):
        raw = "Line one.\n\n\n\nLine two."
        result = TranscriptService._clean_transcript(raw)
        assert result == "Line one. Line two."

    def test_clean_vtt_removes_header(self):
        content = "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\nHello world\n\n"
        result = TranscriptService._clean_vtt(content)
        assert "WEBVTT" not in result
        assert "Hello world" in result

    def test_clean_vtt_removes_tags(self):
        content = "WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<c>Hello</c> <c>world</c>\n\n"
        result = TranscriptService._clean_vtt(content)
        assert "<c>" not in result
        assert "Hello world" in result

    def test_clean_vtt_skips_sequence_numbers(self):
        content = "WEBVTT\n\n1\n00:00:01.000 --> 00:00:04.000\nHello\n\n"
        result = TranscriptService._clean_vtt(content)
        assert result.strip() == "Hello"


class TestTranscriptServiceValidation:
    def test_invalid_url_raises(self):
        service = TranscriptService()
        with pytest.raises(TranscriptError, match="Invalid YouTube URL"):
            service.get_transcript("https://example.com")

    def test_valid_url_calls_api(self, sample_video_url):
        service = TranscriptService()
        with patch.object(service, "_fetch_via_api", return_value="transcript") as mock:
            result = service.get_transcript(sample_video_url)
            assert result == "transcript"
            mock.assert_called_once()
