"""Chapter/timeline service — extract or infer video chapters with timestamps."""

import json
import re

import httpx
import yt_dlp
from loguru import logger

from app.config import settings


class Chapter:
    """Represents a video chapter/section."""

    def __init__(self, title: str, timestamp: str, seconds: int):
        self.title = title
        self.timestamp = timestamp
        self.seconds = seconds

    def to_dict(self) -> dict:
        return {"title": self.title, "timestamp": self.timestamp, "seconds": self.seconds}

    def __repr__(self) -> str:
        return f"Chapter({self.timestamp} {self.title})"


_SYSTEM_PROMPT = """You are an expert at analyzing video transcripts and identifying logical sections. Given a transcript, identify the main chapters or sections. For each chapter, provide a short title and indicate where in the video it occurs (as a percentage or approximate timestamp)."""


class ChapterService:
    """Extracts chapters from video metadata or infers them from transcript analysis."""

    def __init__(self):
        self._client = httpx.Client(timeout=120)

    def get_chapters(self, url: str, transcript: str = "") -> list[dict]:
        """Get chapters for a YouTube video.

        1. Try to extract from video metadata via yt-dlp.
        2. Fall back to inferring from the transcript via LLM.

        Args:
            url: A valid YouTube URL.
            transcript: Optional transcript text for LLM inference.

        Returns:
            List of chapter dicts with 'title', 'timestamp', and 'seconds'.
        """
        # Step 1: Try yt-dlp for native chapters
        chapters = self._extract_native_chapters(url)
        if chapters:
            logger.info("Found {} native chapters via yt-dlp", len(chapters))
            return [c.to_dict() for c in chapters]

        # Step 2: Try description timestamps
        chapters = self._extract_description_chapters(url)
        if chapters:
            logger.info("Found {} chapters from description", len(chapters))
            return [c.to_dict() for c in chapters]

        # Step 3: Infer from transcript
        if transcript.strip():
            logger.info("No native chapters found, inferring from transcript")
            return self._infer_chapters(transcript)

        logger.info("No chapters available")
        return []

    def _extract_native_chapters(self, url: str) -> list[Chapter] | None:
        """Extract chapters embedded in video metadata."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                raw_chapters = info.get("chapters", [])
                if not raw_chapters:
                    return None

                chapters = []
                for ch in raw_chapters:
                    seconds = ch.get("start_time", 0)
                    timestamp = self._format_timestamp(seconds)
                    title = ch.get("title", "Untitled")
                    chapters.append(Chapter(title=title, timestamp=timestamp, seconds=seconds))
                return chapters
        except Exception as exc:
            logger.warning("Chapter extraction failed: {}", exc)
            return None

    def _extract_description_chapters(self, url: str) -> list[Chapter] | None:
        """Extract chapters from video description timestamps like 0:00 Intro."""
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                description = info.get("description", "")

            # Match patterns like "0:00 Introduction" or "00:00:00 - Title"
            pattern = r"(\d{1,2}:\d{2}(?::\d{2})?)\s*[-–:]?\s*(.+)"
            matches = re.findall(pattern, description)
            if not matches:
                return None

            chapters = []
            for ts, title in matches:
                seconds = self._parse_timestamp(ts)
                title = title.strip()
                if title and len(title) < 100:
                    chapters.append(Chapter(title=title, timestamp=ts, seconds=seconds))

            return chapters if chapters else None
        except Exception as exc:
            logger.warning("Description chapter extraction failed: {}", exc)
            return None

    def _infer_chapters(self, transcript: str) -> list[dict]:
        """Use an LLM to infer chapters from the transcript."""
        provider = settings.llm_provider.lower()

        try:
            if provider == "ollama":
                result = self._infer_ollama(transcript)
            elif provider == "openai":
                result = self._infer_openai(transcript)
            elif provider == "gemini":
                result = self._infer_gemini(transcript)
            else:
                return []
        except Exception as exc:
            logger.warning("LLM chapter inference failed: {}", exc)
            return []

        return result

    def _infer_ollama(self, transcript: str) -> list[dict]:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        user_prompt = (
            "Analyze this video transcript and identify 5-10 logical chapters/sections. "
            "Respond with a JSON array of objects, each with 'title' and 'timestamp' fields. "
            "For timestamps, estimate based on transcript position (e.g., '00:00', '05:30', '12:15').\n\n"
            f"Transcript:\n\n{transcript[:12000]}"
        )
        payload = {
            "model": settings.ollama_model,
            "system": _SYSTEM_PROMPT,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.2},
        }
        resp = self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json().get("response", "[]")
        return self._parse_chapter_json(data)

    def _infer_openai(self, transcript: str) -> list[dict]:
        if not settings.openai_api_key:
            return []
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        user_prompt = (
            "Analyze this video transcript and identify 5-10 logical chapters/sections. "
            "Respond with a JSON array of objects, each with 'title' and 'timestamp' fields.\n\n"
            f"Transcript:\n\n{transcript[:12000]}"
        )
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        resp = self._client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return self._parse_chapter_json(content)

    def _infer_gemini(self, transcript: str) -> list[dict]:
        if not settings.gemini_api_key:
            return []
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
        )
        user_prompt = (
            "Analyze this video transcript and identify 5-10 logical chapters/sections. "
            "Respond with a JSON array of objects, each with 'title' and 'timestamp' fields.\n\n"
            f"Transcript:\n\n{transcript[:12000]}"
        )
        payload = {
            "contents": [{"parts": [{"text": f"{_SYSTEM_PROMPT}\n\n{user_prompt}"}]}],
            "generationConfig": {"temperature": 0.2},
        }
        resp = self._client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return self._parse_chapter_json(text)

    @staticmethod
    def _parse_chapter_json(raw: str) -> list[dict]:
        """Parse chapter JSON from LLM response."""
        try:
            # Try to extract JSON array from the response
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                data = json.loads(match.group())
            else:
                data = json.loads(raw)

            chapters = []
            for item in data:
                if isinstance(item, dict):
                    title = item.get("title", item.get("name", "Untitled"))
                    ts = item.get("timestamp", item.get("time", "00:00"))
                    seconds = ChapterService._parse_timestamp(str(ts))
                    chapters.append({"title": title, "timestamp": str(ts), "seconds": seconds})
            return chapters
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("Failed to parse chapter JSON: {}", exc)
            return []

    @staticmethod
    def _parse_timestamp(ts: str) -> int:
        """Convert HH:MM:SS or MM:SS to total seconds."""
        parts = ts.strip().split(":")
        try:
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            return 0
        except ValueError:
            return 0

    @staticmethod
    def _format_timestamp(seconds: int) -> str:
        h, remainder = divmod(int(seconds), 3600)
        m, s = divmod(remainder, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
