from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/bughunter"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "super_secret_jwt_key_change_in_production"
    HACKERONE_API_TOKEN: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
