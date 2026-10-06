import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "RAGForge"
    APP_PORT: int = 8000
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./ragforge.db"

    # JWT Authentication
    JWT_SECRET: str = "ragforge_dev_jwt_secret_key_minimum_32_chars_long_12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://localhost:80",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, str) and v.startswith("["):
            import json
            try:
                return json.loads(v)
            except Exception:
                return [v]
        elif isinstance(v, list):
            return v
        return []

    # Storage
    UPLOAD_DIR: str = "./storage/uploads"
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB

    # RAG parameters
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.65

    # Embeddings (gemini, openai)
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_DIMENSIONS: int = 768
    EMBEDDING_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    @property
    def effective_gemini_api_key(self) -> str:
        return self.GEMINI_API_KEY or self.EMBEDDING_API_KEY or self.LLM_API_KEY or ""

    # LLM (gemini, openai, mock)
    LLM_PROVIDER: str = "gemini"
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_API_KEY: str = ""
    LLM_TEMPERATURE: float = 0.2
    LLM_MAX_TOKENS: int = 1024

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
