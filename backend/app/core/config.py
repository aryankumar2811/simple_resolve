from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    DATABASE_URL: str = "postgresql://simpleresolved:simpleresolved@localhost:5432/simpleresolved"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"


settings = Settings()
