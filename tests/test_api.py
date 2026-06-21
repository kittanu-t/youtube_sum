"""Tests for API routes."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.routes import router


@pytest.fixture
def app():
    """Create a minimal FastAPI app with the router for testing."""
    app = FastAPI()
    app.include_router(router, prefix="/api")
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestVideoInfoEndpoint:
    def test_invalid_url(self, client):
        response = client.get("/api/video-info", params={"url": "https://example.com"})
        assert response.status_code == 400

    def test_valid_url_returns_info(self, client):
        mock_info = MagicMock()
        mock_info.video_id = "abc123"
        mock_info.title = "Test"
        mock_info.channel = "Channel"
        mock_info.duration = "03:00"
        mock_info.thumbnail = ""
        mock_info.description = ""

        with patch("api.routes.YouTubeService") as MockService:
            MockService.validate_url.return_value = True
            MockService.get_video_info.return_value = mock_info
            response = client.get(
                "/api/video-info", params={"url": "https://youtube.com/watch?v=abc123"}
            )
            assert response.status_code == 200


class TestSummarizeEndpoint:
    def test_invalid_url(self, client):
        response = client.post("/api/summarize", json={"url": "https://example.com"})
        assert response.status_code == 400

    def test_valid_request(self, client):
        mock_info = MagicMock()
        mock_info.video_id = "abc123"
        mock_info.title = "Test"
        mock_info.channel = "Channel"
        mock_info.duration = "03:00"

        with (
            patch("api.routes.YouTubeService") as MockYT,
            patch("api.routes.TranscriptService") as MockTS,
            patch("api.routes.SummarizationService") as MockSS,
            patch("api.routes.ChapterService") as MockCS,
            patch("api.routes.HistoryService") as MockHS,
        ):
            MockYT.validate_url.return_value = True
            MockYT.extract_video_id.return_value = "abc123"
            MockYT.get_video_info.return_value = mock_info
            MockTS.return_value.get_transcript.return_value = "transcript text"
            MockSS.return_value.summarize.return_value = "summary text"
            MockCS.return_value.get_chapters.return_value = []
            MockHS.get_by_video_id.return_value = None

            response = client.post(
                "/api/summarize",
                json={
                    "url": "https://youtube.com/watch?v=abc123",
                    "level": "short",
                    "language": "en",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert "summary" in data


class TestNotesEndpoint:
    def test_invalid_url(self, client):
        response = client.post("/api/notes", json={"url": "https://example.com"})
        assert response.status_code == 400


class TestTranslateEndpoint:
    def test_translate_request(self, client):
        with patch("api.routes.TranslationService") as MockTS:
            MockTS.return_value.translate.return_value = "translated text"
            response = client.post(
                "/api/translate",
                json={
                    "text": "Hello",
                    "target_language": "th",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["translated_text"] == "translated text"


class TestExportEndpoint:
    def test_export_markdown(self, client):
        response = client.post(
            "/api/export",
            json={
                "video_id": "abc",
                "summary": "Test summary",
                "format": "markdown",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert data["filename"].endswith(".md")

    def test_export_txt(self, client):
        response = client.post(
            "/api/export",
            json={
                "video_id": "abc",
                "format": "txt",
            },
        )
        assert response.status_code == 200
        assert response.json()["filename"].endswith(".txt")

    def test_export_json(self, client):
        response = client.post(
            "/api/export",
            json={
                "video_id": "abc",
                "format": "json",
            },
        )
        assert response.status_code == 200

    def test_export_csv(self, client):
        response = client.post(
            "/api/export",
            json={
                "video_id": "abc",
                "format": "csv",
            },
        )
        assert response.status_code == 200
        assert response.json()["filename"].endswith(".csv")

    def test_invalid_format(self, client):
        response = client.post(
            "/api/export",
            json={
                "video_id": "abc",
                "format": "pdf",
            },
        )
        assert response.status_code == 400


class TestHistoryEndpoints:
    def test_get_history(self, client):
        with patch("api.routes.HistoryService") as MockHS:
            MockHS.get_all.return_value = []
            MockHS.count.return_value = 0
            response = client.get("/api/history")
            assert response.status_code == 200

    def test_delete_history(self, client):
        with patch("api.routes.HistoryService") as MockHS:
            MockHS.delete.return_value = True
            response = client.delete("/api/history/1")
            assert response.status_code == 200

    def test_delete_not_found(self, client):
        with patch("api.routes.HistoryService") as MockHS:
            MockHS.delete.return_value = False
            response = client.delete("/api/history/999")
            assert response.status_code == 404

    def test_clear_history(self, client):
        with patch("api.routes.HistoryService") as MockHS:
            MockHS.clear_all.return_value = 5
            response = client.delete("/api/history")
            assert response.status_code == 200
