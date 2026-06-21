"""FastAPI routes for the YouTube Summarization Agent."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.chapter_service import ChapterService
from services.export_service import ExportData, ExportService
from services.history_service import HistoryService
from services.notes_service import NotesError, NotesService
from services.summarization_service import SummarizationError, SummarizationService
from services.transcript_service import TranscriptError, TranscriptService
from services.translation_service import TranslationError, TranslationService
from services.youtube_service import YouTubeService

router = APIRouter()


# ── Request / Response models ──────────────────────────────────────


class SummarizeRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    level: str = Field("detailed", description="Summary level: short, detailed, bullet")
    language: str = Field("en", description="Output language: en, th")


class SummarizeResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    duration: str
    summary: str
    chapters: list = []
    key_points: list = []


class NotesRequest(BaseModel):
    url: str = Field(..., description="YouTube video URL")
    language: str = Field("en", description="Output language: en, th")


class NotesResponse(BaseModel):
    video_id: str
    title: str
    study_notes: str
    chapters: list = []


class TranslateRequest(BaseModel):
    text: str = Field(..., description="Text to translate")
    target_language: str = Field(..., description="Target language: en, th")


class TranslateResponse(BaseModel):
    translated_text: str
    target_language: str


class VideoInfoResponse(BaseModel):
    video_id: str
    title: str
    channel: str
    duration: str
    thumbnail: str
    description: str


class ExportRequest(BaseModel):
    video_id: str
    video_title: str = ""
    channel: str = ""
    duration: str = ""
    language: str = "en"
    summary: str = ""
    study_notes: str = ""
    chapters: list = []
    key_points: list = []
    format: str = Field("markdown", description="Export format: markdown, txt, json, csv")


class ExportResponse(BaseModel):
    content: str
    filename: str
    mime_type: str


class HistoryEntry(BaseModel):
    id: int
    video_id: str
    video_title: str
    channel: str
    duration: str
    language: str
    summary: str
    study_notes: str
    chapters: list = []
    key_points: list = []
    created_at: str


# ── Endpoints ──────────────────────────────────────────────────────


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "service": "youtube_sum"}


@router.get("/video-info", response_model=VideoInfoResponse)
async def get_video_info(url: str = Query(..., description="YouTube video URL")):
    """Get video metadata from a YouTube URL."""
    try:
        info = YouTubeService.get_video_info(url)
        return VideoInfoResponse(
            video_id=info.video_id,
            title=info.title,
            channel=info.channel,
            duration=info.duration,
            thumbnail=info.thumbnail,
            description=info.description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_video(request: SummarizeRequest):
    """Fetch transcript and generate a summary for a YouTube video."""
    # Validate URL
    if not YouTubeService.validate_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    video_id = YouTubeService.extract_video_id(request.url)

    # Check history cache
    cached = HistoryService.get_by_video_id(video_id)
    if cached and cached.get("summary"):
        return SummarizeResponse(
            video_id=cached["video_id"],
            title=cached.get("video_title", ""),
            channel=cached.get("channel", ""),
            duration=cached.get("duration", ""),
            summary=cached["summary"],
            chapters=cached.get("chapters", []),
            key_points=cached.get("key_points", []),
        )

    # Get video info
    try:
        info = YouTubeService.get_video_info(request.url)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Fetch transcript
    try:
        transcript = TranscriptService().get_transcript(request.url)
    except TranscriptError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Generate summary
    try:
        summary = SummarizationService().summarize(
            transcript, level=request.level, language=request.language
        )
    except SummarizationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Get chapters
    chapters = []
    try:
        chapters = ChapterService().get_chapters(request.url, transcript)
    except Exception:
        pass

    # Extract key points from summary (simple bullet extraction)
    key_points = []
    for line in summary.splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            point = stripped[2:].strip()
            if point:
                key_points.append(point)
        elif stripped.startswith(("1. ", "2. ", "3. ", "4. ", "5. ")):
            point = stripped[3:].strip()
            if point:
                key_points.append(point)

    # Save to history
    try:
        HistoryService.save(
            video_id=video_id,
            video_title=info.title,
            channel=info.channel,
            duration=info.duration,
            language=request.language,
            summary=summary,
            chapters=chapters,
            key_points=key_points,
        )
    except Exception:
        pass

    return SummarizeResponse(
        video_id=video_id,
        title=info.title,
        channel=info.channel,
        duration=info.duration,
        summary=summary,
        chapters=chapters,
        key_points=key_points,
    )


@router.post("/notes", response_model=NotesResponse)
async def generate_notes(request: NotesRequest):
    """Generate structured study notes for a YouTube video."""
    if not YouTubeService.validate_url(request.url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    video_id = YouTubeService.extract_video_id(request.url)

    # Get video info
    try:
        info = YouTubeService.get_video_info(request.url)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Fetch transcript
    try:
        transcript = TranscriptService().get_transcript(request.url)
    except TranscriptError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # Generate notes
    try:
        notes = NotesService().generate_notes(transcript, language=request.language)
    except NotesError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    # Get chapters
    chapters = []
    try:
        chapters = ChapterService().get_chapters(request.url, transcript)
    except Exception:
        pass

    # Save to history
    try:
        HistoryService.save(
            video_id=video_id,
            video_title=info.title,
            channel=info.channel,
            duration=info.duration,
            language=request.language,
            study_notes=notes,
            chapters=chapters,
        )
    except Exception:
        pass

    return NotesResponse(
        video_id=video_id,
        title=info.title,
        study_notes=notes,
        chapters=chapters,
    )


@router.post("/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """Translate text between English and Thai."""
    try:
        translated = TranslationService().translate(request.text, request.target_language)
        return TranslateResponse(
            translated_text=translated,
            target_language=request.target_language,
        )
    except TranslationError as exc:
        raise HTTPException(status_code=502, detail=str(exc))


@router.post("/export", response_model=ExportResponse)
async def export_content(request: ExportRequest):
    """Export summary/notes in various formats."""
    data = ExportData(
        video_id=request.video_id,
        video_title=request.video_title,
        channel=request.channel,
        duration=request.duration,
        language=request.language,
        summary=request.summary,
        study_notes=request.study_notes,
        chapters=request.chapters,
        key_points=request.key_points,
    )

    exporter = ExportService()
    fmt = request.format.lower()

    if fmt == "markdown":
        content = exporter.export_markdown(data)
        filename = f"{request.video_id}_summary.md"
        mime = "text/markdown"
    elif fmt == "txt":
        content = exporter.export_txt(data)
        filename = f"{request.video_id}_summary.txt"
        mime = "text/plain"
    elif fmt == "json":
        content = exporter.export_json(data)
        filename = f"{request.video_id}_summary.json"
        mime = "application/json"
    elif fmt == "csv":
        content = exporter.export_flashcards_csv(request.study_notes)
        filename = f"{request.video_id}_flashcards.csv"
        mime = "text/csv"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {fmt}")

    return ExportResponse(content=content, filename=filename, mime_type=mime)


@router.get("/history")
async def get_history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    """Get summary history."""
    entries = HistoryService.get_all(limit=limit, offset=offset)
    total = HistoryService.count()
    return {"total": total, "entries": entries}


@router.delete("/history/{entry_id}")
async def delete_history(entry_id: int):
    """Delete a history entry."""
    deleted = HistoryService.delete(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted", "id": entry_id}


@router.delete("/history")
async def clear_history():
    """Clear all history."""
    count = HistoryService.clear_all()
    return {"status": "cleared", "count": count}
