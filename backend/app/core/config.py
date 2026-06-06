from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    groq_api_key: str
    chroma_persist_dir: str = "./chroma_data"
    chunk_size: int = 800
    chunk_overlap: int = 150
    retrieval_k: int = 5
    model_name: str = "llama-3.1-8b-instant"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()