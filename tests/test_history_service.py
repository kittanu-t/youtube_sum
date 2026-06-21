"""Tests for HistoryService."""

import pytest

from app.config import settings
from app.database import get_db, init_db
from services.history_service import HistoryService


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    """Use a temp database for each test."""
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(settings, "database_path", db_path)
    init_db()


class TestHistoryService:
    def test_save_and_retrieve(self):
        HistoryService.save(
            video_id="abc123",
            video_title="Test Video",
            channel="Test Channel",
            duration="03:30",
            language="en",
            summary="Test summary",
            study_notes="Test notes",
            chapters=[{"title": "Intro", "timestamp": "00:00", "seconds": 0}],
            key_points=["Point 1"],
        )
        entries = HistoryService.get_all()
        assert len(entries) == 1
        assert entries[0]["video_id"] == "abc123"
        assert entries[0]["video_title"] == "Test Video"

    def test_get_by_video_id(self):
        HistoryService.save(video_id="abc123", video_title="Test")
        HistoryService.save(video_id="xyz789", video_title="Other")

        result = HistoryService.get_by_video_id("abc123")
        assert result is not None
        assert result["video_title"] == "Test"

    def test_get_by_video_id_not_found(self):
        result = HistoryService.get_by_video_id("nonexistent")
        assert result is None

    def test_delete(self):
        HistoryService.save(video_id="abc", video_title="Test")
        entries = HistoryService.get_all()
        assert len(entries) == 1

        deleted = HistoryService.delete(entries[0]["id"])
        assert deleted is True
        assert HistoryService.count() == 0

    def test_delete_nonexistent(self):
        deleted = HistoryService.delete(9999)
        assert deleted is False

    def test_clear_all(self):
        HistoryService.save(video_id="a", video_title="A")
        HistoryService.save(video_id="b", video_title="B")
        assert HistoryService.count() == 2

        count = HistoryService.clear_all()
        assert count == 2
        assert HistoryService.count() == 0

    def test_count_empty(self):
        assert HistoryService.count() == 0

    def test_chapters_parsed_as_list(self):
        HistoryService.save(
            video_id="abc",
            chapters=[{"title": "Intro", "timestamp": "00:00", "seconds": 0}],
        )
        entries = HistoryService.get_all()
        assert isinstance(entries[0]["chapters"], list)
        assert len(entries[0]["chapters"]) == 1

    def test_key_points_parsed_as_list(self):
        HistoryService.save(video_id="abc", key_points=["A", "B"])
        entries = HistoryService.get_all()
        assert isinstance(entries[0]["key_points"], list)
        assert entries[0]["key_points"] == ["A", "B"]

    def test_get_all_pagination(self):
        for i in range(5):
            HistoryService.save(video_id=f"vid_{i}", video_title=f"Video {i}")

        entries = HistoryService.get_all(limit=2, offset=0)
        assert len(entries) == 2

        entries = HistoryService.get_all(limit=2, offset=2)
        assert len(entries) == 2
