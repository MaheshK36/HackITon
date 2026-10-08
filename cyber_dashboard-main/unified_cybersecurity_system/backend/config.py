"""Environment-backed settings with safe local-demo defaults."""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv("CYBER_MODE", "DEMO").upper()
    cors_origins: tuple[str, ...] = tuple(
        value.strip() for value in os.getenv("CYBER_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8000,http://127.0.0.1:8000").split(",") if value.strip()
    )
    require_api_key: bool = os.getenv("CYBER_REQUIRE_API_KEY", "false").lower() == "true"
    api_key: str = os.getenv("CYBER_API_KEY", "")
    max_event_bytes: int = int(os.getenv("CYBER_MAX_EVENT_BYTES", "16384"))


settings = Settings()
