from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str = "postgresql://simpleresolved:simpleresolved@localhost:5432/simpleresolved"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def fix_db_url(cls, v: str) -> str:
        # Railway may provide postgres:// which SQLAlchemy 2.x doesn't accept
        if v.startswith("postgres://"):
            v = v.replace("postgres://", "postgresql://", 1)
        return v


settings = Settings()
