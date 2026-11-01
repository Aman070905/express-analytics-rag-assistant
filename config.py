from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]

class Settings(BaseSettings):
    gemini_api_key: str = Field(default="", validation_alias="GEMINI_API_KEY")
    chat_model: str = "gemini-2.5-flash"
    embedding_model: str = "models/gemini-embedding-001"
    chroma_dir: str = str(PROJECT_ROOT / "chroma_db")
    collection_name: str = "technical_docs"
    chunk_size: int = 900
    chunk_overlap: int = 150
    retrieval_k: int = 6
    max_retries: int = 1
    max_upload_mb: int = 15
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
