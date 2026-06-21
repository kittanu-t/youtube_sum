"""Tests for YouTubeService."""

import pytest

from services.youtube_service import YouTubeService


class TestValidateUrl:
    def test_valid_standard_url(self):
        assert YouTubeService.validate_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_valid_short_url(self):
        assert YouTubeService.validate_url("https://youtu.be/dQw4w9WgXcQ")

    def test_valid_shorts_url(self):
        assert YouTubeService.validate_url("https://www.youtube.com/shorts/dQw4w9WgXcQ")

    def test_valid_embed_url(self):
        assert YouTubeService.validate_url("https://www.youtube.com/embed/dQw4w9WgXcQ")

    def test_invalid_url(self):
        assert not YouTubeService.validate_url("https://example.com/video")

    def test_empty_url(self):
        assert not YouTubeService.validate_url("")

    def test_url_without_protocol(self):
        assert YouTubeService.validate_url("www.youtube.com/watch?v=dQw4w9WgXcQ")


class TestExtractVideoId:
    def test_standard_url(self, sample_video_url, sample_video_id):
        assert YouTubeService.extract_video_id(sample_video_url) == sample_video_id

    def test_short_url(self, sample_video_id):
        url = f"https://youtu.be/{sample_video_id}"
        assert YouTubeService.extract_video_id(url) == sample_video_id

    def test_shorts_url(self, sample_video_id):
        url = f"https://www.youtube.com/shorts/{sample_video_id}"
        assert YouTubeService.extract_video_id(url) == sample_video_id

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError, match="Could not extract video ID"):
            YouTubeService.extract_video_id("https://example.com")


class TestFormatDuration:
    def test_seconds_only(self):
        assert YouTubeService._format_duration(45) == "00:45"

    def test_minutes_and_seconds(self):
        assert YouTubeService._format_duration(210) == "03:30"

    def test_hours_minutes_seconds(self):
        assert YouTubeService._format_duration(3661) == "01:01:01"

    def test_zero(self):
        assert YouTubeService._format_duration(0) == "00:00"
