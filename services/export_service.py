"""Export service — generate Markdown, TXT, and CSV output from summaries and notes."""

import csv
import io
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ExportData:
    """Container for all data that can be exported."""

    video_id: str
    video_title: str = ""
    channel: str = ""
    duration: str = ""
    language: str = "en"
    summary: str = ""
    study_notes: str = ""
    chapters: list[dict] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)


class ExportService:
    """Generates export files in various formats."""

    def export_markdown(self, data: ExportData) -> str:
        """Generate a full Markdown document.

        Args:
            data: The export data container.

        Returns:
            Complete Markdown string.
        """
        lines = []

        # Header
        lines.append(f"# {data.video_title or 'Video Summary'}")
        lines.append("")
        if data.channel:
            lines.append(f"**Channel:** {data.channel}")
        if data.duration:
            lines.append(f"**Duration:** {data.duration}")
        if data.video_id:
            lines.append(f"**Video ID:** [{data.video_id}](https://www.youtube.com/watch?v={data.video_id})")
        lines.append(f"**Language:** {data.language}")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Summary
        if data.summary:
            lines.append("## Summary")
            lines.append("")
            lines.append(data.summary)
            lines.append("")
            lines.append("---")
            lines.append("")

        # Chapters
        if data.chapters:
            lines.append("## Chapters")
            lines.append("")
            for ch in data.chapters:
                ts = ch.get("timestamp", "00:00")
                title = ch.get("title", "Untitled")
                lines.append(f"- **{ts}** — {title}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Key Points
        if data.key_points:
            lines.append("## Key Points")
            lines.append("")
            for i, point in enumerate(data.key_points, 1):
                lines.append(f"{i}. {point}")
            lines.append("")
            lines.append("---")
            lines.append("")

        # Study Notes
        if data.study_notes:
            lines.append("## Study Notes")
            lines.append("")
            lines.append(data.study_notes)
            lines.append("")

        return "\n".join(lines)

    def export_txt(self, data: ExportData) -> str:
        """Generate a plain text document.

        Args:
            data: The export data container.

        Returns:
            Plain text string with basic formatting.
        """
        lines = []

        lines.append(data.video_title or "Video Summary")
        lines.append("=" * len(data.video_title or "Video Summary"))
        lines.append("")

        if data.channel:
            lines.append(f"Channel: {data.channel}")
        if data.duration:
            lines.append(f"Duration: {data.duration}")
        lines.append(f"Video: https://www.youtube.com/watch?v={data.video_id}")
        lines.append("")

        if data.summary:
            lines.append("SUMMARY")
            lines.append("-" * 40)
            # Strip markdown for plain text
            plain = self._strip_markdown(data.summary)
            lines.append(plain)
            lines.append("")

        if data.chapters:
            lines.append("CHAPTERS")
            lines.append("-" * 40)
            for ch in data.chapters:
                ts = ch.get("timestamp", "00:00")
                title = ch.get("title", "Untitled")
                lines.append(f"  {ts}  {title}")
            lines.append("")

        if data.key_points:
            lines.append("KEY POINTS")
            lines.append("-" * 40)
            for i, point in enumerate(data.key_points, 1):
                lines.append(f"  {i}. {point}")
            lines.append("")

        if data.study_notes:
            lines.append("STUDY NOTES")
            lines.append("-" * 40)
            plain = self._strip_markdown(data.study_notes)
            lines.append(plain)

        return "\n".join(lines)

    def export_flashcards_csv(self, notes: str) -> str:
        """Extract Q&A pairs from study notes and export as CSV for flashcards.

        Parses review questions from the notes and generates CSV with
        Question,Answer columns.

        Args:
            notes: Study notes text (may contain review questions).

        Returns:
            CSV string with Question,Answer columns.
        """
        qa_pairs = self._extract_qa(notes)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Question", "Answer"])

        for question, answer in qa_pairs:
            writer.writerow([question, answer])

        return output.getvalue()

    def export_json(self, data: ExportData) -> str:
        """Export all data as JSON.

        Args:
            data: The export data container.

        Returns:
            Pretty-printed JSON string.
        """
        output = {
            "video_id": data.video_id,
            "title": data.video_title,
            "channel": data.channel,
            "duration": data.duration,
            "language": data.language,
            "summary": data.summary,
            "chapters": data.chapters,
            "key_points": data.key_points,
            "study_notes": data.study_notes,
            "generated_at": datetime.now().isoformat(),
        }
        return json.dumps(output, ensure_ascii=False, indent=2)

    @staticmethod
    def _strip_markdown(text: str) -> str:
        """Remove common Markdown formatting for plain text export."""
        import re

        # Remove headers
        text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
        # Remove bold/italic
        text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
        text = re.sub(r"\*(.+?)\*", r"\1", text)
        text = re.sub(r"__(.+?)__", r"\1", text)
        text = re.sub(r"_(.+?)_", r"\1", text)
        # Remove links, keep text
        text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)
        # Remove horizontal rules
        text = re.sub(r"^-{3,}\s*$", "", text, flags=re.MULTILINE)
        # Clean up list markers
        text = re.sub(r"^[-*]\s+", "  • ", text, flags=re.MULTILINE)
        text = re.sub(r"^\d+\.\s+", "  ", text, flags=re.MULTILINE)

        return text.strip()

    @staticmethod
    def _extract_qa(notes: str) -> list[tuple[str, str]]:
        """Extract question-answer pairs from study notes."""
        import re

        qa_pairs = []

        # Pattern: **Q:** question ... **A:** answer
        pattern = r"\*\*[Qq]\*[:.]?\s*(.+?)\s*\*\*[Aa]\*[:.]?\s*(.+?)(?=\*\*[Qq]|\Z)"
        matches = re.findall(pattern, notes, re.DOTALL)
        for q, a in matches:
            qa_pairs.append((q.strip(), a.strip()))

        # Pattern: "Question: ... Answer:" in numbered/bullet lists
        if not qa_pairs:
            # Look for lines that start with numbers and contain question-like content
            lines = notes.splitlines()
            for line in lines:
                stripped = line.strip()
                # Match "1. Question? ... Answer: ..."
                qa_match = re.match(r"\d+\.\s*(.+?)\?\s*[-–:]?\s*(.+)", stripped)
                if qa_match:
                    qa_pairs.append((qa_match.group(1).strip() + "?", qa_match.group(2).strip()))

        # If still no Q&A found, generate from key concepts
        if not qa_pairs:
            # Create simple concept-based flashcards
            concept_pattern = r"\*\*(.+?)\*\*[:.]?\s*(.+?)(?=\*\*|$)"
            matches = re.findall(concept_pattern, notes, re.DOTALL)[:10]
            for concept, definition in matches:
                q = f"What is {concept.strip()}?"
                a = definition.strip()[:200]
                qa_pairs.append((q, a))

        return qa_pairs
