"""Shared test fixtures."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set environment variables for testing."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("DATABASE_PATH", ":memory:")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY", "")


@pytest.fixture
def sample_video_url():
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def sample_video_id():
    return "dQw4w9WgXcQ"


@pytest.fixture
def sample_transcript():
    return (
        "This is a sample transcript from a YouTube video about testing. "
        "The speaker discusses the importance of unit testing, integration testing, "
        "and end-to-end testing. They explain that testing helps catch bugs early "
        "and improves code quality. The video covers pytest as the recommended "
        "testing framework for Python projects."
    )


@pytest.fixture
def sample_summary():
    return (
        "## Overview\n\n"
        "This video covers testing methodologies in Python.\n\n"
        "## Key Points\n\n"
        "- Testing is important\n"
        "- Use pytest for Python\n"
        "- Mock external dependencies"
    )


@pytest.fixture
def sample_video_info():
    return {
        "video_id": "dQw4w9WgXcQ",
        "title": "Test Video",
        "channel": "Test Channel",
        "duration": "03:30",
        "thumbnail": "https://example.com/thumb.jpg",
        "description": "A test video description",
    }


@pytest.fixture
def mock_ollama_response():
    """Mock a successful Ollama API response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": "This is a mocked summary."}
    mock_resp.raise_for_status = MagicMock()
    return mock_resp


@pytest.fixture
def mock_ollama_client(mock_ollama_response):
    """Mock httpx.Client for Ollama calls."""
    with patch("httpx.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.post.return_value = mock_ollama_response
        mock_client_cls.return_value = mock_client
        yield mock_client
