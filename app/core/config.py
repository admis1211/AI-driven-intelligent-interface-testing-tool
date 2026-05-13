from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "AI驱动智能接口测试工具"
    APP_VERSION: str = "1.0.0"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_BASE: str = "https://api.siliconflow.cn/v1"
    OPENAI_MODEL: str = "deepseek-ai/DeepSeek-V3.2"
    OPENAI_TEMPERATURE: float = 0.7

    # Vector store configuration
    EMBEDDING_MODEL: str = "BAAI/bge-large-zh-v1.5"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    VECTOR_STORE_DIR: str = "./vectorstore"
    FAISS_INDEX_NAME: str = "faiss_index"

    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_STORE_DIR, exist_ok=True)
