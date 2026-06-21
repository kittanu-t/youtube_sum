"""Transcript service — fetch and clean YouTube video transcripts."""

import re

from loguru import logger
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)
from youtube_transcript_api._errors import CouldNotRetrieveTranscript
from youtube_transcript_api.formatters import TextFormatter

from services.youtube_service import YouTubeService


class TranscriptError(Exception):
    """Raised when a transcript cannot be retrieved."""

    pass


class TranscriptService:
    """Fetches and cleans YouTube video transcripts.

    Primary method: youtube-transcript-api (free, no download).
    Fallback: yt-dlp subtitle extraction.
    """

    def __init__(self):
        self._formatter = TextFormatter()

    def get_transcript(
        self,
        url: str,
        languages: list[str] | None = None,
    ) -> str:
        """Fetch the transcript for a YouTube video.

        Args:
            url: A valid YouTube URL.
            languages: Preferred language codes (e.g., ["en", "th"]).
                       Defaults to ["en"].

        Returns:
            Cleaned transcript text.

        Raises:
            TranscriptError: If no transcript is available.
        """
        if not YouTubeService.validate_url(url):
            raise TranscriptError(f"Invalid YouTube URL: {url}")

        video_id = YouTubeService.extract_video_id(url)
        if languages is None:
            languages = ["en"]

        logger.info("Fetching transcript for {} (languages={})", video_id, languages)

        # Primary: youtube-transcript-api
        try:
            return self._fetch_via_api(video_id, languages)
        except (NoTranscriptFound, TranscriptsDisabled, CouldNotRetrieveTranscript) as exc:
            logger.warning("Transcript API failed: {}. Trying fallback...", exc)
        except VideoUnavailable:
            raise TranscriptError(f"Video {video_id} is unavailable or private")
        except Exception as exc:
            logger.warning("Transcript API error: {}. Trying fallback...", exc)

        # Fallback: yt-dlp subtitle extraction
        try:
            return self._fetch_via_ytdlp(url, languages)
        except Exception as exc:
            logger.error("All transcript methods failed for {}", video_id)
            raise TranscriptError(f"Could not retrieve transcript for {video_id}: {exc}") from exc

    def _fetch_via_api(self, video_id: str, languages: list[str]) -> str:
        """Fetch transcript using youtube-transcript-api."""
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Try to find a manually created transcript first
        try:
            transcript = transcript_list.find_manually_created_transcript(languages)
            logger.info("Found manually created transcript in {}", transcript.language_code)
        except NoTranscriptFound:
            # Fall back to auto-generated
            transcript = transcript_list.find_generated_transcript(languages)
            logger.info("Found auto-generated transcript in {}", transcript.language_code)

        entries = transcript.fetch()
        raw_text = self._formatter.format_transcript(entries)
        return self._clean_transcript(raw_text)

    def _fetch_via_ytdlp(self, url: str, languages: list[str]) -> str:
        """Fetch transcript using yt-dlp as fallback."""
        import os
        import tempfile

        lang = languages[0] if languages else "en"
        tmpdir = tempfile.mkdtemp()

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": True,
            "subtitleslangs": [lang],
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmpdir, "%(id)s"),
        }

        import yt_dlp

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded subtitle file
        for fname in os.listdir(tmpdir):
            if fname.endswith(f".{lang}.vtt"):
                filepath = os.path.join(tmpdir, fname)
                with open(filepath, encoding="utf-8") as f:
                    content = f.read()
                os.remove(filepath)
                os.rmdir(tmpdir)
                return self._clean_vtt(content)

        os.rmdir(tmpdir)
        raise TranscriptError(f"No subtitles downloaded via yt-dlp for language '{lang}'")

    @staticmethod
    def _clean_transcript(text: str) -> str:
        """Clean a plain-text transcript.

        - Removes timestamps and metadata lines.
        - Collapses whitespace.
        - Strips leading/trailing whitespace.
        """
        lines = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            # Skip timestamp lines like "00:00:01.000 --> 00:00:04.000"
            if re.match(r"^\d{2}:\d{2}", stripped) and "-->" in stripped:
                continue
            # Skip WEBVTT header
            if stripped.startswith("WEBVTT"):
                continue
            # Skip sequence numbers
            if stripped.isdigit():
                continue
            lines.append(stripped)

        return " ".join(lines)

    @staticmethod
    def _clean_vtt(content: str) -> str:
        """Extract plain text from VTT subtitle format."""
        import re

        lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("WEBVTT") or stripped.startswith("NOTE"):
                continue
            if "-->" in stripped:
                continue
            if stripped.isdigit():
                continue
            # Remove VTT tags like <c>...</c>
            cleaned = re.sub(r"<[^>]+>", "", stripped)
            if cleaned:
                lines.append(cleaned)

        return " ".join(lines)
