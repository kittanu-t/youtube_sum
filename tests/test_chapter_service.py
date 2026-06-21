"""Tests for ChapterService."""

import pytest

from services.chapter_service import Chapter, ChapterService


class TestChapter:
    def test_to_dict(self):
        ch = Chapter(title="Intro", timestamp="00:00", seconds=0)
        d = ch.to_dict()
        assert d["title"] == "Intro"
        assert d["timestamp"] == "00:00"
        assert d["seconds"] == 0

    def test_repr(self):
        ch = Chapter(title="Intro", timestamp="00:00", seconds=0)
        assert "Intro" in repr(ch)


class TestTimestampParsing:
    def test_parse_hhmmss(self):
        assert ChapterService._parse_timestamp("01:30:45") == 5445

    def test_parse_mmss(self):
        assert ChapterService._parse_timestamp("03:30") == 210

    def test_parse_zero(self):
        assert ChapterService._parse_timestamp("00:00") == 0

    def test_parse_invalid(self):
        assert ChapterService._parse_timestamp("abc") == 0


class TestTimestampFormatting:
    def test_format_seconds(self):
        assert ChapterService._format_timestamp(45) == "00:45"

    def test_format_minutes(self):
        assert ChapterService._format_timestamp(210) == "03:30"

    def test_format_hours(self):
        assert ChapterService._format_timestamp(3661) == "01:01:01"


class TestChapterJsonParsing:
    def test_parse_valid_json(self):
        raw = '[{"title": "Intro", "timestamp": "00:00"}, {"title": "Main", "timestamp": "05:30"}]'
        chapters = ChapterService._parse_chapter_json(raw)
        assert len(chapters) == 2
        assert chapters[0]["title"] == "Intro"

    def test_parse_empty_json(self):
        chapters = ChapterService._parse_chapter_json("[]")
        assert chapters == []

    def test_parse_invalid_json(self):
        chapters = ChapterService._parse_chapter_json("not json")
        assert chapters == []

    def test_parse_json_with_name_field(self):
        raw = '[{"name": "Intro", "time": "00:00"}]'
        chapters = ChapterService._parse_chapter_json(raw)
        assert len(chapters) == 1
        assert chapters[0]["title"] == "Intro"
