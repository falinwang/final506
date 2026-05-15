from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ticketmaster_api_key: str = ""
    cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
