"""YouTube service — URL validation, video ID extraction, video info retrieval."""

import re
from dataclasses import dataclass
from typing import Optional

import requests
import yt_dlp
from loguru import logger


@dataclass
class VideoInfo:
    """Structured video metadata."""

    video_id: str
    title: str
    channel: str
    duration: str
    thumbnail: str
    description: str


# Matches youtube.com/watch?v=..., youtu.be/..., youtube.com/shorts/...
_YOUTUBE_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{11})",
    r"(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})",
]


class YouTubeService:
    """Handles YouTube URL validation and video metadata retrieval."""

    @staticmethod
    def validate_url(url: str) -> bool:
        """Check if the URL is a valid YouTube video URL.

        Args:
            url: The URL to validate.

        Returns:
            True if the URL matches a known YouTube pattern.
        """
        return any(re.match(p, url.strip()) for p in _YOUTUBE_PATTERNS)

    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract the 11-character video ID from a YouTube URL.

        Args:
            url: A valid YouTube URL.

        Returns:
            The video ID string.

        Raises:
            ValueError: If no video ID can be extracted.
        """
        for pattern in _YOUTUBE_PATTERNS:
            match = re.search(pattern, url.strip())
            if match:
                return match.group(1)
        raise ValueError(f"Could not extract video ID from: {url}")

    @classmethod
    def get_video_info(cls, url: str) -> VideoInfo:
        """Fetch video metadata using yt-dlp.

        Args:
            url: A valid YouTube URL.

        Returns:
            VideoInfo with title, channel, duration, etc.

        Raises:
            ValueError: If the URL is invalid.
            RuntimeError: If video info cannot be retrieved.
        """
        if not cls.validate_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")

        video_id = cls.extract_video_id(url)
        logger.info("Fetching video info for {}", video_id)

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "skip_download": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:
            logger.error("yt-dlp extraction failed: {}", exc)
            raise RuntimeError(f"Failed to fetch video info: {exc}") from exc

        if info is None:
            raise RuntimeError("No video info returned")

        duration_sec = info.get("duration") or 0
        duration_str = cls._format_duration(duration_sec)

        return VideoInfo(
            video_id=video_id,
            title=info.get("title", "Unknown Title"),
            channel=info.get("channel", info.get("uploader", "Unknown Channel")),
            duration=duration_str,
            thumbnail=info.get("thumbnail", ""),
            description=info.get("description", "")[:500],
        )

    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Convert seconds to HH:MM:SS or MM:SS string."""
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
