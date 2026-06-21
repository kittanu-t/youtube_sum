"""Application configuration via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Loads configuration from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM Provider ---
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:latest"

    # --- Optional: OpenAI ---
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"

    # --- Optional: Gemini ---
    gemini_api_key: str = ""

    # --- App Settings ---
    database_path: Path = Path("./youtube_sum.db")
    output_dir: Path = Path("./output")
    default_language: str = "en"
    max_transcript_length: int = 60000
    chunk_size: int = 8000
    chunk_overlap: int = 500

    # --- Server ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    streamlit_port: int = 8501


settings = Settings()
