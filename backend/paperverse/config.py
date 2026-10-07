from functools import lru_cache
import os
from pathlib import Path


class Settings:
    def __init__(self) -> None:
        self.data_dir = Path(os.getenv("PAPERVERSE_DATA_DIR", "./data")).resolve()
        self.database_url = os.getenv("PAPERVERSE_DATABASE_URL", "sqlite:///./data/paperverse.db")
        self.redis_url = os.getenv("PAPERVERSE_REDIS_URL", "redis://localhost:6379/0")
        self.queue_mode = os.getenv("PAPERVERSE_QUEUE_MODE", "local").lower()
        self.max_upload_bytes = int(os.getenv("PAPERVERSE_MAX_UPLOAD_MB", "50")) * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()
