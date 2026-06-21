"""History service — SQLite CRUD for video summary history."""

import json

from loguru import logger

from app.database import get_db


class HistoryService:
    """Manages video summary history in SQLite."""

    @staticmethod
    def save(
        video_id: str,
        video_title: str = "",
        channel: str = "",
        duration: str = "",
        language: str = "en",
        summary: str = "",
        study_notes: str = "",
        chapters: list | None = None,
        key_points: list | None = None,
    ) -> int:
        """Save a summary to history.

        Args:
            video_id: YouTube video ID.
            video_title: Video title.
            channel: Channel name.
            duration: Video duration string.
            language: Summary language code.
            summary: Summary text.
            study_notes: Study notes text.
            chapters: List of chapter dicts.
            key_points: List of key point strings.

        Returns:
            The row ID of the inserted record.
        """
        conn = get_db()
        try:
            cursor = conn.execute(
                """INSERT INTO history
                   (video_id, video_title, channel, duration, language,
                    summary, study_notes, chapters, key_points)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    video_id,
                    video_title,
                    channel,
                    duration,
                    language,
                    summary,
                    study_notes,
                    json.dumps(chapters or [], ensure_ascii=False),
                    json.dumps(key_points or [], ensure_ascii=False),
                ),
            )
            conn.commit()
            row_id = cursor.lastrowid
            logger.info("Saved history entry {} for video {}", row_id, video_id)
            return row_id
        finally:
            conn.close()

    @staticmethod
    def get_all(limit: int = 50, offset: int = 0) -> list[dict]:
        """Retrieve history entries, most recent first.

        Args:
            limit: Maximum number of entries to return.
            offset: Number of entries to skip.

        Returns:
            List of history entry dicts.
        """
        conn = get_db()
        try:
            rows = conn.execute(
                "SELECT * FROM history ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
            return [HistoryService._row_to_dict(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_by_video_id(video_id: str) -> dict | None:
        """Get the most recent history entry for a video.

        Args:
            video_id: YouTube video ID.

        Returns:
            History entry dict, or None if not found.
        """
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT * FROM history WHERE video_id = ? ORDER BY created_at DESC LIMIT 1",
                (video_id,),
            ).fetchone()
            return HistoryService._row_to_dict(row) if row else None
        finally:
            conn.close()

    @staticmethod
    def delete(entry_id: int) -> bool:
        """Delete a history entry by ID.

        Args:
            entry_id: The row ID to delete.

        Returns:
            True if a row was deleted.
        """
        conn = get_db()
        try:
            cursor = conn.execute("DELETE FROM history WHERE id = ?", (entry_id,))
            conn.commit()
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Deleted history entry {}", entry_id)
            return deleted
        finally:
            conn.close()

    @staticmethod
    def clear_all() -> int:
        """Delete all history entries.

        Returns:
            Number of rows deleted.
        """
        conn = get_db()
        try:
            cursor = conn.execute("DELETE FROM history")
            conn.commit()
            count = cursor.rowcount
            logger.info("Cleared {} history entries", count)
            return count
        finally:
            conn.close()

    @staticmethod
    def count() -> int:
        """Get total number of history entries."""
        conn = get_db()
        try:
            row = conn.execute("SELECT COUNT(*) as cnt FROM history").fetchone()
            return row["cnt"] if row else 0
        finally:
            conn.close()

    @staticmethod
    def _row_to_dict(row) -> dict:
        """Convert a sqlite3.Row to a dict with parsed JSON fields."""
        d = dict(row)
        for field in ("chapters", "key_points"):
            if field in d and isinstance(d[field], str):
                try:
                    d[field] = json.loads(d[field])
                except json.JSONDecodeError:
                    d[field] = []
        return d
