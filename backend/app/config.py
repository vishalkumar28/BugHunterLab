from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "BugHunterLab"
    api_prefix: str = "/api"
    database_url: str = f"sqlite:///{ROOT_DIR / 'database' / 'bughunterlab.db'}"
    tools_dir: Path = ROOT_DIR / "tools"
    evidence_dir: Path = ROOT_DIR / "database" / "evidence"
    allowed_origins: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(env_prefix="BUGHUNTERLAB_", extra="ignore")


settings = Settings()