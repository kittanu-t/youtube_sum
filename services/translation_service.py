"""Translation service — translate text between English and Thai via LLM."""

from typing import Optional

import httpx
from loguru import logger

from app.config import settings


_SYSTEM_EN_TO_TH = """You are a professional translator. Translate the following text from English to Thai (ภาษาไทย). Maintain the original meaning, tone, and formatting (including Markdown). Output ONLY the translation, no explanations."""

_SYSTEM_TH_TO_EN = """You are a professional translator. Translate the following text from Thai (ภาษาไทย) to English. Maintain the original meaning, tone, and formatting (including Markdown). Output ONLY the translation, no explanations."""


class TranslationError(Exception):
    """Raised when translation fails."""
    pass


class TranslationService:
    """Translates text between English and Thai using the configured LLM provider."""

    def __init__(self, model: Optional[str] = None):
        self.model = model or settings.ollama_model
        self._client = httpx.Client(timeout=300)

    def translate(self, text: str, target_language: str) -> str:
        """Translate text to the target language.

        Args:
            text: The text to translate.
            target_language: Target language code ("en" or "th").

        Returns:
            Translated text.

        Raises:
            TranslationError: If translation fails.
        """
        if not text.strip():
            return ""

        logger.info("Translating {} chars to {}", len(text), target_language)

        if target_language == "th":
            system = _SYSTEM_EN_TO_TH
        elif target_language == "en":
            system = _SYSTEM_TH_TO_EN
        else:
            raise TranslationError(f"Unsupported target language: {target_language}")

        provider = settings.llm_provider.lower()
        if provider == "ollama":
            return self._call_ollama(system, text)
        elif provider == "openai":
            return self._call_openai(system, text)
        elif provider == "gemini":
            return self._call_gemini(system, text)
        else:
            raise TranslationError(f"Unknown LLM provider: {provider}")

    def _call_ollama(self, system: str, text: str) -> str:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
        payload = {
            "model": self.model,
            "system": system,
            "prompt": text,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 4096},
        }
        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
        except httpx.HTTPError as exc:
            raise TranslationError(f"Ollama request failed: {exc}") from exc

    def _call_openai(self, system: str, text: str) -> str:
        if not settings.openai_api_key:
            raise TranslationError("OpenAI API key not configured")
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
        payload = {
            "model": settings.openai_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            "max_tokens": 4096,
            "temperature": 0.2,
        }
        try:
            resp = self._client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except httpx.HTTPError as exc:
            raise TranslationError(f"OpenAI request failed: {exc}") from exc

    def _call_gemini(self, system: str, text: str) -> str:
        if not settings.gemini_api_key:
            raise TranslationError("Gemini API key not configured")
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": f"{system}\n\n{text}"}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 4096},
        }
        try:
            resp = self._client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except httpx.HTTPError as exc:
            raise TranslationError(f"Gemini request failed: {exc}") from exc
