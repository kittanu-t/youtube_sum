"""Summarization service — chunk transcripts and summarize via LLM."""

import httpx
from loguru import logger

from app.config import settings

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

_SYSTEM_SUMMARY = """You are an expert summarizer. Given a YouTube video transcript, produce a clear, well-structured summary in the requested format. Use Markdown. Be concise but thorough."""

_SYSTEM_CHUNK = """You are an expert at summarizing text. Summarize the following portion of a YouTube video transcript. Focus on the key points, ideas, and facts discussed. Write in clear, plain language. Do not add commentary."""

_SYSTEM_SYNTHESIZE = """You are an expert editor. You are given multiple partial summaries of a single YouTube video. Synthesize them into one coherent, well-structured final summary. Merge overlapping points, preserve important details, and maintain logical flow. Use Markdown formatting."""

_PROMPT_SHORT = """Summarize this video transcript in a short format:

1. **Overview**: One paragraph (3-5 sentences) summarizing the entire video.
2. **Key Takeaways**: 5-7 bullet points of the most important ideas.

Transcript:
{text}"""

_PROMPT_DETAILED = """Summarize this video transcript in detail:

1. **Overview**: A comprehensive 2-3 paragraph summary.
2. **Key Sections**: Break the video into logical sections with headings. Summarize each section in 2-3 sentences.
3. **Key Takeaways**: 8-12 bullet points of the most important ideas and insights.
4. **Notable Quotes**: Any memorable or impactful quotes (if present).

Transcript:
{text}"""

_PROMPT_BULLET = """Summarize this video transcript using only bullet points:

- Extract all important facts, ideas, arguments, and insights.
- Use nested sub-bullets where appropriate.
- Group related points under bold headings.
- Include at least 15-25 bullet points.

Transcript:
{text}"""


class SummarizationError(Exception):
    """Raised when summarization fails."""

    pass


class SummarizationService:
    """Summarizes text using the configured LLM provider (Ollama, OpenAI, or Gemini)."""

    def __init__(self, model: str | None = None):
        self.model = model or settings.ollama_base_url
        self._client = httpx.Client(timeout=300)

    def summarize(
        self,
        text: str,
        level: str = "detailed",
        language: str = "en",
    ) -> str:
        """Summarize text at the given level.

        Args:
            text: The transcript or text to summarize.
            level: One of "short", "detailed", "bullet".
            language: Output language code ("en" or "th").

        Returns:
            Markdown-formatted summary string.

        Raises:
            SummarizationError: If the LLM call fails.
        """
        if not text.strip():
            raise SummarizationError("Cannot summarize empty text")

        logger.info("Summarizing {} chars at '{}' level in {}", len(text), level, language)

        # Chunk if the text is long
        chunks = self._chunk_text(text)
        logger.info("Split into {} chunks", len(chunks))

        if len(chunks) == 1:
            return self._summarize_single(chunks[0], level, language)

        # Multi-chunk: summarize each, then synthesize
        partials = []
        for i, chunk in enumerate(chunks):
            logger.debug("Summarizing chunk {}/{}", i + 1, len(chunks))
            partial = self._call_llm(
                system=_SYSTEM_CHUNK,
                user=chunk,
            )
            if partial:
                partials.append(partial)

        combined = "\n\n".join(partials)
        return self._synthesize(combined, level, language)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _summarize_single(self, text: str, level: str, language: str) -> str:
        """Summarize a single chunk."""
        prompt_map = {
            "short": _PROMPT_SHORT,
            "detailed": _PROMPT_DETAILED,
            "bullet": _PROMPT_BULLET,
        }
        template = prompt_map.get(level, _PROMPT_DETAILED)

        lang_instruction = ""
        if language == "th":
            lang_instruction = "\n\nWrite the entire summary in Thai (ภาษาไทย)."

        user_prompt = template.format(text=text) + lang_instruction
        return self._call_llm(system=_SYSTEM_SUMMARY, user=user_prompt)

    def _synthesize(self, partials: str, level: str, language: str) -> str:
        """Synthesize partial summaries into a final summary."""
        lang_instruction = ""
        if language == "th":
            lang_instruction = "\n\nWrite the entire summary in Thai (ภาษาไทย)."

        user_prompt = (
            f"Synthesize these partial summaries into one final {level} summary.\n\n"
            + lang_instruction
            + "\n\nPartial Summaries:\n\n"
            + partials
        )
        return self._call_llm(system=_SYSTEM_SYNTHESIZE, user=user_prompt)

    def _call_llm(self, system: str, user: str) -> str:
        """Call the configured LLM provider."""
        provider = settings.llm_provider.lower()

        if provider == "ollama":
            return self._call_ollama(system, user)
        elif provider == "openai":
            return self._call_openai(system, user)
        elif provider == "gemini":
            return self._call_gemini(system, user)
        else:
            raise SummarizationError(f"Unknown LLM provider: {provider}")

    def _call_ollama(self, system: str, user: str) -> str:
        """Call Ollama's /api/generate endpoint."""
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": settings.ollama_model,
            "system": system,
            "prompt": user,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 4096,
            },
        }

        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
        except httpx.HTTPError as exc:
            logger.error("Ollama request failed: {}", exc)
            raise SummarizationError(f"Ollama request failed: {exc}") from exc

    def _call_openai(self, system: str, user: str) -> str:
        """Call OpenAI Chat Completions API."""
        if not settings.openai_api_key:
            raise SummarizationError("OpenAI API key not configured")

        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": 4096,
            "temperature": 0.3,
        }

        try:
            resp = self._client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPError as exc:
            logger.error("OpenAI request failed: {}", exc)
            raise SummarizationError(f"OpenAI request failed: {exc}") from exc

    def _call_gemini(self, system: str, user: str) -> str:
        """Call Gemini API."""
        if not settings.gemini_api_key:
            raise SummarizationError("Gemini API key not configured")

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 4096,
            },
        }

        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise SummarizationError("Gemini returned no candidates")
            parts = candidates[0]["content"]["parts"]
            return parts[0]["text"].strip()
        except httpx.HTTPError as exc:
            logger.error("Gemini request failed: {}", exc)
            raise SummarizationError(f"Gemini request failed: {exc}") from exc

    @staticmethod
    def _chunk_text(text: str) -> list[str]:
        """Split text into overlapping chunks."""
        chunk_size = settings.chunk_size
        overlap = settings.chunk_overlap

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            # Try to break at a sentence boundary
            if end < len(text):
                # Look for a period, question mark, or newline near the boundary
                for sep in [". ", "? ", "! ", "\n"]:
                    pos = text.rfind(sep, start, end)
                    if pos != -1 and pos > start + chunk_size // 2:
                        end = pos + len(sep)
                        break
            chunks.append(text[start:end])
            start = end - overlap

        return chunks
