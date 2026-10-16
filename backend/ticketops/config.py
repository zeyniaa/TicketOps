from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TICKETOPS_", env_file=str(ROOT / ".env"), extra="ignore")
    database_url: str = "sqlite:///./ticketops.db"
    ollama_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:4b"
    llm_enabled: bool = True
    llm_timeout: float = 180
    model_path: str = str(ROOT / "ml/artifacts/baseline.joblib")
    manifest_path: str = str(ROOT / "ml/artifacts/manifest.json")
    allowed_origins: str = "http://127.0.0.1:5178,http://localhost:5178,http://127.0.0.1:8018,http://localhost:8018"
    secure_cookies: bool = False
    worker_lease_seconds: int = 480

settings = Settings()
