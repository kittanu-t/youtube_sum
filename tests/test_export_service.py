"""Tests for ExportService."""

import json

import pytest

from services.export_service import ExportData, ExportService


@pytest.fixture
def sample_data():
    return ExportData(
        video_id="dQw4w9WgXcQ",
        video_title="Test Video",
        channel="Test Channel",
        duration="03:30",
        language="en",
        summary="## Overview\n\nThis is a test summary.\n\n- Point 1\n- Point 2",
        study_notes="## Overview\n\nTest notes.\n\n## Key Concepts\n\n**Concept A**: Definition A",
        chapters=[
            {"title": "Intro", "timestamp": "00:00", "seconds": 0},
            {"title": "Main", "timestamp": "05:30", "seconds": 330},
        ],
        key_points=["Point 1", "Point 2"],
    )


class TestExportMarkdown:
    def test_contains_title(self, sample_data):
        result = ExportService().export_markdown(sample_data)
        assert "# Test Video" in result

    def test_contains_channel(self, sample_data):
        result = ExportService().export_markdown(sample_data)
        assert "Test Channel" in result

    def test_contains_summary(self, sample_data):
        result = ExportService().export_markdown(sample_data)
        assert "test summary" in result

    def test_contains_chapters(self, sample_data):
        result = ExportService().export_markdown(sample_data)
        assert "Intro" in result
        assert "05:30" in result

    def test_contains_study_notes(self, sample_data):
        result = ExportService().export_markdown(sample_data)
        assert "## Study Notes" in result

    def test_empty_data(self):
        data = ExportData(video_id="abc")
        result = ExportService().export_markdown(data)
        assert "Video Summary" in result


class TestExportTxt:
    def test_plain_text_no_markdown(self, sample_data):
        result = ExportService().export_txt(sample_data)
        assert "**" not in result
        assert "Test Video" in result

    def test_contains_chapters(self, sample_data):
        result = ExportService().export_txt(sample_data)
        assert "CHAPTERS" in result
        assert "Intro" in result


class TestExportJson:
    def test_valid_json(self, sample_data):
        result = ExportService().export_json(sample_data)
        parsed = json.loads(result)
        assert parsed["video_id"] == "dQw4w9WgXcQ"
        assert parsed["title"] == "Test Video"
        assert len(parsed["chapters"]) == 2

    def test_has_generated_at(self, sample_data):
        result = ExportService().export_json(sample_data)
        parsed = json.loads(result)
        assert "generated_at" in parsed


class TestExportFlashcardsCsv:
    def test_csv_format(self, sample_data):
        result = ExportService().export_flashcards_csv(sample_data.study_notes)
        lines = result.strip().split("\n")
        assert lines[0] == "Question,Answer"

    def test_csv_with_no_qa(self):
        result = ExportService().export_flashcards_csv("Some random text")
        lines = result.strip().split("\n")
        # Should at least have header
        assert lines[0] == "Question,Answer"


class TestStripMarkdown:
    def test_removes_headers(self):
        text = "# Title\n## Subtitle"
        result = ExportService._strip_markdown(text)
        assert "#" not in result
        assert "Title" in result

    def test_removes_bold(self):
        text = "**bold text**"
        result = ExportService._strip_markdown(text)
        assert "**" not in result
        assert "bold text" in result

    def test_removes_links(self):
        text = "[link text](http://example.com)"
        result = ExportService._strip_markdown(text)
        assert "link text" in result
<longcat_arg_value>
