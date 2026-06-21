"""Study notes service — generate structured study notes from transcripts."""

import httpx
from loguru import logger

from app.config import settings

_SYSTEM_PROMPT = """You are an expert educator and note-taker. Given a YouTube video transcript, generate comprehensive, well-structured study notes in Markdown format. Be thorough, clear, and educational."""

_USER_TEMPLATE = """Generate detailed study notes for this video transcript.

Include ALL of the following sections:

## 📋 Overview
A 2-3 paragraph summary of the video's main topic and purpose.

## 🧠 Key Concepts
Define and explain the 5-10 most important concepts, theories, or ideas discussed. Each concept should have a bold name followed by a clear explanation.

## 📌 Important Points
A numbered list of the most critical facts, arguments, or insights (at least 10 points).

## ⏱️ Timeline
Break the video into logical segments with approximate timestamps or sequence markers. For each segment, provide a 1-sentence summary.

## ✅ Actionable Takeaways
Specific, actionable advice or steps the viewer can apply (5-8 bullet points).

## ❓ Questions for Review
Thought-provoking questions to test understanding of the material (5-7 questions). Include answers in collapsible details tags.

## 📚 Vocabulary
Key terms, jargon, or technical words used in the video with simple definitions (at least 5 terms).

## 🔗 Further Reading
Suggest 3-5 related topics, books, or resources for deeper learning.

{lang_instruction}

Transcript:
{text}"""


class NotesError(Exception):
    """Raised when study note generation fails."""

    pass


class NotesService:
    """Generates structured study notes from video transcripts."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.ollama_model
        self._client = httpx.Client(timeout=300)

    def generate_notes(
        self,
        transcript: str,
        language: str = "en",
    ) -> str:
        """Generate structured study notes from a transcript.

        Args:
            transcript: The video transcript text.
            language: Output language code ("en" or "th").

        Returns:
            Markdown-formatted study notes.

        Raises:
            NotesError: If note generation fails.
        """
        if not transcript.strip():
            raise NotesError("Cannot generate notes from empty transcript")

        logger.info("Generating study notes ({} chars, lang={})", len(transcript), language)

        # Chunk if needed
        chunks = self._chunk_text(transcript)
        if len(chunks) == 1:
            return self._generate_single(chunks[0], language)

        # Multi-chunk: generate notes per chunk, then merge
        partial_notes = []
        for i, chunk in enumerate(chunks):
            logger.debug("Generating notes for chunk {}/{}", i + 1, len(chunks))
            notes = self._generate_single(chunk, language)
            if notes:
                partial_notes.append(notes)

        return self._merge_notes(partial_notes, language)

    def _generate_single(self, text: str, language: str) -> str:
        """Generate notes for a single chunk."""
        lang_instruction = (
            "\n\nWrite the entire response in Thai (ภาษาไทย)." if language == "th" else ""
        )
        user_prompt = _USER_TEMPLATE.format(text=text, lang_instruction=lang_instruction)
        return self._call_llm(user_prompt)

    def _merge_notes(self, partials: list[str], language: str) -> str:
        """Merge partial notes into a single document."""
        lang_instruction = (
            " Write the entire response in Thai (ภาษาไทย)." if language == "th" else ""
        )
        user_prompt = (
            "Merge these partial study notes into one comprehensive, well-organized document. "
            "Remove duplicates, combine related sections, and maintain all section headings. "
            + lang_instruction
            + "\n\n"
            + "\n\n---\n\n".join(partials)
        )
        return self._call_llm(user_prompt)

    def _call_llm(self, user_prompt: str) -> str:
        """Call the configured LLM provider."""
        provider = settings.llm_provider.lower()

        if provider == "ollama":
            return self._call_ollama(user_prompt)
        elif provider == "openai":
            return self._call_openai(user_prompt)
        elif provider == "gemini":
            return self._call_gemini(user_prompt)
        else:
            raise NotesError(f"Unknown LLM provider: {provider}")

    def _call_ollama(self, user_prompt: str) -> str:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "system": _SYSTEM_PROMPT,
            "prompt": user_prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 4096},
        }
        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except httpx.HTTPError as exc:
            raise NotesError(f"Ollama request failed: {exc}") from exc

    def _call_openai(self, user_prompt: str) -> str:
        if not settings.openai_api_key:
            raise NotesError("OpenAI API key not configured")
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 4096,
            "temperature": 0.3,
        }
        try:
            resp = self._client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except httpx.HTTPError as exc:
            raise NotesError(f"OpenAI request failed: {exc}") from exc

    def _call_gemini(self, user_prompt: str) -> str:
        if not settings.gemini_api_key:
            raise NotesError("Gemini API key not configured")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": f"{_SYSTEM_PROMPT}\n\n{user_prompt}"}]}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
        }
        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except httpx.HTTPError as exc:
            raise NotesError(f"Gemini request failed: {exc}") from exc

    @staticmethod
    def _chunk_text(text: str) -> list[str]:
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap
        if len(text) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            if end < len(text):
                for sep in [". ", "? ", "! ", "\n"]:
                    pos = text.rfind(sep, start, end)
                    if pos != -1 and pos > start + chunk_size // 2:
                        end = pos + len(sep)
                        break
            chunks.append(text[start:end])
            start = end - overlap
        return chunks
